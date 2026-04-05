"""Postgres models for Study, Condition, Participant, Session, and Run.

Designed for Supabase (Postgres); Participant links to Supabase Auth via
auth_user_id (auth.users.id). All tables use created_at/updated_at timestamps.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import TIMESTAMP, TEXT, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import ExcludeConstraint, JSONB, UUID as PG_UUID
from sqlmodel import Column, Field, SQLModel

from slumber.utils.time import utc_now


class TimestampMixin(SQLModel):
    """Created/updated timestamps (timezone-aware)."""

    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=TIMESTAMP(timezone=True),
        sa_column_kwargs={"nullable": False, "server_default": text("now()")},
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=TIMESTAMP(timezone=True),
        sa_column_kwargs={"nullable": False, "server_default": text("now()")},
    )


class Study(TimestampMixin, table=True):
    """Study registered in the backend.

    id is the logical study id (e.g. from study.yaml); name is human-readable.
    """

    __tablename__ = "study"

    id: str = Field(..., max_length=255, primary_key=True)
    name: str = Field(..., max_length=512)


class Condition(TimestampMixin, table=True):
    """Condition for a study: procedures and DAG as JSON.

    Synced from study folder condition YAML files. id is the condition
    identifier (e.g. condition_1); procedures and dag are stored as JSONB.
    """

    __tablename__ = "condition"

    id: str = Field(..., max_length=255, primary_key=True)
    study_id: str = Field(..., foreign_key="study.id", max_length=255)
    procedures: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))
    dag: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))


class Participant(TimestampMixin, table=True):
    """Participant in a study, linked to Supabase Auth.

    One auth user can have one participant record per study. participant_id
    is the study-specific id (e.g. sub-001); auth_user_id references auth.users.id.
    """

    __tablename__ = "participant"
    __table_args__ = (
        UniqueConstraint(
            "study_id", "participant_id", name="uq_participant_study_participant_id"
        ),
    )

    id: str = Field(..., max_length=255, primary_key=True)
    study_id: str = Field(..., foreign_key="study.id", max_length=255)
    participant_id: str = Field(..., max_length=255, index=True)
    auth_user_id: UUID = Field(
        ...,
        sa_column=Column(PG_UUID(as_uuid=True), nullable=False, index=True),
    )


class Session(TimestampMixin, table=True):
    """Scheduled session for a participant (optionally tied to a condition).

    earliest_start_at and latest_start_at define the allowed start window
    (participant may start the session any time in that range). No two sessions
    for the same participant may have overlapping windows (DB exclusion).
    """

    __tablename__ = "session"
    __table_args__ = (
        ExcludeConstraint(
            ("participant_id", "="),
            (func.tstzrange("earliest_start_at", "latest_start_at", "[]"), "&&"),
            name="uq_session_participant_no_overlap",
            using="gist",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    participant_id: str = Field(..., foreign_key="participant.id", max_length=255)
    condition_id: str | None = Field(
        default=None, foreign_key="condition.id", max_length=255
    )
    earliest_start_at: datetime = Field(..., sa_type=TIMESTAMP(timezone=True))
    latest_start_at: datetime = Field(..., sa_type=TIMESTAMP(timezone=True))


class Run(TimestampMixin, table=True):
    """A single run (execution) for a session.

    parent_run_id supports retries or chained runs; status and run_directory
    track execution state and output location.
    """

    __tablename__ = "run"

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="session.id")
    parent_run_id: int | None = Field(default=None, foreign_key="run.id")
    start_time: datetime = Field(
        default_factory=utc_now,
        sa_type=TIMESTAMP(timezone=True),
        sa_column_kwargs={"nullable": False, "server_default": text("now()")},
    )
    end_time: datetime | None = Field(default=None, sa_type=TIMESTAMP(timezone=True))
    status: str = Field(
        ..., max_length=64, index=True
    )  # e.g. pending, running, completed, failed
    run_directory: str = Field(..., sa_column=Column(TEXT, nullable=False))
