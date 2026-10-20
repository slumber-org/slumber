"""Fixed dark brand tokens and Quasar colour map for the GUI.

Hex values match ``docs/stylesheets/extra.css``.
Call sites should import role tokens and helpers, not raw Quasar names.
Mulish is packaged under ``assets/fonts/`` (SIL OFL) for offline use.
"""

from __future__ import annotations

import weakref
from pathlib import Path
from typing import Any

# Palette, by role
PAGE_BG = "#020617"  # Ink Black: page background, current-step row, upcoming progress segments
SURFACE = "#1E293B"  # Deep Space Blue: header, cards, sidebar, nav bar, dialogs
SURFACE_ALT = "#1E3672"  # callouts and inline code inside cards
BRAND = "#1D4ED8"  # Royal Azure: logo and primary buttons (Next, Complete, Confirm)
ACCENT = "#00B3FF"  # Fresh Sky: done and skipped steps (list and progress bar), Previous outline
SECONDARY = "#94E2FF"  # Frosted Blue: current step, secondary text
ATTENTION = "#FFD60A"  # Gold: attention actions such as End Session
POSITIVE = "#34D399"  # successful actions only
NEGATIVE = "#F87171"  # errors only
TEXT = "#F8FAFC"  # Bright Snow: body text and button labels

# The design uses no borders. Kept only until the frame, stepper, card and dialog
# drop their border classes; remove it together with ``--slumber-border`` then.
SURFACE_BORDER = "#334155"

# Dialog backdrop: PAGE_BG at 72% (never pure black).
SCRIM = "rgba(2, 6, 23, 0.72)"

# Quasar ``ui.colors``: BRAND is Quasar primary (primary buttons). ACCENT, SECONDARY and
# TEXT are applied explicitly through the CSS variables below.
COLORS = {
    "primary": BRAND,
    "secondary": SURFACE,
    "accent": ACCENT,
    "dark": PAGE_BG,
    "dark-page": PAGE_BG,
    "positive": POSITIVE,
    "negative": NEGATIVE,
    "info": SECONDARY,
    "warning": ATTENTION,
}

# Logo heights; the width follows the image's own proportions.
LOGO_SIZE = {
    "hero": "7rem",
    "header": "calc(var(--slumber-header-h) * 0.56)",
    "hub": "clamp(3.5rem, 11vh, 6rem)",
}

# Classes defined in ``_THEME_CSS``; sizes step down on smaller windows.
TYPE_SCALE = {
    "display": "slumber-display",
    "title": "slumber-title",
    "body": "slumber-body",
    "caption": "slumber-caption",
}

FONT_FAMILY = "Mulish"
FONTS_URL_PREFIX = "/slumber-fonts"
FONT_FILES = {
    400: "mulish-latin-400-normal.woff2",
    600: "mulish-latin-600-normal.woff2",
    700: "mulish-latin-700-normal.woff2",
}

# Component stylesheets already added, per page (see ``add_component_css``).
_LOADED_COMPONENT_CSS: weakref.WeakKeyDictionary[Any, set[str]] = (
    weakref.WeakKeyDictionary()
)

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
DEFAULT_LOGO_PATH = ASSETS_DIR / "logo.png"
DEFAULT_FAVICON_PATH = ASSETS_DIR / "favicon.png"

POWERED_BY = "Powered by SLUMBER"

_FONT_FACE_CSS = "\n".join(
    f"""
@font-face {{
  font-family: '{FONT_FAMILY}';
  font-style: normal;
  font-weight: {weight};
  font-display: swap;
  src: url('{FONTS_URL_PREFIX}/{filename}') format('woff2');
}}""".strip()
    for weight, filename in FONT_FILES.items()
)

_THEME_CSS = f"""
{_FONT_FACE_CSS}
:root {{
  --slumber-page-bg: {PAGE_BG};
  --slumber-surface: {SURFACE};
  --slumber-surface-alt: {SURFACE_ALT};
  --slumber-brand: {BRAND};
  --slumber-accent: {ACCENT};
  --slumber-secondary: {SECONDARY};
  --slumber-attention: {ATTENTION};
  --slumber-text: {TEXT};
  --slumber-border: {SURFACE_BORDER};
  --slumber-font: '{FONT_FAMILY}', system-ui, sans-serif;
  --slumber-fs: 17px;
  --slumber-h1: 30px;
  --slumber-h2: 22px;
  --slumber-pad: 32px;
  --slumber-header-h: 64px;
}}
@media (max-width: 1199px) {{
  :root {{ --slumber-fs: 16px; --slumber-h1: 28px; --slumber-h2: 20px; --slumber-pad: 24px; }}
}}
@media (max-width: 799px) {{
  :root {{ --slumber-h1: 26px; }}
}}
@media (max-height: 760px) {{
  :root {{ --slumber-h1: 26px; --slumber-pad: 24px; --slumber-header-h: 52px; }}
}}
@media (max-height: 640px) {{
  :root {{ --slumber-header-h: 48px; }}
}}
body, .q-page, .nicegui-content {{
  font-family: var(--slumber-font) !important;
  background-color: var(--slumber-page-bg) !important;
  color: var(--slumber-text);
}}
.slumber-display {{ font-size: clamp(28px, 5vh, 40px); line-height: 1.15; }}
.slumber-title {{ font-size: var(--slumber-h1); line-height: 1.2; }}
.slumber-body {{ font-size: var(--slumber-fs); line-height: 1.5; }}
.slumber-caption {{ font-size: 12px; line-height: 1.4; }}
"""

