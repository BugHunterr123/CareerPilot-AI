"""Dashboard: one call that gathers the student's real data for the home page."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_profile
from app.models import (CareerRecommendation, Company, MockInterview, ProfileLink, Resume, Roadmap, SavedQuestion, Skill,
                        SkillGapReport, User)
from app.routers.progress import journey, readiness
from app.security import get_current_user
from app.serializers import task_out
from app.services.roles import role_title

router = APIRouter(prefix="/api", tags=["progress & dashboard"])


@router.get("/dashboard")
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prof = get_profile(db, user)
    resume = db.scalar(select(Resume).where(Resume.user_id == user.id, Resume.is_active.is_(True)))
    skills = db.scalars(select(Skill).where(Skill.user_id == user.id)).all()
    recs = db.scalars(select(CareerRecommendation).where(CareerRecommendation.user_id == user.id)
                      .order_by(CareerRecommendation.match_pct.desc()).limit(3)).all()
    company = db.get(Company, prof.target_company_id) if prof.target_company_id else None
    gap = db.scalar(select(SkillGapReport).where(SkillGapReport.user_id == user.id).order_by(SkillGapReport.id.desc()))
    rm = db.scalar(select(Roadmap).where(Roadmap.user_id == user.id, Roadmap.is_active.is_(True)))
    last_mi = db.scalar(select(MockInterview).where(MockInterview.user_id == user.id, MockInterview.status == "completed")
                        .order_by(MockInterview.id.desc()))
    fields = [prof.college, prof.degree, prof.branch, prof.graduation_year, resume is not None, prof.optional_step_done]
    steps = journey(db, user)
    nxt = next((s for s in steps if not s["done"]), None)
    return {
        "name": user.full_name.split()[0],
        "profile_completion": round(100 * sum(bool(f) for f in fields) / len(fields)),
        "journey": steps,
        "next_step": nxt,
        "resume": {"filename": resume.filename, "status": resume.parse_status, "reviewed": resume.reviewed,
                   "strengths": resume.analysis.get("strengths", [])[:2]} if resume else None,
        "skills": {"total": len(skills), **{lv: sum(s.level == lv for s in skills) for lv in ("validated", "project", "claimed", "inferred")},
                   "top": [s.name for s in sorted(skills, key=lambda s: ["validated", "project", "claimed", "inferred"].index(s.level))[:8]]},
        "roles": [{"role_key": r.role_key, "title": r.title, "match_pct": r.match_pct} for r in recs],
        "target": {"role": role_title(prof.target_role_key) if prof.target_role_key else None,
                   "company": company.name if company else None, "company_slug": company.slug if company else None},
        "gap": {"shown": gap.summary["shown"], "partial": gap.summary["partial"], "missing": gap.summary["missing"],
                "top": [i["skill"] for i in gap.items if i["priority"] == "high"][:5]} if gap else None,
        "roadmap": {"total": len(rm.tasks), "done": sum(t.status == "done" for t in rm.tasks), "plan_type": rm.plan_type,
                    "upcoming": [task_out(t) for t in rm.tasks if t.status == "todo"][:4]} if rm else None,
        "saved_questions": db.scalar(select(func.count()).where(SavedQuestion.user_id == user.id)),
        "last_interview": {"id": last_mi.id, "overall": last_mi.overall, "type": last_mi.itype,
                           "date": last_mi.created_at.isoformat()} if last_mi else None,
        "readiness": readiness(db, user),
        "links_added": db.scalar(select(func.count()).where(ProfileLink.user_id == user.id)),
    }
