"""
Personal Career Assistant: free-form chat about anything placement related.

Every answer is grounded in two kinds of context:
  * the student's own data (profile, skills, projects, gaps, roadmap, recent results)
  * CareerPilot's sourced content, found by retrieval (app/services/retrieval.py)

With an AI key: the model answers any question. Company facts must come from the
retrieved sources (cited as [n]); if the sources do not cover it, the model says so.
General concepts (e.g. "what is normalisation") may come from the model's own knowledge
and are marked as general explanations.

Without an AI key: we still answer the free-text question honestly from the same
data: the best matching sourced content and the student's own records, with links,
and we say clearly that AI answers are not switched on.
"""
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (CareerRecommendation, Company, MockInterview, Project, Roadmap, Skill, SkillGapReport,
                        StudentProfile, User)
from app.services import llm
from app.services.retrieval import Doc, mentioned_companies, public_index
from app.services.roles import role_title

PERSONAL = re.compile(r"\b(my|me|mine|am i|should i|for me|do i need)\b", re.I)
MIN_SCORE = 2.5


def context(db: Session, user_id: int) -> dict:
    user = db.get(User, user_id)
    prof = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))
    company = db.get(Company, prof.target_company_id) if prof and prof.target_company_id else None
    rm = db.scalar(select(Roadmap).where(Roadmap.user_id == user_id, Roadmap.is_active.is_(True)))
    nxt = [t for t in rm.tasks if t.status == "todo"][:5] if rm else []
    gap = db.scalar(select(SkillGapReport).where(SkillGapReport.user_id == user_id).order_by(SkillGapReport.id.desc()))
    recs = db.scalars(select(CareerRecommendation).where(CareerRecommendation.user_id == user_id)
                      .order_by(CareerRecommendation.match_pct.desc()).limit(3)).all()
    skills = db.scalars(select(Skill).where(Skill.user_id == user_id)).all()
    projects = db.scalars(select(Project).where(Project.user_id == user_id)).all()
    last_iv = db.scalar(select(MockInterview).where(MockInterview.user_id == user_id, MockInterview.status == "completed")
                        .order_by(MockInterview.id.desc()))
    return {"user": user, "profile": prof, "company": company, "next": nxt, "gap": gap, "recs": recs,
            "skills": skills, "projects": projects, "last_interview": last_iv, "roadmap": rm}


def profile_docs(ctx: dict) -> list[Doc]:
    docs = []
    if ctx["skills"]:
        docs.append(Doc("profile", "Your skills (from your resume and practice)",
                        "my skills resume strengths " + " ".join(f"{s.name} {s.level}" for s in ctx["skills"]),
                        href="/skills/", extra={"lines": [f"{s.name}: {s.level} ({s.confidence} confidence)" for s in ctx["skills"][:25]]}))
    for p in ctx["projects"]:
        docs.append(Doc("profile", f"Your project: {p.name}", f"my project resume {p.name} {p.description} {' '.join(p.technologies or [])}",
                        href="/resume/", extra={"lines": [p.description[:300], "Tech: " + ", ".join(p.technologies or [])]}))
    if ctx["gap"]:
        top = [i for i in ctx["gap"].items if i["priority"] in ("high", "medium")][:8]
        s = ctx["gap"].summary
        docs.append(Doc("profile", f"Your latest gap analysis ({s['role']}{' at ' + s['company'] if s.get('company') else ''})",
                        "my gaps weak missing improve skill gap study prepare focus target company role need learn " + " ".join(i["skill"] for i in top), href="/gaps/",
                        extra={"lines": [f"{i['skill']}: {i['priority']} priority ({i['status']})" for i in top]}))
    if ctx["next"]:
        docs.append(Doc("profile", "Your next roadmap tasks", "my plan roadmap next study today schedule tasks " +
                        " ".join(t.topic for t in ctx["next"]), href="/roadmap/",
                        extra={"lines": [f"{t.topic} ({t.est_minutes} min, {t.priority} priority, due {t.due_date:%d %b})" for t in ctx["next"]]}))
    if ctx["recs"]:
        docs.append(Doc("profile", "Roles that fit your evidence", "my roles career suit job recommendation " +
                        " ".join(r.title for r in ctx["recs"]), href="/careers/",
                        extra={"lines": [f"{r.title}: {r.match_pct:.0f}% match" for r in ctx["recs"]]}))
    if ctx["last_interview"] and ctx["last_interview"].report:
        rep = ctx["last_interview"].report.content
        docs.append(Doc("profile", "Your latest mock interview", "my mock interview score feedback result weak " +
                        " ".join(rep.get("revision_topics", [])), href=f"/interview/session/?id={ctx['last_interview'].id}",
                        extra={"lines": [f"Overall {rep.get('overall')}/5"] + rep.get("improvements", [])[:3]}))
    return docs


