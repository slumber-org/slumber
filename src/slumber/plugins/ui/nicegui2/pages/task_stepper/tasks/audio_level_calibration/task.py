"""Volume task - simple slider for setting audio level."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from nicegui import ui

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui2.state import PageGraphState


@dataclass
class AudioLevelCalibrationConfig:
    """Configuration for the audio level calibration task."""

    title: str = "Set Audio Level"
    description: str = (
        "Adjust the slider to set your desired audio volume level during the night."
    )
    min_volume: int = 0
    max_volume: int = 100
    default_volume: int = 50
    save_button_text: str = "Save Level"


def render(
    state: PageGraphState,
    on_complete: callable,
    task_cfg: AudioLevelCalibrationConfig | None = None,
    task_index: int = 0,
) -> None:
    """Render the volume slider task.

    Args:
        state: App state
        on_complete: Callback to call when task is completed (on save)
        task_cfg: Task configuration
        task_index: Index of this task within the page's task list.
    """
    if task_cfg is None:
        task_cfg = AudioLevelCalibrationConfig()

    # Track saved state
    saved_level = [task_cfg.default_volume]
    has_saved = [False]

    # Title and description
    ui.label(task_cfg.title).classes("text-h5 font-bold mb-2 text-primary")
    ui.label(task_cfg.description).classes("text-body1 mb-6 text-primary")

    # Centered container for slider and below (slider is 1/2 of task width)
    with ui.column().classes("w-full items-center gap-2"):
        # Volume slider (half width of task container)
        def on_slider_change(value):
            current_level.set_text(f"Current Level: {int(value)}")

        slider = (
            ui.slider(
                min=task_cfg.min_volume,
                max=task_cfg.max_volume,
                value=task_cfg.default_volume,
            )
            .props("label-always label-color=secondary")
            .classes("w-1/2")
        )
        slider.on("change", lambda e: on_slider_change(e.args))

        # Current level display
        current_level = ui.label(
            f"Current Audio Level: {task_cfg.default_volume}"
        ).classes("text-body2 text-primary")

        # Saved level display
        saved_display = ui.label("Not saved yet").classes(
            "text-primary text-body2 mb-4"
        )

        # Save button
        def save_volume():
            level = int(slider.value)
            saved_level[0] = level
            has_saved[0] = True
            saved_display.set_text(f"Saved Level: {level}")
            saved_display.classes("text-primary text-body2 mb-4")
            ui.notify(f"Volume level {level} saved", type="positive")
            # Mark task as completed on first save
            on_complete()

        ui.button(
            task_cfg.save_button_text,
            icon="save",
            on_click=save_volume,
        ).props("size=lg rounded unelevated color=positive text-color=primary").classes(
            "w-full max-w-xs"
        )
