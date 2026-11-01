"""
Mock Interview Service: builds a NEW question plan for every session, asks ONE question
at a time, scores each answer on a transparent 4-part rubric, and the final report is
computed only from that session's answers.

Rubric (each 0-5):  Concepts  (did you mention the key points?)
                    Depth     (examples, reasons, trade-offs, numbers)
                    Structure (definition -> example -> trade-off, or STAR for HR)
                    Clarity   (length and sentence length in a sensible range)

Questions: with an AI key the model writes questions for the chosen role, company, type,
difficulty and the student's own resume projects. Without a key we draw from the question
bank (role-specific, company-reported questions first, and questions from your recent
sessions last), so two sessions rarely look the same.
A mock score is practice feedback, never a prediction of a real hiring decision.
"""
import random
import re

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, MockInterview, PracticeQuestion, Project, Skill
from app.services import llm
from app.services.interview_bank import HR, ROLE_TECH, ROLE_TOPICS, TECH
from app.services.roles import role_title

DEPTH_WORDS = ["because", "for example", "e.g", "such as", "trade-off", "tradeoff", "complexity", "o(", "instead",
               "i built", "i used", "we used", "which means", "so that", "%", "ms", "users"]
STAR_WORDS = [["situation", "when", "during", "in my"], ["task", "goal", "had to", "needed to"],
              ["i did", "i took", "i decided", "my role", "i wrote", "i built", "i talked", "i "],
              ["result", "outcome", "finally", "in the end", "learned", "learnt", "improved"]]
FILLERS = ["um", "uh", "basically", "like like", "you know"]
STOP = set("the a an and or of to in on for with is are was were be this that it as at by from what how why when "
           "which your you can will would should about into than then them they their there these those have has "
           "had not but also more most such each other some any all one two use used using like".split())


def key_terms(text: str, k: int = 5) -> list[list[str]]:
    """Turn a model answer into up to k keyword 'points' for the rule scorer."""
    words = [w for w in re.findall(r"[a-zA-Z][a-zA-Z0-9+#-]{3,}", text.lower()) if w not in STOP]
    seen = list(dict.fromkeys(words))
    return [[w[:6] if len(w) > 7 else w] for w in seen[:k]]


def _projects_qs(db: Session, user_id: int) -> list[dict]:
    out = []
    for p in db.scalars(select(Project).where(Project.user_id == user_id).limit(4)):
        techs = [t.lower() for t in (p.technologies or [])][:4]
        out.append({"q": f"Walk me through your project '{p.name}'. What problem did it solve and what exactly did you do?",
                    "kind": "project", "topic": "Project", "origin": "Your resume",
                    "points": [["problem", "needed", "users"], ["i built", "i designed", "i wrote", "my part", "i "]]
                              + [[t] for t in techs[:2]] + [["challenge", "difficult", "issue", "bug"], ["result", "%", "users", "accuracy", "faster"]]})
        if techs:
            out.append({"q": f"In '{p.name}', why did you choose {p.technologies[0]}? What would you change now?",
                        "kind": "project", "topic": "Project", "origin": "Your resume",
                        "points": [[techs[0]], ["because", "reason", "easy", "fast"], ["alternative", "instead", "compared", "other"], ["change", "improve", "next time"]]})
    return out


def _company_qs(db: Session, company: Company | None) -> tuple[list[dict], list[dict]]:
    """Technical and HR interview questions seeded for this company (with their labels)."""
    if not company:
        return [], []
    tech, hr = [], []
    rows = db.scalars(select(PracticeQuestion).where(PracticeQuestion.company_id == company.id,
                                                     PracticeQuestion.qtype.in_(["short", "hr"])))
    for q in rows:
        item = {"q": q.question, "kind": "hr" if q.qtype == "hr" else "technical", "topic": q.subject,
                "points": key_terms(q.answer) or [["example"]], "difficulty": q.difficulty,
                "origin": f"{company.name}: {q.label}"}
        (hr if q.qtype == "hr" else tech).append(item)
    return tech, hr


def _recent_questions(db: Session, user_id: int) -> set[str]:
    rows = db.scalars(select(MockInterview).where(MockInterview.user_id == user_id).order_by(MockInterview.id.desc()).limit(3))
    return {item["q"] for m in rows for item in (m.plan or [])}


