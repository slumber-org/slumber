"""Headless demo run integration check."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from slumber.cli.main import app
from slumber.constants import PACKAGE_ROOT

_DEMO_DIR = PACKAGE_ROOT / "examples" / "demo"


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
