"""Recording status indicator icon."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nicegui import ui

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui2.state import PageGraphState


def render(state: PageGraphState) -> None:
    """Render the recording status indicator.

    Args:
        state: App state containing recording_active attribute
    """
    recording = getattr(state, "recording_active", False)
    icon = "fiber_manual_record" if recording else "fiber_manual_record"
    color = "negative" if recording else "grey"
    tooltip = "Recording now" if recording else "Not recording now"
    with ui.element("div").tooltip(tooltip):
        ui.icon(icon, size="xs").classes(f"text-{color}")
