"""Company Explorer: searchable companies with source-backed hiring guides."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_profile, log_event
from app.models import Company, PracticeQuestion, User
from app.schemas import SelectCompanyIn
from app.security import get_current_user
from app.serializers import company_detail, company_summary
from app.services.roles import ROLES

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("")
def list_companies(q: str = "", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    stmt = select(Company).order_by(Company.name)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Company.name.ilike(like), Company.overview.ilike(like)))
    counts = dict(db.execute(select(PracticeQuestion.company_id, func.count()).group_by(PracticeQuestion.company_id)).all())
    prof = get_profile(db, user)
    return {"selected_id": prof.target_company_id,
            "companies": [company_summary(c, counts.get(c.id, 0)) for c in db.scalars(stmt)]}


@router.get("/{slug}")
def get_company(slug: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.scalar(select(Company).where(Company.slug == slug))
    if not c:
        raise HTTPException(404, "We do not have this company yet. A general role-based guide is still available.")
    out = company_detail(c)
    out["question_count"] = db.scalar(select(func.count()).where(PracticeQuestion.company_id == c.id))
    out["selected"] = get_profile(db, user).target_company_id == c.id
    return out


@router.post("/{slug}/select")
def select_company(slug: str, body: SelectCompanyIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.scalar(select(Company).where(Company.slug == slug))
    if not c:
        raise HTTPException(404, "Company not found.")
    prof = get_profile(db, user)
    prof.target_company_id = c.id
    if body.role_key and body.role_key in ROLES:
        prof.target_role_key = body.role_key
    elif not prof.target_role_key and c.roles:
        prof.target_role_key = c.roles[0].role_key
    log_event(db, user.id, "company_selected", company=c.slug)
    db.commit()
    return {"ok": True, "target_company_id": c.id, "target_role_key": prof.target_role_key}
