"""Tests for DB models: schema consistency and instantiation."""

from __future__ import annotations

from datetime import date, time
from uuid import uuid4


from slumber.db.models import (
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
    """Condition can be instantiated with study_id, name, procedures, dag."""
    condition = Condition(
        study_id="test-study",
        name="condition_1",
        procedures={"pre_sleep": {"steps": [{"task": "instruction"}]}},
        dag={
            "components": [{"name": "MASTER", "unit_type": "Master"}],
            "connections": [],
            "process_components": [],
        },
    )
    assert condition.study_id == "test-study"
    assert condition.name == "condition_1"
    assert "pre_sleep" in condition.procedures
    assert condition.dag["components"][0]["name"] == "MASTER"


def test_participant_model_instantiation() -> None:
    """Participant can be instantiated with study_id, participant_id, auth_user_id."""
    uid = uuid4()
    participant = Participant(
        study_id="test-study",
        participant_id="sub-001",
        auth_user_id=uid,
    )
    assert participant.study_id == "test-study"
    assert participant.participant_id == "sub-001"
    assert participant.auth_user_id == uid


def test_session_model_instantiation() -> None:
    """Session can be instantiated with required fields."""
    session = Session(
        participant_id=1,
        scheduled_date=date(2025, 3, 6),
    )
    assert session.participant_id == 1
    assert session.scheduled_date == date(2025, 3, 6)
    assert session.condition_id is None
    assert session.min_start_time is None
    assert session.max_start_time is None


def test_session_model_with_optional_times() -> None:
    """Session accepts optional min/max start times."""
    session = Session(
        participant_id=1,
        scheduled_date=date(2025, 3, 6),
        min_start_time=time(22, 0),
        max_start_time=time(6, 0),
    )
    assert session.min_start_time == time(22, 0)
    assert session.max_start_time == time(6, 0)


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
    """Condition table has study_id FK and unique (study_id, name)."""
    assert Condition.__tablename__ == "condition"
    assert "study_id" in Condition.model_fields
    assert "procedures" in Condition.model_fields
    assert "dag" in Condition.model_fields


def test_participant_table_metadata() -> None:
    """Participant table has auth_user_id (UUID) and unique (study_id, participant_id)."""
    assert Participant.__tablename__ == "participant"
    assert "auth_user_id" in Participant.model_fields
    assert Participant.model_fields["auth_user_id"].annotation is not None


def test_session_table_metadata() -> None:
    """Session table has participant_id, condition_id, scheduled_date."""
    assert Session.__tablename__ == "session"
    assert "participant_id" in Session.model_fields
    assert "condition_id" in Session.model_fields
    assert "scheduled_date" in Session.model_fields


def test_run_table_metadata() -> None:
    """Run table has session_id, parent_run_id, status, run_directory."""
    assert Run.__tablename__ == "run"
    assert "session_id" in Run.model_fields
    assert "parent_run_id" in Run.model_fields
    assert "status" in Run.model_fields
    assert "run_directory" in Run.model_fields
