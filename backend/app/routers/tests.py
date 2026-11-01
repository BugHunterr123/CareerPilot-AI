"""
Timed practice tests (coding or MCQ/aptitude).

Coding test: questions shown one by one; code runs on the server against the visible
tests ("Run") and against all tests including hidden ones ("Submit answer").
MCQ test: answers are checked only when the test is finished.
Every answered question is recorded as a normal attempt, so progress and gap analysis see it.
"""
import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import log_event, owned
from app.models import Company, PracticeQuestion, PracticeTest, QuestionAttempt, User
from app.models.common import utcnow
from app.ratelimit import limiter
from app.schemas import CodeRunIn, PracticeTestIn, TestAnswerIn
from app.security import get_current_user
from app.serializers import question_out
from app.services import code_runner
from app.services.grading import correct_option_index, mcq_is_correct

router = APIRouter(prefix="/api/tests", tags=["practice tests"])
MIN_PER_CODING = {"easy": 15, "medium": 20, "hard": 30}
GRACE = timedelta(seconds=60)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _pick(db: Session, user_id: int, body: PracticeTestIn) -> list[PracticeQuestion]:
    stmt = select(PracticeQuestion)
    if body.kind == "coding":
        stmt = stmt.where(PracticeQuestion.qtype == "coding", PracticeQuestion.starter_code != "")
    else:
        stmt = stmt.where(PracticeQuestion.qtype == "mcq")
    pool = [q for q in db.scalars(stmt) if body.kind == "coding" or correct_option_index(q) is not None]
    done = set(db.scalars(select(QuestionAttempt.question_id).where(QuestionAttempt.user_id == user_id,
                                                                    QuestionAttempt.is_correct.is_(True))))
    rnd = random.Random()

    def rank(q: PracticeQuestion) -> tuple:
        same_company = body.company_id is None or q.company_id == body.company_id
        same_diff = body.difficulty == "mixed" or q.difficulty == body.difficulty
        return (not same_company, not same_diff, q.id in done, rnd.random())

    if body.company_id is not None:
        # never fill a company test with another company's questions; general ones are allowed
        pool = [q for q in pool if q.company_id in (body.company_id, None)]
    pool.sort(key=rank)
    if body.difficulty != "mixed":
        return pool[: body.count]
    # mixed: rotate easy -> medium -> hard so a 3-question test is one of each, like real online tests
    order = ["easy", "medium", "hard"]
    buckets = {d: [q for q in pool if q.difficulty == d] for d in order}
    chosen: list[PracticeQuestion] = []
    while len(chosen) < body.count and any(buckets.values()):
        for d in order:
            if buckets[d] and len(chosen) < body.count:
                chosen.append(buckets[d].pop(0))
    chosen.sort(key=lambda q: order.index(q.difficulty) if q.difficulty in order else 1)
    return chosen


def _expired(t: PracticeTest) -> bool:
    return utcnow() > _aware(t.created_at) + timedelta(minutes=t.minutes) + GRACE


def _finish(db: Session, t: PracticeTest) -> None:
    if t.status == "completed":
        return
    qs = {q.id: q for q in db.scalars(select(PracticeQuestion).where(PracticeQuestion.id.in_(t.question_ids)))}
    answers = dict(t.answers or {})
    total = 0.0
    for qid in t.question_ids:
        a = answers.get(str(qid))
        q = qs.get(qid)
        if not a or not q:
            continue
        if t.kind == "mcq":
            a["correct"] = mcq_is_correct(q, a.get("choice", ""))
            total += 1 if a["correct"] else 0
        else:
            a["correct"] = bool(a.get("total")) and a.get("passed") == a.get("total")
            total += (a.get("passed", 0) / a["total"]) if a.get("total") else 0
        db.add(QuestionAttempt(user_id=t.user_id, question_id=qid, response=(a.get("choice") or a.get("code") or "")[:8000],
                               is_correct=a["correct"], self_marked=False))
    t.answers = answers
    t.score = round(100 * total / max(1, len(t.question_ids)), 1)
    t.status = "completed"
    t.finished_at = utcnow()
    log_event(db, t.user_id, "test_done", test_id=t.id, test_kind=t.kind, score=t.score)
    db.commit()


