"""Settings for the Farewell page."""

from __future__ import annotations

from pydantic import BaseModel


class FarewellSettings(BaseModel):
    """Settings for the Farewell page."""

    # Content source
    markdown_path: str = "farewell.md"

    # Visual elements
    icon: str = "check_circle"
    icon_size: str = "100px"

    # Primary action button
    button_text: str = "Close Software"
    button_icon: str = "close"


__all__ = ["FarewellSettings"]
