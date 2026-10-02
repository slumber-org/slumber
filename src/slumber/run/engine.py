"""RunEngine: run directory, logging, phase/event/action loop."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from slumber.config.paths import resolve_settings, run_placeholders
from slumber.config.plugins import (
    PluginGroup,
    merge_frame_settings,
    merge_layout_settings,
    resolve_plugin_spec,
)
from slumber.pipeline.manager import PipelineManager
from slumber.plugins import get_registry
from slumber.run.context import RunContext, create_run_dir
from slumber.run.logging import configure_run_logging
from slumber.schemas.condition import Action, Condition, Phase
from slumber.schemas.plugin import PluginSpec
from slumber.schemas.study import Study
from slumber.ui.activities.base import Activity as ActivityPlugin
from slumber.ui.backend import MountedActivity, UIBackend

if TYPE_CHECKING:
    from slumber.plugins.registry import PluginRegistry

_RUN_METADATA_FILE = "run.json"


def _write_run_metadata(
    run_dir: Path,
    context: RunContext,
    condition_name: str,
    started_at: datetime,
) -> None:
    """Write ``run.json`` with run context and start timestamp."""
    metadata = {
        "study_id": context.study_id,
        "condition_name": condition_name,
        "participant_id": context.participant_id,
        "session_id": context.session_id,
        "run_id": context.run_id,
        "started_at": started_at.isoformat(),
    }
    (run_dir / _RUN_METADATA_FILE).write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )


class RunEngine:
    """Drive one condition run: phases, events, actions, until ``end_run``."""

    def __init__(
        self,
        study: Study,
        condition: Condition,
        context: RunContext,
        study_dir: Path,
        *,
        registry: PluginRegistry | None = None,
        pipelines: PipelineManager | None = None,
        ui: UIBackend | None = None,
    ) -> None:
        self._study = study
        self._condition = condition
        self._context = context
        self._study_dir = study_dir.resolve()
        self._registry = registry if registry is not None else get_registry()
        self._pipelines = pipelines
        self._ui_override = ui

        self._run_dir: Path | None = None
        self._placeholders: dict[str, str] = {}
        self._handler_ids: list[int] = []
        self._ui: UIBackend | None = None
        self._active_phase: Phase | None = None
        self._ended = False

    @property
    def study(self) -> Study:
        """Study manifest for this run."""
        return self._study

    @property
    def condition(self) -> Condition:
        """Condition being executed."""
        return self._condition

    @property
    def context(self) -> RunContext:
        """Run identity and layout placeholder values."""
        return self._context

    @property
    def study_dir(self) -> Path:
        """Absolute path to the study package root."""
        return self._study_dir

    @property
    def run_dir(self) -> Path | None:
        """Run output directory once :meth:`run` has created it."""
        return self._run_dir

    @property
    def placeholders(self) -> dict[str, str]:
        """Expanded path placeholders for the active run."""
        return dict(self._placeholders)

    @property
    def active_phase(self) -> Phase | None:
        """Currently mounted phase, if any."""
        return self._active_phase

    @property
    def ended(self) -> bool:
        """Whether ``end_run`` has completed."""
        return self._ended

    def run(self) -> Path:
        """Create the run directory, start the UI, and drive until ``end_run``.

        Returns:
            Path to the created run directory.

        Raises:
            ValueError: If plugin resolution fails.
            TypeError: If the resolved UI is not a :class:`UIBackend`.
        """
        self._run_dir = create_run_dir(self._study, self._context, self._study_dir)
        started_at = datetime.now(tz=timezone.utc)
        _write_run_metadata(
            self._run_dir, self._context, self._condition.name, started_at
        )

        self._placeholders = run_placeholders(
            self._study_dir,
            study_id=self._study.study_id,
            study_name=self._study.study_name,
            assets_dir=self._study.assets_dir,
            run_dir=self._run_dir,
            run_id=self._context.run_id,
            condition_id=self._context.condition_id,
            participant_id=self._context.participant_id,
            session_id=self._context.session_id,
        )

        if self._pipelines is None:
            self._pipelines = PipelineManager(self._condition)

        self._handler_ids = configure_run_logging(
            self._study,
            self._context,
            self._run_dir,
            study_dir=self._study_dir,
            placeholders=self._placeholders,
        )

        try:
            logger.info(
                "Run started  study={!r} condition={!r} run_id={!r}",
                self._study.study_id,
                self._condition.name,
                self._context.run_id,
            )
            self._ui = self._ui_override or self._resolve_ui()
            self._ui.start(self)
            if not self._ended:
                self.end_run()
            logger.info(
                "Run completed  run_id={!r}  dir={}",
                self._context.run_id,
                self._run_dir,
            )
        finally:
            for handler_id in self._handler_ids:
                logger.remove(handler_id)
            self._handler_ids = []

        assert self._run_dir is not None
        return self._run_dir

    def start_phase(self, phase_id: str) -> None:
        """Stop the previous phase and mount *phase_id*."""
        if self._ended:
            logger.debug("Ignoring start_phase {!r}; run already ended.", phase_id)
            return
        if self._ui is None:
            raise RuntimeError("UI backend is not started.")

        try:
            phase = self._condition.phases_mapping[phase_id]
        except KeyError as e:
            available = sorted(self._condition.phase_ids)
            raise KeyError(
                f"Unknown phase {phase_id!r}. Available: {available}."
            ) from e

        if self._active_phase is not None:
            self._ui.unmount_phase()
            self._active_phase = None

        study_frame = self._study.ui.settings.get("frame")
        frame = merge_frame_settings(study_frame, phase.frame)
        self._ui.apply_frame(frame)

        layout = self._resolve_layout(phase)
        activities = self._resolve_activities(phase)
        self._active_phase = phase
        logger.info("Starting phase {!r}", phase_id)
        self._ui.mount_phase(phase, layout, activities)

    def start_pipeline(self, pipeline_id: str) -> None:
        """Start a named pipeline."""
        if self._ended:
            return
        if self._pipelines is None:
            raise RuntimeError("Pipeline manager is not initialized.")
        self._pipelines.start(pipeline_id)

    def stop_pipeline(self, pipeline_id: str) -> None:
        """Stop a named pipeline."""
        if self._pipelines is None:
            raise RuntimeError("Pipeline manager is not initialized.")
        self._pipelines.stop(pipeline_id)

    def end_run(self) -> None:
        """Stop pipelines, unmount UI, and mark the run finished."""
        if self._ended:
            return
        self._ended = True
        logger.info("Ending run  run_id={!r}", self._context.run_id)
        if self._pipelines is not None:
            self._pipelines.stop_all()
        if self._ui is not None:
            if self._active_phase is not None:
                self._ui.unmount_phase()
                self._active_phase = None
            self._ui.stop()

    def emit(self, name: str, *, source_activity_id: str | None = None) -> None:
        """Dispatch a study event to activity then phase ``on`` handlers.

        Args:
            name: Event name (e.g. ``phase_completed``, ``end_sleep``).
            source_activity_id: Emitting activity id when the event came from
                ``host.emit``; ``None`` for layout events such as
                ``phase_completed``.
        """
        if self._ended:
            logger.debug("Ignoring event {!r}; run already ended.", name)
            return
        if self._active_phase is None:
            logger.warning("Event {!r} with no active phase; ignoring.", name)
            return

        phase = self._active_phase
        logger.debug(
            "Event {!r} (phase={!r}, activity={!r})",
            name,
            phase.id,
            source_activity_id,
        )

        handlers_do: list[Action] = []
        if source_activity_id is not None:
            activity = next(
                (a for a in phase.activities if a.id == source_activity_id),
                None,
            )
            if activity is not None:
                for handler in activity.on:
                    if handler.event == name:
                        handlers_do.extend(handler.do)

        for handler in phase.on:
            if handler.event == name:
                handlers_do.extend(handler.do)

        if not handlers_do:
            logger.debug("No handlers for event {!r}", name)
            return

        for action in handlers_do:
            if self._ended:
                break
            self._execute_action(action)

    def _execute_action(self, action: Action) -> None:
        if action.start_phase is not None:
            self.start_phase(action.start_phase)
        elif action.start_pipeline is not None:
            self.start_pipeline(action.start_pipeline)
        elif action.stop_pipeline is not None:
            self.stop_pipeline(action.stop_pipeline)
        elif action.end_run:
            self.end_run()
        else:
            raise ValueError(f"Unsupported action: {action!r}")

    def _resolve_ui(self) -> UIBackend:
        ui_settings = resolve_settings(
            dict(self._study.ui.settings),
            study_root=self._study_dir,
            placeholders=self._placeholders,
        )
        ui_spec = PluginSpec(type=self._study.ui.type, settings=ui_settings)
        resolved = resolve_plugin_spec(ui_spec, PluginGroup.UI, registry=self._registry)
        if not isinstance(resolved, UIBackend):
            raise TypeError(
                f"UI plugin {self._study.ui.type!r} must be a UIBackend, "
                f"got {type(resolved).__name__}."
            )
        return resolved

    def _resolve_layout(self, phase: Phase) -> Any:
        layout_settings = merge_layout_settings(self._study, phase.layout)
        layout_settings = resolve_settings(
            layout_settings,
            study_root=self._study_dir,
            placeholders=self._placeholders,
        )
        layout_spec = PluginSpec(type=phase.layout.type, settings=layout_settings)
        return resolve_plugin_spec(
            layout_spec, PluginGroup.LAYOUTS, registry=self._registry
        )

    def _resolve_activities(self, phase: Phase) -> list[MountedActivity]:
        mounted: list[MountedActivity] = []
        for activity_config in phase.activities:
            settings = resolve_settings(
                dict(activity_config.settings),
                study_root=self._study_dir,
                placeholders=self._placeholders,
            )
            spec = PluginSpec(type=activity_config.type, settings=settings)
            instance = resolve_plugin_spec(
                spec, PluginGroup.ACTIVITIES, registry=self._registry
            )
            if not isinstance(instance, ActivityPlugin):
                raise TypeError(
                    f"Activity {activity_config.id!r} type "
                    f"{activity_config.type!r} must be an Activity plugin, "
                    f"got {type(instance).__name__}."
                )
            mounted.append(MountedActivity(config=activity_config, instance=instance))
        return mounted


def run_study(
    study: Study,
    condition_name: str,
    context: RunContext,
    study_dir: Path,
    registry: PluginRegistry | None = None,
) -> Path:
    """Run a study condition via :class:`RunEngine`.

    Args:
        study: Loaded study manifest (with conditions).
        condition_name: Name of the condition to run.
        context: Run context (ids for layout and logging placeholders).
        study_dir: Absolute path to the study folder.
        registry: Plugin registry; uses the default registry when None.

    Returns:
        Path to the created run directory.

    Raises:
        ValueError: If *condition_name* is not found in the study.
    """
    conditions_by_name = {c.name: c for c in study.conditions}
    if condition_name not in conditions_by_name:
        available = sorted(conditions_by_name)
        raise ValueError(
            f"Condition {condition_name!r} not found in study {study.study_id!r}. "
            f"Available: {available}."
        )
    condition = conditions_by_name[condition_name]
    return RunEngine(
        study,
        condition,
        context,
        study_dir,
        registry=registry,
    ).run()
