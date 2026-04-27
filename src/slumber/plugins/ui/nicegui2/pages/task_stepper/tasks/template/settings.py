"""Settings for the template task."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TemplateSettings(BaseModel):
    """Settings for the template task."""

    title: str = "Template Task"
    description: str = "This is a template task example"
    show_button: bool = True
    button_text: str = "Complete"


__all__ = ["TemplateSettings"]
