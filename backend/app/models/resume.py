"""Resume files, parsed content, skills (with evidence) and projects."""
from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.common import IdMixin, TimestampMixin


class Resume(IdMixin, TimestampMixin, Base):
    __tablename__ = "resumes"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    stored_path: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    text: Mapped[str] = mapped_column(Text, default="")
    # parsed = structured extraction (education, skills, projects, experience ...)
    parsed: Mapped[dict] = mapped_column(JSON, default=dict)
    # analysis = report (strengths, missing info, suggestions, directions)
    analysis: Mapped[dict] = mapped_column(JSON, default=dict)
    parse_status: Mapped[str] = mapped_column(String(20), default="ok")  # ok / needs_review
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    engine: Mapped[str] = mapped_column(String(20), default="rules")  # rules / llm


class Project(IdMixin, TimestampMixin, Base):
    __tablename__ = "projects"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    technologies: Mapped[list] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(20), default="resume")  # resume / manual / github
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)


class Skill(IdMixin, TimestampMixin, Base):
    """One skill of one student. How much we trust it lives in `evidence`."""
    __tablename__ = "skills"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    category: Mapped[str] = mapped_column(String(60))
    # Strongest evidence level: validated > project > claimed > inferred
    level: Mapped[str] = mapped_column(String(20), default="claimed")
    confidence: Mapped[str] = mapped_column(String(10), default="low")  # low / medium / high
    next_step: Mapped[str] = mapped_column(Text, default="")
    needs_validation: Mapped[str] = mapped_column(Text, default="")
    user_added: Mapped[bool] = mapped_column(Boolean, default=False)
    evidence: Mapped[list["SkillEvidence"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class SkillEvidence(IdMixin, TimestampMixin, Base):
    __tablename__ = "skill_evidence"
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))  # claimed / project / experience / practice / inferred / github
    source: Mapped[str] = mapped_column(String(200))  # e.g. "Resume: Skills section", "Project: Smart Notes"
    quote: Mapped[str] = mapped_column(Text, default="")
