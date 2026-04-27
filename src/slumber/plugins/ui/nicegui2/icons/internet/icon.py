"""Internet status indicator icon."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nicegui import ui

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui2.state import PageGraphState


def render(state: PageGraphState) -> None:
    """Render the internet status indicator.

    Args:
        state: App state containing internet_connected attribute
    """
    connected = getattr(state, "internet_connected", True)
    icon = "wifi" if connected else "wifi_off"
    color = "secondary" if connected else "warning"
    tooltip = "Connected" if connected else "No internet"
    with ui.element("div").tooltip(tooltip):
        ui.icon(icon, size="xs").classes(f"text-{color}")
