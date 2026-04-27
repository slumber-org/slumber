"""Dynamic theme system for nicegui2 UI.

Call `set_theme("dark")` or `set_theme("light")` to switch at runtime.
`apply()` sets up Quasar colors globally via `ui.colors()`.

Pages should use Quasar color names directly:
- color=primary, color=secondary, color=positive, etc.
- text-primary, text-secondary for text colors
- bg-background, bg-surface, border-secondary for backgrounds/borders
"""

from __future__ import annotations

from slumber.plugins.ui.nicegui2.themes.schemas import Theme

# Current theme
_active_name: str = "dark"
_active: Theme | None = None


def set_theme(name: str) -> None:
    """Switch theme at runtime ("dark" or "light")."""
    global _active_name, _active
    _active_name = name
    import importlib
    module = importlib.import_module(
        f"slumber.plugins.ui.nicegui2.themes.{name}.theme"
    )
    _active = module.theme


def _register_fonts(theme: Theme) -> str:
    """Register font files from theme directory and return CSS @font-face rules."""
    from nicegui import app

    theme_dir = theme.theme_dir
    base_url = f"/fonts/{theme_dir.parent.name}/{theme_dir.name}"

    # Register theme directory as static files (if not already done)
    # NiceGUI handles duplicates gracefully
    try:
        app.add_static_files(base_url, str(theme_dir))
    except RuntimeError:
        # Already registered
        pass

    # Build @font-face CSS with relative URLs
    css_parts = []
    if theme.font_path and theme.font_path.exists():
        css_parts.append(f"""
        @font-face {{
            font-family: 'Mulish';
            src: url('{base_url}/{theme.font_path.name}') format('truetype');
            font-weight: 400 700;
            font-style: normal;
        }}
        """)
    if theme.font_italic_path and theme.font_italic_path.exists():
        css_parts.append(f"""
        @font-face {{
            font-family: 'Mulish';
            src: url('{base_url}/{theme.font_italic_path.name}') format('truetype');
            font-weight: 400 700;
            font-style: italic;
        }}
        """)

    return "\n".join(css_parts) if css_parts else ""


def apply() -> None:
    """Apply active theme (colors, fonts) to NiceGUI."""
    from nicegui import ui

    # Ensure theme is loaded
    global _active
    if _active is None:
        set_theme(_active_name)
    assert _active is not None, "Failed to load theme"

    # Load local fonts from theme folder
    font_css = _register_fonts(_active)
    if font_css:
        ui.add_head_html(f"""
            <style>
                {font_css}
                body, .q-body, .q-app {{
                    font-family: 'Mulish', sans-serif !important;
                }}
            </style>
        """)

    # Apply Quasar colors from theme
    ui.colors(**_active.colors)
