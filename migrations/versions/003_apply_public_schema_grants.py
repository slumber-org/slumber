"""Apply public schema grants for API roles.

Revision ID: 003
Revises: 002
Create Date: 2026-03-20

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str | Sequence[str] | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Grant least-privilege schema and table access to Supabase API roles.

    - anon: schema USAGE only; no table grants (all tables require authentication).
    - authenticated: SELECT/INSERT/UPDATE/DELETE; RLS policies enforce row-level access.
    - service_role: full privileges for admin CLI operations (bypasses RLS by default).
    """
    op.execute("GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role")

    # authenticated: row-level operations only (no TRUNCATE / REFERENCES)
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated"
    )
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated")
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public"
        " GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public"
        " GRANT USAGE, SELECT ON SEQUENCES TO authenticated"
    )

    # service_role: full access for admin CLI and migrations
    op.execute("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO service_role")
    op.execute("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO service_role")
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public"
        " GRANT ALL PRIVILEGES ON TABLES TO service_role"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public"
        " GRANT ALL PRIVILEGES ON SEQUENCES TO service_role"
    )


def downgrade() -> None:
    """Revoke schema and table privileges from Supabase API roles."""
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public"
        " REVOKE ALL PRIVILEGES ON SEQUENCES FROM service_role"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public"
        " REVOKE ALL PRIVILEGES ON TABLES FROM service_role"
    )
    op.execute(
        "REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM service_role"
    )
    op.execute("REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM service_role")

    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public"
        " REVOKE USAGE, SELECT ON SEQUENCES FROM authenticated"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public"
        " REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM authenticated"
    )
    op.execute(
        "REVOKE USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public FROM authenticated"
    )
    op.execute(
        "REVOKE SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM authenticated"
    )

    op.execute("REVOKE USAGE ON SCHEMA public FROM anon, authenticated, service_role")
