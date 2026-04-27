"""Settings for the Welcome page."""

from __future__ import annotations

from pydantic import BaseModel, Field


class WelcomeSettings(BaseModel):
    """Settings for the Welcome page."""

    # Content source
    markdown_path: str = "welcome.md"

    # Primary action button
    button_text: str = "Start Session"
    button_icon: str = "play_arrow"
    # Default condition to start when button is clicked (from study.ui.settings.welcome.default_condition)
    default_condition: str | None = None


__all__ = ["WelcomeSettings"]
