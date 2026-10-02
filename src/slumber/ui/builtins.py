"""Built-in UI backends and layouts (not entry points).

``resolve_plugin_spec`` consults these maps for ``ui`` and ``layouts`` groups.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from slumber.plugins.base import ConfiguredPlugin
from slumber.schemas.study import GuiSettings, StepperLayoutDefaults


class HeadlessSettings(BaseModel):
    """Headless UI accepts no settings (empty model, extra forbidden)."""

    model_config = ConfigDict(extra="forbid")


class HubLayoutSettings(BaseModel):
    """Hub layout has no settings in 0.1."""

    model_config = ConfigDict(extra="forbid")


class GuiBackend(ConfiguredPlugin):
    """Participant GUI (NiceGUI). Full mount lives in the UI run stack."""

    settings_model = GuiSettings


class HeadlessBackend(ConfiguredPlugin):
    """No window; activities that finish on mount auto-complete."""

    settings_model = HeadlessSettings


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
