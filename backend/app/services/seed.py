"""
Loads seed data into the database (safe to run on every start).

  app/seed/data/companies/*.json        source-backed company guides + question banks
  app/seed/data/practice/*.json         runnable coding problems + MCQs per company (tested)
  app/seed/data/general_questions.json  CareerPilot practice questions (label: AI practice)
  app/seed/data/resources.json          free learning resources, tagged by topic

Re-seeding UPDATES rows in place: companies keep their id and questions are matched
by a stable key (qkey), so students' saved questions, attempts and targets survive.
This is reference content, not demo data: there are no sample students or results.
"""
import hashlib
import re
import json
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Company, HiringStage, JobRole, LearningResource, PracticeQuestion, SourceRef

DATA = Path(__file__).resolve().parent.parent / "seed" / "data"
log = logging.getLogger("careerpilot.seed")
QFIELDS = ("stage_kind", "subject", "qtype", "difficulty", "question", "code", "options", "answer", "explanation",
           "hints", "concepts", "sample_io", "solution", "label", "source_note", "title", "tests", "starter_code",
           "io_format", "solutions_other", "source_id", "company_id")


def _role_key(title: str) -> str:
    t = title.lower()
    rules = [("data engineer", "data_engineer"), ("data scien", "data_scientist"), ("machine learning", "ml_engineer"),
             ("ml engineer", "ml_engineer"), ("ai engineer", "ai_engineer"), ("business intelligence", "bi_analyst"),
             ("support", "tech_support"), ("test", "qa_automation"), ("qa", "qa_automation"),
             ("full stack", "full_stack_developer"), ("full-stack", "full_stack_developer"), ("backend", "backend_developer")]
    for needle, key in rules:
        if needle in t:
            return key
    if "analyst" in t and ("data" in t or "business" in t or "analytics" in t):
        return "data_analyst"
    return "software_developer"


_STOP = {"the", "a", "an", "of", "to", "in", "and", "is", "for", "given", "find", "write", "program", "print",
         "array", "string", "number", "numbers", "n"}


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower())) - _STOP


def _has_runnable_version(question: str, runnable_words: list[set[str]]) -> bool:
    """True when a converted, test-backed version of this reported coding question exists.
    Matching is by word overlap because the converted statement is rewritten with full I/O."""
    w = _words(question)
    return bool(w) and any(len(w & r) / len(w) >= 0.4 for r in runnable_words)


def _qkey(prefix: str, q: dict) -> str:
    return q.get("qkey") or f"{prefix}-{hashlib.sha1(q['question'].strip().lower().encode()).hexdigest()[:12]}"


def _question_values(q: dict, company_id: int | None, source_id: int | None, stage_kind: str, default_note: str) -> dict:
    io = {k: q[k] for k in ("input_format", "output_format", "constraints") if q.get(k)}
    return {
        "company_id": company_id, "source_id": source_id, "stage_kind": stage_kind,
        "subject": q.get("subject", "Other"), "qtype": q.get("type", "short"), "difficulty": q.get("difficulty", "medium"),
        "question": q["question"], "code": q.get("code", "") or "", "options": q.get("options"), "answer": q.get("answer", "") or "",
        "explanation": q.get("explanation", "") or "", "hints": q.get("hints", []) or [], "concepts": q.get("concepts", []) or [],
        "sample_io": q.get("sample_io", "") or "", "solution": q.get("solution", "") or "",
        "label": q.get("label", "AI practice"), "source_note": (q.get("source_note") or default_note)[:300],
        "title": (q.get("title") or "")[:160], "tests": q.get("tests", []) or [], "starter_code": q.get("starter_code", "") or "",
        "io_format": io, "solutions_other": q.get("solutions_other", {}) or {},
    }


def _upsert_questions(db: Session, rows: list[tuple[str, dict]], existing: dict[str, PracticeQuestion]) -> int:
    seen = set()
    for key, values in rows:
        if key in seen:
            continue
        seen.add(key)
        q = existing.get(key)
        if q is None:
            db.add(PracticeQuestion(qkey=key, **values))
        else:
            for f in QFIELDS:
                setattr(q, f, values[f])
    for key, q in existing.items():
        if key not in seen:
            db.delete(q)  # removed from the content files
    return len(seen)


