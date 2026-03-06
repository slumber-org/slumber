"""Tests for Procedure and Step schemas."""

import pytest
from pydantic import ValidationError

from slumber.schemas import Procedure, Step


class TestStep:
    """Tests for Step schema."""

    def test_valid_minimal(self) -> None:
        step = Step(task_type="instruction")
        assert step.task_type == "instruction"
        assert step.settings is None

    def test_valid_with_task_alias(self) -> None:
        step = Step(task="instruction")
        assert step.task_type == "instruction"

    def test_valid_with_settings(self) -> None:
        step = Step(
            task_type="survey",
            settings={"survey_config_path": "surveys/q.json"},
        )
        assert step.settings is not None
        assert step.settings["survey_config_path"] == "surveys/q.json"

    def test_task_type_required(self) -> None:
        with pytest.raises(ValidationError):
            Step(task_type="")


class TestProcedure:
    """Tests for Procedure schema."""

    def test_valid_minimal(self) -> None:
        proc = Procedure(steps=[Step(task_type="instruction")])
        assert proc.n_steps == 1

    def test_steps_min_length(self) -> None:
        with pytest.raises(ValidationError):
            Procedure(steps=[])

    def test_steps_required(self) -> None:
        with pytest.raises(ValidationError):
            Procedure()  # type: ignore[call-arg]
