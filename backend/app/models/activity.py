"""Mock interviews, progress events, manual job applications, assistant chat."""
from datetime import date

from sqlalchemy import JSON, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.common import IdMixin, TimestampMixin


class MockInterview(IdMixin, TimestampMixin, Base):
    __tablename__ = "mock_interviews"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role_key: Mapped[str] = mapped_column(String(60))
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    itype: Mapped[str] = mapped_column(String(20))  # technical / coding / project / hr / behavioural / mixed
    difficulty: Mapped[str] = mapped_column(String(10))
    duration_min: Mapped[int] = mapped_column(Integer, default=15)
    status: Mapped[str] = mapped_column(String(12), default="active")  # active / completed
    scoring_mode: Mapped[str] = mapped_column(String(20), default="rubric-rules")
    plan: Mapped[list] = mapped_column(JSON, default=list)  # questions + rubric hints, asked one by one
    current_index: Mapped[int] = mapped_column(Integer, default=0)
    overall: Mapped[float | None] = mapped_column(Float, nullable=True)
    responses: Mapped[list["InterviewResponse"]] = relationship(cascade="all, delete-orphan", lazy="selectin",
                                                                 order_by="InterviewResponse.index")
    report: Mapped["FeedbackReport"] = relationship(cascade="all, delete-orphan", uselist=False, lazy="selectin")


class InterviewResponse(IdMixin, TimestampMixin, Base):
    __tablename__ = "interview_responses"
    interview_id: Mapped[int] = mapped_column(ForeignKey("mock_interviews.id", ondelete="CASCADE"), index=True)
    index: Mapped[int] = mapped_column(Integer)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    scores: Mapped[dict] = mapped_column(JSON, default=dict)  # rubric criterion -> {score, reason}
    feedback: Mapped[dict] = mapped_column(JSON, default=dict)
    total: Mapped[float] = mapped_column(Float, default=0)


class FeedbackReport(IdMixin, TimestampMixin, Base):
    __tablename__ = "feedback_reports"
    interview_id: Mapped[int] = mapped_column(ForeignKey("mock_interviews.id", ondelete="CASCADE"), unique=True)
    content: Mapped[dict] = mapped_column(JSON, default=dict)


class ProgressEvent(IdMixin, TimestampMixin, Base):
    """Append-only log. The Progress page and readiness numbers are computed from it."""
    __tablename__ = "progress_events"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(40))  # task_done / attempt / interview_done / plan_generated ...
    detail: Mapped[dict] = mapped_column(JSON, default=dict)


class JobApplication(IdMixin, TimestampMixin, Base):
    __tablename__ = "job_applications"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(120), default="")
    status: Mapped[str] = mapped_column(String(30), default="applied")
    applied_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    interview_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    outcome: Mapped[str] = mapped_column(String(60), default="")
    notes: Mapped[str] = mapped_column(Text, default="")


class ChatMessage(IdMixin, TimestampMixin, Base):
    __tablename__ = "chat_messages"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(12))  # user / assistant
    content: Mapped[str] = mapped_column(Text)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)  # citations, actions, engine
