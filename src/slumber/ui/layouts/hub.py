"""Hub layout: single activity full bleed in the AppFrame body."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger
from pydantic import BaseModel, ConfigDict

from slumber.ui.layouts.base import Layout, LayoutHost

if TYPE_CHECKING:
    from slumber.ui.backend import MountedActivity


class HubLayoutSettings(BaseModel):
    """Hub layout has no settings in 0.1."""

    model_config = ConfigDict(extra="forbid")


class HubLayout(Layout):
    """One activity, full bleed; does not emit ``phase_completed`` itself."""

    settings_model = HubLayoutSettings

    def __init__(self, settings: HubLayoutSettings | None = None) -> None:
        super().__init__(settings or HubLayoutSettings())
        self._mounted_instance: Any | None = None

    def mount(self, host: LayoutHost, activities: list[MountedActivity]) -> None:
        """Mount the first (only) activity into the body."""
        from nicegui import ui

        if not activities:
            logger.warning("HubLayout mounted with no activities.")
            return
        if len(activities) > 1:
            logger.warning(
                "HubLayout expected one activity; using the first of {}.",
                len(activities),
            )

        mounted = activities[0]
        with host.container:
            slot = ui.column().classes(
                "w-full h-full flex flex-col items-center justify-center p-6"
            )

        def on_complete(activity_id: str) -> None:
            del activity_id  # hub does not advance on complete

        activity_host = host.make_activity_host(
            mounted.config.id,
            slot,
            on_complete=on_complete,
        )
        self._mounted_instance = mounted.instance
        mounted.instance.mount(activity_host)

    def unmount(self) -> None:
        """Unmount the hub activity."""
        if self._mounted_instance is not None:
            self._mounted_instance.unmount()
            self._mounted_instance = None