def _out(db: Session, t: PracticeTest) -> dict:
    qs = {q.id: q for q in db.scalars(select(PracticeQuestion).where(PracticeQuestion.id.in_(t.question_ids)))}
    company = db.get(Company, t.company_id) if t.company_id else None
    done = t.status == "completed"
    items = []
    for qid in t.question_ids:
        q = qs.get(qid)
        if not q:
            continue
        item = question_out(q, hide_answer=not done)
        a = (t.answers or {}).get(str(qid))
        if a:
            item["my_answer"] = {k: v for k, v in a.items() if done or k != "correct"}
        if done and t.kind == "mcq":
            idx = correct_option_index(q)
            item["correct_option"] = q.options[idx] if idx is not None else None
        items.append(item)
    ends = _aware(t.created_at) + timedelta(minutes=t.minutes)
    return {"id": t.id, "kind": t.kind, "company_id": t.company_id, "company_name": company.name if company else None,
            "difficulty": t.difficulty, "minutes": t.minutes, "status": t.status, "score": t.score,
            "started_at": _aware(t.created_at).isoformat(), "ends_at": ends.isoformat(),
            "finished_at": t.finished_at.isoformat() if t.finished_at else None,
            "answered": len(t.answers or {}), "questions": items}


@router.post("", status_code=201)
def create(body: PracticeTestIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.company_id is not None and not db.get(Company, body.company_id):
        raise HTTPException(404, "Company not found.")
    picked = _pick(db, user.id, body)
    if not picked:
        raise HTTPException(404, "No questions match this test yet. Try another difficulty or company.")
    minutes = body.minutes or (sum(MIN_PER_CODING.get(q.difficulty, 20) for q in picked) if body.kind == "coding"
                               else max(5, len(picked)))
    t = PracticeTest(user_id=user.id, kind=body.kind, company_id=body.company_id, difficulty=body.difficulty,
                     minutes=minutes, question_ids=[q.id for q in picked], answers={})
    db.add(t)
    db.commit()
    out = _out(db, t)
    if len(picked) < body.count:
        out["note"] = f"Only {len(picked)} matching questions were available, so the test has {len(picked)}."
    return out


@router.get("")
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(PracticeTest).where(PracticeTest.user_id == user.id).order_by(PracticeTest.id.desc()).limit(50)).all()
    names = {c.id: c.name for c in db.scalars(select(Company))}
    for t in rows:
        if t.status == "active" and _expired(t):
            _finish(db, t)
    return [{"id": t.id, "kind": t.kind, "company_name": names.get(t.company_id), "difficulty": t.difficulty,
             "status": t.status, "score": t.score, "questions": len(t.question_ids), "answered": len(t.answers or {}),
             "created_at": _aware(t.created_at).isoformat()} for t in rows]


@router.get("/{tid}")
def get(tid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    t = owned(db, PracticeTest, tid, user)
    if t.status == "active" and _expired(t):
        _finish(db, t)
    return _out(db, t)


def _active(db: Session, tid: int, user: User, qid: int) -> tuple[PracticeTest, PracticeQuestion]:
    t = owned(db, PracticeTest, tid, user)
    if t.status != "active":
        raise HTTPException(409, "This test is already finished.")
    if _expired(t):
        _finish(db, t)
        raise HTTPException(409, "Time is up. The test was submitted with your saved answers.")
    if qid not in t.question_ids:
        raise HTTPException(404, "That question is not part of this test.")
    return t, db.get(PracticeQuestion, qid)


@router.post("/{tid}/run", dependencies=[Depends(limiter("code"))])
async def run(tid: int, qid: int, body: CodeRunIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _, q = _active(db, tid, user, qid)
    if not q.tests:
        raise HTTPException(409, "This question has no test cases.")
    if body.stdin is not None:
        return {"custom": True, **(await run_in_threadpool(code_runner.run_python, body.code, body.stdin))}
    return await run_in_threadpool(code_runner.run_tests, body.code, q.tests, False)


@router.post("/{tid}/answer", dependencies=[Depends(limiter("code"))])
async def answer(tid: int, body: TestAnswerIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    t, q = _active(db, tid, user, body.question_id)
    answers = dict(t.answers or {})
    if t.kind == "coding":
        if not body.code or not body.code.strip():
            raise HTTPException(422, "Write some code before submitting.")
        result = await run_in_threadpool(code_runner.run_tests, body.code, q.tests, True)
        answers[str(q.id)] = {"code": body.code[:20000], "passed": result["passed"], "total": result["total"]}
        t.answers = answers
        db.commit()
        return {"saved": True, **result}
    if not body.choice:
        raise HTTPException(422, "Pick an option.")
    answers[str(q.id)] = {"choice": body.choice}
    t.answers = answers
    db.commit()
    return {"saved": True}


@router.post("/{tid}/finish")
def finish(tid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    t = owned(db, PracticeTest, tid, user)
    _finish(db, t)
    return _out(db, t)
