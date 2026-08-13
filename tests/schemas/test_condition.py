"""Tests for Condition schema and load_conditions_from_dir."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from slumber.schemas import DAG, Condition, Procedure, load_conditions_from_dir


def _minimal_dag() -> dict:
    return {
        "components": [{"name": "MASTER", "unit_type": "Master", "settings": {}}],
        "connections": [],
        "process_components": [],
    }


def _minimal_procedure() -> dict:
    return {
        "steps": [{"task_type": "instruction", "settings": None}],
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
        assert cond.procedures["pre_sleep"].n_steps == 1
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


def _minimal_condition_yaml(name: str = "condition_1") -> str:
    """Minimal valid condition YAML for load_conditions_from_dir tests."""
    return f"""
name: {name}
procedures:
  pre_sleep:
    steps:
      - task: instruction
dag:
  components:
    - name: MASTER
      unit_type: Master
  connections: []
  process_components: []
"""


class TestLoadConditionsFromDir:
    """Tests for load_conditions_from_dir (slumber.schemas)."""

    def test_loads_conditions_from_directory(self, tmp_path: Path) -> None:
        (tmp_path / "control.yaml").write_text(
            _minimal_condition_yaml("condition_1"), encoding="utf-8"
        )
        (tmp_path / "other.yaml").write_text(
            _minimal_condition_yaml("condition_2"), encoding="utf-8"
        )
        conditions = load_conditions_from_dir(tmp_path)
        names = [c.name for c in conditions]
        assert "condition_1" in names
        assert "condition_2" in names
        assert len(conditions) == 2

    def test_returns_empty_list_for_empty_dir(self, tmp_path: Path) -> None:
        assert load_conditions_from_dir(tmp_path) == []