def _render(d: Doc) -> str:
    x = d.extra
    if d.kind == "question":
        ans = (x.get("answer") or "").strip()
        if ans.lower() in ("see the solution.", "see the solution") or not ans:
            ans = "Open it in Practice to see the full solution" + (" and run your code against the tests." if x.get("runnable") else ".")
        exp = f" {x['explanation']}" if x.get("explanation") and not x.get("runnable") else ""
        return f"{d.title} ({d.label})\nQ: {x['question'][:500]}\nA: {ans[:600]}{exp[:300]}"
    if d.kind == "stage":
        parts = [f"{d.title} ({d.label})", x.get("what", "")[:400]]
        if x.get("format"):
            parts.append("Format: " + "; ".join(x["format"][:3]))
        if x.get("study"):
            parts.append("Study: " + ", ".join(x["study"][:8]))
        return "\n".join(p for p in parts if p)
    if d.kind == "role":
        facts = "; ".join(x.get("facts", [])[:4])
        return f"{d.title} ({d.label or 'see source'})\nSkills: {', '.join(x.get('skills', [])[:10])}" + (f"\nReported: {facts}" if facts else "")
    if d.kind == "resource":
        return f"Learning resource: {d.title} ({x.get('provider')}, about {x.get('minutes')} min)"
    if d.kind == "profile":
        return d.title + ":\n" + "\n".join(f"- {ln}" for ln in x.get("lines", []) if ln)
    return f"{d.title}\n{d.text[:400]}"


def _short(text: str, n: int) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0].rstrip(",;:") + "..."


def _render_brief(d: Doc) -> str:
    """Compact version for the no-AI answer: bold title, two short lines, the link sits in the citations."""
    x = d.extra
    head = f"**{d.title}**" + (f" ({d.label})" if d.label and d.kind != "profile" else "")
    if d.kind == "question":
        ans = (x.get("answer") or "").strip()
        if ans.lower().startswith("see the solution") or not ans:
            ans = "Open it in Practice for the full solution" + (" and to run your code." if x.get("runnable") else ".")
        return f"{head}\nQ: {_short(x['question'], 220)}\nA: {_short(ans, 260)}"
    if d.kind == "stage":
        lines = [head, _short(x.get("what", ""), 240)]
        if x.get("study"):
            lines.append("Study: " + ", ".join(x["study"][:6]))
        return "\n".join(ln for ln in lines if ln)
    if d.kind == "profile":
        return f"**{d.title}**\n" + "\n".join(f"- {ln}" for ln in x.get("lines", [])[:6] if ln)
    if d.kind in ("role", "resource"):
        return _render(d)
    words = (d.text or "").split()
    if len(words) > 1 and words[0] == words[1]:
        words = words[1:]
    return f"{head}\n{_short(' '.join(words), 260)}"


def _cite(docs: list[Doc]) -> list[dict]:
    out, seen = [], set()
    for d in docs:
        key = (d.title, d.url, d.href)
        if key in seen:
            continue
        seen.add(key)
        out.append({"title": d.title, "label": d.label, "url": d.url, "href": d.href, "kind": d.kind})
    return out


def retrieve_for(db: Session, msg: str, ctx: dict) -> tuple[list[Doc], list[Doc]]:
    """Returns (public docs, personal docs) relevant to the message."""
    from app.services.retrieval import Index
    companies = mentioned_companies(db, msg)
    if not companies and ctx["company"] and re.search(r"\b(company|target|drive|round|stage|test|interview)\b", msg, re.I):
        companies = {ctx["company"].name}
    idx = public_index(db)
    hits = idx.search(msg, k=8, companies=companies or None)
    if companies:
        hits = [h for h in hits if h[1].company in companies or h[1].company is None] or hits
    public = [d for s, d in hits if s >= MIN_SCORE][:5]
    pdocs = profile_docs(ctx)
    personal = []
    if pdocs and PERSONAL.search(msg):
        p_hits = Index(pdocs).search(msg, k=3)
        personal = [d for s, d in p_hits if s > 0.5]
        if re.search(r"\b(study|prepare|focus|learn|work on|next)\b", msg, re.I):
            first = [d for d in pdocs if d.title.startswith(("Your latest gap analysis", "Your next roadmap tasks"))]
            personal = first + [d for d in personal if d not in first]
        if PERSONAL.search(msg) and not personal and re.search(r"resume|skill|project|plan|gap|next|role|weak|ready|study|prepare|focus|improve|target", msg, re.I):
            personal = pdocs[:2]
    return public, personal


SMALL_TALK = re.compile(r"^\s*(hi|hello|hey|hii+|good (morning|afternoon|evening)|thanks?|thank you|ok(ay)?|cool|bye)\b[\s!.?]*$", re.I)


def small_talk(msg: str, ctx: dict) -> str | None:
    if not SMALL_TALK.match(msg):
        return None
    if re.match(r"\s*(thanks?|thank you|ok|okay|cool|bye)", msg, re.I):
        return "Happy to help. Ask me anything else about your preparation whenever you like."
    user = ctx.get("user")
    name = ((getattr(user, "full_name", "") or "").split(" ") or [""])[0]
    return (f"Hi{' ' + name if name else ''}! Ask me anything about placement prep: a concept (\"what is normalisation?\"), "
            "a company's rounds (\"what does the Infosys online test cover?\"), your skill gaps, or how to explain your projects.")


