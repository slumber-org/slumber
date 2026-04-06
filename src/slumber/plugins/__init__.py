"""Plugin system: registry and built-in units/tasks/UI backends."""

from slumber.plugins.errors import PluginNotFoundError
from slumber.plugins.registry import (
    EntryPointGroup,
    PluginRegistry,
    get_registry,
)
from slumber.plugins.ui.base import UIBackend
from slumber.plugins.units import build_unit_from_settings

__all__ = [
    "EntryPointGroup",
    "PluginNotFoundError",
    "PluginRegistry",
    "UIBackend",
    "build_unit_from_settings",
    "get_registry",
]
