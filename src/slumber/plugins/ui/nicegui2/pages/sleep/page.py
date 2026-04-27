"""Sleep page - active sleep session with music status display."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from nicegui import ui

from slumber.plugins.ui.nicegui2.shell.shell import render_shell
from slumber.plugins.ui.nicegui2.shell.settings import ShellSettings
from slumber.plugins.ui.nicegui2.pages.sleep.settings import SleepSettings

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui2.state import PageGraphState


def render(
    state: PageGraphState,
    refresh: Callable[[], None],
    shell_cfg: ShellSettings | None = None,
    page_cfg: SleepSettings | None = None,
) -> None:
    """Render sleep page with wake/sleep controls."""
    if shell_cfg is None:
        shell_cfg = ShellSettings()
    if page_cfg is None:
        page_cfg = SleepSettings()

    # Track sleep state (music is tied to sleep state)
    is_sleeping = [False]

    # Check if recording is already active from backend
    is_recording = [getattr(state, "recording_active", False)]

    def start_recording() -> None:
        is_recording[0] = True
        setattr(state, "recording_active", True)
        ui.notify("Recording started.")
        # Refresh shell indicators to update recording icon
        if hasattr(state, "refresh_indicators"):
            state.refresh_indicators()
        content.refresh()

    def stop_recording() -> None:
        is_recording[0] = False
        setattr(state, "recording_active", False)
        ui.notify("Recording stopped.")
        # Refresh shell indicators to update recording icon
        if hasattr(state, "refresh_indicators"):
            state.refresh_indicators()
        content.refresh()

    def toggle_sleep() -> None:
        is_sleeping[0] = not is_sleeping[0]
        if is_sleeping[0]:
            ui.notify("TODO - Go to sleep (log event, start music)")
        else:
            ui.notify("TODO - Wake up (log event, stop music)")
            state.fire_routing_event("wakeup")

        content.refresh()

    def end_session() -> None:
        with ui.dialog() as dialog, ui.card().classes("bg-surface p-6 w-80"):
            with ui.column().classes("w-full items-center gap-4"):
                ui.label("End Session?").classes(
                    "text-h5 font-bold text-primary text-center"
                )
                ui.label("Are you sure you want to end the session?").classes(
                    "text-body1 text-secondary text-center"
                )
                with ui.row().classes("w-full justify-center gap-3 mt-2"):
                    ui.button("Cancel", on_click=dialog.close).props(
                        "unelevated color=negative text-color=primary"
                    )
                    ui.button(
                        "End Session",
                        on_click=lambda: [
                            stop_recording(),
                            dialog.close(),
                            state.fire_routing_event("finish"),
                        ],
                    ).props("unelevated color=warning text-color=primary")
        dialog.open()

    @ui.refreshable
    def content() -> None:
        with ui.column().classes("w-full h-full items-center justify-center p-8 gap-6"):
            # Title
            ui.label("Sleep Page").classes("text-h3 font-bold text-center text-primary")

            # Status card showing sleep and music state
            with ui.card().classes("w-full max-w-md bg-surface p-6 mb-4"):
                with ui.column().classes("w-full items-center gap-4"):
                    # Sleep status
                    sleep_status = "Sleeping" if is_sleeping[0] else "Awake"
                    sleep_icon = "bedtime" if is_sleeping[0] else "alarm"
                    with ui.row().classes("items-center gap-3"):
                        ui.icon(sleep_icon, size="32px").classes("text-primary")
                        ui.label(f"Status: {sleep_status}").classes(
                            "text-h6 font-bold text-primary"
                        )

                    ui.separator().classes("bg-secondary")

                    # Music status (tied to sleep state)
                    music_status = "Playing" if is_sleeping[0] else "Stopped"
                    music_icon = "music_note" if is_sleeping[0] else "music_off"
                    with ui.row().classes("items-center gap-3"):
                        ui.icon(music_icon, size="28px").classes("text-primary")
                        ui.label(f"Music: {music_status}").classes(
                            "text-h6 font-bold text-primary"
                        )

            # Main action buttons
            with ui.column().classes("w-full max-w-md gap-4 mt-6"):
                if not is_recording[0]:
                    # Start recording button (large)
                    ui.button(
                        "Start Recording",
                        icon="fiber_manual_record",
                        on_click=start_recording,
                    ).props(
                        "size=xl rounded unelevated color=positive text-color=primary"
                    ).classes("w-full py-4")
                else:
                    # Sleep/Wake toggle button (large)
                    sleep_icon = (
                        page_cfg.wake_button_icon
                        if is_sleeping[0]
                        else page_cfg.sleep_button_icon
                    )
                    sleep_text = (
                        page_cfg.wake_button_text
                        if is_sleeping[0]
                        else page_cfg.sleep_button_text
                    )
                    ui.button(
                        sleep_text,
                        icon=sleep_icon,
                        on_click=toggle_sleep,
                    ).props(
                        "size=xl rounded unelevated color=positive text-color=primary"
                    ).classes("w-full py-4")

            # End session button (at bottom, smaller)
            with ui.column().classes("w-full max-w-md gap-3 mt-8"):
                ui.separator().classes("bg-secondary mb-2")
                ui.button(
                    page_cfg.end_session_text,
                    icon=page_cfg.end_session_icon,
                    on_click=end_session,
                ).props(
                    "size=md rounded outline color=secondary text-color=primary"
                ).classes("w-full")

    render_shell(state, refresh, shell_cfg, content)  # type: ignore[arg-type]
