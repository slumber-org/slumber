"""Settings dropdown menu."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from nicegui import ui

from slumber.plugins.ui.nicegui2.menus.settings.settings import (
    SettingsMenuSettings,
    SettingsMenuItem,
)

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui2.state import PageGraphState


def render(
    state: PageGraphState,
    refresh: Callable[[], None],
    cfg: SettingsMenuSettings,
) -> None:
    """Render the Settings dropdown menu.

    Args:
        state: App state
        refresh: Function to refresh UI
        cfg: Settings menu configuration
    """
    with ui.button(cfg.label, icon="settings").props("flat dense text-color=primary"):
        with ui.menu().classes("bg-surface border-secondary"):
            for item in cfg.items:
                if item.type == "theme":
                    _render_theme_item(state, refresh, item)


def _render_theme_item(
    state: PageGraphState, refresh: Callable[[], None], item: SettingsMenuItem
) -> None:
    """Render a theme selection item."""
    with ui.menu_item(item.label, auto_close=False).classes("text-primary"):
        with ui.menu().classes("bg-surface border-secondary"):
            for theme in item.options:
                ui.menu_item(
                    theme, lambda t=theme: _set_theme(state, t, refresh)
                ).classes("text-primary")


def _set_theme(state: PageGraphState, theme: str, refresh: Callable[[], None]) -> None:
    """Apply theme selection."""
    from slumber.plugins.ui.nicegui2.themes.theming import set_theme, apply

    setattr(state, "theme", theme)
    set_theme(theme)
    apply()
    ui.notify(f"Theme changed to {theme}")
    refresh()
