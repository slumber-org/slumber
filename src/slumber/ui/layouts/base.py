"""Layout ABC and host protocol for phase body arrangement."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol

from slumber.plugins.base import ConfiguredPlugin

if TYPE_CHECKING:
    from slumber.ui.backend import MountedActivity


class LayoutHost(Protocol):
    """Services a layout needs from the GUI backend."""

    @property
    def container(self) -> Any:
        """NiceGUI element that fills the AppFrame body."""
        ...

    def emit_phase_completed(self) -> None:
        """Notify the engine that the layout finished all steps."""
        ...

    def make_activity_host(
        self,
        activity_id: str,
        container: Any,
        *,
        on_complete: Callable[[str], None],
    ) -> Any:
        """Build an ActivityHost for one mounted activity."""
        ...


class Layout(ConfiguredPlugin, ABC):
    """How a phase's body is arranged inside the AppFrame."""

    @abstractmethod
    def mount(self, host: LayoutHost, activities: list[MountedActivity]) -> None:
        """Render into *host.container* and mount activities."""

    def unmount(self) -> None:
        """Tear down layout UI and unmount activities (optional override)."""
