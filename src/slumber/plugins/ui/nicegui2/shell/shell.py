"""Shell: menu bar with Help, Settings, and status indicators.

This is the container that wraps all pages.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from nicegui import ui, app

from slumber.constants import PACKAGE_ROOT
from slumber.plugins.ui.nicegui2.shell.settings import ShellSettings
from slumber.plugins.ui.nicegui2.icons import load_icon
from slumber.plugins.ui.nicegui2.menus import load_menu
from slumber.plugins.ui.nicegui2.themes.theming import apply, set_theme
from slumber.plugins.ui.nicegui2.utils import to_pascal_case

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui2.state import PageGraphState


# Register root assets folder for SVG logo
_ROOT_ASSETS_DIR = PACKAGE_ROOT / "assets"
if _ROOT_ASSETS_DIR.exists():
    try:
        app.add_static_files("/static", str(_ROOT_ASSETS_DIR))
    except RuntimeError:
        pass  # Already registered


def _disable_zoom() -> None:
    """Disable zooming via keyboard shortcuts, mouse wheel, and pinch gestures."""
    ui.add_body_html(
        """
        <script>
        // Disable keyboard shortcuts (Ctrl + / Ctrl - / Ctrl 0)
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && (e.key === '+' || e.key === '-' || e.key === '0')) {
                e.preventDefault();
            }
        });

        // Disable Ctrl + mouse wheel zoom
        document.addEventListener('wheel', function(e) {
            if (e.ctrlKey || e.metaKey) {
                e.preventDefault();
            }
        }, { passive: false });

        // Disable pinch-to-zoom on touch devices
        document.addEventListener('touchstart', function(e) {
            if (e.touches.length > 1) {
                e.preventDefault();
            }
        }, { passive: false });

        // Set viewport meta tag to prevent zooming
        const meta = document.querySelector('meta[name="viewport"]');
        if (meta) {
            meta.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
        }
        </script>
        """
    )


def render_shell(
    state: PageGraphState,
    refresh: Callable[[], None],
    cfg: ShellSettings,
    content: Callable[[], None],
) -> None:
    """Render the shell wrapper around page content.

    Args:
        state: App state (for indicator status)
        refresh: Function to refresh UI
        cfg: Shell configuration
        content: Function that renders the actual page content
    """
    # Use theme from state if set, otherwise from config
    current_theme = getattr(state, "theme", cfg.theme)
    set_theme(current_theme)
    apply()

    # Disable zooming (keyboard shortcuts, mouse wheel, pinch gestures)
    _disable_zoom()

    with ui.column().classes("w-full h-screen p-0 m-0 gap-0 bg-background"):
        # Menu bar at top
        _render_menu_bar(state, refresh, cfg)

        # Page content fills remaining space (no gap, no margin)
        with ui.column().classes("w-full flex-grow p-0 m-0 gap-0"):
            content()


def _render_menu_bar(
    state: PageGraphState, refresh: Callable[[], None], cfg: ShellSettings
) -> None:
    """Render the top menu bar."""
    with ui.row().classes(
        "w-full items-center justify-between px-4 py-2 bg-surface border-b border-secondary shrink-0"
    ):
        # Left: Logo + app name
        with ui.row().classes("items-center gap-3"):
            if cfg.show_logo:
                ui.image("/static/logo.svg").style(
                    "height: 32px; width: 32px; object-fit: contain;"
                )
            ui.label(cfg.brand_text).classes("text-subtitle1 font-bold text-primary")

        # Center: Status indicators
        _render_indicators(state, cfg)
        # Store reference to indicators refresh function in state
        setattr(state, "refresh_indicators", _render_indicators.refresh)

        # Right: Menus
        with ui.row().classes("items-center gap-1"):
            _render_menus(state, refresh, cfg)


@ui.refreshable
def _render_indicators(state: PageGraphState, cfg: ShellSettings) -> None:
    """Render status indicators dynamically from config."""
    with ui.row().classes("items-center gap-4"):
        for icon in cfg.icons:
            icon_name = icon.type
            try:
                icon_render = load_icon(icon_name)
                icon_render(state)
            except ImportError as e:
                ui.notify(f"Failed to load icon '{icon_name}': {e}")


def _render_menus(
    state: PageGraphState, refresh: Callable[[], None], cfg: ShellSettings
) -> None:
    """Render menus dynamically from config."""
    for menu in cfg.menus:
        menu_name = menu.type
        try:
            menu_render = load_menu(menu_name)
            # Load the settings class from the menu module
            settings_module_path = (
                f"slumber.plugins.ui.nicegui2.menus.{menu_name}.settings"
            )
            settings_module = __import__(settings_module_path, fromlist=["*"])
            # Get the Settings class (expected to be named {MenuName}MenuSettings)
            settings_class_name = f"{to_pascal_case(menu_name)}MenuSettings"
            settings_class = getattr(settings_module, settings_class_name, None)
            if settings_class is None:
                ui.notify(
                    f"Settings class '{settings_class_name}' not found for menu '{menu_name}'"
                )
                continue
            # Instantiate with items and settings from config
            menu_cfg = settings_class(items=menu.items or [], **menu.settings)
            menu_render(state, refresh, menu_cfg)
        except ImportError as e:
            ui.notify(f"Failed to load menu '{menu_name}': {e}")
