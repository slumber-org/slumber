"""Plugin discovery: registry and ConfiguredPlugin contract."""

from slumber.plugins.base import ConfiguredPlugin
from slumber.plugins.errors import PluginNotFoundError
from slumber.plugins.registry import (
    EntryPointGroup,
    PluginRegistry,
    get_registry,
    reset_registry,
)

__all__ = [
    "ConfiguredPlugin",
    "EntryPointGroup",
    "PluginNotFoundError",
    "PluginRegistry",
    "get_registry",
    "reset_registry",
]
