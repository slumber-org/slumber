"""Layout ABC and host protocol for phase body arrangement."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar, Protocol

from pydantic import BaseModel

from slumber.plugins.base import ConfiguredPlugin

if TYPE_CHECKING:
    from slumber.ui.activities.base import Activity
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
    """How a phase's body is arranged inside the AppFrame.

    A layout keeps its own styles in :attr:`css`; the GUI backend adds them when it
    mounts the layout, so ``mount`` only builds elements. To show an activity, a
    layout calls :meth:`mount_activity`; :meth:`unmount_activity` removes it.
    """

    css: ClassVar[str] = ""
    """Stylesheet for this layout, using the shared ``--slumber-*`` variables."""

    def __init__(self, settings: BaseModel | None = None) -> None:
        super().__init__(settings)
        self._mounted_activity: Activity | None = None

    @abstractmethod
    def mount(self, host: LayoutHost, activities: list[MountedActivity]) -> None:
        """Build the layout in *host.container* and decide which activity to show.

        Each activity is shown with :meth:`mount_activity`.
        """

    def unmount(self) -> None:
        """Tear down the layout by unmounting the activity it shows.

        A layout with more to clean up overrides this and calls ``super().unmount()``.
        """
        self.unmount_activity()

    def mount_activity(
        self,
        host: LayoutHost,
        mounted: MountedActivity,
        container: Any,
        *,
        on_complete: Callable[[str], None],
    ) -> None:
        """Mount one activity into *container*, in place of any already shown.

        This is the step every layout repeats; the layout's own ``mount`` decides
        when to call it.

        Args:
            host: The layout's host, which builds the activity's own host.
            mounted: The activity to show.
            container: Element the activity renders into.
            on_complete: Called with the activity's id when it calls ``complete()``.
        """
        self.unmount_activity()
        activity_host = host.make_activity_host(
            mounted.config.id, container, on_complete=on_complete
        )
        self._mounted_activity = mounted.instance
        mounted.instance.mount(activity_host)

    def unmount_activity(self) -> None:
        """Unmount the activity being shown, if any.

        Call this before clearing the container the activity rendered into.
        """
        if self._mounted_activity is not None:
            self._mounted_activity.unmount()
            self._mounted_activity = None
