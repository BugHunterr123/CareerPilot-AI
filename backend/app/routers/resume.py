"""Mandatory resume upload, parsing, review/edit and deletion."""
import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.deps import get_profile, log_event
from app.models import Project, Resume, User
from app.ratelimit import limiter
from app.schemas import ResumeReviewIn
from app.security import get_current_user
from app.services.profile_analysis import analyse_text, build_report, sync_projects
from app.services.recommender import recommend
from app.services.resume_files import ResumeFileError, extract_text, validate_upload
from app.services.skills_engine import rebuild_skills

router = APIRouter(prefix="/api/resume", tags=["resume"])


def active_resume(db: Session, user: User) -> Resume | None:
    return db.scalar(select(Resume).where(Resume.user_id == user.id, Resume.is_active.is_(True)))


def resume_out(db: Session, r: Resume) -> dict:
    projects = db.scalars(select(Project).where(Project.user_id == r.user_id)).all()
    return {"id": r.id, "filename": r.filename, "size_bytes": r.size_bytes, "uploaded_at": r.created_at.isoformat(),
            "parse_status": r.parse_status, "warnings": r.warnings, "reviewed": r.reviewed, "engine": r.engine,
            "parsed": r.parsed, "analysis": r.analysis, "text_preview": r.text[:1500],
            "projects": [{"id": p.id, "name": p.name, "description": p.description, "technologies": p.technologies,
                          "source": p.source} for p in projects]}


def _refresh(db: Session, user: User, r: Resume) -> None:
    """Re-run everything that depends on the resume: projects -> skills -> roles -> report."""
    sync_projects(db, user.id, r.parsed)
    rebuild_skills(db, user.id)
    recommend(db, user.id)
    r.analysis = build_report(db, user.id, r.parsed)
    db.commit()


@router.post("", status_code=201, dependencies=[Depends(limiter("ai"))])
async def upload(file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    try:
        ext = validate_upload(file.filename or "", data)
        text = extract_text(ext, data)
    except ResumeFileError as exc:
        raise HTTPException(422, str(exc))
    parsed, engine, warnings = analyse_text(text)
    # keep only the latest resume: delete older files and rows
    for old in db.scalars(select(Resume).where(Resume.user_id == user.id)):
        Path(old.stored_path).unlink(missing_ok=True)
        db.delete(old)
    folder = Path(settings.upload_dir) / str(user.id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid.uuid4().hex}{ext}"  # random name: never trust the uploaded filename
    path.write_bytes(data)
    r = Resume(user_id=user.id, filename=(file.filename or "resume")[:255], stored_path=str(path),
               content_type=file.content_type or "", size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
               text=text, parsed=parsed, warnings=warnings, engine=engine,
               parse_status="needs_review" if (not parsed["skills"] and not parsed["projects"]) else "ok")
    db.add(r)
    db.flush()
    prof = get_profile(db, user)
    edu = next((e for e in parsed["education"] if e.get("institution")), None)
    if edu and not prof.college:  # pre-fill, the student can edit it
        prof.college = edu["institution"][:200]
    _refresh(db, user, r)
    log_event(db, user.id, "resume_uploaded", engine=engine, skills=len(parsed["skills"]))
    db.commit()
    return resume_out(db, r)


@router.get("")
def get(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = active_resume(db, user)
    if not r:
        return None  # "nothing yet" is a normal state, not an error
    return resume_out(db, r)


@router.put("/review")
def review(body: ResumeReviewIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """The student corrects what we extracted. Their version wins from now on."""
    r = active_resume(db, user)
    if not r:
        raise HTTPException(404, "Upload your resume first.")
    parsed = dict(r.parsed)
    before = {s.lower() for s in parsed.get("skills", [])}
    parsed["skills"] = list(dict.fromkeys(s.strip() for s in body.skills if s.strip()))
    removed = [s for s in before if s not in {x.lower() for x in parsed["skills"]}]
    from app.services.taxonomy import canonical
    parsed["removed_skills"] = list({c for s in removed if (c := canonical(s))})
    parsed["projects"] = [p.model_dump() for p in body.projects]
    parsed["education"] = [e.model_dump() | {"raw": ""} for e in body.education]
    parsed["certifications"] = [c for c in body.certifications if c.strip()]
    parsed["achievements"] = [a for a in body.achievements if a.strip()]
    r.parsed = parsed
    r.reviewed = True
    r.parse_status = "ok"
    _refresh(db, user, r)
    log_event(db, user.id, "resume_reviewed")
    db.commit()
    return resume_out(db, r)


@router.get("/file")
def download(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = active_resume(db, user)
    if not r or not Path(r.stored_path).exists():
        raise HTTPException(404, "No resume file found.")
    return FileResponse(r.stored_path, filename=r.filename)


@router.delete("")
def delete(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = active_resume(db, user)
    if not r:
        raise HTTPException(404, "No resume to delete.")
    Path(r.stored_path).unlink(missing_ok=True)
    db.delete(r)
    db.commit()
    return {"ok": True, "message": "Your resume file and its extracted text were deleted."}


SAMPLE = Path(__file__).resolve().parent.parent.parent / "sample_data" / "sample_resume.pdf"


@router.get("/sample", include_in_schema=False)
def sample_resume():
    """A clearly labelled synthetic resume for trying the app. It is never loaded automatically."""
    if not SAMPLE.exists():
        raise HTTPException(404, "Sample resume not available.")
    return FileResponse(SAMPLE, media_type="application/pdf", filename="CareerPilot_sample_resume_SYNTHETIC.pdf")
