"""Database connection and URL from environment.

Uses DATABASE_URL (Postgres connection string) for migrations and direct
DB access. For Supabase, obtain the connection string from the project
dashboard (Connect → URI). SUPABASE_URL and SUPABASE_ANON_KEY are used
for API/Auth in separate modules.
"""

from __future__ import annotations

import os


def get_database_url() -> str:
    """Return Postgres connection URL from environment.

    Prefers DATABASE_URL. For Supabase, use the URI from project settings
    (e.g. postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres).

    Returns:
        Connection string for SQLAlchemy/Alembic.

    Raises:
        ValueError: If DATABASE_URL is missing or empty.
    """
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        raise ValueError(
            "DATABASE_URL is not set. Set it to your Postgres connection string "
            "(e.g. from Supabase project: Connect → URI)."
        )
    return url
