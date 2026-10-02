"""Replace condition procedures/dag columns with 0.1 entry/phases/pipelines.

Revision ID: 006
Revises: 005
Create Date: 2026-10-02

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: str | Sequence[str] | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Store 0.1 condition shape (entry, phases, pipelines)."""
    op.add_column(
        "condition",
        sa.Column("entry", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "condition",
        sa.Column("phases", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "condition",
        sa.Column("pipelines", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.execute(
        "UPDATE condition SET entry = 'legacy', "
        "phases = '[]'::jsonb, pipelines = '[]'::jsonb "
        "WHERE entry IS NULL"
    )
    op.alter_column("condition", "entry", nullable=False)
    op.alter_column("condition", "phases", nullable=False)
    op.alter_column("condition", "pipelines", nullable=False)
    op.drop_column("condition", "procedures")
    op.drop_column("condition", "dag")


def downgrade() -> None:
    """Restore legacy procedures/dag columns."""
    op.add_column(
        "condition",
        sa.Column("procedures", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "condition",
        sa.Column("dag", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.execute(
        "UPDATE condition SET procedures = '{}'::jsonb, dag = '{}'::jsonb "
        "WHERE procedures IS NULL"
    )
    op.alter_column("condition", "procedures", nullable=False)
    op.alter_column("condition", "dag", nullable=False)
    op.drop_column("condition", "pipelines")
    op.drop_column("condition", "phases")
    op.drop_column("condition", "entry")