def bank_plan(db: Session, user_id: int, role_key: str, itype: str, difficulty: str, n: int,
              company: Company | None) -> list[dict]:
    rnd = random.Random()
    cname = company.name if company else "this company"
    recent = _recent_questions(db, user_id)
    prefs = ROLE_TOPICS.get(role_key, ROLE_TOPICS["software_developer"])

    def ok_diff(d: str) -> bool:
        return difficulty == "mixed" or d == difficulty or (difficulty == "hard" and d == "medium")

    tech = [{"q": q, "kind": "technical", "topic": t, "points": pts, "difficulty": d, "origin": "CareerPilot practice"}
            for t, d, q, pts in TECH + ROLE_TECH if ok_diff(d)]
    c_tech, c_hr = _company_qs(db, company)
    tech += [x for x in c_tech if ok_diff(x["difficulty"]) or difficulty == "easy"]

    def tech_rank(x: dict) -> tuple:
        topic_pos = prefs.index(x["topic"]) if x["topic"] in prefs else len(prefs) + 1
        return (x["q"] in recent, not x["origin"].startswith(cname), topic_pos > 3, topic_pos, rnd.random())

    tech.sort(key=tech_rank)
    coding = [x for x in tech if x["topic"] in ("Coding", "Pseudocode")] or [x for x in tech if x["topic"] == "SQL"]
    hr_bank = [{"q": q.replace("{company}", cname), "kind": "hr", "topic": "HR", "origin": "CareerPilot practice",
                "points": [[w.replace("{company_l}", cname.lower()) for w in syn] for syn in pts]} for d, q, pts in HR]
    hr = sorted(c_hr + hr_bank, key=lambda x: (x["q"] in recent, not x["origin"].startswith(cname), rnd.random()))
    proj = _projects_qs(db, user_id)
    rnd.shuffle(proj)
    proj.sort(key=lambda x: x["q"] in recent)
    if itype == "mixed":
        plan = hr[:1] + proj[:1] + tech[: max(1, n - 3)] + hr[1:2]
    elif itype == "project":
        plan = proj + tech
    elif itype == "coding":
        plan = coding + tech
    elif itype in ("hr", "behavioural"):
        plan = hr
    else:
        plan = tech
    plan = [dict(x) for x in plan[:n]]
    for x in plan:
        x["points"] = [list(p) for p in x["points"]]
        x.setdefault("source", "bank")
    return plan


class AIQuestion(BaseModel):
    question: str = Field(min_length=10, max_length=600)
    kind: str = Field(pattern=r"^(technical|coding|project|hr)$")
    topic: str = Field(max_length=60)
    key_points: list[str] = Field(min_length=2, max_length=7)


class AIPlan(BaseModel):
    questions: list[AIQuestion] = Field(min_length=1, max_length=10)


def ai_plan(db: Session, user_id: int, role_key: str, itype: str, difficulty: str, n: int, company: Company | None) -> list[dict] | None:
    projects = [f"{p.name}: {', '.join(p.technologies or [])}. {(p.description or '')[:200]}"
                for p in db.scalars(select(Project).where(Project.user_id == user_id).limit(4))]
    skills = [s.name for s in db.scalars(select(Skill).where(Skill.user_id == user_id).limit(30))]
    stages = "; ".join(f"{s.name}: {', '.join(s.study[:6])}" for s in company.stages) if company else "no company chosen"
    recent = list(_recent_questions(db, user_id))[:12]
    plan = llm.try_structured(
        "You are an experienced campus interviewer in India. Write a mock interview question set. "
        "Questions must fit the role, interview type and difficulty, use the student's real projects for project "
        "questions (never invent projects), and follow the company's reported interview topics when given. "
        "Do not claim that a question was asked by the company. Each question gets 3-6 short key points a good answer "
        "should cover. Do not repeat the student's recent questions. Return exactly the number of questions asked for. "
        "For a mixed interview use one HR question, one question on a real project, and technical questions for the rest. "
        "Keep each question to one or two sentences, the way an interviewer would say it.",
        f"Role: {role_title(role_key)}\nCompany: {company.name if company else 'none'}\nCompany stages and topics: {stages}\n"
        f"Interview type: {itype}\nDifficulty: {difficulty}\nNumber of questions: {n}\n"
        f"Student projects: {projects or 'none listed'}\nStudent skills: {skills or 'none listed'}\n"
        f"Recent questions to avoid: {recent}", AIPlan, temperature=0.7)
    if not plan:
        return None
    out = []
    for q in plan.questions[:n]:
        pts = [key_terms(kp, 2)[0] + [kp.lower()[:40]] if key_terms(kp, 2) else [kp.lower()[:40]] for kp in q.key_points]
        out.append({"q": q.question, "kind": "technical" if q.kind == "coding" else q.kind, "topic": q.topic,
                    "points": pts, "key_points": q.key_points, "origin": "Written by AI for this session", "source": "ai"})
    return out


def build_plan(db: Session, user_id: int, role_key: str, itype: str, difficulty: str, n: int,
               company: Company | None) -> list[dict]:
    """AI-written questions when an LLM is configured; the role/company-aware bank otherwise.
    A short AI set is topped up from the bank so the session always has n questions."""
    plan = ai_plan(db, user_id, role_key, itype, difficulty, n, company) or []
    if len(plan) < n:
        seen = {q["q"].strip().lower() for q in plan}
        extra = [q for q in bank_plan(db, user_id, role_key, itype, difficulty, n, company) if q["q"].strip().lower() not in seen]
        plan += extra[: n - len(plan)]
    return plan



