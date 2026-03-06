"""Plugin system: registry, types, and built-in units/tasks/UI backends."""

from slumber.plugins.errors import PluginNotFoundError
from slumber.plugins.registry import (
    EntryPointGroup,
    PluginRegistry,
    get_registry,
)
from slumber.plugins.types import TaskClass, UIBackend, UnitClass
from slumber.plugins.units import build_unit_from_settings

__all__ = [
    "EntryPointGroup",
    "PluginNotFoundError",
    "PluginRegistry",
    "TaskClass",
    "UIBackend",
    "UnitClass",
    "build_unit_from_settings",
    "get_registry",
]
