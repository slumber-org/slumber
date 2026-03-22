"""Sleep page: idle hub between procedures, emits session events."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from nicegui import ui

from slumber.ext.ui.nicegui.layouts import centered_fullscreen_layout
from slumber.ext.ui.nicegui.theme import (
    AWAKE_AMBER,
    NEGATIVE,
    SLEEP_INDIGO,
    SURFACE_LIGHT,
    SURFACE_MID,
    TEXT_SECONDARY,
)

if TYPE_CHECKING:
    from slumber.ext.ui.nicegui.state import AppState


def render_sleep_page(state: AppState, refresh: object) -> None:
    """Render the sleep page.

    Args:
        state: App state.
        refresh: Callable to refresh the UI after state changes.
    """
    cfg = state.ui_config.sleep
    is_asleep = state.is_asleep
    accent = SLEEP_INDIGO if is_asleep else AWAKE_AMBER

    with centered_fullscreen_layout(content_gap=None):
        with ui.column().classes(
            "flex-1 flex flex-col justify-center items-center min-h-0"
        ):
            if state.logo_url:
                ui.image(state.logo_url).classes("w-20 h-20 rounded-xl")
            else:
                ui.icon(
                    cfg.asleep_icon if is_asleep else cfg.awake_icon,
                    size="96px",
                ).classes(f"text-[{accent}]")

            ui.label(cfg.asleep_label if is_asleep else cfg.awake_label).classes(
                f"text-h3 font-bold text-[{accent}]"
            )
            ui.label(cfg.asleep_subtitle if is_asleep else cfg.awake_subtitle).classes(
                f"text-body1 text-[{TEXT_SECONDARY}]"
            )

            with ui.column().classes("items-center gap-3 mt-10"):
                if not is_asleep:

                    async def going_to_sleep() -> None:
                        confirmed = await _confirm(
                            cfg.sleep_confirm_title,
                            cfg.sleep_confirm_message,
                        )
                        if confirmed:
                            logger.info("Participant going to sleep")
                            state.is_asleep = True
                            state.fire_event("sleep_start")
                            refresh()  # type: ignore[operator]

                    ui.button(
                        cfg.sleep_button,
                        icon=cfg.sleep_button_icon,
                        on_click=going_to_sleep,
                    ).props("size=lg rounded unelevated").style(
                        f"min-width: 220px; background-color: {SLEEP_INDIGO} !important; "
                        "color: white; letter-spacing: 1px"
                    )
                else:

                    async def im_awake() -> None:
                        confirmed = await _confirm(
                            cfg.wake_confirm_title,
                            cfg.wake_confirm_message,
                        )
                        if confirmed:
                            logger.info("Participant woke up")
                            state.is_asleep = False
                            state.fire_event("wake_up")
                            refresh()  # type: ignore[operator]

                    ui.button(
                        cfg.wake_button,
                        icon=cfg.wake_button_icon,
                        on_click=im_awake,
                    ).props("size=lg rounded unelevated").style(
                        f"min-width: 220px; background-color: {AWAKE_AMBER} !important; "
                        "color: #1a1a2e; letter-spacing: 1px"
                    )

        async def end_session() -> None:
            confirmed = await _confirm(
                cfg.end_confirm_title,
                cfg.end_confirm_message,
            )
            if confirmed:
                logger.info("Participant ending session")
                state.fire_event("session_end")
                refresh()  # type: ignore[operator]

        with ui.row().classes("w-full justify-center shrink-0"):
            ui.button(
                cfg.end_button,
                icon=cfg.end_button_icon,
                on_click=end_session,
            ).props("size=md rounded outline").style(
                "min-width: 220px; letter-spacing: 1px"
            ).classes(f"text-[{NEGATIVE}]").set_enabled(not is_asleep)


async def _confirm(title: str, message: str) -> bool:
    """Show a styled confirmation dialog."""
    with (
        ui.dialog() as dialog,
        ui.card()
        .classes(f"px-6 py-5 bg-[{SURFACE_MID}] border border-[{SURFACE_LIGHT}]")
        .props("flat bordered"),
    ):
        ui.label(title).classes("text-h6 font-bold")
        ui.label(message).classes(f"text-body1 text-[{TEXT_SECONDARY}] mt-1")
        with ui.row().classes("justify-end w-full mt-4 gap-2"):
            ui.button("Cancel", on_click=lambda: dialog.submit(False)).props(
                "flat rounded"
            )
            ui.button("Confirm", on_click=lambda: dialog.submit(True)).props(
                "rounded unelevated color=primary"
            )
    return await dialog  # type: ignore[return-value]
