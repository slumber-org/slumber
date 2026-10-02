"""Initial schema: study, condition, participant, session, run.

Revision ID: 001
Revises:
Create Date: 2025-03-06

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create study, condition, participant, session, run tables."""
    op.create_table(
        "study",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=512), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("ALTER TABLE study ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY study_select ON study FOR SELECT TO authenticated USING (true)"
    )

    op.create_table(
        "condition",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("study_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "procedures", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("dag", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["study_id"], ["study.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("study_id", "name", name="uq_condition_study_name"),
    )
    op.execute("ALTER TABLE condition ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY condition_select ON condition FOR SELECT TO authenticated USING (true)"
    )

    op.create_table(
        "participant",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("study_id", sa.String(length=255), nullable=False),
        sa.Column("participant_id", sa.String(length=255), nullable=False),
        sa.Column("auth_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["study_id"], ["study.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "study_id",
            "participant_id",
            name="uq_participant_study_participant_id",
        ),
    )
    op.create_index(
        op.f("ix_participant_participant_id"),
        "participant",
        ["participant_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_participant_auth_user_id"),
        "participant",
        ["auth_user_id"],
        unique=False,
    )
    op.execute("ALTER TABLE participant ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY participant_select_own ON participant FOR SELECT TO authenticated USING (auth_user_id = auth.uid())"
    )
    op.execute(
        "CREATE POLICY participant_insert_own ON participant FOR INSERT TO authenticated WITH CHECK (auth_user_id = auth.uid())"
    )
    op.execute(
        "CREATE POLICY participant_update_own ON participant FOR UPDATE TO authenticated USING (auth_user_id = auth.uid()) WITH CHECK (auth_user_id = auth.uid())"
    )

    op.create_table(
        "session",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("participant_id", sa.Integer(), nullable=False),
        sa.Column("condition_id", sa.Integer(), nullable=True),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("min_start_time", sa.Time(), nullable=True),
        sa.Column("max_start_time", sa.Time(), nullable=True),
        sa.Column(
            "start_time",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "end_time",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["condition_id"],
            ["condition.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["participant_id"],
            ["participant.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "participant_id",
            "scheduled_date",
            "min_start_time",
            "max_start_time",
            name="uq_session_participant_date_min_max_time",
        ),
    )
    op.create_index(
        "uq_session_participant_date_when_times_null",
        "session",
        ["participant_id", "scheduled_date"],
        unique=True,
        postgresql_where=sa.text("min_start_time IS NULL AND max_start_time IS NULL"),
    )
    op.execute("ALTER TABLE session ENABLE ROW LEVEL SECURITY")
    op.execute(
        """CREATE POLICY session_all_own ON session FOR ALL TO authenticated
        USING (participant_id IN (SELECT id FROM participant WHERE auth_user_id = auth.uid()))
        WITH CHECK (participant_id IN (SELECT id FROM participant WHERE auth_user_id = auth.uid()))"""
    )

    op.create_table(
        "run",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("parent_run_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("run_directory", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["parent_run_id"],
            ["run.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["session.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("ALTER TABLE run ENABLE ROW LEVEL SECURITY")
    op.execute(
        """CREATE POLICY run_all_own ON run FOR ALL TO authenticated
        USING (session_id IN (SELECT id FROM session WHERE participant_id IN (SELECT id FROM participant WHERE auth_user_id = auth.uid())))
        WITH CHECK (session_id IN (SELECT id FROM session WHERE participant_id IN (SELECT id FROM participant WHERE auth_user_id = auth.uid())))"""
    )
    op.create_index(op.f("ix_run_status"), "run", ["status"], unique=False)


def downgrade() -> None:
    """Drop run, session, participant, condition, study tables."""
    op.drop_index(op.f("ix_run_status"), table_name="run")
    op.drop_table("run")
    op.drop_index(
        "uq_session_participant_date_when_times_null",
        table_name="session",
    )
    op.drop_table("session")
    op.drop_index(op.f("ix_participant_auth_user_id"), table_name="participant")
    op.drop_index(op.f("ix_participant_participant_id"), table_name="participant")
    op.drop_table("participant")
    op.drop_table("condition")
    op.drop_table("study")