_STEM_WORDS = {
    "anomal": "anomalies", "consisten": "consistency", "contribut": "contribution", "durab": "durability",
    "escalat": "escalation", "expir": "expiry", "hallucinat": "hallucination", "idempot": "idempotency",
    "imbalanc": "class imbalance", "improv": "improvement", "isolat": "isolation", "redundan": "redundancy",
    "regulari": "regularisation", "retriev": "retrieval", "summar": "summary", "validat": "validation",
    "1nf": "1NF", "2nf": "2NF", "@": "decorator (@)", "df": "DataFrame", "ps": "ps command", "o(n)": "O(n) time",
    "{company_l}": "the company", "ask": "asking questions", "bar": "bar chart", "get": "GET", "post": "POST", "put": "PUT",
}


def _point_label(p: list[str]) -> str:
    """Readable name for a key point: the AI's phrase if there is one, else its main keyword
    (bank keywords are matching stems such as "idempot", so they are mapped to words)."""
    if len(p[-1]) > 12:
        return p[-1]
    first = p[0].strip()
    if first in ("i", "my role") or first.startswith("i "):
        return "what you personally did"
    return _STEM_WORDS.get(first, first)


def score_rules(item: dict, answer: str) -> dict:
    text = answer.lower()
    words = re.findall(r"[a-z0-9']+", text)
    sentences = [s for s in re.split(r"[.!?]+\s*", answer) if s.strip()]
    hit = [p for p in item["points"] if any(syn.lower() in text for syn in p)]
    missed = [_point_label(p) for p in item["points"] if p not in hit]
    concepts = round(5 * len(hit) / max(1, len(item["points"])))
    depth_hits = sum(1 for w in DEPTH_WORDS if w in text)
    depth = min(5, depth_hits + (1 if len(words) > 60 else 0))
    if item["kind"] in ("hr", "project"):
        star = sum(1 for group in STAR_WORDS if any(w in text for w in group))
        structure = min(5, star + (1 if len(sentences) >= 3 else 0))
    else:
        structure = min(5, (2 if len(sentences) >= 2 else 0) + (1 if any(w in text for w in ["is ", "means", "refers"]) else 0)
                        + (1 if any(w in text for w in ["example", "e.g", "such as", "for instance"]) else 0)
                        + (1 if any(w in text for w in ["but", "however", "whereas", "trade", "while"]) else 0))
    avg = len(words) / max(1, len(sentences))
    clarity = 5 if 40 <= len(words) <= 220 else 3 if 20 <= len(words) <= 320 else 1
    if avg > 30:
        clarity -= 1
    if any(f" {f} " in f" {text} " for f in FILLERS):
        clarity -= 1
    clarity = max(0, clarity)
    reasons = {
        "concepts": f"Mentioned {len(hit)} of {len(item['points'])} key points.",
        "depth": f"{depth_hits} signs of depth (reasons, examples, numbers, trade-offs).",
        "structure": "Checked for situation, task, action, result." if item["kind"] in ("hr", "project")
        else "Checked for definition, example and comparison.",
        "clarity": f"{len(words)} words, about {avg:.0f} words per sentence.",
    }
    scores = {k: {"score": v, "reason": reasons[k]} for k, v in
              {"concepts": concepts, "depth": depth, "structure": structure, "clarity": clarity}.items()}
    good = [f"Covered: {', '.join(_point_label(p) for p in hit[:4])}"] if hit else []
    return {"scores": scores, "good": good, "missing": missed, "engine": "rules", "quote": "", "better_answer": ""}


class Criterion(BaseModel):
    score: int = Field(ge=0, le=5)
    reason: str = Field(max_length=400)


class AIScore(BaseModel):
    concepts: Criterion
    depth: Criterion
    structure: Criterion
    clarity: Criterion
    good: list[str] = Field(default_factory=list, max_length=4)
    missing: list[str] = Field(default_factory=list, max_length=6)
    quote: str = Field("", max_length=300, description="a short exact quote from the answer that the feedback refers to")
    better_answer: str = Field("", max_length=900, description="a 2-4 line outline of a stronger answer")


def score_ai(item: dict, answer: str) -> dict | None:
    ai = llm.try_structured(
        "You are a fair, specific campus interviewer. Score the student's answer from 0 to 5 on four criteria: "
        "concepts (key points covered), depth (examples, reasons, trade-offs, numbers), structure (definition -> example "
        "-> trade-off, or STAR for HR/project answers) and clarity (concise, easy to follow). Give each a one-sentence "
        "reason that refers to what the student actually wrote. Quote one short exact phrase from the answer. "
        "If the answer is empty, off-topic or nonsense, give low scores and say so. Never invent facts about the student.",
        f"Question: {item['q']}\nKey points a good answer covers: {item.get('key_points') or [p[-1] for p in item['points']]}\n"
        f"Student answer:\n{answer}", AIScore, temperature=0.1)
    if not ai:
        return None
    quote = ai.quote.strip().strip('"')
    if quote and quote.lower() not in answer.lower():
        quote = ""  # never show a "quote" the student did not write
    scores = {k: {"score": getattr(ai, k).score, "reason": getattr(ai, k).reason}
              for k in ("concepts", "depth", "structure", "clarity")}
    return {"scores": scores, "good": ai.good, "missing": ai.missing, "engine": "llm", "quote": quote,
            "better_answer": ai.better_answer}


def score(item: dict, answer: str) -> dict:
    return score_ai(item, answer) or score_rules(item, answer)
