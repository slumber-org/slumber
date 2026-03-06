"""Tests for slumber study validate command (slumber.cli.study)."""

from dataclasses import dataclass
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
    """Registry that accepts any unit_type and real task plugins (for validate success tests)."""
    import ezmsg.core as ez

    from slumber.plugins import get_registry

    @dataclass
    class _DummySettings:
        pass

    class _DummyUnit(ez.Unit):
        SETTINGS = _DummySettings

        def __init__(self, settings: _DummySettings) -> None:
            super().__init__(settings)
            self.settings = settings

    real = get_registry()
    reg = MagicMock()
    reg.get_unit.return_value = _DummyUnit
    reg.get_task.side_effect = real.get_task
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
        with (
            patch.object(Path, "cwd", return_value=study_path),
            patch(
                "slumber.config.plugins.get_registry",
                return_value=_mock_registry_for_validate_success(),
            ),
        ):
            result = runner.invoke(app, ["study", "validate"])
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
        with (
            patch.object(Path, "cwd", return_value=tmp_path),
            patch(
                "slumber.config.plugins.get_registry",
                return_value=_mock_registry_for_validate_success(),
            ),
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
        with patch.object(Path, "cwd", return_value=study_path):
            result = runner.invoke(app, ["study", "validate"])
        assert result.exit_code == 1
        assert "Plugin validation failed" in result.output
        assert "Master" in result.output

    def test_validate_exits_1_when_no_study_in_cwd(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        with patch.object(Path, "cwd", return_value=tmp_path):
            result = runner.invoke(app, ["study", "validate"])
        assert result.exit_code == 1
        assert "study.yaml" in result.output
        assert "not found" in result.output.lower()

    def test_validate_exits_1_when_manifest_invalid(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        study_path = tmp_path / "bad-study"
        study_path.mkdir()
        (study_path / "conditions").mkdir()
        (study_path / "study.yaml").write_text(
            "study_id: x\n# name missing\n", encoding="utf-8"
        )
        with patch.object(Path, "cwd", return_value=study_path):
            result = runner.invoke(app, ["study", "validate"])
        assert result.exit_code == 1
        assert "Study manifest error" in result.output or "study.yaml" in result.output

    def test_validate_exits_1_when_condition_invalid(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        study_path = init_study(
            tmp_path, "v-study", create_env_example=False, create_gitignore=False
        )
        (study_path / "conditions" / "bad.yaml").write_text(
            "name: x\n# procedures and dag missing\n", encoding="utf-8"
        )
        with patch.object(Path, "cwd", return_value=study_path):
            result = runner.invoke(app, ["study", "validate"])
        assert result.exit_code == 1
        assert "Condition file error" in result.output or "bad.yaml" in result.output
