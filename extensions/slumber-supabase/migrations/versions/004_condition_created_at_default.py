"""Set timestamp defaults and update triggers for all core tables.

Revision ID: 004
Revises: 003
Create Date: 2026-03-20

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: str | Sequence[str] | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_CORE_TABLES = ["study", "condition", "participant", "session", "run"]


def upgrade() -> None:
    """Set timestamp defaults and update triggers for core tables."""
    for table in _CORE_TABLES:
        op.execute(f"ALTER TABLE {table} ALTER COLUMN created_at SET DEFAULT now()")
        op.execute(f"ALTER TABLE {table} ALTER COLUMN updated_at SET DEFAULT now()")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION slumber_set_updated_at()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$;
        """
    )

    for table in _CORE_TABLES:
        op.execute(f"DROP TRIGGER IF EXISTS tr_{table}_updated_at ON {table}")
        op.execute(
            f"""
            CREATE TRIGGER tr_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION slumber_set_updated_at()
            """
        )


def downgrade() -> None:
    """Drop timestamp defaults and update triggers for core tables."""
    for table in reversed(_CORE_TABLES):
        op.execute(f"DROP TRIGGER IF EXISTS tr_{table}_updated_at ON {table}")

    op.execute("DROP FUNCTION IF EXISTS slumber_set_updated_at()")

    for table in reversed(_CORE_TABLES):
        op.execute(f"ALTER TABLE {table} ALTER COLUMN updated_at DROP DEFAULT")
        op.execute(f"ALTER TABLE {table} ALTER COLUMN created_at DROP DEFAULT")
