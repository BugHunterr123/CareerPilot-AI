"""
Skill Intelligence: turns resume + optional profiles + practice results into a list
of skills, each with EVIDENCE and an honest confidence level.

Evidence levels (strongest first):
  validated  - you answered practice / interview questions on it correctly
  project    - a project, internship or GitHub repo shows you used it
  claimed    - it is listed in your resume (skills section / certificate)
  inferred   - not written anywhere, but strongly implied by something else (AI-inferred)

A skill mentioned once in a skills list is "claimed" with LOW confidence. Never more.
"""
import re
from collections import defaultdict

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import ProfileLink, Project, PracticeQuestion, QuestionAttempt, Resume, Skill, SkillEvidence
from app.services.taxonomy import INFERENCES, PATTERNS, canonical, category_of

# Which practice subject validates which skill
SUBJECT_TO_SKILL = {
    "SQL": "SQL", "DBMS": "DBMS", "OOP": "OOP", "OS": "Operating Systems", "Networks": "Computer Networks",
    "Coding": "Data Structures", "Pseudocode": "Algorithms", "Python": "Python", "Java": "Java",
    "Cloud": "Cloud Computing", "Security": "Cyber Security", "ML": "Machine Learning", "Web": "HTML",
}
LEVEL_ORDER = ["validated", "project", "claimed", "inferred"]


def _sentence_with(text: str, pats: list[re.Pattern]) -> str | None:
    for sent in re.split(r"(?<=[.;!?])\s+", text):
        if any(p.search(sent) for p in pats):
            return sent.strip()[:240]
    return None


def collect_evidence(db: Session, user_id: int) -> dict[str, list[tuple[str, str, str]]]:
    ev: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    resume = db.scalar(select(Resume).where(Resume.user_id == user_id, Resume.is_active.is_(True)))
    parsed = resume.parsed if resume else {}
    removed = set(parsed.get("removed_skills", []))

    for tok in parsed.get("skills", []):
        c = canonical(tok)
        if c:
            ev[c].append(("claimed", "Resume: skills section", tok))
    for line in parsed.get("certifications", []):
        for name, pats in PATTERNS.items():
            if any(p.search(line) for p in pats):
                ev[name].append(("claimed", "Certification", line[:200]))
    for line in parsed.get("achievements", []):
        for name in ("Algorithms", "Data Structures", "Leadership", "Communication", "Teamwork"):
            if any(p.search(line) for p in PATTERNS[name]):
                ev[name].append(("claimed", "Resume: achievements", line[:200]))

    projects = db.scalars(select(Project).where(Project.user_id == user_id)).all()
    for proj in projects:
        text = f"{proj.description} "
        listed = {canonical(t) or t for t in (proj.technologies or [])}
        for name, pats in PATTERNS.items():
            quote = _sentence_with(text, pats)
            if quote or name in listed:
                kind = "github" if proj.source == "github" else "project"
                ev[name].append((kind, f"Project: {proj.name}", quote or f"Listed in the project's tech stack: {name}"))
    for exp in parsed.get("experience", []):
        text = f"{exp.get('title', '')}. {exp.get('description', '')}"
        for name, pats in PATTERNS.items():
            quote = _sentence_with(text, pats)
            if quote:
                ev[name].append(("experience", f"Experience: {exp.get('title', '')[:80]}", quote))

    for link in db.scalars(select(ProfileLink).where(ProfileLink.user_id == user_id)).all():
        for lang in link.summary.get("languages", [])[:8] if link.status == "ok" else []:
            c = canonical(lang)
            if c:
                ev[c].append(("github", f"GitHub ({link.url})", f"Language used in public repositories: {lang}"))
        text = f"{link.manual_details} {link.summary.get('page_text', '')}"
        for name, pats in PATTERNS.items():  # LinkedIn/LeetCode/portfolio details count as claims, not proof
            quote = _sentence_with(text, pats)
            if quote:
                ev[name].append(("claimed", f"{link.kind.capitalize()} (optional profile)", quote))

    # practice results -> validated skills
    rows = db.execute(
        select(PracticeQuestion.subject, func.count(), func.sum(case((QuestionAttempt.is_correct.is_(True), 1), else_=0)))
        .join(PracticeQuestion, PracticeQuestion.id == QuestionAttempt.question_id)
        .where(QuestionAttempt.user_id == user_id).group_by(PracticeQuestion.subject)
    ).all()
    for subject, total, correct in rows:
        skill = SUBJECT_TO_SKILL.get(subject)
        correct = int(correct or 0)
        if skill and total >= 3 and correct / total >= 0.7:
            ev[skill].append(("practice", "CareerPilot practice", f"{correct} of {total} {subject} questions answered correctly"))

    present = set(ev)
    for src, target, reason in INFERENCES:
        if src in present and target not in present:
            ev[target].append(("inferred", f"AI-inferred from {src}", reason))
    for name in removed:
        ev.pop(name, None)
    return ev


def summarise(entries: list[tuple[str, str, str]]) -> tuple[str, str, str, str]:
    kinds = {k for k, _, _ in entries}
    proj_sources = {s for k, s, _ in entries if k in ("project", "experience", "github")}
    if "practice" in kinds:
        level, conf = "validated", "high"
    elif proj_sources:
        level = "project"
        conf = "high" if len(proj_sources) >= 2 else "medium"
    elif "claimed" in kinds:
        level, conf = "claimed", "low"
    else:
        level, conf = "inferred", "low"
    needs = {
        "validated": "",
        "project": "Shown in a project. Interviewers will still ask you to explain how you used it.",
        "claimed": "Only listed on your resume. Nothing yet shows how well you know it.",
        "inferred": "Not written on your resume. We guessed it from a related skill.",
    }[level]
    nxt = {
        "validated": "Keep it fresh with a few harder questions each week.",
        "project": "Answer 5 practice questions on it to validate it.",
        "claimed": "Use it in a small project or answer practice questions to back it up.",
        "inferred": "If you really know it, add it to your resume with a project line.",
    }[level]
    return level, conf, needs, nxt


def rebuild_skills(db: Session, user_id: int) -> list[Skill]:
    """Recompute the skill profile. Skills the student added by hand are kept."""
    ev = collect_evidence(db, user_id)
    manual = {s.name: s for s in db.scalars(select(Skill).where(Skill.user_id == user_id, Skill.user_added.is_(True)))}
    db.query(Skill).filter(Skill.user_id == user_id, Skill.user_added.is_(False)).delete()
    for name, s in manual.items():
        ev.setdefault(name, []).append(("claimed", "Added by you", "Added manually on the Skills page"))
        db.delete(s)
    db.flush()
    out = []
    for name, entries in sorted(ev.items()):
        level, conf, needs, nxt = summarise(entries)
        skill = Skill(user_id=user_id, name=name, category=category_of(name), level=level, confidence=conf,
                      needs_validation=needs, next_step=nxt, user_added=name in manual)
        seen = set()
        for kind, source, quote in entries:
            if (kind, source) in seen:
                continue
            seen.add((kind, source))
            skill.evidence.append(SkillEvidence(kind=kind, source=source, quote=quote))
        db.add(skill)
        out.append(skill)
    db.commit()
    return out
