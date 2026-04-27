"""Settings for the Help menu."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HelpMenuItem(BaseModel):
    """A single help menu item."""

    label: str
    markdown_path: str


class HelpMenuSettings(BaseModel):
    """Settings for the Help menu."""

    label: str = "Help"
    items: list[HelpMenuItem] = Field(default_factory=list)
    settings: dict = Field(default_factory=dict)


__all__ = ["HelpMenuSettings", "HelpMenuItem"]
