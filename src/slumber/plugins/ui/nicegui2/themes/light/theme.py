from __future__ import annotations

from pathlib import Path

from slumber.plugins.ui.nicegui2.themes.schemas import Theme

# Base palette
INK_BLACK = "#020617"
DEEP_SPACE_BLUE = "#1E293B"
ROYAL_AZURE = "#1D4ED8"
FRESH_SKY = "#00B3FF"
FROSTED_BLUE = "#94E2FF"
GOLD = "#FFD60A"
BRIGHT_SNOW = "#F8FAFC"

_theme_dir = Path(__file__).parent

# Font file paths
FONT_PATH = _theme_dir / "Mulish-VariableFont_wght.ttf"
FONT_ITALIC_PATH = _theme_dir / "Mulish-Italic-VariableFont_wght.ttf"
COLORS = {
    "primary": INK_BLACK,
    "secondary": ROYAL_AZURE,
    "accent": DEEP_SPACE_BLUE,
    "positive": FRESH_SKY,
    "negative": FRESH_SKY,
    "warning": GOLD,
    "info": FROSTED_BLUE,
    "background": BRIGHT_SNOW,
    "surface": FROSTED_BLUE,
}

# New schema-based theme instance
theme = Theme(
    name="light",
    theme_dir=_theme_dir,
    font_path=FONT_PATH,
    font_italic_path=FONT_ITALIC_PATH,
    colors=COLORS,
)