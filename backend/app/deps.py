"""Shared dependencies and small helpers for routers."""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ProgressEvent, StudentProfile, User


def get_profile(db: Session, user: User) -> StudentProfile:
    prof = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    if prof is None:
        prof = StudentProfile(user_id=user.id)
        db.add(prof)
        db.commit()
    return prof


def owned(db: Session, model, obj_id: int, user: User):
    """Fetch a row by id ONLY if it belongs to this user. Otherwise 404 (we do not reveal that it exists)."""
    obj = db.get(model, obj_id)
    if obj is None or getattr(obj, "user_id", None) != user.id:
        raise HTTPException(404, "Not found.")
    return obj


def log_event(db: Session, user_id: int, kind: str, **detail) -> None:
    db.add(ProgressEvent(user_id=user_id, kind=kind, detail=detail))
