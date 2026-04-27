"""Modular icon system for the shell.

Each icon is a subfolder containing an icon.py file with a render() function.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui2.state import PageGraphState


def load_icon(icon_name: str) -> Callable[[PageGraphState], None]:
    """Dynamically load an icon module by name.

    Args:
        icon_name: Name of the icon folder (e.g., "internet", "power")

    Returns:
        The render function from the icon module

    Raises:
        ImportError: If the icon module cannot be loaded
    """
    module_path = f"slumber.plugins.ui.nicegui2.icons.{icon_name}.icon"
    module = __import__(module_path, fromlist=["render"])
    return module.render
