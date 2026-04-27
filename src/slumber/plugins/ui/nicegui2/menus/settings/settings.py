"""Settings for the Settings menu."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SettingsMenuItem(BaseModel):
    """A single settings menu item."""

    label: str
    type: str
    options: list[str] = Field(default_factory=list)


class SettingsMenuSettings(BaseModel):
    """Settings for the Settings menu."""

    label: str = "Settings"
    items: list[SettingsMenuItem] = Field(default_factory=list)
    settings: dict = Field(default_factory=dict)


__all__ = ["SettingsMenuSettings", "SettingsMenuItem"]
