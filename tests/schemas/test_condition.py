"""Tests for Condition schema."""

import pytest
from pydantic import ValidationError

from slumber.schemas import Condition, DAG, Procedure


def _minimal_dag() -> dict:
    return {
        "components": [{"name": "MASTER", "unit_type": "Master", "settings": {}}],
        "connections": [],
        "process_components": [],
    }


def _minimal_procedure() -> dict:
    return {
        "tasks": [{"type": "instruction", "title": "Intro", "kwargs": {}}],
    }


class TestCondition:
    """Tests for Condition schema."""

    def test_valid_minimal(self) -> None:
        cond = Condition(
            name="condition_1",
            procedures={
                "pre_sleep": Procedure(**(_minimal_procedure())),
                "awakening": Procedure(**(_minimal_procedure())),
                "post_sleep": Procedure(**(_minimal_procedure())),
            },
            dag=DAG(**_minimal_dag()),
        )
        assert cond.name == "condition_1"
        assert "pre_sleep" in cond.procedures
        assert cond.procedures["pre_sleep"].n_tasks == 1
        assert cond.dag.has_component("MASTER")

    def test_name_required(self) -> None:
        with pytest.raises(ValidationError):
            Condition(
                name="",
                procedures={"pre_sleep": Procedure(**(_minimal_procedure()))},
                dag=DAG(**_minimal_dag()),
            )

    def test_procedures_min_length(self) -> None:
        with pytest.raises(ValidationError):
            Condition(
                name="c1",
                procedures={},
                dag=DAG(**_minimal_dag()),
            )

    def test_dag_required(self) -> None:
        with pytest.raises(ValidationError):
            Condition(
                name="c1",
                procedures={"pre_sleep": Procedure(**(_minimal_procedure()))},
            )  # type: ignore[call-arg]
