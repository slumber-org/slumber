"""Activity ABC: layout-agnostic participant-facing steps."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, ClassVar, Protocol

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

    def resolve_path(self, path: str) -> Path:
        """Expand placeholders in *path* and resolve it against the study root.

        Use this for paths an activity finds in its content, so they follow the
        same rules as paths in settings (relative paths are relative to the study
        root; ``{assets_dir}`` and the other placeholders work).
        """
        ...


class Activity(ConfiguredPlugin, ABC):
    """Base class for activity plugins registered under ``slumber.activities``.

    An activity keeps its own styles in :attr:`css`; the GUI backend adds them when
    it mounts a phase that uses the activity, so ``mount`` only builds elements.
    """

    css: ClassVar[str] = ""
    """Stylesheet for this activity, using the shared ``--slumber-*`` variables."""

    @abstractmethod
    def mount(self, activity_host: ActivityHost) -> None:
        """Render into the host and wire interactions."""

    def unmount(self) -> None:
        """Tear down UI for this activity (optional override)."""
