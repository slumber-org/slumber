"""Theme schema definition for nicegui2 UI.

Defines the structure and validation for UI themes using Pydantic.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Theme(BaseModel):
    """UI theme definition with colors and fonts.

    Themes define the visual appearance of the nicegui2 UI, including
    color palette and font files. Logo assets are shell-static and not
    theme-dependent.
    """
    
    model_config = {"frozen": True}
    
    # Identity
    name: str = Field(
        ...,
        min_length=1,
        description="Theme name identifier (e.g., 'dark', 'light').",
    )
    
    # Directory structure
    theme_dir: Path = Field(
        ...,
        description="Root directory for this theme's files.",
    )

    # Fonts
    font_path: Path | None = Field(
        default=None,
        description="Path to primary variable font file.",
    )
    font_italic_path: Path | None = Field(
        default=None,
        description="Path to italic variable font file.",
    )
    
    # Color palette - Quasar color mappings
    colors: dict[Literal[
        "primary", "secondary", "accent",
        "positive", "negative", "warning", "info",
        "dark", "light", "background", "surface"
    ], str] = Field(
        ...,
        min_length=1,
        description="Quasar color mappings for ui.colors(). Keys are Quasar color names, values are hex colors.",
    )
    
    @field_validator("colors")
    @classmethod
    def validate_hex_colors(cls, v: dict[str, str]) -> dict[str, str]:
        """Validate all colors are valid hex format."""
        for key, color in v.items():
            if not color.startswith("#"):
                raise ValueError(f"Color '{key}' must start with '#': {color!r}")
            hex_part = color[1:]
            if len(hex_part) not in (3, 6, 8):
                raise ValueError(
                    f"Color '{key}' has invalid length: {color!r}. "
                    "Expected #RGB, #RRGGBB, or #RRGGBBAA."
                )
            try:
                int(hex_part, 16)
            except ValueError:
                raise ValueError(f"Color '{key}' has invalid hex: {color!r}")
        return v
