"""Utilities for the Supabase stack: optional extra detection, CLI guards, ``DATABASE_URL``."""

from __future__ import annotations

import importlib.util
import os

import typer
from slumber.constants import DATABASE_URL_ENV

SUPABASE_INSTALL_HINT = (
    "This requires the slumber-supabase extension. "
    "Install with: pip install 'slumber[supabase]' or uv sync --extra supabase"
)


def is_supabase_extra_installed() -> bool:
    """Return True if the third-party ``supabase`` package is importable."""
    return importlib.util.find_spec("supabase") is not None


def exit_unless_supabase_extra_installed(*, reason: str | None = None) -> None:
    """Exit via Typer if the ``supabase`` package is not installed.

    Args:
        reason: Optional context line printed before :data:`SUPABASE_INSTALL_HINT`.
    """
    if is_supabase_extra_installed():
        return

    if reason:
        typer.echo(reason, err=True)

    typer.echo(SUPABASE_INSTALL_HINT, err=True)
    raise typer.Exit(1)


def get_database_url() -> str:
    """Return Postgres connection URL from environment.

    Prefers DATABASE_URL. For Supabase, use the URI from project settings
    (e.g. postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres).

    Returns:
        Connection string for SQLAlchemy/Alembic.

    Raises:
        ValueError: If DATABASE_URL is missing or empty.
    """
    url = os.getenv(DATABASE_URL_ENV, "").strip()
    if not url:
        raise ValueError(
            "DATABASE_URL is not set. Set it to your Postgres connection string "
            "(e.g. from Supabase project: Connect → URI)."
        )
    return url
