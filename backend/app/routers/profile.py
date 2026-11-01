"""Student profile (mandatory education details + optional preferences) and optional links."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_profile, owned
from app.models import ProfileLink, User
from app.schemas import LinkIn, ProfileIn
from app.security import get_current_user
from app.serializers import profile_out, user_out
from app.services.external_profiles import analyse_link, validate_url
from app.services.skills_engine import rebuild_skills

router = APIRouter(prefix="/api/profile", tags=["profile"])


def link_out(l: ProfileLink) -> dict:
    return {"id": l.id, "kind": l.kind, "url": l.url, "consent": l.consent, "status": l.status, "note": l.note,
            "manual_details": l.manual_details, "summary": l.summary,
            "last_checked": l.last_checked.isoformat() if l.last_checked else None}


@router.get("")
def get(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prof = get_profile(db, user)
    links = db.scalars(select(ProfileLink).where(ProfileLink.user_id == user.id)).all()
    return {"user": user_out(user), "profile": profile_out(prof), "links": [link_out(l) for l in links]}


@router.put("")
def update(body: ProfileIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prof = get_profile(db, user)
    data = body.model_dump(exclude_unset=True)
    if "full_name" in data and data["full_name"]:
        user.full_name = data.pop("full_name").strip()
    data.pop("full_name", None)
    for k, v in data.items():
        if isinstance(v, list):
            v = [x.strip() for x in v if x and x.strip()][:30]
        setattr(prof, k, v)
    db.commit()
    return {"user": user_out(user), "profile": profile_out(prof)}


@router.post("/optional-done")
def optional_done(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The student finished (or skipped) the optional links step."""
    prof = get_profile(db, user)
    prof.optional_step_done = True
    db.commit()
    return {"ok": True}


@router.post("/links", status_code=201)
def add_link(body: LinkIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        url = validate_url(body.kind, body.url)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    link = ProfileLink(user_id=user.id, kind=body.kind, url=url, consent=body.consent, manual_details=body.manual_details)
    analyse_link(link)
    db.add(link)
    db.commit()
    rebuild_skills(db, user.id)
    return link_out(link)


@router.post("/links/{link_id}/check")
def recheck(link_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    link = owned(db, ProfileLink, link_id, user)
    analyse_link(link)
    db.commit()
    rebuild_skills(db, user.id)
    return link_out(link)


@router.delete("/links/{link_id}")
def delete_link(link_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(owned(db, ProfileLink, link_id, user))
    db.commit()
    rebuild_skills(db, user.id)
    return {"ok": True}