def load_company(db: Session, data: dict, practice: dict | None = None) -> Company:
    c = db.scalar(select(Company).where(Company.slug == data["slug"]))
    if c is None:
        c = Company(slug=data["slug"])
        db.add(c)
    c.name = data["name"]
    c.overview = data.get("overview", "")
    c.overview_source_key = data.get("overview_source")
    c.careers_url = data.get("careers_url")
    c.variation_note = data.get("variation_note", "")
    c.research_date = data.get("research_date", "2026-11-01")
    c.sources.clear()
    c.roles.clear()
    c.stages.clear()
    db.flush()
    for s in data.get("sources", []):
        c.sources.append(SourceRef(key=s["id"], url=s["url"], title=s.get("title", ""), publisher=s.get("publisher", ""),
                                   date=s.get("date"), accessed=data.get("research_date", "2026-11-01"), label=s.get("label", "Third-party")))
    for r in data.get("roles", []):
        c.roles.append(JobRole(title=r["title"], description=r.get("description", ""), role_key=_role_key(r["title"]),
                               skills=r.get("skills", []), eligibility=r.get("eligibility", []), compensation=r.get("compensation", [])))
    kinds = {}
    for st in data.get("stages", []):
        kinds[st["order"]] = st.get("kind", "other")
        c.stages.append(HiringStage(order=st["order"], name=st["name"], kind=st.get("kind", "other"), what=st.get("what", ""),
                                    format=st.get("format", []), evaluates=st.get("evaluates", []), study=st.get("study", []),
                                    tips=st.get("tips", []), before_next=st.get("before_next", ""),
                                    label=st.get("label", "Candidate-reported")))
    db.flush()
    by_key = {s.key: s.id for s in c.sources}
    practice = practice or {}
    runnable = practice.get("coding", [])
    runnable_words = [_words(f"{q.get('title', '')} {q['question']}") for q in runnable]
    rows = []
    for q in data.get("questions", []):
        if q.get("type") == "coding" and _has_runnable_version(q["question"], runnable_words):
            continue  # replaced by its runnable (tested) version below
        vals = _question_values(q, c.id, by_key.get(q.get("source")), kinds.get(q.get("stage_order"), "technical_mcq"), "")
        rows.append((_qkey(c.slug, q), vals))
    for q in runnable + practice.get("mcq", []):
        stage_kind = kinds.get(q.get("stage_order"), "coding" if q.get("type") == "coding" else "technical_mcq")
        vals = _question_values(q, c.id, by_key.get(q.get("source")), stage_kind, "Written for practice")
        rows.append((_qkey(c.slug, q), vals))
    existing = {q.qkey: q for q in db.scalars(select(PracticeQuestion).where(PracticeQuestion.company_id == c.id))
                if q.qkey}
    for q in db.scalars(select(PracticeQuestion).where(PracticeQuestion.company_id == c.id, PracticeQuestion.qkey.is_(None))):
        db.delete(q)  # rows from before stable keys existed
    _upsert_questions(db, rows, existing)
    return c


def _hash(*paths: Path) -> str:
    h = hashlib.sha256()
    for p in paths:
        if p.exists():
            h.update(p.read_bytes())
    h.update(Path(__file__).read_bytes())  # loader changes also re-seed
    return h.hexdigest()


def seed_all(db: Session) -> dict:
    counts = {"companies": 0, "general_questions": 0, "resources": 0}
    res = json.loads((DATA / "resources.json").read_text())
    have = {(r.topic, r.url) for r in db.scalars(select(LearningResource))}
    for r in res:
        if (r["topic"], r["url"]) not in have:
            db.add(LearningResource(**r))
            counts["resources"] += 1
    general = json.loads((DATA / "general_questions.json").read_text())
    existing = {q.qkey: q for q in db.scalars(select(PracticeQuestion).where(PracticeQuestion.company_id.is_(None))) if q.qkey}
    for q in db.scalars(select(PracticeQuestion).where(PracticeQuestion.company_id.is_(None), PracticeQuestion.qkey.is_(None))):
        db.delete(q)
    rows = [(_qkey("gen", q), _question_values(q, None, None, q.get("stage_kind", "technical_mcq"),
                                                "CareerPilot practice question (not reported by candidates)") | {"label": "AI practice"})
            for q in general]
    counts["general_questions"] = _upsert_questions(db, rows, existing)
    stamps = {c.slug: c.seed_hash for c in db.scalars(select(Company))}
    for path in sorted((DATA / "companies").glob("*.json")):
        try:
            data = json.loads(path.read_text())
            ppath = DATA / "practice" / path.name
            practice = json.loads(ppath.read_text()) if ppath.exists() else None
        except json.JSONDecodeError as exc:
            log.error("Skipping %s: %s", path.name, exc)
            continue
        stamp = _hash(path, ppath)
        if stamps.get(data["slug"]) == stamp:
            continue
        load_company(db, data, practice).seed_hash = stamp
        counts["companies"] += 1
    db.commit()
    return counts
