"""Settings for the template page."""

from __future__ import annotations

from pydantic import BaseModel


class TemplateSettings(BaseModel):
    """Settings for the template page."""

    title: str = "Template Page"
    description: str = "This is a template page example"


__all__ = ["TemplateSettings"]
