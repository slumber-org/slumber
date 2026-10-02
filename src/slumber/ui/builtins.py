"""Built-in UI backends and layouts (not entry points).

``resolve_plugin_spec`` consults these maps for ``ui`` and ``layouts`` groups.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from slumber.plugins.base import ConfiguredPlugin
from slumber.schemas.study import GuiSettings, StepperLayoutDefaults
from slumber.ui.backend import MountedActivity, UIBackend
from slumber.ui.headless import HeadlessBackend, HeadlessSettings

__all__ = [
    "BUILT_IN_LAYOUTS",
    "BUILT_IN_UI",
    "GuiBackend",
    "HeadlessBackend",
    "HeadlessSettings",
    "HubLayout",
    "HubLayoutSettings",
    "StepperLayout",
]


class HubLayoutSettings(BaseModel):
    """Hub layout has no settings in 0.1."""

    model_config = ConfigDict(extra="forbid")


class GuiBackend(UIBackend):
    """Participant GUI (NiceGUI). Full mount lives in the UI run stack."""

    settings_model = GuiSettings

    def start(self, engine: Any) -> None:
        """GUI event loop is not implemented in this package slice yet."""
        raise NotImplementedError(
            "ui.type 'gui' is not implemented yet; use headless or wait for the UI stack."
        )

    def apply_frame(self, frame: dict[str, Any]) -> None:
        """Apply AppFrame overrides (implemented with the GUI stack)."""
        raise NotImplementedError("gui apply_frame is not implemented yet.")

    def mount_phase(
        self,
        phase: Any,
        layout: ConfiguredPlugin,
        activities: list[MountedActivity],
    ) -> None:
        """Mount phase body (implemented with the GUI stack)."""
        raise NotImplementedError("gui mount_phase is not implemented yet.")

    def unmount_phase(self) -> None:
        """Unmount phase body (implemented with the GUI stack)."""
        raise NotImplementedError("gui unmount_phase is not implemented yet.")


class StepperLayout(ConfiguredPlugin):
    """Ordered activities with optional list and nav buttons."""

    settings_model = StepperLayoutDefaults


class HubLayout(ConfiguredPlugin):
    """Single activity, full bleed in the AppFrame body."""

    settings_model = HubLayoutSettings


BUILT_IN_UI: dict[str, type[ConfiguredPlugin]] = {
    "gui": GuiBackend,
    "headless": HeadlessBackend,
}

BUILT_IN_LAYOUTS: dict[str, type[ConfiguredPlugin]] = {
    "stepper": StepperLayout,
    "hub": HubLayout,
}
