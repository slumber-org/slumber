"""Tests for slumber condition sync CLI command."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from slumber.cli.main import app


_MINIMAL_CONDITION_YAML = """\
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

_MINIMAL_STUDY_YAML = """\
study_id: test-study
name: Test Study
"""


def _make_study_dir(tmp_path: Path, condition_names: list[str]) -> Path:
    """Create a minimal study folder with the given conditions."""
    study_dir = tmp_path / "test-study"
    study_dir.mkdir()
    (study_dir / "study.yaml").write_text(_MINIMAL_STUDY_YAML, encoding="utf-8")
    conditions_dir = study_dir / "conditions"
    conditions_dir.mkdir()
    for name in condition_names:
        (conditions_dir / f"{name}.yaml").write_text(
            _MINIMAL_CONDITION_YAML.format(name=name), encoding="utf-8"
        )
    return study_dir


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestConditionSync:
    def test_syncs_all_conditions_by_default(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """With no --conditions flag, all conditions in the study are synced."""
        study_dir = _make_study_dir(tmp_path, ["condition_1", "condition_2"])
        mock_client = MagicMock()
        mock_client.table.return_value.upsert.return_value.execute.return_value.data = [
            {"id": "test-study_condition_1"}
        ]

        with (
            patch("slumber.cli.condition.get_client", return_value=mock_client),
            patch(
                "slumber.cli.condition.sync_conditions",
                return_value=[{"id": "test-study_condition_1"}],
            ) as mock_sync,
        ):
            result = runner.invoke(
                app,
                ["condition", "sync", "--study-dir", str(study_dir)],
            )

        assert result.exit_code == 0, result.output
        assert mock_sync.call_count == 2
        assert "Synced 2 condition(s)" in result.output

    def test_syncs_selected_conditions(self, runner: CliRunner, tmp_path: Path) -> None:
        """--conditions filters to only the named conditions."""
        study_dir = _make_study_dir(tmp_path, ["condition_1", "condition_2"])

        with (
            patch("slumber.cli.condition.get_client", return_value=MagicMock()),
            patch(
                "slumber.cli.condition.sync_conditions",
                return_value=[{"id": "test-study_condition_1"}],
            ) as mock_sync,
        ):
            result = runner.invoke(
                app,
                [
                    "condition",
                    "sync",
                    "--study-dir",
                    str(study_dir),
                    "--conditions",
                    "condition_1",
                ],
            )

        assert result.exit_code == 0, result.output
        assert mock_sync.call_count == 1
        synced_condition = mock_sync.call_args[0][2][0]
        assert synced_condition.name == "condition_1"
        assert "Synced 1 condition(s)" in result.output

    def test_exits_with_error_for_unknown_condition_name(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Unknown --conditions name exits 1 with a clear error listing available names."""
        study_dir = _make_study_dir(tmp_path, ["condition_1"])

        result = runner.invoke(
            app,
            [
                "condition",
                "sync",
                "--study-dir",
                str(study_dir),
                "--conditions",
                "does_not_exist",
            ],
        )

        assert result.exit_code == 1
        assert "does_not_exist" in result.output
        assert "condition_1" in result.output

    def test_exits_with_error_when_study_dir_missing(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Non-existent study dir exits 1 with error."""
        result = runner.invoke(
            app,
            [
                "condition",
                "sync",
                "--study-dir",
                str(tmp_path / "no-such-study"),
            ],
        )

        assert result.exit_code == 1

    def test_exits_with_error_when_service_role_key_missing(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Missing service role key exits 1 with error."""
        study_dir = _make_study_dir(tmp_path, ["condition_1"])

        with patch(
            "slumber.cli.condition.get_client",
            side_effect=ValueError("SUPABASE_SERVICE_ROLE_KEY is not set"),
        ):
            result = runner.invoke(
                app,
                ["condition", "sync", "--study-dir", str(study_dir)],
            )

        assert result.exit_code == 1
        assert "SUPABASE_SERVICE_ROLE_KEY" in result.output

    def test_exits_with_error_when_sync_fails(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """When sync_conditions raises, exits 1 with error message."""
        study_dir = _make_study_dir(tmp_path, ["condition_1"])

        with (
            patch("slumber.cli.condition.get_client", return_value=MagicMock()),
            patch(
                "slumber.cli.condition.sync_conditions",
                side_effect=RuntimeError("DB error"),
            ),
        ):
            result = runner.invoke(
                app,
                ["condition", "sync", "--study-dir", str(study_dir)],
            )

        assert result.exit_code == 1
        assert "DB error" in result.output

    def test_no_conditions_in_study_exits_cleanly(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Empty conditions directory exits 0 with informational message."""
        study_dir = _make_study_dir(tmp_path, [])

        result = runner.invoke(
            app,
            ["condition", "sync", "--study-dir", str(study_dir)],
        )

        assert result.exit_code == 0
        assert "No conditions found" in result.output
