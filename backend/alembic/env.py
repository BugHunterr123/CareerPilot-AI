"""Alembic migration environment. Uses the same DATABASE_URL and models as the app."""
from alembic import context

from app.config import settings
from app.db import Base, make_engine
import app.models  # noqa: F401  (registers all tables)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=settings.db_url, target_metadata=target_metadata, literal_binds=True,
                      render_as_batch=settings.db_url.startswith("sqlite"))
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = make_engine(settings.db_url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata,
                          render_as_batch=settings.db_url.startswith("sqlite"))
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
