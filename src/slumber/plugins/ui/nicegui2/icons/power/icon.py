"""Power status indicator icon."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nicegui import ui

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui2.state import PageGraphState


def render(state: PageGraphState) -> None:
    """Render the power status indicator.

    Args:
        state: App state containing power_connected attribute
    """
    plugged = getattr(state, "power_connected", True)
    icon = "power" if plugged else "battery_full"
    color = "secondary" if plugged else "warning"
    tooltip = "Plugged in" if plugged else "Battery"
    with ui.element("div").tooltip(tooltip):
        ui.icon(icon, size="xs").classes(f"text-{color}")
