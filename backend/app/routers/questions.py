"""Question bank: search, filter, save, attempt, run code, and track incorrect answers."""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import log_event
from app.models import Company, PracticeQuestion, QuestionAttempt, SavedQuestion, SourceRef, User
from app.ratelimit import limiter
from app.schemas import AttemptIn, CodeRunIn
from app.security import get_current_user
from app.serializers import question_out
from app.services import code_runner
from app.services.grading import correct_option_index, mcq_is_correct

router = APIRouter(prefix="/api/questions", tags=["questions"])


def _stats(db: Session, user_id: int, qids: list[int]) -> dict[int, dict]:
    out: dict[int, dict] = {}
    rows = db.scalars(select(QuestionAttempt).where(QuestionAttempt.user_id == user_id,
                                                    QuestionAttempt.question_id.in_(qids)).order_by(QuestionAttempt.id))
    for a in rows:
        s = out.setdefault(a.question_id, {"attempts": 0, "correct": 0, "last_correct": None})
        s["attempts"] += 1
        s["correct"] += int(a.is_correct)
        s["last_correct"] = a.is_correct
    return out


@router.get("")
def search(q: str = "", company: str = "", subject: str = "", qtype: str = "", difficulty: str = "", label: str = "",
           saved: bool = False, incorrect: bool = False, runnable: bool = False,
           page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=50),
           user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Filters combine with AND. Coding problems are language-agnostic: there is no language filter;
    the UI only chooses which solution language to show."""
    stmt = select(PracticeQuestion)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(PracticeQuestion.question.ilike(like), PracticeQuestion.subject.ilike(like),
                              PracticeQuestion.title.ilike(like)))
    if runnable:
        stmt = stmt.where(PracticeQuestion.qtype == "coding", PracticeQuestion.starter_code != "")
    if company == "general":
        stmt = stmt.where(PracticeQuestion.company_id.is_(None))
    elif company:
        stmt = stmt.join(Company, Company.id == PracticeQuestion.company_id).where(Company.slug == company)
    for col, val in ((PracticeQuestion.subject, subject), (PracticeQuestion.qtype, qtype),
                     (PracticeQuestion.difficulty, difficulty), (PracticeQuestion.label, label)):
        if val:
            stmt = stmt.where(col == val)
    if saved:
        stmt = stmt.where(PracticeQuestion.id.in_(select(SavedQuestion.question_id).where(SavedQuestion.user_id == user.id)))
    if incorrect:  # questions whose LATEST attempt was wrong
        last = (select(QuestionAttempt.question_id, func.max(QuestionAttempt.id).label("mid"))
                .where(QuestionAttempt.user_id == user.id).group_by(QuestionAttempt.question_id).subquery())
        wrong = select(QuestionAttempt.question_id).join(last, last.c.mid == QuestionAttempt.id).where(QuestionAttempt.is_correct.is_(False))
        stmt = stmt.where(PracticeQuestion.id.in_(wrong))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(PracticeQuestion.company_id.is_(None), PracticeQuestion.id)
                      .offset((page - 1) * page_size).limit(page_size)).all()
    ids = [r.id for r in rows]
    saved_ids = set(db.scalars(select(SavedQuestion.question_id).where(SavedQuestion.user_id == user.id,
                                                                       SavedQuestion.question_id.in_(ids))))
    stats = _stats(db, user.id, ids)
    sources = {s.id: s for s in db.scalars(select(SourceRef).where(SourceRef.id.in_([r.source_id for r in rows if r.source_id])))}
    names = dict(db.execute(select(Company.id, Company.name)).all())
    return {"total": total, "page": page, "page_size": page_size,
            "items": [question_out(r, sources.get(r.source_id), r.id in saved_ids, stats.get(r.id),
                                   company_name=names.get(r.company_id)) for r in rows]}


@router.get("/{qid:int}")
def get_one(qid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.get(PracticeQuestion, qid)
    if not q:
        raise HTTPException(404, "Question not found.")
    src = db.get(SourceRef, q.source_id) if q.source_id else None
    saved = bool(db.scalar(select(SavedQuestion).where(SavedQuestion.user_id == user.id, SavedQuestion.question_id == qid)))
    comp = db.get(Company, q.company_id) if q.company_id else None
    return question_out(q, src, saved, _stats(db, user.id, [qid]).get(qid), company_name=comp.name if comp else None)


@router.get("/facets")
def facets(company: str = "", qtype: str = "", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Filter options. With company/qtype given, subjects/labels/difficulties only list values that exist
    for that selection (with counts), so the UI never offers a combination that is always empty."""
    base = select(PracticeQuestion)
    if company == "general":
        base = base.where(PracticeQuestion.company_id.is_(None))
    elif company:
        base = base.join(Company, Company.id == PracticeQuestion.company_id).where(Company.slug == company)
    if qtype:
        base = base.where(PracticeQuestion.qtype == qtype)
    sub = base.subquery()

    def counts(col: str) -> list[dict]:
        rows = db.execute(select(sub.c[col], func.count()).group_by(sub.c[col]).order_by(sub.c[col])).all()
        return [{"value": v, "count": n} for v, n in rows if v]

    companies = db.execute(select(Company.slug, Company.name, Company.id).order_by(Company.name)).all()
    attempts = db.scalar(select(func.count()).where(QuestionAttempt.user_id == user.id))
    correct = db.scalar(select(func.count()).where(QuestionAttempt.user_id == user.id, QuestionAttempt.is_correct.is_(True)))
    saved = db.scalar(select(func.count()).where(SavedQuestion.user_id == user.id))
    all_types = [x for x in db.scalars(select(PracticeQuestion.qtype).distinct().order_by(PracticeQuestion.qtype)) if x]
    subj = counts("subject")
    return {"subjects": [x["value"] for x in subj], "subject_counts": subj, "types": all_types,
            "difficulties": ["easy", "medium", "hard"], "difficulty_counts": counts("difficulty"),
            "labels": [x["value"] for x in counts("label")], "label_counts": counts("label"),
            "total": db.scalar(select(func.count()).select_from(sub)),
            "companies": [{"slug": s, "name": n, "id": i} for s, n, i in companies],
            "mine": {"attempts": attempts, "correct": correct, "saved": saved}}


