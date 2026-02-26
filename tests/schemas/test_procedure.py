"""Tests for Procedure and Task schemas."""

import pytest
from pydantic import ValidationError

from slumber.schemas import Procedure, Task


class TestTask:
    """Tests for Task schema."""

    def test_valid_minimal(self) -> None:
        task = Task(type="instruction", title="Read this")
        assert task.type == "instruction"
        assert task.title == "Read this"
        assert task.kwargs == {}

    def test_valid_with_kwargs(self) -> None:
        task = Task(
            type="survey",
            title="Questionnaire",
            kwargs={"survey_config_path": "surveys/q.json"},
        )
        assert task.kwargs["survey_config_path"] == "surveys/q.json"

    def test_type_required(self) -> None:
        with pytest.raises(ValidationError):
            Task(type="", title="X")

    def test_title_required(self) -> None:
        with pytest.raises(ValidationError):
            Task(type="instruction", title="")


class TestProcedure:
    """Tests for Procedure schema."""

    def test_valid_minimal(self) -> None:
        proc = Procedure(tasks=[Task(type="instruction", title="Step 1")])
        assert proc.n_tasks == 1
        assert proc.show_task_list is True
        assert proc.allow_skip_tasks is False

    def test_valid_show_item_list_alias(self) -> None:
        proc = Procedure.model_validate(
            {
                "tasks": [{"type": "instruction", "title": "Step 1"}],
                "show_item_list": False,
            }
        )
        assert proc.show_task_list is False

    def test_valid_allow_skip_tasks(self) -> None:
        proc = Procedure(
            tasks=[Task(type="instruction", title="Step 1")],
            allow_skip_tasks=True,
        )
        assert proc.allow_skip_tasks is True

    def test_tasks_min_length(self) -> None:
        with pytest.raises(ValidationError):
            Procedure(tasks=[])

    def test_tasks_required(self) -> None:
        with pytest.raises(ValidationError):
            Procedure()  # type: ignore[call-arg]
