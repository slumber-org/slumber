"""Hub layout: a single activity filling the AppFrame body."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger
from pydantic import BaseModel, ConfigDict

from slumber.ui.layouts.base import Layout, LayoutHost

if TYPE_CHECKING:
    from slumber.ui.backend import MountedActivity


HUB_CSS = """
.slumber-hub {
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--slumber-pad);
  scrollbar-width: thin;
  scrollbar-color: var(--slumber-secondary) transparent;
}
"""


class HubLayoutSettings(BaseModel):
    """Hub layout has no settings in 0.1."""

    model_config = ConfigDict(extra="forbid")


class HubLayout(Layout):
    """One activity filling the body; does not emit ``phase_completed`` itself."""

    settings_model = HubLayoutSettings
    css = HUB_CSS

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
            slot = ui.element("div").classes("slumber-hub")

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
