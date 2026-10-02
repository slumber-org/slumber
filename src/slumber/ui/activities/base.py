"""Activity ABC: layout-agnostic participant-facing steps."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol

from slumber.plugins.base import ConfiguredPlugin


class ActivityHost(Protocol):
    """API injected at mount: container, complete/emit, and path helpers.

    ``container`` is a NiceGUI element under the GUI backend, or ``None`` when
    running headless.
    """

    container: Any | None

    def complete(self) -> None:
        """Mark this mounted activity finished as a layout step."""
        ...

    def emit(self, name: str) -> None:
        """Emit a named study event to the RunEngine."""
        ...


class Activity(ConfiguredPlugin, ABC):
    """Base class for activity plugins registered under ``slumber.activities``."""

    @abstractmethod
    def mount(self, activity_host: ActivityHost) -> None:
        """Render into the host and wire interactions."""

    def unmount(self) -> None:
        """Tear down UI for this activity (optional override)."""
