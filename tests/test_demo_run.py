"""Headless integration checks for the example studies."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from slumber.cli.main import app
from slumber.constants import PACKAGE_ROOT

_DEMO_DIR = PACKAGE_ROOT / "examples" / "demo"
_SLEEP_STUDY_DIR = PACKAGE_ROOT / "examples" / "sleep-study"


@pytest.mark.skipif(not _DEMO_DIR.is_dir(), reason="examples/demo not present")
class TestHeadlessDemoRun:
    """Run examples/demo headless and assert run artifacts."""

    def test_headless_demo_exits_with_artifacts(self, runner: CliRunner) -> None:
        result = runner.invoke(
            app,
            [
                "study",
                "run",
                "--study-dir",
                str(_DEMO_DIR),
                "--condition",
                "demo",
                "--ui",
                "headless",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "Run complete:" in result.output

        run_dir = Path(result.output.strip().split("Run complete:")[-1].strip())
        assert run_dir.is_dir()
        assert (run_dir / "run.json").is_file()
        assert (run_dir / "clock.jsonl").is_file()

        meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        assert meta["study_id"] == "demo"
        assert meta["condition_name"] == "demo"
        assert meta["run_id"]


@pytest.mark.skipif(
    not _SLEEP_STUDY_DIR.is_dir(), reason="examples/sleep-study not present"
)
class TestHeadlessSleepStudyRun:
    """Run each examples/sleep-study condition headless and assert run artifacts."""

    @pytest.mark.parametrize("condition", ["relaxation", "control"])
    def test_headless_condition_exits_with_artifacts(
        self, runner: CliRunner, tmp_path: Path, condition: str
    ) -> None:
        study_dir = tmp_path / "sleep-study"
        shutil.copytree(_SLEEP_STUDY_DIR, study_dir)

        result = runner.invoke(
            app,
            [
                "study",
                "run",
                "--study-dir",
                str(study_dir),
                "--condition",
                condition,
                "--ui",
                "headless",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "Run complete:" in result.output

        run_dir = Path(result.output.strip().split("Run complete:")[-1].strip())
        assert run_dir.parent == study_dir / "runs"
        for artifact in ("run.json", "run.log", "recording.jsonl"):
            assert (run_dir / artifact).is_file(), artifact

        meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        assert meta["study_id"] == "sleep-study"
        assert meta["condition_name"] == condition
