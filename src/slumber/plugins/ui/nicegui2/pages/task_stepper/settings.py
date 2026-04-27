"""Settings for the Task Stepper page."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TaskStepperSettings(BaseModel):
    """Settings for the Task Stepper page."""

    # List of task module names to display in order
    tasks: list[str] = Field(
        default_factory=lambda: ["instructions", "survey", "audio_level_calibration"]
    )

    # Task settings dict keyed by task name (from YAML)
    task_settings: dict[str, dict] = Field(default_factory=dict)

    # Navigation button labels
    next_button_text: str = "Next"
    prev_button_text: str = "Previous"
    finish_button_text: str = "Finish"

    # Colors
    completed_color: str = "positive"
    current_color: str = "primary"
    pending_color: str = "grey"


__all__ = ["TaskStepperSettings"]
