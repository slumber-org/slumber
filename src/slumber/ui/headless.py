"""Headless UI backend: auto-complete activities; sleep emits ``end_sleep``."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from loguru import logger
from pydantic import BaseModel, ConfigDict

from slumber.ui.backend import MountedActivity, UIBackend

# Brief pause before auto ``end_sleep`` so a just-started pipeline subprocess can
# reach unit ``initialize`` (e.g. create ``clock.jsonl``) before ``stop_pipeline``.
_SLEEP_END_SETTLE_S = 0.5

if TYPE_CHECKING:
    from pathlib import Path

    from slumber.plugins.base import ConfiguredPlugin
    from slumber.run.engine import RunEngine
    from slumber.schemas.condition import Phase


class HeadlessSettings(BaseModel):
    """Headless UI accepts no settings (empty model, extra forbidden)."""

    model_config = ConfigDict(extra="forbid")


class _HeadlessActivityHost:
    """ActivityHost for headless mounts (no GUI container)."""

    container = None

    def __init__(
        self,
        engine: RunEngine,
        activity_id: str,
        *,
        on_complete: Callable[[str], None],
    ) -> None:
        self._engine = engine
        self._activity_id = activity_id
        self._on_complete = on_complete

    def complete(self) -> None:
        """Mark this activity finished as a layout step."""
        self._on_complete(self._activity_id)

    def emit(self, name: str) -> None:
        """Forward a study event to the engine."""
        self._engine.emit(name, source_activity_id=self._activity_id)

    def resolve_path(self, path: str) -> Path:
        """Resolve *path* against the study root (placeholders expanded)."""
        return self._engine.resolve_path(path)


class HeadlessBackend(UIBackend):
    """No window. Activities that finish on mount auto-complete.

    Open-ended ``sleep`` activities emit ``end_sleep`` immediately after mount
    so a condition can finish without a browser.
    """

    settings_model = HeadlessSettings

    def __init__(self, settings: HeadlessSettings | None = None) -> None:
        super().__init__(settings)
        self._engine: RunEngine | None = None
        self._mounted: list[MountedActivity] = []

    def start(self, engine: RunEngine) -> None:
        """Start at the condition entry phase; returns when the run ends."""
        self._engine = engine
        logger.info(
            "headless: condition={!r} entry={!r}",
            engine.condition.name,
            engine.condition.entry,
        )
        engine.start_phase(engine.condition.entry)

    def apply_frame(self, frame: dict[str, Any], phase: Phase) -> None:
        """Log frame overrides (no chrome in headless)."""
        logger.debug("headless: apply_frame {} phase={!r}", frame, phase.id)

    def mount_phase(
        self,
        phase: Phase,
        layout: ConfiguredPlugin,
        activities: list[MountedActivity],
    ) -> None:
        """Mount activities; emit ``phase_completed`` or ``end_sleep`` as needed."""
        del layout  # headless does not render layout chrome
        if self._engine is None:
            raise RuntimeError("HeadlessBackend.start() must be called first.")

        engine = self._engine
        self._mounted = list(activities)
        completed: set[str] = set()

        def on_complete(activity_id: str) -> None:
            completed.add(activity_id)
            logger.debug(
                "headless: activity {!r} completed in phase {!r}",
                activity_id,
                phase.id,
            )

        for mounted in activities:
            host = _HeadlessActivityHost(
                engine,
                mounted.config.id,
                on_complete=on_complete,
            )
            logger.info(
                "headless: mounting activity {!r} (type={!r}) in phase {!r}",
                mounted.config.id,
                mounted.config.type,
                phase.id,
            )
            mounted.instance.mount(host)

        if all(item.config.id in completed for item in activities):
            engine.emit("phase_completed")
            return

        for mounted in activities:
            if mounted.config.id in completed:
                continue
            if mounted.config.type == "sleep":
                logger.info(
                    "headless: emitting end_sleep for activity {!r}",
                    mounted.config.id,
                )
                time.sleep(_SLEEP_END_SETTLE_S)
                engine.emit("end_sleep", source_activity_id=mounted.config.id)

    def unmount_phase(self) -> None:
        """Unmount previously mounted activity plugins."""
        for mounted in self._mounted:
            mounted.instance.unmount()
        self._mounted = []

    def stop(self) -> None:
        """Clear engine reference after the run ends."""
        self._engine = None
