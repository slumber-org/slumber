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

    def test_defaults(self) -> None:
        proc = Procedure(steps=[Step(task_type="instruction")])
        assert proc.trigger is None
        assert proc.when is None
        assert proc.show_task_list is True
        assert proc.allow_skip is False

    def test_trigger(self) -> None:
        proc = Procedure(
            steps=[Step(task_type="instruction")],
            trigger="session_start",
        )
        assert proc.trigger == "session_start"

    def test_when_dict(self) -> None:
        proc = Procedure(
            steps=[Step(task_type="instruction")],
            trigger="wake_up",
            when={"awakening_count": 1},
        )
        assert proc.when == {"awakening_count": 1}

    def test_when_dict_with_operator(self) -> None:
        proc = Procedure(
            steps=[Step(task_type="instruction")],
            trigger="wake_up",
            when={"awakening_count": {"gt": 1}},
        )
        assert proc.when == {"awakening_count": {"gt": 1}}

    def test_when_callable_string(self) -> None:
        proc = Procedure(
            steps=[Step(task_type="instruction")],
            trigger="wake_up",
            when="my_study.guards:is_rem_awakening",
        )
        assert proc.when == "my_study.guards:is_rem_awakening"

    def test_show_task_list_false(self) -> None:
        proc = Procedure(
            steps=[Step(task_type="instruction")],
            show_task_list=False,
        )
        assert proc.show_task_list is False

    def test_allow_skip_true(self) -> None:
        proc = Procedure(
            steps=[Step(task_type="instruction")],
            allow_skip=True,
        )
        assert proc.allow_skip is True
