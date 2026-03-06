"""Alembic migration environment.

Uses DATABASE_URL from the environment (e.g. Supabase Postgres URI).
Import all DB models so that SQLModel.metadata is populated for autogenerate.
"""

from pathlib import Path

from alembic import context
from sqlalchemy import create_engine
from sqlmodel import SQLModel

from slumber.db.connection import get_database_url
from slumber.db.models import (  # noqa: E402, F401
    Condition,
    Participant,
    Run,
    Session,
    Study,
)

# Ensure src is on path so slumber is importable when running alembic.
_src = Path(__file__).resolve().parent.parent / "src"
if _src.exists() and str(_src) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_src))

config = context.config
target_metadata = SQLModel.metadata


def get_url() -> str:
    """Return database URL from environment (not from alembic.ini)."""
    return get_database_url()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generate SQL only)."""
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connect to database)."""
    connectable = create_engine(get_url())
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