# Rules that must beat Quasar's own !important utilities (text colour, disabled opacity).
# NiceGUI 3 puts those in a late cascade layer, so ours go in its ``overrides`` layer;
# earlier NiceGUI versions have no layers and take the rules as they are.
_OVERRIDE_CSS = f"""
.q-dialog__backdrop {{ background: {SCRIM} !important; }}
.q-btn.slumber-btn {{
  min-height: 44px;
  padding: 0 22px;
  border-radius: 8px;
  font: 700 16px/1 var(--slumber-font);
  letter-spacing: 0;
  text-transform: none;
}}
.q-btn.slumber-btn .q-icon {{ font-size: 18px; }}
.q-btn.slumber-btn .on-left {{ margin-right: 8px; }}
.q-btn.slumber-btn .on-right {{ margin-left: 8px; }}
.q-btn.slumber-btn-primary {{
  background: var(--slumber-brand) !important;
  color: var(--slumber-text) !important;
}}
.q-btn.slumber-btn-secondary {{ color: var(--slumber-text) !important; font-weight: 600; }}
.q-btn.slumber-btn-secondary:before {{ border: 1.5px solid var(--slumber-accent); }}
.q-btn.slumber-btn-attention {{ color: var(--slumber-attention) !important; font-weight: 600; }}
.q-btn.slumber-btn-attention:before {{ border: 1.5px solid var(--slumber-attention); }}
.q-btn.slumber-btn-lg {{ min-height: 56px; padding: 0 44px; border-radius: 10px; font-size: 18px; }}
.q-btn.slumber-btn.disabled {{ opacity: 0.4 !important; }}
.q-btn.slumber-btn:focus-visible {{ outline: 2px solid var(--slumber-text); outline-offset: 2px; }}
"""


def mount_fonts(app: Any) -> None:
    """Serve packaged Mulish files under ``FONTS_URL_PREFIX``."""
    if FONTS_DIR.is_dir():
        app.add_static_files(FONTS_URL_PREFIX, str(FONTS_DIR))


def build_theme_css() -> str:
    """Return the theme CSS, layering the overrides when NiceGUI uses cascade layers."""
    from nicegui import __version__

    overrides = _OVERRIDE_CSS
    if int(__version__.split(".")[0]) >= 3:
        overrides = f"@layer overrides {{\n{_OVERRIDE_CSS}\n}}"
    return _THEME_CSS + overrides


def apply_theme() -> None:
    """Load typeface, CSS variables, and Quasar colours (call once at GUI start)."""
    from nicegui import ui

    ui.add_css(build_theme_css())
    ui.colors(**COLORS)


def add_component_css(css: str, *, client: Any | None = None) -> None:
    """Add a component's own CSS to a page, once per page.

    Components keep their styles next to their code and style with the shared
    ``--slumber-*`` variables from :func:`apply_theme`, never with raw colours.
    Widgets call this while they build; a layout's ``css`` is added by the GUI
    backend.

    Args:
        css: Stylesheet text.
        client: The NiceGUI page to add it to. Defaults to the current one; pass
            it when the current element may already have been removed.
    """
    from nicegui import context, ui

    client = client or context.client
    loaded = _LOADED_COMPONENT_CSS.setdefault(client, set())
    if css not in loaded:
        loaded.add(css)
        with client:
            ui.add_css(css)


def default_logo_path() -> Path | None:
    """Return the packaged logo path when the file exists."""
    return DEFAULT_LOGO_PATH if DEFAULT_LOGO_PATH.is_file() else None


def default_favicon_path() -> Path | None:
    """Return the packaged favicon path when the file exists."""
    return DEFAULT_FAVICON_PATH if DEFAULT_FAVICON_PATH.is_file() else None
