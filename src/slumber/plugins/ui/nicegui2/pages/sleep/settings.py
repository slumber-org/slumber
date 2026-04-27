"""Settings for the Sleep page."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SleepSettings(BaseModel):
    """Settings for the Sleep page."""

    # Sleep button (asleep state)
    sleep_button_text: str = "Go to Sleep"
    sleep_button_icon: str = "bedtime"

    # Wake button (awake state)
    wake_button_text: str = "Wake Up"
    wake_button_icon: str = "alarm"

    # End session button
    end_session_text: str = "End Session"
    end_session_icon: str = "logout"


__all__ = ["SleepSettings"]
