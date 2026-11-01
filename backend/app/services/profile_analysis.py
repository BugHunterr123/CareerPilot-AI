"""
Profile Analysis Service: resume text -> structured profile -> report.

Rule-based parsing always runs. If an LLM is configured, it is asked for the same
structure, and anything it returns that cannot be found in the resume text is
DROPPED (a hallucination guard), so the AI can only organise, never invent.
"""
import re

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Project, Skill
from app.services import llm
from app.services.resume_parser import parse_resume
from app.services.taxonomy import canonical


class LLMProject(BaseModel):
    name: str
    description: str = ""
    technologies: list[str] = Field(default_factory=list)


class LLMResume(BaseModel):
    skills: list[str] = Field(default_factory=list)
    projects: list[LLMProject] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


def _in_text(phrase: str, text: str) -> bool:
    words = [w for w in re.findall(r"\w+", phrase.lower()) if len(w) > 2][:4]
    low = text.lower()
    return bool(words) and all(w in low for w in words)


def analyse_text(text: str) -> tuple[dict, str, list[str]]:
    parsed = parse_resume(text)
    engine = "rules"
    ai = llm.try_structured(
        "You extract facts from a student's resume. Copy only what is written. Never add skills or projects.",
        text[:12000], LLMResume)
    if ai:
        engine = "llm"
        skills = [s for s in ai.skills if _in_text(s, text) or canonical(s)]
        parsed["skills"] = list(dict.fromkeys(parsed["skills"] + skills))
        good = [p.model_dump() for p in ai.projects if _in_text(p.name, text)]
        if len(good) >= len(parsed["projects"]):
            parsed["projects"] = good
        for key in ("certifications", "achievements"):
            extra = [x for x in getattr(ai, key) if _in_text(x, text)]
            parsed[key] = list(dict.fromkeys(parsed[key] + extra))
    warnings = []
    if not parsed["skills"]:
        warnings.append("We could not find a skills section. Add your skills below so we can analyse them.")
    if not parsed["projects"]:
        warnings.append("We could not find any projects. Projects are the strongest evidence of your skills; add them below.")
    if not parsed["education"]:
        warnings.append("We could not find your education details. Please check them in your profile.")
    short_lines = sum(1 for ln in text.split("\n") if 0 < len(ln.strip()) < 12)
    if short_lines > 40:
        warnings.append("Your resume may use columns or tables, which can scramble the reading order. Please review carefully.")
    return parsed, engine, warnings


def sync_projects(db: Session, user_id: int, parsed: dict) -> None:
    """Resume projects are replaced on each upload; projects added by hand are kept."""
    db.query(Project).filter(Project.user_id == user_id, Project.source == "resume").delete()
    for p in parsed.get("projects", []):
        db.add(Project(user_id=user_id, name=p["name"][:200], description=p.get("description", ""),
                       technologies=p.get("technologies", []), source="resume"))
    db.commit()


def build_report(db: Session, user_id: int, parsed: dict) -> dict:
    """The resume analysis report shown on the Resume Analysis page."""
    skills = db.scalars(select(Skill).where(Skill.user_id == user_id)).all()
    projects = db.scalars(select(Project).where(Project.user_id == user_id)).all()
    proven = [s.name for s in skills if s.level in ("project", "validated")]
    claimed_only = [s.name for s in skills if s.level == "claimed" and s.category != "Communication and Behavioural"]
    numbers = [p.name for p in projects if re.search(r"\d", p.description or "")]
    strengths, missing, tips = [], [], []
    if proven:
        strengths.append(f"{len(proven)} skills are backed by your projects: {', '.join(proven[:8])}.")
    if numbers:
        strengths.append(f"You use numbers to show impact in: {', '.join(numbers[:3])}.")
    if len(projects) >= 3:
        strengths.append(f"You list {len(projects)} projects, which gives interviewers plenty to ask about.")
    if parsed.get("certifications"):
        strengths.append(f"{len(parsed['certifications'])} certification(s) listed.")
    if claimed_only:
        missing.append(f"Listed but not shown in any project: {', '.join(claimed_only[:8])}.")
    if not parsed.get("experience"):
        missing.append("No internship or work experience found. That is normal for many freshers; projects matter more.")
    if not any(e.get("score") for e in parsed.get("education", [])):
        missing.append("No CGPA or percentage found. Many campus drives filter on it, so add it if you can.")
    if not parsed.get("links"):
        missing.append("No GitHub or portfolio link. Optional, but it lets interviewers see your code.")
    if len(projects) - len(numbers) > 0:
        tips.append("Add one number to each project (users, rows of data, accuracy, response time).")
    if claimed_only:
        tips.append(f"Either show {claimed_only[0]} in a project line or move it to a 'familiar with' list.")
    tips.append("Start each project bullet with a verb: Built, Designed, Reduced, Tested.")
    tips.append("Keep it to one page and put Projects above Certifications.")
    return {"strengths": strengths, "missing": missing, "suggestions": tips,
            "skill_count": len(skills), "project_count": len(projects)}
