"""Modular menu system for the shell.

Each menu is a subfolder containing a menu.py file with a render() function.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui2.state import PageGraphState


def load_menu(menu_name: str) -> Callable[[PageGraphState, Callable[[], None]], None]:
    """Dynamically load a menu module by name.

    Args:
        menu_name: Name of the menu folder (e.g., "help", "settings")

    Returns:
        The render function from the menu module

    Raises:
        ImportError: If the menu module cannot be loaded
    """
    module_path = f"slumber.plugins.ui.nicegui2.menus.{menu_name}.menu"
    module = __import__(module_path, fromlist=["render"])
    return module.render
