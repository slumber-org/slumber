"""Tests for slumber study validate command."""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from slumber.cli.main import app
from slumber.config.study import STUDY_YAML_FILENAME, init_study


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestValidateCommand:
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
        with patch.object(Path, "cwd", return_value=study_path):
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
        with patch.object(Path, "cwd", return_value=tmp_path):
            result = runner.invoke(
                app,
                ["study", "validate", "--study-dir", str(study_path)],
            )
        assert result.exit_code == 0
        assert "v-study" in result.output

    def test_validate_exits_1_when_no_study_in_cwd(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        with patch.object(Path, "cwd", return_value=tmp_path):
            result = runner.invoke(app, ["study", "validate"])
        assert result.exit_code == 1
        assert "Study folder not found" in result.output
        assert "study.yaml" in result.output

    def test_validate_exits_1_when_manifest_invalid(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        study_path = tmp_path / "bad-study"
        study_path.mkdir()
        (study_path / "conditions").mkdir()
        (study_path / STUDY_YAML_FILENAME).write_text(
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
