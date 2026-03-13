"""Tests for slumber study validate command (slumber.cli.study)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from slumber.cli.main import app
from slumber.config import init_study


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _mock_registry_for_validate_success() -> MagicMock:
    """Registry that accepts any unit_type and provides real task/UI plugins (for validate success tests)."""
    import ezmsg.core as ez

    from slumber.plugins import EntryPointGroup
    from slumber.plugins.tasks.instruction import InstructionTask
    from slumber.plugins.ui.headless import HeadlessUIBackend
    from slumber.plugins.units import Settings

    class _DummySettings(Settings):
        """Minimal settings so build_unit_from_settings and ez.Unit accept the unit."""

        pass

    class _DummyUnit(ez.Unit):
        SETTINGS = _DummySettings

        def __init__(self, settings: _DummySettings) -> None:
            super().__init__(settings)
            self.settings = settings

    def get_plugin(group: EntryPointGroup, key: str):
        if group == EntryPointGroup.UNITS:
            return _DummyUnit
        if group == EntryPointGroup.TASKS:
            if key == "instruction":
                return InstructionTask
            raise LookupError(f"Unknown task type: {key!r}")
        if group == EntryPointGroup.UI_BACKENDS:
            if key == "headless":
                return HeadlessUIBackend()
            raise LookupError(f"Unknown UI backend: {key!r}")
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
        (study_path / "conditions" / "control.yaml").write_text(
            minimal_condition_yaml, encoding="utf-8"
        )
        with patch(
            "slumber.config.plugins.get_registry",
            return_value=_mock_registry_for_validate_success(),
        ):
            result = runner.invoke(
                app, ["study", "validate", "--study-dir", str(study_path)]
            )
        assert result.exit_code == 0
        assert "v-study" in result.output
        assert "Conditions: 1" in result.output
        assert "condition_1" in result.output

    def test_validate_with_study_dir_option(
        self, runner: CliRunner, tmp_path: Path, minimal_condition_yaml: str
    ) -> None:
        study_path = init_study(
            tmp_path, "v-study", create_env_example=False, create_gitignore=False
        )
        (study_path / "conditions" / "c.yaml").write_text(
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
        assert result.exit_code == 0
        assert "v-study" in result.output

    def test_validate_exits_1_when_plugin_validation_fails(
        self, runner: CliRunner, tmp_path: Path, minimal_condition_yaml: str
    ) -> None:
        study_path = init_study(
            tmp_path, "v-study", create_env_example=False, create_gitignore=False
        )
        (study_path / "conditions" / "control.yaml").write_text(
            minimal_condition_yaml, encoding="utf-8"
        )
        result = runner.invoke(
            app, ["study", "validate", "--study-dir", str(study_path)]
        )
        assert result.exit_code == 1
        assert "Plugin validation failed" in result.output
        assert "Master" in result.output

    def test_validate_exits_1_when_no_study_dir_provided(
        self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Validate requires --study-dir or STUDY_DIR (prompts in interactive mode, aborts in non-interactive)."""
        monkeypatch.delenv("STUDY_DIR", raising=False)
        # Prevent callback default `load_dotenv()` from loading repository .env.
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
            "study_id: x\n# name missing\n", encoding="utf-8"
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
            "name: x\n# procedures and dag missing\n", encoding="utf-8"
        )
        result = runner.invoke(
            app, ["study", "validate", "--study-dir", str(study_path)]
        )
        assert result.exit_code == 1
        assert "Condition file error" in result.output or "bad.yaml" in result.output
