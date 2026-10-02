"""Tests for slumber study run CLI command (local only)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from slumber.cli.main import app
from slumber.config import init_study

_MINIMAL_CONDITION = """\
name: ctrl
entry: setup
phases:
  - id: setup
    layout:
      type: stepper
    activities:
      - id: welcome
        type: instruction
        settings:
          content: Hello
    on:
      - event: phase_completed
        do:
          - end_run
pipelines: []
"""


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def study_dir(tmp_path: Path) -> Path:
    sd = init_study(tmp_path, "s1", create_env_example=False, create_gitignore=False)
    (sd / "conditions" / "ctrl.yaml").write_text(_MINIMAL_CONDITION, encoding="utf-8")
    return sd


def _invoke_local(
    runner: CliRunner,
    study_dir: Path,
    condition: str = "ctrl",
    *,
    ui: str | None = None,
) -> object:
    args = ["study", "run", "--study-dir", str(study_dir), "--condition", condition]
    if ui is not None:
        args.extend(["--ui", ui])
    return runner.invoke(app, args)


class TestStudyRunLocalCLI:
    def test_local_run_succeeds(self, runner: CliRunner, study_dir: Path) -> None:
        result = _invoke_local(runner, study_dir)
        assert result.exit_code == 0, result.output
        assert "Run complete" in result.output
        assert "run-" in result.output
        assert re.search(
            r"run-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            result.output,
            re.IGNORECASE,
        )

    def test_ui_override_headless(self, runner: CliRunner, study_dir: Path) -> None:
        manifest = study_dir / "study.yaml"
        data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
        data["ui"] = {"type": "gui"}
        manifest.write_text(
            yaml.dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        result = _invoke_local(runner, study_dir, ui="headless")
        assert result.exit_code == 0, result.output
        assert "Run complete" in result.output

    def test_invalid_ui_override_exits(
        self, runner: CliRunner, study_dir: Path
    ) -> None:
        result = _invoke_local(runner, study_dir, ui="qt")
        assert result.exit_code == 1
        assert "Invalid --ui" in result.output

    def test_local_run_custom_participant_placeholder_in_path(
        self,
        runner: CliRunner,
        study_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """PARTICIPANT_ID is used when the run layout includes the placeholder."""
        manifest = study_dir / "study.yaml"
        data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
        data.setdefault("runs", {})
        data["runs"]["layout"] = "sub-{participant_id}/run-{run_id}"
        manifest.write_text(
            yaml.dump(data, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        monkeypatch.setenv("PARTICIPANT_ID", "p1")
        result = _invoke_local(runner, study_dir)
        assert result.exit_code == 0, result.output
        assert "sub-p1" in result.output

    def test_requires_condition(self, runner: CliRunner, study_dir: Path) -> None:
        result = runner.invoke(
            app,
            ["study", "run", "--study-dir", str(study_dir)],
        )
        assert result.exit_code != 0
        assert "condition" in result.output.lower()

    def test_scheduled_flag_is_not_accepted(
        self, runner: CliRunner, study_dir: Path
    ) -> None:
        result = runner.invoke(
            app,
            [
                "study",
                "run",
                "--study-dir",
                str(study_dir),
                "--condition",
                "ctrl",
                "--scheduled",
            ],
        )
        assert result.exit_code != 0
        assert "No such option" in result.output or "scheduled" in result.output.lower()

    def test_exits_on_missing_study_dir(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        result = runner.invoke(
            app,
            [
                "study",
                "run",
                "--study-dir",
                str(tmp_path / "nonexistent"),
                "--condition",
                "ctrl",
            ],
        )
        assert result.exit_code == 1
