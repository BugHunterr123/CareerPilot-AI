"""Recommendations, gap reports, roadmaps and the practice question bank."""
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.common import IdMixin, TimestampMixin


class CareerRecommendation(IdMixin, TimestampMixin, Base):
    __tablename__ = "career_recommendations"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role_key: Mapped[str] = mapped_column(String(60))
    title: Mapped[str] = mapped_column(String(120))
    match_pct: Mapped[float] = mapped_column(Float)
    details: Mapped[dict] = mapped_column(JSON, default=dict)  # why, relevant, missing, learn, projects, resources
    limited_info: Mapped[bool] = mapped_column(Boolean, default=True)


class SkillGapReport(IdMixin, TimestampMixin, Base):
    __tablename__ = "skill_gap_reports"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role_key: Mapped[str] = mapped_column(String(60))
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    job_description: Mapped[str] = mapped_column(Text, default="")
    items: Mapped[list] = mapped_column(JSON, default=list)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)


class Roadmap(IdMixin, TimestampMixin, Base):
    __tablename__ = "roadmaps"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role_key: Mapped[str] = mapped_column(String(60))
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    weekly_hours: Mapped[int] = mapped_column(Integer, default=8)
    start_date: Mapped[date] = mapped_column(Date)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    plan_type: Mapped[str] = mapped_column(String(40))  # company-specific / general role-based
    notes: Mapped[list] = mapped_column(JSON, default=list)
    generation_ms: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tasks: Mapped[list["RoadmapTask"]] = relationship(cascade="all, delete-orphan", lazy="selectin",
                                                       order_by="RoadmapTask.due_date, RoadmapTask.id")


class RoadmapTask(IdMixin, TimestampMixin, Base):
    __tablename__ = "roadmap_tasks"
    roadmap_id: Mapped[int] = mapped_column(ForeignKey("roadmaps.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    week: Mapped[int] = mapped_column(Integer)
    due_date: Mapped[date] = mapped_column(Date)
    topic: Mapped[str] = mapped_column(String(160))
    skill: Mapped[str] = mapped_column(String(80), default="")
    explanation: Mapped[str] = mapped_column(Text, default="")
    why: Mapped[str] = mapped_column(Text, default="")
    resources: Mapped[list] = mapped_column(JSON, default=list)
    practice: Mapped[dict] = mapped_column(JSON, default=dict)  # filter for the question bank
    est_minutes: Mapped[int] = mapped_column(Integer, default=60)
    priority: Mapped[str] = mapped_column(String(10), default="medium")
    status: Mapped[str] = mapped_column(String(12), default="todo")  # todo / done / skipped
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PracticeQuestion(IdMixin, Base):
    __tablename__ = "practice_questions"
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=True, index=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("source_refs.id", ondelete="SET NULL"), nullable=True)
    stage_kind: Mapped[str] = mapped_column(String(40), default="technical_mcq")
    subject: Mapped[str] = mapped_column(String(40), index=True)
    qtype: Mapped[str] = mapped_column(String(12))  # mcq / coding / sql / short / hr
    difficulty: Mapped[str] = mapped_column(String(10), default="medium")
    role_keys: Mapped[list] = mapped_column(JSON, default=list)  # empty = useful for every role
    question: Mapped[str] = mapped_column(Text)
    code: Mapped[str] = mapped_column(Text, default="")  # pseudocode shown with an MCQ
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)
    answer: Mapped[str] = mapped_column(Text, default="")
    explanation: Mapped[str] = mapped_column(Text, default="")
    hints: Mapped[list] = mapped_column(JSON, default=list)
    concepts: Mapped[list] = mapped_column(JSON, default=list)
    sample_io: Mapped[str] = mapped_column(Text, default="")
    solution: Mapped[str] = mapped_column(Text, default="")
    # Candidate-reported / AI practice / Third-party: shown on every card.
    label: Mapped[str] = mapped_column(String(30), default="AI practice")
    source_note: Mapped[str] = mapped_column(String(300), default="")
    # v2: a stable key so re-seeding updates questions in place (user attempts are kept)
    qkey: Mapped[str | None] = mapped_column(String(80), nullable=True, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(160), default="")
    # Runnable coding problems: stdin/stdout test cases + a Python starter template
    tests: Mapped[list] = mapped_column(JSON, default=list)  # [{input, output, hidden}]
    starter_code: Mapped[str] = mapped_column(Text, default="")
    io_format: Mapped[dict] = mapped_column(JSON, default=dict)  # input_format / output_format / constraints
    solutions_other: Mapped[dict] = mapped_column(JSON, default=dict)  # {"java": "...", "cpp": "..."}


class QuestionAttempt(IdMixin, TimestampMixin, Base):
    __tablename__ = "question_attempts"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("practice_questions.id", ondelete="CASCADE"), index=True)
    response: Mapped[str] = mapped_column(Text, default="")
    is_correct: Mapped[bool] = mapped_column(Boolean)
    self_marked: Mapped[bool] = mapped_column(Boolean, default=False)  # True for coding/short answers


class SavedQuestion(IdMixin, TimestampMixin, Base):
    __tablename__ = "saved_questions"
    __table_args__ = (UniqueConstraint("user_id", "question_id"),)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("practice_questions.id", ondelete="CASCADE"))


class PracticeTest(IdMixin, TimestampMixin, Base):
    """A timed test: a fixed set of coding or MCQ questions answered one by one."""
    __tablename__ = "practice_tests"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(10))  # coding / mcq
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(10), default="mixed")
    minutes: Mapped[int] = mapped_column(Integer, default=30)
    question_ids: Mapped[list] = mapped_column(JSON, default=list)
    answers: Mapped[dict] = mapped_column(JSON, default=dict)  # question id -> {response, passed, total, correct}
    status: Mapped[str] = mapped_column(String(12), default="active")  # active / completed
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
