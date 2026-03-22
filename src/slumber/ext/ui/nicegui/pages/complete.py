"""Completion page: session finished, app shutdown."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nicegui import app, ui

from slumber.ext.ui.nicegui.theme import POSITIVE, TEXT_SECONDARY

if TYPE_CHECKING:
    from slumber.ext.ui.nicegui.state import AppState


def render_complete_page(state: AppState, refresh: object) -> None:
    """Render the completion page.

    Args:
        state: App state.
        refresh: Callable to refresh the UI after state changes.
    """
    cfg = state.ui_config.complete

    with ui.column().classes("items-center justify-center w-full h-screen gap-2"):
        ui.icon(cfg.icon, size="80px").classes(f"text-[{POSITIVE}]")
        ui.label(cfg.title).classes(f"text-h3 font-bold text-[{POSITIVE}] mt-2")
        ui.label(cfg.subtitle).classes(f"text-body1 text-[{TEXT_SECONDARY}]")

        ui.button(
            cfg.close_button,
            icon=cfg.close_icon,
            on_click=lambda: app.shutdown(),
        ).classes("mt-8").props("size=lg rounded outline").style(
            "min-width: 220px; letter-spacing: 1px"
        )