def rules_answer(msg: str, ctx: dict, public: list[Doc], personal: list[Doc]) -> tuple[str, list[Doc]]:
    intro = "Here is what CareerPilot's sourced guides, question bank and your data say (AI answers are not switched on for this site yet):"
    if not public and not personal:
        return ("I could not find anything about that in CareerPilot's sources or your profile (AI answers are not switched on for this site yet). "
                "Try a topic or company name (for example \"SQL joins\", \"deadlock\" or \"Infosys online test\"). "
                "Once the site admin adds an AI key, I can answer general questions like this one directly."), []
    blocks, used = [], []
    for d in personal[:2]:
        blocks.append(_render_brief(d))
        used.append(d)
    for d in public[: 2 if personal else 3]:
        blocks.append(_render_brief(d))
        used.append(d)
    note = ""
    if any(d.company for d in public):
        note = "\n\nHiring processes change by year, role and college. Check the linked source before relying on a number."
    return intro + "\n\n" + "\n\n".join(blocks) + note, used


def llm_answer(msg: str, history: list[dict], ctx: dict, public: list[Doc], personal: list[Doc]) -> tuple[str, list[Doc]]:
    u, prof = ctx["user"], ctx["profile"]
    me = [f"Name: {u.full_name}" if u else "",
          f"Education: {prof.degree} {prof.branch}, {prof.college}, graduating {prof.graduation_year}" if prof and prof.degree else "",
          f"Target: {role_title(prof.target_role_key) if prof and prof.target_role_key else 'not chosen'}"
          f" at {ctx['company'].name if ctx['company'] else 'no company chosen'}",
          "Skills: " + ", ".join(f"{s.name} ({s.level})" for s in ctx["skills"][:30]) if ctx["skills"] else "Skills: none recorded yet",
          "Projects: " + "; ".join(f"{p.name} [{', '.join(p.technologies or [])}]" for p in ctx["projects"][:5]) if ctx["projects"] else "Projects: none recorded yet"]
    if ctx["gap"]:
        me.append("Top gaps: " + "; ".join(f"{i['skill']} ({i['priority']})" for i in ctx["gap"].items[:10]))
    if ctx["next"]:
        me.append("Next roadmap tasks: " + "; ".join(t.topic for t in ctx["next"]))
    sources = [f"[{n}] {_render(d)}" + (f" (source: {d.url})" if d.url else "") for n, d in enumerate(public, 1)]
    system = (
        "You are CareerPilot's career assistant: a friendly, direct placement mentor for an Indian college student. "
        "Answer ANY question the student asks (technical concepts, coding help, interview prep, study plans, their resume, companies). "
        "Rules: 1) For facts about a specific company (rounds, patterns, cutoffs, packages, eligibility, previously asked questions) "
        "use ONLY the numbered sources below and cite them like [1]. If they do not cover it, say you do not have verified "
        "information for that and suggest the official careers page. Never invent company facts or numbers. "
        "2) For general concepts you may use your own knowledge. 3) For anything about the student use only the profile below; "
        "if something is missing, say so. 4) Plain English, short paragraphs or short '- ' lists. You may use **bold**, `inline code` and ``` code blocks. No tables, no headings, no em dashes. Keep it under 250 words unless the student asks for more.\n\n"
        "STUDENT PROFILE\n" + "\n".join(x for x in me if x) +
        "\n\nSOURCES\n" + ("\n".join(sources) if sources else "(no matching sources for this question)"))
    msgs = [{"role": "system", "content": system}] + history[-8:] + [{"role": "user", "content": msg}]
    text = llm.complete(msgs, temperature=0.3, max_tokens=1200)
    cited = [public[int(n) - 1] for n in dict.fromkeys(re.findall(r"\[(\d+)\]", text)) if 0 < int(n) <= len(public)]
    return text.strip(), cited + personal[:1]


def answer(db: Session, user_id: int, msg: str, history: list[dict]) -> dict:
    ctx = context(db, user_id)
    public, personal = retrieve_for(db, msg, ctx)
    if llm.llm_enabled():
        try:
            text, used = llm_answer(msg, history, ctx, public, personal)
            return {"content": text, "citations": _cite(used), "engine": "llm"}
        except llm.LLMError as exc:
            text, used = rules_answer(msg, ctx, public, personal)
            return {"content": f"{exc.user_message} Meanwhile, here is what CareerPilot's own sources say.\n\n" +
                    text.split("\n\n", 1)[-1], "citations": _cite(used), "engine": "rules", "ai_error": exc.user_message}
    chat = small_talk(msg, ctx)
    if chat:
        return {"content": chat, "citations": [], "engine": "rules"}
    text, used = rules_answer(msg, ctx, public, personal)
    return {"content": text, "citations": _cite(used), "engine": "rules"}
