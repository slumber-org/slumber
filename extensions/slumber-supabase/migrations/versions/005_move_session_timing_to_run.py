"""Move session start/end timing columns to run.

Revision ID: 005
Revises: 004
Create Date: 2026-03-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: str | Sequence[str] | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add run timing fields and remove session timing fields."""
    op.add_column(
        "run",
        sa.Column(
            "start_time",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.add_column(
        "run",
        sa.Column("end_time", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.execute(
        """
        UPDATE run r
        SET start_time = COALESCE(s.start_time, r.created_at),
            end_time = s.end_time
        FROM session s
        WHERE s.id = r.session_id
        """
    )

    op.drop_column("session", "start_time")
    op.drop_column("session", "end_time")


def downgrade() -> None:
    """Restore session timing fields and remove run timing fields."""
    op.add_column(
        "session",
        sa.Column("start_time", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "session",
        sa.Column("end_time", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.execute(
        """
        UPDATE session s
        SET start_time = t.start_time,
            end_time = t.end_time
        FROM (
            SELECT
                session_id,
                MIN(start_time) AS start_time,
                MAX(end_time) AS end_time
            FROM run
            GROUP BY session_id
        ) t
        WHERE s.id = t.session_id
        """
    )

    op.drop_column("run", "end_time")
    op.drop_column("run", "start_time")
