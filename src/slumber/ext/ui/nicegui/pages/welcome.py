"""Welcome page: study info and session start."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nicegui import ui

from slumber.ext.ui.nicegui.layouts import centered_fullscreen_layout
from slumber.ext.ui.nicegui.theme import TEXT_SECONDARY

if TYPE_CHECKING:
    from slumber.ext.ui.nicegui.state import AppState


def render_welcome_page(state: AppState, refresh: object) -> None:
    """Render the welcome page.

    Args:
        state: App state.
        refresh: Callable to refresh the UI after state changes.
    """
    cfg = state.ui_config.welcome

    with centered_fullscreen_layout():
        if state.logo_url:
            ui.image(state.logo_url).classes("w-28 h-28 rounded-xl")
        else:
            ui.icon(cfg.icon, size="80px").classes(f"text-[{TEXT_SECONDARY}]")
        ui.label(state.study.name).classes("text-h3 font-bold mt-4")
        ui.label(cfg.subtitle).classes(f"text-subtitle1 text-[{TEXT_SECONDARY}]")

        def start_session() -> None:
            state.fire_event("session_start")
            refresh()  # type: ignore[operator]

        ui.button(
            cfg.start_button, icon=cfg.start_icon, on_click=start_session
        ).classes("mt-6").props("size=lg rounded color=primary unelevated").style(
            "min-width: 220px; letter-spacing: 1px"
        )
