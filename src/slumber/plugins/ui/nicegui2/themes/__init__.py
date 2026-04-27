"""Themes package for nicegui2 UI.

Usage:
    from slumber.plugins.ui.nicegui2.themes import get_theme
    
    theme = get_theme("dark")  # or "light"
    theme.apply()
"""

from __future__ import annotations

from pathlib import Path

from slumber.plugins.ui.nicegui2.themes.schemas import Theme


THEMES_DIR = Path(__file__).parent


def get_theme(name: str) -> Theme:
    """Get a theme by name.

    Args:
        name: Theme name (e.g., "dark", "light")

    Returns:
        Validated Theme instance with colors, fonts, and assets

    Raises:
        ValueError: If theme doesn't exist
    """
    try:
        import importlib
        module = importlib.import_module(
            f"slumber.plugins.ui.nicegui2.themes.{name}.theme"
        )
        return module.theme
    except ImportError as e:
        available = [d.name for d in THEMES_DIR.iterdir() if d.is_dir() and not d.name.startswith("_")]
        raise ValueError(f"Theme '{name}' not found. Available: {available}") from e


def list_themes() -> list[str]:
    """List available theme names."""
    return [d.name for d in THEMES_DIR.iterdir() if d.is_dir() and not d.name.startswith("_")]
