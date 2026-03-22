"""NiceGUI page modules."""

from __future__ import annotations

from nicegui import ui

from slumber.ext.ui.nicegui.theme import TEXT_SECONDARY

POWERED_BY = "Powered by SLUMBER"


def render_powered_by() -> None:
    """Render the 'Powered by SLUMBER' footer line."""
    ui.label(POWERED_BY).classes(f"text-caption text-[{TEXT_SECONDARY}] opacity-60")
