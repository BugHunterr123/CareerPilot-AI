"""Companies, their roles, recruitment stages, sources and learning resources."""
from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.common import IdMixin, TimestampMixin


class Company(IdMixin, TimestampMixin, Base):
    __tablename__ = "companies"
    slug: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    overview: Mapped[str] = mapped_column(Text, default="")
    overview_source_key: Mapped[str | None] = mapped_column(String(20), nullable=True)
    careers_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    variation_note: Mapped[str] = mapped_column(Text, default="")
    research_date: Mapped[str] = mapped_column(String(20), default="")
    seed_hash: Mapped[str] = mapped_column(String(64), default="")  # lets the seeder skip unchanged files
    roles: Mapped[list["JobRole"]] = relationship(cascade="all, delete-orphan", lazy="selectin", order_by="JobRole.id")
    stages: Mapped[list["HiringStage"]] = relationship(cascade="all, delete-orphan", lazy="selectin", order_by="HiringStage.order")
    sources: Mapped[list["SourceRef"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class SourceRef(IdMixin, Base):
    """Where a claim came from. label tells the student how much to trust it."""
    __tablename__ = "source_refs"
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    key: Mapped[str] = mapped_column(String(20))  # e.g. "s3" (unique within a company)
    url: Mapped[str] = mapped_column(String(600))
    title: Mapped[str] = mapped_column(String(300), default="")
    publisher: Mapped[str] = mapped_column(String(120), default="")
    date: Mapped[str | None] = mapped_column(String(20), nullable=True)  # page's own date, if shown
    accessed: Mapped[str] = mapped_column(String(20), default="")
    label: Mapped[str] = mapped_column(String(30))  # Official / Candidate-reported / Third-party


class JobRole(IdMixin, Base):
    __tablename__ = "job_roles"
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text, default="")
    role_key: Mapped[str] = mapped_column(String(60), default="software_developer")
    skills: Mapped[list] = mapped_column(JSON, default=list)
    eligibility: Mapped[list] = mapped_column(JSON, default=list)  # [{text, source}]
    compensation: Mapped[list] = mapped_column(JSON, default=list)  # [{text, source}]


class HiringStage(IdMixin, Base):
    __tablename__ = "hiring_stages"
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    order: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(160))
    kind: Mapped[str] = mapped_column(String(40))  # aptitude / coding / technical_mcq / ... / hr_interview
    what: Mapped[str] = mapped_column(Text, default="")
    format: Mapped[list] = mapped_column(JSON, default=list)  # [{text, source}]
    evaluates: Mapped[list] = mapped_column(JSON, default=list)
    study: Mapped[list] = mapped_column(JSON, default=list)
    tips: Mapped[list] = mapped_column(JSON, default=list)
    before_next: Mapped[str] = mapped_column(Text, default="")
    label: Mapped[str] = mapped_column(String(30), default="Candidate-reported")


class LearningResource(IdMixin, Base):
    """A free study link, tagged by topic so the planner can pick the right ones."""
    __tablename__ = "learning_resources"
    title: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(String(500))
    provider: Mapped[str] = mapped_column(String(80), default="")
    kind: Mapped[str] = mapped_column(String(20), default="article")  # article / docs / practice / video / course
    topic: Mapped[str] = mapped_column(String(60), index=True)  # matches skill names / subjects
    free: Mapped[bool] = mapped_column(Boolean, default=True)
    minutes: Mapped[int] = mapped_column(Integer, default=30)
