"""Users, their student profile and optional external profile links."""
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.common import IdMixin, TimestampMixin


class User(IdMixin, TimestampMixin, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    # Bumped when the password changes: every login token issued before that stops working.
    token_version: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # cascade="all, delete-orphan" => deleting a user deletes all of their data.
    profile: Mapped["StudentProfile"] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    links: Mapped[list["ProfileLink"]] = relationship(cascade="all, delete-orphan")


class StudentProfile(IdMixin, TimestampMixin, Base):
    __tablename__ = "student_profiles"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    college: Mapped[str] = mapped_column(String(200), default="")
    degree: Mapped[str] = mapped_column(String(80), default="")
    branch: Mapped[str] = mapped_column(String(120), default="")
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cgpa: Mapped[str | None] = mapped_column(String(10), nullable=True)
    # Optional preferences (every one of these can be skipped)
    interests: Mapped[list] = mapped_column(JSON, default=list)
    preferred_roles: Mapped[list] = mapped_column(JSON, default=list)
    preferred_locations: Mapped[list] = mapped_column(JSON, default=list)
    job_type: Mapped[str | None] = mapped_column(String(30), nullable=True)  # internship / full-time / both
    weekly_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    certifications: Mapped[list] = mapped_column(JSON, default=list)
    achievements: Mapped[list] = mapped_column(JSON, default=list)
    # The student's chosen target (set in Company Explorer / Career Recommendations)
    target_role_key: Mapped[str | None] = mapped_column(String(60), nullable=True)
    target_company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    optional_step_done: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(back_populates="profile")


class ProfileLink(IdMixin, TimestampMixin, Base):
    """An OPTIONAL external profile (GitHub, LinkedIn, LeetCode, portfolio...).
    We only ever store the public URL, never a password."""
    __tablename__ = "profile_links"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    url: Mapped[str] = mapped_column(String(500))
    consent: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="not_checked")  # ok / unavailable / invalid / manual
    note: Mapped[str] = mapped_column(Text, default="")
    manual_details: Mapped[str] = mapped_column(Text, default="")  # e.g. pasted LinkedIn skills
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    last_checked: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
