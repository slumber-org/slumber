"""Tests for slumber study validate command (slumber.cli.study)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from slumber.cli.main import app
from slumber.config import init_study
from slumber.plugins import EntryPointGroup, reset_registry
from slumber.ui.activities.instruction import InstructionActivity


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def _fresh_registry() -> None:
    reset_registry()
    yield
    reset_registry()


def _mock_registry_for_validate_success() -> MagicMock:
    """Registry that provides activity/unit plugins for validate success tests."""
    import ezmsg.core as ez

    from slumber.pipeline.units import Settings

    class _DummySettings(Settings):
        """Minimal settings so build_unit_from_settings accepts the unit."""

    class _DummyUnit(ez.Unit):
        SETTINGS = _DummySettings

    def get_plugin(group: EntryPointGroup, key: str):
        if group == EntryPointGroup.UNITS:
            return _DummyUnit
        if group == EntryPointGroup.ACTIVITIES:
            if key == "instruction":
                return InstructionActivity
            raise LookupError(f"Unknown activity type: {key!r}")
        raise LookupError(f"Unknown group: {group!r}")

    reg = MagicMock()
    reg.get_plugin.side_effect = get_plugin
    return reg


class TestStudyValidateCLI:
    """Tests for slumber study validate."""

    def test_validate_succeeds_in_study_dir_with_valid_conditions(
        self, runner: CliRunner, tmp_path: Path, minimal_condition_yaml: str
    ) -> None:
        study_path = init_study(
            tmp_path, "v-study", create_env_example=False, create_gitignore=False
        )
        (study_path / "conditions" / "condition_1.yaml").write_text(
            minimal_condition_yaml, encoding="utf-8"
        )
        with patch(
            "slumber.config.plugins.get_registry",
            return_value=_mock_registry_for_validate_success(),
        ):
            result = runner.invoke(
                app, ["study", "validate", "--study-dir", str(study_path)]
            )
        assert result.exit_code == 0, result.output
        assert "v-study" in result.output
        assert "Conditions: 1" in result.output
        assert "condition_1" in result.output

    def test_validate_with_study_dir_option(
        self, runner: CliRunner, tmp_path: Path, minimal_condition_yaml: str
    ) -> None:
        study_path = init_study(
            tmp_path, "v-study", create_env_example=False, create_gitignore=False
        )
        (study_path / "conditions" / "condition_1.yaml").write_text(
            minimal_condition_yaml, encoding="utf-8"
        )
        with patch(
            "slumber.config.plugins.get_registry",
            return_value=_mock_registry_for_validate_success(),
        ):
            result = runner.invoke(
                app,
                ["study", "validate", "--study-dir", str(study_path)],
            )
        assert result.exit_code == 0, result.output
        assert "v-study" in result.output

    def test_validate_exits_1_when_plugin_validation_fails(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        study_path = init_study(
            tmp_path, "v-study", create_env_example=False, create_gitignore=False
        )
        (study_path / "conditions" / "condition_1.yaml").write_text(
            """
name: condition_1
entry: setup
phases:
  - id: setup
    layout: {type: stepper}
    activities:
      - id: welcome
        type: not_a_real_activity
    on:
      - event: phase_completed
        do: [end_run]
pipelines: []
""",
            encoding="utf-8",
        )
        result = runner.invoke(
            app, ["study", "validate", "--study-dir", str(study_path)]
        )
        assert result.exit_code == 1
        assert "Plugin validation failed" in result.output
        assert "not_a_real_activity" in result.output

    def test_validate_exits_1_when_no_study_dir_provided(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Validate requires --study-dir or STUDY_DIR."""
        monkeypatch.delenv("STUDY_DIR", raising=False)
        result = runner.invoke(
            app,
            ["--env", str(tmp_path / "does-not-exist.env"), "study", "validate"],
        )
        assert result.exit_code == 1
        assert (
            "study-dir" in result.output.lower()
            or "study_dir" in result.output.lower()
            or "study directory" in result.output.lower()
            or "aborted" in result.output.lower()
        )

    def test_validate_exits_1_when_manifest_invalid(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        study_path = tmp_path / "bad-study"
        study_path.mkdir()
        (study_path / "conditions").mkdir()
        (study_path / "study.yaml").write_text(
            "study_id: x\n# study_name missing\n", encoding="utf-8"
        )
        result = runner.invoke(
            app, ["study", "validate", "--study-dir", str(study_path)]
        )
        assert result.exit_code == 1
        assert (
            "Study manifest error" in result.output
            or "study.yaml" in result.output
            or "Validation error" in result.output
        )

    def test_validate_exits_1_when_condition_invalid(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        study_path = init_study(
            tmp_path, "v-study", create_env_example=False, create_gitignore=False
        )
        (study_path / "conditions" / "bad.yaml").write_text(
            "name: x\n# phases missing\n", encoding="utf-8"
        )
        result = runner.invoke(
            app, ["study", "validate", "--study-dir", str(study_path)]
        )
        assert result.exit_code == 1
        assert "Condition file error" in result.output or "bad.yaml" in result.output
