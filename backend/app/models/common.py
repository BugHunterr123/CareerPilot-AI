"""Small helpers shared by the model files."""
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IdMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
