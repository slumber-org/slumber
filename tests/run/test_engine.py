"""Tests for RunEngine phase/event/action loop."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from slumber.config import init_study, load_study
from slumber.pipeline.manager import PipelineManager
from slumber.run import RunContext, RunEngine, run_study
from slumber.schemas.condition import Phase
from slumber.ui.headless import HeadlessBackend


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

_PIPELINE_CONDITION = """\
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
          - start_pipeline: main
          - start_phase: sleep
  - id: sleep
    layout:
      type: hub
    activities:
      - id: sleep
        type: sleep
        on:
          - event: end_sleep
            do:
              - stop_pipeline: main
              - end_run
pipelines:
  - id: main
    units:
      - id: clock
        type: clock
        settings:
          rate: 2.0
    connections: []
"""

_AWAKENING_CONDITION = """\
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
          - start_phase: sleep
  - id: sleep
    frame:
      header: false
      footer: false
    layout:
      type: hub
    activities:
      - id: sleep
        type: sleep
        on:
          - event: marked_awake
            do:
              - start_phase: awakening
          - event: end_sleep
            do:
              - start_phase: morning
  - id: awakening
    layout:
      type: stepper
    activities:
      - id: awake
        type: instruction
        settings:
          content: Awake
    on:
      - event: phase_completed
        do:
          - start_phase: sleep
  - id: morning
    layout:
      type: stepper
    activities:
      - id: done
        type: instruction
        settings:
          content: Morning
    on:
      - event: phase_completed
        do:
          - end_run
pipelines: []
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

    def test_cleans_up_log_handlers_on_success(self, tmp_path: Path) -> None:
        study_dir, study = _make_study(tmp_path, _MINIMAL_CONDITION)
        removed: list[int] = []
        with (
            patch(
                "slumber.run.engine.configure_run_logging",
                return_value=[42, 43],
            ),
            patch("slumber.run.engine.logger.remove", side_effect=removed.append),
        ):
            run_study(study, "ctrl", _ctx(), study_dir)
        assert sorted(removed) == [42, 43]

    def test_cleans_up_log_handlers_on_error(self, tmp_path: Path) -> None:
        study_dir, study = _make_study(tmp_path, _MINIMAL_CONDITION)
        removed: list[int] = []

        class BoomUI:
            settings_model = None

            def start(self, engine: RunEngine) -> None:
                raise RuntimeError("boom")

            def apply_frame(self, frame: dict) -> None:
                pass

            def mount_phase(self, phase, layout, activities) -> None:
                pass

            def unmount_phase(self) -> None:
                pass

            def stop(self) -> None:
                pass

        condition = study.conditions[0]
        engine = RunEngine(
            study,
            condition,
            _ctx(),
            study_dir,
            ui=BoomUI(),  # type: ignore[arg-type]
        )
        with (
            patch(
                "slumber.run.engine.configure_run_logging",
                return_value=[99],
            ),
            patch("slumber.run.engine.logger.remove", side_effect=removed.append),
            pytest.raises(RuntimeError, match="boom"),
        ):
            engine.run()
        assert removed == [99]


class TestFramePerPhase:
    def test_apply_frame_gets_resolved_frame_and_phase_title(
        self, tmp_path: Path
    ) -> None:
        study_dir, _ = _make_study(tmp_path, _AWAKENING_CONDITION)
        (study_dir / "study.yaml").write_text(
            "study_id: s1\n"
            'study_name: "Night Study"\n'
            "ui:\n"
            "  type: gui\n"
            "  settings:\n"
            "    frame:\n"
            "      header:\n"
            '        title: "{study_name}"\n'
            "        show_phase_title: true\n",
            encoding="utf-8",
        )
        study = load_study(study_dir)
        calls: list[tuple[dict, str | None]] = []

        class RecordingBackend(HeadlessBackend):
            def apply_frame(self, frame: dict, phase: Phase) -> None:
                calls.append((frame, phase.display_title))

        RunEngine(
            study, study.conditions[0], _ctx(), study_dir, ui=RecordingBackend()
        ).run()

        assert [title for _, title in calls] == ["setup", "sleep", "morning"]
        assert calls[0][0]["header"] == {
            "title": "Night Study",
            "show_phase_title": True,
        }
        assert calls[1][0]["header"] is False


class TestResolvePath:
    def test_expands_placeholders_and_uses_the_study_root(self, tmp_path: Path) -> None:
        study_dir, _ = _make_study(tmp_path, _MINIMAL_CONDITION)
        study = load_study(study_dir)
        resolved: dict[str, Path] = {}
        absolute = (tmp_path / "elsewhere" / "c.png").resolve()

        class RecordingBackend(HeadlessBackend):
            def mount_phase(self, phase, layout, activities) -> None:
                engine = self._engine
                resolved["placeholder"] = engine.resolve_path("{assets_dir}/a.png")
                resolved["relative"] = engine.resolve_path("assets/b.png")
                resolved["absolute"] = engine.resolve_path(str(absolute))
                super().mount_phase(phase, layout, activities)

        RunEngine(
            study, study.conditions[0], _ctx(), study_dir, ui=RecordingBackend()
        ).run()

        root = study_dir.resolve()
        assert resolved["placeholder"] == root / "assets" / "a.png"
        assert resolved["relative"] == root / "assets" / "b.png"
        assert resolved["absolute"] == absolute


class TestRunEngineFlow:
    def test_instruction_phase_completes_and_ends(self, tmp_path: Path) -> None:
        study_dir, study = _make_study(tmp_path, _MINIMAL_CONDITION)
        run_dir = run_study(study, "ctrl", _ctx(), study_dir)
        assert (run_dir / "run.json").is_file()

    def test_pipeline_start_and_stop(self, tmp_path: Path) -> None:
        study_dir, study = _make_study(tmp_path, _PIPELINE_CONDITION)
        condition = study.conditions[0]
        pipelines = PipelineManager(condition)
        engine = RunEngine(
            study,
            condition,
            _ctx(),
            study_dir,
            pipelines=pipelines,
        )
        engine.run()
        assert pipelines.running == frozenset()

    def test_headless_sleep_emits_end_sleep_not_awakening_loop(
        self, tmp_path: Path
    ) -> None:
        """Headless emits end_sleep on mount, so awakening is skipped."""
        study_dir, study = _make_study(tmp_path, _AWAKENING_CONDITION)
        phases_seen: list[str] = []
        condition = study.conditions[0]
        engine = RunEngine(study, condition, _ctx(), study_dir)
        original_start = engine.start_phase

        def tracking_start(phase_id: str) -> None:
            phases_seen.append(phase_id)
            original_start(phase_id)

        engine.start_phase = tracking_start  # type: ignore[method-assign]
        engine.run()
        assert phases_seen == ["setup", "sleep", "morning"]
        assert "awakening" not in phases_seen