@router.post("/{qid}/attempt")
def attempt(qid: int, body: AttemptIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.get(PracticeQuestion, qid)
    if not q:
        raise HTTPException(404, "Question not found.")
    if q.qtype == "mcq" and q.options:
        correct = mcq_is_correct(q, body.response)
        self_marked = False
    else:
        if body.self_correct is None:
            raise HTTPException(422, "For this question, compare with the model answer and mark yourself right or wrong.")
        correct, self_marked = bool(body.self_correct), True
    db.add(QuestionAttempt(user_id=user.id, question_id=q.id, response=body.response, is_correct=correct, self_marked=self_marked))
    log_event(db, user.id, "attempt", question_id=q.id, subject=q.subject, correct=correct)
    db.commit()
    idx = correct_option_index(q) if q.qtype == "mcq" else None
    return {"correct": correct, "answer": q.answer, "explanation": q.explanation, "self_marked": self_marked,
            "correct_option": q.options[idx] if idx is not None else None,
            "stats": _stats(db, user.id, [q.id]).get(q.id)}


@router.post("/{qid}/save")
def save(qid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not db.get(PracticeQuestion, qid):
        raise HTTPException(404, "Question not found.")
    if not db.scalar(select(SavedQuestion).where(SavedQuestion.user_id == user.id, SavedQuestion.question_id == qid)):
        db.add(SavedQuestion(user_id=user.id, question_id=qid))
        db.commit()
    return {"saved": True}


@router.delete("/{qid}/save")
def unsave(qid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(SavedQuestion).filter(SavedQuestion.user_id == user.id, SavedQuestion.question_id == qid).delete()
    db.commit()
    return {"saved": False}


def _runnable(db: Session, qid: int) -> PracticeQuestion:
    q = db.get(PracticeQuestion, qid)
    if not q:
        raise HTTPException(404, "Question not found.")
    if not q.tests:
        raise HTTPException(409, "This question has no test cases to run. Compare with the model solution instead.")
    return q


@router.post("/{qid}/run", dependencies=[Depends(limiter("code"))])
async def run_code(qid: int, body: CodeRunIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Run Python code against the VISIBLE test cases (or a custom input). Nothing is recorded."""
    q = _runnable(db, qid)
    if body.stdin is not None:
        r = await run_in_threadpool(code_runner.run_python, body.code, body.stdin)
        return {"custom": True, **r}
    return await run_in_threadpool(code_runner.run_tests, body.code, q.tests, False)


@router.post("/{qid}/submit", dependencies=[Depends(limiter("code"))])
async def submit_code(qid: int, body: CodeRunIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Run against ALL tests (hidden included) and record the attempt (correct = every test passed)."""
    q = _runnable(db, qid)
    result = await run_in_threadpool(code_runner.run_tests, body.code, q.tests, True)
    db.add(QuestionAttempt(user_id=user.id, question_id=q.id, response=body.code[:8000],
                           is_correct=result["all_passed"], self_marked=False))
    log_event(db, user.id, "attempt", question_id=q.id, subject=q.subject, correct=result["all_passed"],
              passed=result["passed"], total=result["total"])
    db.commit()
    return {**result, "solution": q.solution, "explanation": q.explanation, "stats": _stats(db, user.id, [q.id]).get(q.id)}
