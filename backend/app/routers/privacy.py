"""Privacy: export everything we store about you, or delete your account."""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import (ChatMessage, JobApplication, MockInterview, ProfileLink, Project, QuestionAttempt, Resume, Roadmap,
                        Skill, User)
from app.schemas import DeleteAccountIn
from app.security import get_current_user, verify_password
from app.serializers import profile_out, roadmap_out, skill_out, user_out

router = APIRouter(prefix="/api/privacy", tags=["privacy"])


@router.get("/export")
def export(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = lambda m: db.scalars(select(m).where(m.user_id == user.id)).all()  # noqa: E731
    resume = q(Resume)
    return {
        "user": user_out(user), "profile": profile_out(user.profile),
        "resume": [{"filename": r.filename, "uploaded_at": r.created_at.isoformat(), "parsed": r.parsed} for r in resume],
        "projects": [{"name": p.name, "description": p.description, "technologies": p.technologies} for p in q(Project)],
        "skills": [skill_out(s) for s in q(Skill)],
        "links": [{"kind": l.kind, "url": l.url, "status": l.status} for l in q(ProfileLink)],
        "roadmaps": [roadmap_out(r) for r in q(Roadmap)],
        "attempts": [{"question_id": a.question_id, "correct": a.is_correct, "at": a.created_at.isoformat()} for a in q(QuestionAttempt)],
        "interviews": [{"id": m.id, "type": m.itype, "overall": m.overall, "report": m.report.content if m.report else None}
                       for m in q(MockInterview)],
        "applications": [{"company": a.company_name, "status": a.status} for a in q(JobApplication)],
        "chat": [{"role": c.role, "content": c.content} for c in q(ChatMessage)],
    }


@router.delete("/account")
def delete_account(body: DeleteAccountIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(403, "Password is incorrect.")
    for r in db.scalars(select(Resume).where(Resume.user_id == user.id)):
        Path(r.stored_path).unlink(missing_ok=True)
    db.delete(user)  # foreign keys use ON DELETE CASCADE, so all rows owned by the user go too
    db.commit()
    return {"ok": True, "message": "Your account and all your data were deleted."}
