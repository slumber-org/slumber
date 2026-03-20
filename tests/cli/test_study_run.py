"""Tests for slumber study run CLI command."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from slumber.cli.main import app
from slumber.config import init_study


_MINIMAL_CONDITION = """\
name: ctrl
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

_NOW = datetime(2025, 10, 1, 23, 0, 0, tzinfo=timezone.utc)
_PARTICIPANT_ROW = {"id": "s1_sub-001", "study_id": "s1", "participant_id": "sub-001"}
_SESSION_ROW = {"id": 42, "participant_id": "s1_sub-001", "condition_id": "s1_ctrl"}
_RUN_ROW = {"id": 7, "session_id": 42, "status": "running", "run_directory": ""}


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def study_dir(tmp_path: Path) -> Path:
    sd = init_study(tmp_path, "s1", create_env_example=False, create_gitignore=False)
    (sd / "conditions" / "ctrl.yaml").write_text(_MINIMAL_CONDITION, encoding="utf-8")
    return sd


def _invoke(runner: CliRunner, study_dir: Path) -> object:
    return runner.invoke(app, ["study", "run", "--study-dir", str(study_dir)])


class TestStudyRunCLI:
    def _patched_run(self, runner: CliRunner, study_dir: Path, **session_overrides):
        session = {**_SESSION_ROW, **session_overrides}
        mock_client = MagicMock()
        with (
            patch(
                "slumber.cli.study.get_authenticated_client", return_value=mock_client
            ),
            patch(
                "slumber.cli.study.get_participant_for_study",
                return_value=_PARTICIPANT_ROW,
            ),
            patch("slumber.cli.study.get_active_session", return_value=session),
            patch("slumber.cli.study.create_run", return_value=_RUN_ROW),
            patch("slumber.cli.study.update_run"),
            patch("slumber.cli.study.utc_now", return_value=_NOW),
            patch("slumber.cli.study.init_sentry"),
        ):
            return _invoke(runner, study_dir)

    def test_successful_run(self, runner: CliRunner, study_dir: Path) -> None:
        result = self._patched_run(runner, study_dir)
        assert result.exit_code == 0, result.output
        assert "Run complete" in result.output

    def test_run_dir_in_output(self, runner: CliRunner, study_dir: Path) -> None:
        result = self._patched_run(runner, study_dir)
        assert result.exit_code == 0
        # run_id is "7" (DB pk), should appear in the resolved path
        assert "7" in result.output

    def test_db_run_created_with_session_id(
        self, runner: CliRunner, study_dir: Path
    ) -> None:
        mock_client = MagicMock()
        with (
            patch(
                "slumber.cli.study.get_authenticated_client", return_value=mock_client
            ),
            patch(
                "slumber.cli.study.get_participant_for_study",
                return_value=_PARTICIPANT_ROW,
            ),
            patch("slumber.cli.study.get_active_session", return_value=_SESSION_ROW),
            patch("slumber.cli.study.create_run", return_value=_RUN_ROW) as mock_create,
            patch("slumber.cli.study.update_run"),
            patch("slumber.cli.study.utc_now", return_value=_NOW),
            patch("slumber.cli.study.init_sentry"),
        ):
            _invoke(runner, study_dir)
        mock_create.assert_called_once_with(mock_client, 42)

    def test_db_run_updated_completed_on_success(
        self, runner: CliRunner, study_dir: Path
    ) -> None:
        mock_client = MagicMock()
        with (
            patch(
                "slumber.cli.study.get_authenticated_client", return_value=mock_client
            ),
            patch(
                "slumber.cli.study.get_participant_for_study",
                return_value=_PARTICIPANT_ROW,
            ),
            patch("slumber.cli.study.get_active_session", return_value=_SESSION_ROW),
            patch("slumber.cli.study.create_run", return_value=_RUN_ROW),
            patch("slumber.cli.study.update_run") as mock_update,
            patch("slumber.cli.study.utc_now", return_value=_NOW),
            patch("slumber.cli.study.init_sentry"),
        ):
            result = _invoke(runner, study_dir)
        assert result.exit_code == 0
        call_kwargs = mock_update.call_args
        assert call_kwargs.args[1] == 7
        from slumber.backend.run import RunStatus

        assert call_kwargs.kwargs["status"] == RunStatus.COMPLETED
        assert "run_directory" in call_kwargs.kwargs

    def test_db_run_updated_failed_on_error(
        self, runner: CliRunner, study_dir: Path
    ) -> None:
        mock_client = MagicMock()
        with (
            patch(
                "slumber.cli.study.get_authenticated_client", return_value=mock_client
            ),
            patch(
                "slumber.cli.study.get_participant_for_study",
                return_value=_PARTICIPANT_ROW,
            ),
            patch("slumber.cli.study.get_active_session", return_value=_SESSION_ROW),
            patch("slumber.cli.study.create_run", return_value=_RUN_ROW),
            patch("slumber.cli.study.update_run") as mock_update,
            patch("slumber.cli.study.utc_now", return_value=_NOW),
            patch("slumber.cli.study.init_sentry"),
            patch("slumber.cli.study.run_study", side_effect=RuntimeError("boom")),
        ):
            result = _invoke(runner, study_dir)
        assert result.exit_code == 1
        from slumber.backend.run import RunStatus

        mock_update.assert_called_once_with(mock_client, 7, status=RunStatus.FAILED)

    def test_exits_when_not_logged_in(self, runner: CliRunner, study_dir: Path) -> None:
        with patch(
            "slumber.cli.study.get_authenticated_client",
            side_effect=ValueError("Not logged in"),
        ):
            result = _invoke(runner, study_dir)
        assert result.exit_code == 1
        assert "Not logged in" in result.output

    def test_exits_when_not_a_participant(
        self, runner: CliRunner, study_dir: Path
    ) -> None:
        mock_client = MagicMock()
        with (
            patch(
                "slumber.cli.study.get_authenticated_client", return_value=mock_client
            ),
            patch(
                "slumber.cli.study.get_participant_for_study",
                side_effect=ValueError("not a participant"),
            ),
            patch("slumber.cli.study.utc_now", return_value=_NOW),
        ):
            result = _invoke(runner, study_dir)
        assert result.exit_code == 1
        assert "not a participant" in result.output

    def test_exits_when_no_active_session(
        self, runner: CliRunner, study_dir: Path
    ) -> None:
        mock_client = MagicMock()
        with (
            patch(
                "slumber.cli.study.get_authenticated_client", return_value=mock_client
            ),
            patch(
                "slumber.cli.study.get_participant_for_study",
                return_value=_PARTICIPANT_ROW,
            ),
            patch(
                "slumber.cli.study.get_active_session",
                side_effect=ValueError("No session scheduled"),
            ),
            patch("slumber.cli.study.utc_now", return_value=_NOW),
        ):
            result = _invoke(runner, study_dir)
        assert result.exit_code == 1
        assert "No session scheduled" in result.output

    def test_exits_when_session_has_no_condition(
        self, runner: CliRunner, study_dir: Path
    ) -> None:
        result = self._patched_run(runner, study_dir, condition_id=None)
        assert result.exit_code == 1
        assert "no condition" in result.output

    def test_sentry_called_with_study_id(
        self, runner: CliRunner, study_dir: Path
    ) -> None:
        mock_client = MagicMock()
        with (
            patch(
                "slumber.cli.study.get_authenticated_client", return_value=mock_client
            ),
            patch(
                "slumber.cli.study.get_participant_for_study",
                return_value=_PARTICIPANT_ROW,
            ),
            patch("slumber.cli.study.get_active_session", return_value=_SESSION_ROW),
            patch("slumber.cli.study.create_run", return_value=_RUN_ROW),
            patch("slumber.cli.study.update_run"),
            patch("slumber.cli.study.utc_now", return_value=_NOW),
            patch("slumber.cli.study.init_sentry") as mock_sentry,
        ):
            _invoke(runner, study_dir)
        mock_sentry.assert_called_once_with("s1")

    def test_run_completes_when_update_run_raises(
        self, runner: CliRunner, study_dir: Path
    ) -> None:
        """A successful run exits 0 even if recording the status fails."""
        mock_client = MagicMock()
        with (
            patch(
                "slumber.cli.study.get_authenticated_client", return_value=mock_client
            ),
            patch(
                "slumber.cli.study.get_participant_for_study",
                return_value=_PARTICIPANT_ROW,
            ),
            patch("slumber.cli.study.get_active_session", return_value=_SESSION_ROW),
            patch("slumber.cli.study.create_run", return_value=_RUN_ROW),
            patch(
                "slumber.cli.study.update_run",
                side_effect=RuntimeError("network error"),
            ),
            patch("slumber.cli.study.utc_now", return_value=_NOW),
            patch("slumber.cli.study.init_sentry"),
        ):
            result = _invoke(runner, study_dir)
        assert result.exit_code == 0
        assert "Run complete" in result.output

    def test_run_fails_when_update_run_also_raises(
        self, runner: CliRunner, study_dir: Path
    ) -> None:
        """A failed run exits 1 even if recording the FAILED status also raises."""
        mock_client = MagicMock()
        with (
            patch(
                "slumber.cli.study.get_authenticated_client", return_value=mock_client
            ),
            patch(
                "slumber.cli.study.get_participant_for_study",
                return_value=_PARTICIPANT_ROW,
            ),
            patch("slumber.cli.study.get_active_session", return_value=_SESSION_ROW),
            patch("slumber.cli.study.create_run", return_value=_RUN_ROW),
            patch(
                "slumber.cli.study.update_run",
                side_effect=RuntimeError("network error"),
            ),
            patch("slumber.cli.study.utc_now", return_value=_NOW),
            patch("slumber.cli.study.init_sentry"),
            patch("slumber.cli.study.run_study", side_effect=RuntimeError("boom")),
        ):
            result = _invoke(runner, study_dir)
        assert result.exit_code == 1
        assert "boom" in result.output

    def test_exits_on_missing_study_dir(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        result = runner.invoke(
            app, ["study", "run", "--study-dir", str(tmp_path / "nonexistent")]
        )
        assert result.exit_code == 1
