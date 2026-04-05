"""Tests for DB models: schema consistency and instantiation."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from slumber.supabase.models import (
    Condition,
    Participant,
    Run,
    Session,
    Study,
)


def test_study_model_instantiation() -> None:
    """Study can be instantiated with required fields."""
    study = Study(id="test-study", name="Test Study")
    assert study.id == "test-study"
    assert study.name == "Test Study"
    assert study.created_at is not None
    assert study.updated_at is not None


def test_condition_model_instantiation() -> None:
    """Condition can be instantiated with id, study_id, procedures, dag."""
    condition = Condition(
        id="condition_1",
        study_id="test-study",
        procedures={"pre_sleep": {"steps": [{"task": "instruction"}]}},
        dag={
            "components": [{"name": "MASTER", "unit_type": "Master"}],
            "connections": [],
            "process_components": [],
        },
    )
    assert condition.id == "condition_1"
    assert condition.study_id == "test-study"
    assert "pre_sleep" in condition.procedures
    assert condition.dag["components"][0]["name"] == "MASTER"


def test_participant_model_instantiation() -> None:
    """Participant can be instantiated with id, study_id, participant_id, auth_user_id."""
    uid = uuid4()
    participant = Participant(
        id="test-study_sub-001",
        study_id="test-study",
        participant_id="sub-001",
        auth_user_id=uid,
    )
    assert participant.study_id == "test-study"
    assert participant.participant_id == "sub-001"
    assert participant.auth_user_id == uid


def test_session_model_instantiation() -> None:
    """Session can be instantiated with required fields."""
    earliest = datetime(2025, 3, 12, 22, 0, 0, tzinfo=timezone.utc)
    latest = datetime(2025, 3, 13, 6, 0, 0, tzinfo=timezone.utc)
    session = Session(
        participant_id="test-study_sub-001",
        earliest_start_at=earliest,
        latest_start_at=latest,
    )
    assert session.participant_id == "test-study_sub-001"
    assert session.earliest_start_at == earliest
    assert session.latest_start_at == latest
    assert session.condition_id is None


def test_session_model_with_condition() -> None:
    """Session accepts optional condition_id (string)."""
    earliest = datetime(2025, 3, 12, 22, 0, 0, tzinfo=timezone.utc)
    latest = datetime(2025, 3, 13, 6, 0, 0, tzinfo=timezone.utc)
    session = Session(
        participant_id="test-study_sub-001",
        earliest_start_at=earliest,
        latest_start_at=latest,
        condition_id="condition_2",
    )
    assert session.condition_id == "condition_2"


def test_run_model_instantiation() -> None:
    """Run can be instantiated with session_id, status, run_directory."""
    run = Run(
        session_id=1,
        status="pending",
        run_directory="/runs/sub-001/ses-1/run-1",
    )
    assert run.session_id == 1
    assert run.status == "pending"
    assert run.run_directory == "/runs/sub-001/ses-1/run-1"
    assert run.parent_run_id is None
    assert run.start_time is not None
    assert run.end_time is None


def test_run_model_with_parent() -> None:
    """Run accepts optional parent_run_id."""
    run = Run(
        session_id=1,
        parent_run_id=1,
        status="completed",
        run_directory="/runs/sub-001/ses-1/run-2",
    )
    assert run.parent_run_id == 1


def test_study_table_metadata() -> None:
    """Study table has expected name and columns."""
    assert Study.__tablename__ == "study"
    assert "id" in Study.model_fields
    assert "name" in Study.model_fields


def test_condition_table_metadata() -> None:
    """Condition table has id (str PK), study_id FK, procedures, dag."""
    assert Condition.__tablename__ == "condition"
    assert "id" in Condition.model_fields
    assert "study_id" in Condition.model_fields
    assert "procedures" in Condition.model_fields
    assert "dag" in Condition.model_fields


def test_participant_table_metadata() -> None:
    """Participant table has id (str PK), auth_user_id (UUID), unique (study_id, participant_id)."""
    assert Participant.__tablename__ == "participant"
    assert "id" in Participant.model_fields
    assert "auth_user_id" in Participant.model_fields
    assert Participant.model_fields["auth_user_id"].annotation is not None


def test_session_table_metadata() -> None:
    """Session table has participant_id, condition_id, earliest_start_at, latest_start_at."""
    assert Session.__tablename__ == "session"
    assert "participant_id" in Session.model_fields
    assert "condition_id" in Session.model_fields
    assert "earliest_start_at" in Session.model_fields
    assert "latest_start_at" in Session.model_fields


def test_run_table_metadata() -> None:
    """Run table has timing, status, and run path fields."""
    assert Run.__tablename__ == "run"
    assert "session_id" in Run.model_fields
    assert "parent_run_id" in Run.model_fields
    assert "start_time" in Run.model_fields
    assert "end_time" in Run.model_fields
    assert "status" in Run.model_fields
    assert "run_directory" in Run.model_fields
