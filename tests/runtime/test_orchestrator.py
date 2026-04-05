"""Tests for run_study orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from slumber.config import init_study, load_study
from slumber.plugins import EntryPointGroup
from slumber.runtime import RunContext, run_study


def _make_study(tmp_path: Path, condition_yaml: str) -> tuple[Path, object]:
    """Create a minimal study folder and return (study_dir, study)."""
    study_dir = init_study(
        tmp_path, "s1", create_env_example=False, create_gitignore=False
    )
    (study_dir / "conditions" / "ctrl.yaml").write_text(
        condition_yaml, encoding="utf-8"
    )
    return study_dir, load_study(study_dir)


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


def _ctx(study_id: str = "s1") -> RunContext:
    return RunContext(
        study_id=study_id,
        run_id="r001",
        condition_id="ctrl",
        participant_id="sub-001",
        session_id="ses-01",
    )


class TestRunStudy:
    def test_creates_run_directory(self, tmp_path: Path) -> None:
        study_dir, study = _make_study(tmp_path, _MINIMAL_CONDITION)
        run_dir = run_study(study, "ctrl", _ctx(), study_dir)
        assert run_dir.is_dir()

    def test_writes_run_metadata(self, tmp_path: Path) -> None:
        study_dir, study = _make_study(tmp_path, _MINIMAL_CONDITION)
        run_dir = run_study(study, "ctrl", _ctx(), study_dir)
        meta = json.loads((run_dir / "run.json").read_text())
        assert meta["study_id"] == "s1"
        assert meta["condition_name"] == "ctrl"
        assert meta["run_id"] == "r001"
        assert meta["participant_id"] == "sub-001"
        assert meta["session_id"] == "ses-01"
        assert "started_at" in meta

    def test_run_metadata_serializes_optional_ids_as_null(self, tmp_path: Path) -> None:
        study_dir, study = _make_study(tmp_path, _MINIMAL_CONDITION)
        ctx = RunContext(
            study_id="s1",
            run_id="r001",
            condition_id="ctrl",
            participant_id=None,
            session_id=None,
        )
        run_dir = run_study(study, "ctrl", ctx, study_dir)
        meta = json.loads((run_dir / "run.json").read_text())
        assert meta["participant_id"] is None
        assert meta["session_id"] is None

    def test_returns_run_dir_path(self, tmp_path: Path) -> None:
        study_dir, study = _make_study(tmp_path, _MINIMAL_CONDITION)
        run_dir = run_study(study, "ctrl", _ctx(), study_dir)
        assert run_dir.is_absolute()

    def test_raises_on_unknown_condition(self, tmp_path: Path) -> None:
        study_dir, study = _make_study(tmp_path, _MINIMAL_CONDITION)
        with pytest.raises(ValueError, match="not found"):
            run_study(study, "nonexistent", _ctx(), study_dir)

    def test_calls_ui_backend_run(self, tmp_path: Path) -> None:
        study_dir, study = _make_study(tmp_path, _MINIMAL_CONDITION)
        mock_backend = MagicMock()
        mock_registry = MagicMock()
        mock_registry.get_plugin.return_value = mock_backend
        ctx = _ctx()

        run_study(study, "ctrl", ctx, study_dir, registry=mock_registry)

        mock_registry.get_plugin.assert_called_once_with(
            EntryPointGroup.UI_BACKENDS, "headless"
        )
        mock_backend.run.assert_called_once()
        call_args = mock_backend.run.call_args
        assert call_args[0][0] is study  # study
        assert call_args[0][1].name == "ctrl"  # condition
        assert call_args[0][2] is ctx  # context
        assert call_args[0][3] == {}  # config (default empty)

    def test_cleans_up_log_handlers_on_success(self, tmp_path: Path) -> None:
        study_dir, study = _make_study(tmp_path, _MINIMAL_CONDITION)
        removed: list[int] = []
        with patch(
            "slumber.runtime.orchestrator.configure_run_logging", return_value=[42, 43]
        ):
            with patch(
                "slumber.runtime.orchestrator.logger.remove", side_effect=removed.append
            ):
                run_study(study, "ctrl", _ctx(), study_dir)
        assert sorted(removed) == [42, 43]

    def test_cleans_up_log_handlers_on_error(self, tmp_path: Path) -> None:
        study_dir, study = _make_study(tmp_path, _MINIMAL_CONDITION)
        removed: list[int] = []
        mock_backend = MagicMock()
        mock_backend.run.side_effect = RuntimeError("boom")
        mock_registry = MagicMock()
        mock_registry.get_plugin.return_value = mock_backend

        with patch(
            "slumber.runtime.orchestrator.configure_run_logging", return_value=[99]
        ):
            with patch(
                "slumber.runtime.orchestrator.logger.remove", side_effect=removed.append
            ):
                with pytest.raises(RuntimeError, match="boom"):
                    run_study(study, "ctrl", _ctx(), study_dir, registry=mock_registry)
        assert removed == [99]
