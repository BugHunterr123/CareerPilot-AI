"""Progress tracking, readiness indicators, manual job applications, and the dashboard."""
from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_profile, owned
from app.models import (CareerRecommendation, Company, JobApplication, MockInterview, PracticeQuestion, ProgressEvent,
                        QuestionAttempt, Resume, Roadmap, SavedQuestion, Skill, SkillGapReport, User)
from app.schemas import ApplicationIn
from app.security import get_current_user
from app.serializers import task_out
from app.services.roles import role_title

router = APIRouter(prefix="/api", tags=["progress & dashboard"])


def journey(db: Session, user: User) -> list[dict]:
    """The 8-step tracker shown at the top of every page. Each step is done only if the data exists."""
    prof = get_profile(db, user)
    has = lambda model, *cond: db.scalar(select(model.id).where(model.user_id == user.id, *cond).limit(1)) is not None  # noqa: E731
    steps = [
        ("resume", "Resume", has(Resume), "/resume"),
        ("skills", "Skills", has(Skill), "/skills"),
        ("roles", "Roles", prof.target_role_key is not None, "/careers"),
        ("company", "Company", prof.target_company_id is not None, "/companies"),
        ("plan", "Plan", has(Roadmap), "/roadmap"),
        ("practice", "Practice", has(QuestionAttempt), "/practice"),
        ("interview", "Interview", has(MockInterview, MockInterview.status == "completed"), "/interview"),
        ("progress", "Progress", has(ProgressEvent, ProgressEvent.kind == "task_done"), "/progress"),
    ]
    # "Progress" closes the loop: it counts once every earlier step is done and a roadmap task is finished.
    k, l, d, h = steps[-1]
    steps[-1] = (k, l, d and all(s[2] for s in steps[:-1]), h)
    return [{"key": k, "label": l, "done": d, "href": h} for k, l, d, h in steps]


def readiness(db: Session, user: User) -> dict:
    rm = db.scalar(select(Roadmap).where(Roadmap.user_id == user.id, Roadmap.is_active.is_(True)))
    tasks_total = len(rm.tasks) if rm else 0
    tasks_done = sum(t.status == "done" for t in rm.tasks) if rm else 0
    attempts = db.execute(select(PracticeQuestion.subject, QuestionAttempt.is_correct)
                          .join(PracticeQuestion, PracticeQuestion.id == QuestionAttempt.question_id)
                          .where(QuestionAttempt.user_id == user.id)).all()
    by_subj: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for subj, ok in attempts:
        by_subj[subj][0] += 1
        by_subj[subj][1] += int(ok)
    subjects = [{"subject": s, "attempts": a, "correct": c, "accuracy": round(100 * c / a)} for s, (a, c) in by_subj.items()]
    weak = sorted([s for s in subjects if s["attempts"] >= 2 and s["accuracy"] < 60], key=lambda s: s["accuracy"])
    interviews = db.scalars(select(MockInterview).where(MockInterview.user_id == user.id, MockInterview.status == "completed")
                            .order_by(MockInterview.id)).all()
    gap = db.scalar(select(SkillGapReport).where(SkillGapReport.user_id == user.id).order_by(SkillGapReport.id.desc()))
    indicators = [
        {"name": "Roadmap completed", "value": round(100 * tasks_done / tasks_total) if tasks_total else 0, "unit": "%",
         "explain": f"{tasks_done} of {tasks_total} planned tasks marked done."},
        {"name": "Practice accuracy", "value": round(100 * sum(c for _, c in by_subj.values()) / len(attempts)) if attempts else 0,
         "unit": "%", "explain": f"Correct answers across {len(attempts)} recorded attempts."},
        {"name": "Mock interview average", "value": round(sum(m.overall or 0 for m in interviews) / len(interviews), 2) if interviews else 0,
         "unit": "/5", "explain": f"Average rubric score over {len(interviews)} completed mock interview(s)."},
        {"name": "Required skills shown", "value": round(100 * gap.summary["shown"] / gap.summary["total"]) if gap else 0,
         "unit": "%", "explain": (f"{gap.summary['shown']} of {gap.summary['total']} required skills are backed by projects "
                                  "or practice (latest gap analysis).") if gap else "Run a gap analysis to measure this."},
    ]
    nxt = []
    if weak:
        nxt.append(f"Your weakest subject is {weak[0]['subject']} ({weak[0]['accuracy']}% correct). Practise 10 more questions.")
    if rm:
        todo = [t for t in rm.tasks if t.status == "todo"]
        if todo:
            nxt.append(f"Next roadmap task: {todo[0].topic}.")
    if not interviews:
        nxt.append("Try one mock interview to get a baseline score.")
    return {"indicators": indicators, "subjects": sorted(subjects, key=lambda s: -s["attempts"]), "weak": weak,
            "interviews": [{"id": m.id, "date": m.created_at.isoformat(), "overall": m.overall, "type": m.itype} for m in interviews],
            "next": nxt, "note": "Every number here is computed from what you recorded in CareerPilot. It is not a prediction of selection."}


@router.get("/journey")
def get_journey(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return journey(db, user)


@router.get("/progress")
def progress(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    events = db.scalars(select(ProgressEvent).where(ProgressEvent.user_id == user.id).order_by(ProgressEvent.id)).all()
    daily: dict[str, dict] = defaultdict(lambda: {"tasks": 0, "attempts": 0, "correct": 0})
    for e in events:
        d = e.created_at.date().isoformat()
        if e.kind == "task_done":
            daily[d]["tasks"] += 1
        elif e.kind == "attempt":
            daily[d]["attempts"] += 1
            daily[d]["correct"] += int(e.detail.get("correct", False))
    return {**readiness(db, user), "daily": [{"date": d, **v} for d, v in sorted(daily.items())],
            "recent": [{"kind": e.kind, "detail": e.detail, "at": e.created_at.isoformat()} for e in events[-15:][::-1]],
            "applications": [app_out(a) for a in db.scalars(select(JobApplication).where(JobApplication.user_id == user.id)
                                                                .order_by(JobApplication.id.desc()))]}


def app_out(a: JobApplication) -> dict:
    return {"id": a.id, "company_name": a.company_name, "role": a.role, "status": a.status, "outcome": a.outcome,
            "applied_on": a.applied_on.isoformat() if a.applied_on else None, "notes": a.notes,
            "interview_date": a.interview_date.isoformat() if a.interview_date else None}


@router.post("/applications", status_code=201)
def add_app(body: ApplicationIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = JobApplication(user_id=user.id, **body.model_dump())
    db.add(a)
    db.commit()
    return app_out(a)


@router.put("/applications/{aid}")
def edit_app(aid: int, body: ApplicationIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = owned(db, JobApplication, aid, user)
    for k, v in body.model_dump().items():
        setattr(a, k, v)
    db.commit()
    return app_out(a)


@router.delete("/applications/{aid}")
def delete_app(aid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(owned(db, JobApplication, aid, user))
    db.commit()
    return {"ok": True}
