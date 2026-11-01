"""Skill Intelligence and Career Recommendations."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_profile, log_event, owned
from app.models import CareerRecommendation, ProfileLink, Resume, Skill, User
from app.schemas import SelectRoleIn, SkillIn
from app.security import get_current_user
from app.serializers import skill_out
from app.services.recommender import recommend
from app.services.roles import ROLES
from app.services.skills_engine import rebuild_skills
from app.services.taxonomy import CATEGORIES, canonical, category_of

router = APIRouter(prefix="/api", tags=["skills & careers"])


def _basis(db: Session, user: User) -> dict:
    links = db.scalars(select(ProfileLink).where(ProfileLink.user_id == user.id)).all()
    has_resume = db.scalar(select(Resume.id).where(Resume.user_id == user.id)) is not None
    ok = [l.kind for l in links if l.status == "ok"]
    note = ("Based on your resume only. That is enough to get started; adding a GitHub link or practising questions "
            "makes this more accurate.") if not ok else f"Based on your resume plus: {', '.join(ok)}."
    return {"has_resume": has_resume, "sources_used": ["resume"] + ok, "limited_info": not ok, "note": note,
            "unavailable": [{"kind": l.kind, "note": l.note} for l in links if l.status in ("unavailable", "invalid")]}


@router.get("/skills")
def list_skills(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    skills = db.scalars(select(Skill).where(Skill.user_id == user.id).order_by(Skill.name)).all()
    by_level = {lv: sum(s.level == lv for s in skills) for lv in ("validated", "project", "claimed", "inferred")}
    groups = [{"category": c, "skills": [skill_out(s) for s in skills if s.category == c]} for c in CATEGORIES]
    return {"basis": _basis(db, user), "counts": by_level, "total": len(skills),
            "groups": [g for g in groups if g["skills"]]}


@router.post("/skills", status_code=201)
def add_skill(body: SkillIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    name = canonical(body.name) or body.name.strip()
    if db.scalar(select(Skill).where(Skill.user_id == user.id, Skill.name == name)):
        raise HTTPException(409, f"{name} is already in your skills.")
    db.add(Skill(user_id=user.id, name=name, category=category_of(name), user_added=True))
    db.commit()
    rebuild_skills(db, user.id)
    return {"ok": True, "name": name}


@router.delete("/skills/{skill_id}")
def remove_skill(skill_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = owned(db, Skill, skill_id, user)
    r = db.scalar(select(Resume).where(Resume.user_id == user.id, Resume.is_active.is_(True)))
    if r:  # remember the removal so a rebuild does not bring it back
        r.parsed = {**r.parsed, "removed_skills": list(set(r.parsed.get("removed_skills", [])) | {s.name})}
    db.delete(s)
    db.commit()
    return {"ok": True}


@router.post("/skills/rebuild")
def rebuild(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rebuild_skills(db, user.id)
    return list_skills(user, db)


@router.get("/careers")
def careers(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recs = db.scalars(select(CareerRecommendation).where(CareerRecommendation.user_id == user.id)
                      .order_by(CareerRecommendation.match_pct.desc())).all()
    if not recs and db.scalar(select(Skill.id).where(Skill.user_id == user.id)):
        recs = sorted(recommend(db, user.id), key=lambda r: -r.match_pct)
    prof = get_profile(db, user)
    return {"basis": _basis(db, user), "selected": prof.target_role_key,
            "method": "match % = earned weight / total weight. Evidence earns: validated 100%, project 80%, "
                      "claimed 40%, AI-inferred 25%. Core skills weigh 3, important 2, nice-to-have 1. "
                      "+5 points if the role matches an interest you gave. This is a fit indicator, not a hiring prediction.",
            "roles": [{"role_key": r.role_key, "title": r.title, "match_pct": r.match_pct, **r.details} for r in recs]}


@router.post("/careers/refresh")
def refresh(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rebuild_skills(db, user.id)
    recommend(db, user.id)
    return careers(user, db)


@router.post("/careers/select")
def select_role(body: SelectRoleIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.role_key not in ROLES:
        raise HTTPException(422, "Unknown role.")
    prof = get_profile(db, user)
    prof.target_role_key = body.role_key
    log_event(db, user.id, "role_selected", role=body.role_key)
    db.commit()
    return {"ok": True, "target_role_key": body.role_key}


@router.get("/roles")
def roles():
    return [{"role_key": k, "title": v["title"], "summary": v["summary"]} for k, v in ROLES.items()]
