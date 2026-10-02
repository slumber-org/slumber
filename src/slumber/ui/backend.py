"""UI backend ABC shared by gui and headless adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from slumber.plugins.base import ConfiguredPlugin

if TYPE_CHECKING:
    from slumber.run.engine import RunEngine
    from slumber.schemas.condition import Activity as ActivityConfig
    from slumber.schemas.condition import Phase
    from slumber.ui.activities.base import Activity


@dataclass(frozen=True)
class MountedActivity:
    """Resolved activity config plus plugin instance for a phase mount."""

    config: ActivityConfig
    instance: Activity


class UIBackend(ConfiguredPlugin, ABC):
    """Participant UI adapter driven by :class:`~slumber.run.engine.RunEngine`.

    ``start`` prepares the UI and must call ``engine.start_phase(entry)``.
    GUI backends then block in their event loop until ``end_run``; headless
    returns once the engine has finished.
    """

    @abstractmethod
    def start(self, engine: RunEngine) -> None:
        """Prepare the UI and drive the run until ``end_run``."""

    @abstractmethod
    def apply_frame(self, frame: dict[str, Any]) -> None:
        """Apply merged AppFrame settings for the active phase."""

    @abstractmethod
    def mount_phase(
        self,
        phase: Phase,
        layout: ConfiguredPlugin,
        activities: list[MountedActivity],
    ) -> None:
        """Mount layout and activities for *phase*."""

    @abstractmethod
    def unmount_phase(self) -> None:
        """Tear down the active phase layout and activities."""

    def stop(self) -> None:
        """Finalize the UI after ``end_run`` (optional override)."""
