"""Tests for config load (load_and_validate and load_conditions_from_dir)."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from slumber.schemas.condition import Condition
from slumber.schemas.study import Study
from slumber.utils.yaml import load_and_validate


class TestLoadAndValidateStudy:
    """Tests for load_and_validate with Study."""

    def test_loads_valid_manifest(self, tmp_path: Path) -> None:
        manifest = tmp_path / "study.yaml"
        manifest.write_text(
            "study_id: my-study\nname: My Study\nconditions_dir: conditions\n",
            encoding="utf-8",
        )
        study = load_and_validate(manifest, Study)
        assert study.study_id == "my-study"
        assert study.name == "My Study"
        assert study.conditions_dir == "conditions"

    def test_raises_when_file_missing(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError) as exc_info:
            load_and_validate(tmp_path / "missing.yaml", Study)
        assert "missing.yaml" in str(exc_info.value)

    def test_raises_validation_error_on_invalid_content(self, tmp_path: Path) -> None:
        manifest = tmp_path / "study.yaml"
        manifest.write_text("study_id: my-study\n# name missing\n", encoding="utf-8")
        with pytest.raises(ValidationError):
            load_and_validate(manifest, Study)


class TestLoadAndValidateCondition:
    """Tests for load_and_validate with Condition."""

    def test_loads_valid_condition(
        self, tmp_path: Path, minimal_condition_yaml: str
    ) -> None:
        cond_path = tmp_path / "control.yaml"
        cond_path.write_text(minimal_condition_yaml, encoding="utf-8")
        cond = load_and_validate(cond_path, Condition)
        assert isinstance(cond, Condition)
        assert cond.name == "condition_1"
        assert "pre_sleep" in cond.procedures
        assert cond.dag.has_component("MASTER")

    def test_raises_when_file_missing(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError) as exc_info:
            load_and_validate(tmp_path / "missing.yaml", Condition)
        assert "missing.yaml" in str(exc_info.value)

    def test_raises_validation_error_on_invalid_content(self, tmp_path: Path) -> None:
        cond_path = tmp_path / "bad.yaml"
        cond_path.write_text(
            "name: c1\n# procedures and dag missing\n", encoding="utf-8"
        )
        with pytest.raises(ValidationError):
            load_and_validate(cond_path, Condition)
