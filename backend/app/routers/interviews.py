"""AI mock interviewer: one question at a time, rubric scoring, final report."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_profile, owned
from app.models import Company, MockInterview, User
from app.ratelimit import limiter
from app.schemas import AnswerIn, InterviewIn
from app.security import get_current_user
from app.serializers import interview_out
from app.services import interview_flow
from app.services.roles import ROLES

router = APIRouter(prefix="/api/interviews", tags=["mock interviews"])


def _name(db: Session, cid: int | None) -> str | None:
    c = db.get(Company, cid) if cid else None
    return c.name if c else None


@router.post("", status_code=201, dependencies=[Depends(limiter("ai"))])
def start(body: InterviewIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prof = get_profile(db, user)
    role_key = body.role_key or prof.target_role_key or "software_developer"
    if role_key not in ROLES:
        raise HTTPException(422, "Unknown role.")
    company_id = body.company_id if body.company_id is not None else prof.target_company_id
    mi = interview_flow.start(db, user.id, role_key, company_id, body.itype, body.difficulty, body.duration_min)
    return interview_out(mi, _name(db, mi.company_id))


@router.get("")
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(MockInterview).where(MockInterview.user_id == user.id).order_by(MockInterview.id.desc())).all()
    return [{"id": m.id, "itype": m.itype, "difficulty": m.difficulty, "status": m.status, "overall": m.overall,
             "role_key": m.role_key, "created_at": m.created_at.isoformat(), "questions": len(m.plan),
             "answered": len(m.responses), "company_name": _name(db, m.company_id), "scoring_mode": m.scoring_mode} for m in rows]


@router.get("/{iid}")
def get(iid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    mi = owned(db, MockInterview, iid, user)
    return interview_out(mi, _name(db, mi.company_id))


@router.post("/{iid}/answer", dependencies=[Depends(limiter("ai"))])
def answer(iid: int, body: AnswerIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    mi = owned(db, MockInterview, iid, user)
    if mi.status != "active":
        raise HTTPException(409, "This interview is already finished.")
    resp = interview_flow.answer(db, mi, body.answer.strip())
    out = interview_out(mi, _name(db, mi.company_id))
    out["last_feedback"] = {"question": resp.question, "scores": resp.scores, "feedback": resp.feedback, "total": resp.total}
    return out


@router.post("/{iid}/finish")
def finish_early(iid: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    mi = owned(db, MockInterview, iid, user)
    if mi.status == "active":
        if not mi.responses:
            raise HTTPException(409, "Answer at least one question before ending the interview.")
        mi.plan = mi.plan[: len(mi.responses)]
        interview_flow.finish(db, mi)
        db.commit()
    return interview_out(mi, _name(db, mi.company_id))
