"""Login page: email/password authentication via Supabase Auth."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from nicegui import ui

from slumber.ext.ui.nicegui.theme import (
    ACCENT_LAVENDER,
    SURFACE,
    SURFACE_LIGHT,
    TEXT_SECONDARY,
)

if TYPE_CHECKING:
    from slumber.ext.ui.nicegui.state import AppState


def render_login_page(state: AppState, refresh: object) -> None:
    """Render the login page.

    Args:
        state: App state.
        refresh: Callable to refresh the UI after state changes.
    """
    cfg = state.ui_config.login

    with ui.column().classes("items-center justify-center w-full h-screen"):
        ui.icon(cfg.icon, size="64px").classes(f"text-[{ACCENT_LAVENDER}]")
        ui.label(cfg.title).classes("text-h3 font-bold mt-2")
        ui.label(cfg.subtitle).classes(f"text-subtitle1 text-[{TEXT_SECONDARY}]")

        with (
            ui.card()
            .classes(
                f"w-96 mt-6 px-6 py-5 bg-[{SURFACE}] border border-[{SURFACE_LIGHT}]"
            )
            .props("flat bordered")
        ):
            email = ui.input("Email").classes("w-full")
            password = ui.input(
                "Password", password=True, password_toggle_button=True
            ).classes("w-full")
            error_label = ui.label("").classes("text-negative")
            error_label.set_visibility(False)

            async def handle_login() -> None:
                try:
                    from slumber.auth.operations import sign_in

                    sign_in(email.value, password.value)
                    state.authenticated = True
                    state.current_page = "welcome"
                    logger.info("Login successful for {}", email.value)
                    refresh()  # type: ignore[operator]
                except Exception as exc:
                    error_label.text = str(exc)
                    error_label.set_visibility(True)
                    logger.warning("Login failed for {}: {}", email.value, exc)

            ui.button(
                cfg.submit_button, icon=cfg.submit_icon, on_click=handle_login
            ).classes("w-full mt-2").props("rounded unelevated color=primary").style(
                "letter-spacing: 1px"
            )
