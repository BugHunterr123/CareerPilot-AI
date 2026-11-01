"""Database engine + session. One place to change if you swap SQLite for PostgreSQL."""
from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """All ORM models inherit from this."""


def make_engine(url: str):
    is_sqlite = url.startswith("sqlite")
    eng = create_engine(
        url,
        connect_args={"check_same_thread": False, "timeout": 15} if is_sqlite else {},
        pool_pre_ping=not is_sqlite,
    )
    if is_sqlite:
        # SQLite ignores foreign keys unless asked; we need them for cascade deletes.
        @event.listens_for(eng, "connect")
        def _fk_on(dbapi_conn, _):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.execute("PRAGMA journal_mode=WAL")  # readers do not block the writer
            cur.execute("PRAGMA busy_timeout=5000")
            cur.close()
    return eng


engine = make_engine(settings.db_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: one session per request, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
