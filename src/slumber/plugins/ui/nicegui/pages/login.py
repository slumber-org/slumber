"""Login page: email/password authentication via Supabase Auth."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from nicegui import ui

from slumber.plugins.ui.nicegui.layouts import centered_fullscreen_layout
from slumber.plugins.ui.nicegui.theme import (
    SURFACE_LIGHT,
    SURFACE_MID,
    TEXT_SECONDARY,
)
from slumber.supabase.utils import SUPABASE_INSTALL_HINT, is_supabase_extra_installed

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui.state import AppState


def render(state: AppState, refresh: object) -> None:
    """Render the login page.

    Args:
        state: App state.
        refresh: Callable to refresh the UI after state changes.
    """
    supabase_available = is_supabase_extra_installed()
    cfg = state.ui_config.login

    with centered_fullscreen_layout(content_gap=None):
        if state.logo_url:
            ui.image(state.logo_url).classes("w-24 h-24 rounded-xl")
        else:
            ui.icon(cfg.icon, size="64px").classes(f"text-[{TEXT_SECONDARY}]")
        ui.label(cfg.title).classes("text-h3 font-bold mt-2")
        ui.label(cfg.subtitle).classes(f"text-subtitle1 text-[{TEXT_SECONDARY}]")

        with (
            ui.card()
            .classes(
                f"w-96 mt-6 px-6 py-5 bg-[{SURFACE_MID}] border border-[{SURFACE_LIGHT}]"
            )
            .props("flat bordered")
        ):
            email = ui.input("Email").classes("w-full")
            password = ui.input(
                "Password", password=True, password_toggle_button=True
            ).classes("w-full")
            error_label = ui.label("").classes("text-negative")
            error_label.set_visibility(False)

            if not supabase_available:
                ui.label("Supabase dependency missing.").classes(
                    f"text-subtitle2 text-[{TEXT_SECONDARY}]"
                )
                ui.label(SUPABASE_INSTALL_HINT).classes(
                    f"text-caption text-[{TEXT_SECONDARY}]"
                )
                return

            ui.button(
                cfg.submit_button,
                icon=cfg.submit_icon,
                on_click=lambda: _handle_login(
                    email.value, password.value, error_label, state, refresh
                ),
            ).classes("w-full mt-2").props("rounded unelevated color=primary").style(
                "letter-spacing: 1px"
            )


def _handle_login(
    email: str, password: str, error_label: ui.label, state: AppState, refresh: object
) -> None:
    try:
        from slumber.supabase.auth.operations import sign_in
    except ModuleNotFoundError:
        error_label.text = SUPABASE_INSTALL_HINT
        error_label.set_visibility(True)
        return

    try:
        sign_in(email, password)
        logger.info("Login successful for {}", email)
        state.authenticated = True
        state.current_page = "welcome"
        refresh()  # type: ignore[operator]
    except Exception as exc:
        logger.warning("Login failed for {}: {}", email, exc)
        error_label.text = str(exc)
        error_label.set_visibility(True)
