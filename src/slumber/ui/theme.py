"""Fixed dark brand tokens and Quasar colour map for the GUI.

Hex values match ``docs/stylesheets/extra.css`` (indigo moon + amber EEG).
Call sites should import role tokens and helpers, not raw Quasar names.
"""

from __future__ import annotations

from pathlib import Path

# Role tokens (design 0.1)
PAGE_BG = "#151833"  # page background
SURFACE = "#1A1F3C"  # cards / panels
BRAND = "#3D4A8A"  # logo / nav
CTA = "#E8A45A"  # primary buttons / active
SECONDARY = "#94A1B2"  # secondary text / hover
ATTENTION = "#E8A45A"  # alerts / high-contrast highlight
TEXT = "#FFFFFE"  # body text on dark

# Supporting palette (chrome accents, status)
BRAND_LIGHT = "#7B7FC4"
BRAND_DARK = "#2A2F52"
PAGE_BG_DEEP = "#121528"
SURFACE_BORDER = "#2A2F52"
POSITIVE = "#34D399"
NEGATIVE = "#F87171"

# Quasar ``ui.colors`` — CTA is Quasar primary; brand is used explicitly in chrome.
COLORS = {
    "primary": CTA,
    "secondary": SURFACE,
    "accent": ATTENTION,
    "dark": PAGE_BG_DEEP,
    "dark-page": PAGE_BG,
    "positive": POSITIVE,
    "negative": NEGATIVE,
    "info": BRAND_LIGHT,
    "warning": ATTENTION,
}

LOGO_SIZE = {
    "hero": "7rem",
    "header": "2rem",
    "hub": "5rem",
}

TYPE_SCALE = {
    "display": "text-h3",
    "title": "text-h5",
    "body": "text-body1",
    "caption": "text-caption",
}

FONT_FAMILY = "Figtree"
FONT_URL = (
    "https://fonts.googleapis.com/css2?family=Figtree:wght@400;600;700&display=swap"
)

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
DEFAULT_LOGO_PATH = ASSETS_DIR / "logo.png"
DEFAULT_FAVICON_PATH = ASSETS_DIR / "favicon.png"

POWERED_BY = "Powered by SLUMBER"

_THEME_CSS = f"""
:root {{
  --slumber-page-bg: {PAGE_BG};
  --slumber-surface: {SURFACE};
  --slumber-brand: {BRAND};
  --slumber-cta: {CTA};
  --slumber-secondary: {SECONDARY};
  --slumber-attention: {ATTENTION};
  --slumber-text: {TEXT};
  --slumber-border: {SURFACE_BORDER};
  --slumber-font: '{FONT_FAMILY}', system-ui, sans-serif;
}}
body, .q-page, .nicegui-content {{
  font-family: var(--slumber-font) !important;
  background-color: var(--slumber-page-bg) !important;
  color: var(--slumber-text);
}}
"""


def apply_theme() -> None:
    """Load typeface, CSS variables, and Quasar colours (call once at GUI start)."""
    from nicegui import ui

    ui.add_head_html(f'<link rel="stylesheet" href="{FONT_URL}">')
    ui.add_css(_THEME_CSS)
    ui.colors(**COLORS)


def default_logo_path() -> Path | None:
    """Return the packaged logo path when the file exists."""
    return DEFAULT_LOGO_PATH if DEFAULT_LOGO_PATH.is_file() else None


def default_favicon_path() -> Path | None:
    """Return the packaged favicon path when the file exists."""
    return DEFAULT_FAVICON_PATH if DEFAULT_FAVICON_PATH.is_file() else None
