"""Skill gap analysis and the personalised preparation roadmap."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_profile, log_event, owned
from app.models import Company, Roadmap, RoadmapTask, Skill, SkillGapReport, User
from app.schemas import GapIn, RoadmapIn, TaskPatch
from app.security import get_current_user
from app.serializers import roadmap_out, task_out
from app.services import gap_analysis, planner
from app.services.roles import ROLES

router = APIRouter(prefix="/api", tags=["gap & roadmap"])


def gap_out(r: SkillGapReport) -> dict:
    return {"id": r.id, "role_key": r.role_key, "company_id": r.company_id, "created_at": r.created_at.isoformat(),
            "job_description_used": bool(r.job_description), "items": r.items, "summary": r.summary}


@router.post("/gaps")
def run_gap(body: GapIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.role_key not in ROLES:
        raise HTTPException(422, "Unknown role.")
    if body.company_id and not db.get(Company, body.company_id):
        raise HTTPException(404, "Company not found.")
    if not db.scalar(select(Skill.id).where(Skill.user_id == user.id)):
        raise HTTPException(409, "Upload your resume first so we know your current skills.")
    rep = gap_analysis.analyse(db, user.id, body.role_key, body.company_id, body.job_description)
    log_event(db, user.id, "gap_analysis", role=body.role_key, missing=rep.summary["missing"])
    db.commit()
    return gap_out(rep)


@router.get("/gaps/latest")
def latest_gap(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rep = db.scalar(select(SkillGapReport).where(SkillGapReport.user_id == user.id).order_by(SkillGapReport.id.desc()))
    if not rep:
        return None  # "nothing yet" is a normal state, not an error
    return gap_out(rep)


def _company_name(db: Session, cid: int | None) -> str | None:
    c = db.get(Company, cid) if cid else None
    return c.name if c else None


@router.post("/roadmap/generate")
def generate(body: RoadmapIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prof = get_profile(db, user)
    role_key = body.role_key or prof.target_role_key or "software_developer"
    if role_key not in ROLES:
        raise HTTPException(422, "Unknown role.")
    company_id = body.company_id if body.company_id is not None else (prof.target_company_id if body.use_target_company else None)
    if not db.scalar(select(Skill.id).where(Skill.user_id == user.id)):
        raise HTTPException(409, "Upload your resume first so the plan can be built around your skills.")
    if body.weekly_hours:
        prof.weekly_hours = body.weekly_hours
    if body.target_date:
        prof.target_date = body.target_date
    rm = planner.generate(db, user.id, role_key, company_id, body.weekly_hours, body.target_date)
    log_event(db, user.id, "plan_generated", tasks=len(rm.tasks), ms=rm.generation_ms, company=company_id)
    db.commit()
    return roadmap_out(rm, _company_name(db, rm.company_id))


@router.get("/roadmap")
def get_roadmap(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rm = db.scalar(select(Roadmap).where(Roadmap.user_id == user.id, Roadmap.is_active.is_(True)))
    if not rm:
        return None  # "nothing yet" is a normal state, not an error
    return roadmap_out(rm, _company_name(db, rm.company_id))


@router.patch("/roadmap/tasks/{task_id}")
def update_task(task_id: int, body: TaskPatch, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    t = owned(db, RoadmapTask, task_id, user)
    if body.status:
        t.status = body.status
        t.completed_at = datetime.now(timezone.utc) if body.status == "done" else None
        if body.status == "done":
            log_event(db, user.id, "task_done", task_id=t.id, topic=t.topic, skill=t.skill, minutes=t.est_minutes)
    if body.due_date:
        t.due_date = body.due_date
    db.commit()
    return task_out(t)
