"""Plugin registry: discover activities and units via entry points."""

from __future__ import annotations

from collections import defaultdict
from enum import Enum
from typing import Any

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points  # type: ignore[import-untyped]

import ezmsg.core as ez
from loguru import logger

from slumber.plugins.base import ConfiguredPlugin
from slumber.plugins.errors import PluginNotFoundError


class EntryPointGroup(str, Enum):
    """Entry-point group names (public API for extensions)."""

    ACTIVITIES = "slumber.activities"
    UNITS = "slumber.units"


_ENTRY_POINT_GROUP_TO_CLASS = {
    EntryPointGroup.ACTIVITIES: ConfiguredPlugin,
    EntryPointGroup.UNITS: ez.Unit,
}


def _resolve_plugin_for_group(
    group: EntryPointGroup, name: str, loaded_object: Any
) -> Any | None:
    """Return the object to store for this plugin, or None to skip (with a warning).

    Activities must be ConfiguredPlugin subclasses; units must be ez.Unit
    subclasses. Otherwise we warn and skip.
    """
    if isinstance(loaded_object, type) and issubclass(
        loaded_object, _ENTRY_POINT_GROUP_TO_CLASS[group]
    ):
        return loaded_object

    logger.warning(
        "Skipping {}[{}]: expected {!r} subclass, got {!r}.",
        group.value,
        name,
        _ENTRY_POINT_GROUP_TO_CLASS[group].__name__,
        type(loaded_object).__name__,
    )
    return None


def _load_entry_points(group: EntryPointGroup) -> dict[str, Any]:
    """Load entry points for a group; return mapping name -> loaded object.

    Invalid plugins are skipped with a warning.
    """
    result: dict[str, Any] = {}

    all_entry_points = entry_points()
    group_entry_points = (
        all_entry_points.select(group=group.value)
        if hasattr(all_entry_points, "select")
        else all_entry_points.get(group.value, [])
    )

    for entry_point in group_entry_points:
        try:
            loaded = entry_point.load()
            to_store = _resolve_plugin_for_group(group, entry_point.name, loaded)
            if to_store is not None:
                result[entry_point.name] = to_store
        except Exception as error:  # noqa: BLE001
            logger.warning(
                "Failed to load plugin {}[{}]: {}",
                group.value,
                entry_point.name,
                error,
            )
    return result


class PluginRegistry:
    """Registry for activity and unit plugins loaded from entry points."""

    def __init__(self) -> None:
        self._plugins: dict[EntryPointGroup, dict[str, type]] = defaultdict(dict)
        self._load_all()

    def _load_all(self) -> None:
        """Load all entry-point groups."""
        for group in EntryPointGroup:
            self._plugins[group] = _load_entry_points(group)

    def get_plugin(self, group: EntryPointGroup, key: str) -> type:
        """Return the plugin class for the given group and key.

        Args:
            group: Entry-point group.
            key: Entry-point name.

        Returns:
            The plugin class for the given group and key.

        Raises:
            PluginNotFoundError: If no plugin is registered for the given group and key.
        """
        if key not in self._plugins[group]:
            raise PluginNotFoundError(
                group.value,
                key,
                list(self._plugins[group].keys()),
            )
        return self._plugins[group][key]

    def list_plugins(self, group: EntryPointGroup) -> list[str]:
        """Return sorted list of registered plugin keys for the given group."""
        return sorted(self._plugins[group].keys())


_default_registry: PluginRegistry | None = None


def get_registry() -> PluginRegistry:
    """Return the default plugin registry (singleton)."""
    global _default_registry
    if _default_registry is None:
        _default_registry = PluginRegistry()
    return _default_registry


def reset_registry() -> None:
    """Clear the default registry singleton (for tests)."""
    global _default_registry
    _default_registry = None
