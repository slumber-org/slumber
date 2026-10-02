"""Built-in UI backends and layouts (not entry points).

``resolve_plugin_spec`` consults these maps for ``ui`` and ``layouts`` groups.
"""

from __future__ import annotations

from slumber.ui.gui import GuiBackend
from slumber.ui.headless import HeadlessBackend, HeadlessSettings
from slumber.ui.layouts import HubLayout, HubLayoutSettings, StepperLayout

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

BUILT_IN_UI: dict[str, type] = {
    "gui": GuiBackend,
    "headless": HeadlessBackend,
}

BUILT_IN_LAYOUTS: dict[str, type] = {
    "stepper": StepperLayout,
    "hub": HubLayout,
}
