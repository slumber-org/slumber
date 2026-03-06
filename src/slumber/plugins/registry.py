"""Plugin registry: discover and resolve units, tasks, and UI backends via entry points."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points  # type: ignore[import-untyped]

from loguru import logger
import ezmsg.core as ez

from slumber.plugins.tasks.base import Task

if TYPE_CHECKING:
    from slumber.plugins.types import TaskClass, UIBackend, UnitClass


class EntryPointGroup(str, Enum):
    """Entry-point group names (public API for extensions)."""

    UNITS = "slumber.units"
    TASKS = "slumber.tasks"
    UI_BACKENDS = "slumber.ui_backends"


class PluginNotFoundError(LookupError):
    """Raised when a plugin is requested by key but not found in the registry."""

    def __init__(self, group: str, key: str, available: list[str]) -> None:
        self.group = group
        self.key = key
        self.available = available
        super().__init__(
            f"Plugin {group!r} not found for key {key!r}. "
            f"Available: {', '.join(sorted(available)) or '(none)'}."
        )


def _resolve_plugin_for_group(
    group: EntryPointGroup, name: str, loaded_object: Any
) -> Any | None:
    """Return the object to store for this plugin, or None to skip (with a warning).

    Units and tasks must be the expected class type; otherwise we warn and skip.
    """
    if group is EntryPointGroup.UNITS:
        if isinstance(loaded_object, type) and issubclass(loaded_object, ez.Unit):
            return loaded_object
        logger.warning(
            "Skipping {}[{}]: expected ez.Unit subclass, got {!r}.",
            group.value,
            name,
            type(loaded_object).__name__,
        )
        return None

    if group is EntryPointGroup.TASKS:
        if isinstance(loaded_object, type) and issubclass(loaded_object, Task):
            return loaded_object
        logger.warning(
            "Skipping {}[{}]: expected Task subclass, got {!r}.",
            group.value,
            name,
            type(loaded_object).__name__,
        )
        return None

    # UI backends: store instance if it's a class, else store as-is
    if isinstance(loaded_object, type):
        return loaded_object()
    return loaded_object


def _load_entry_points(group: EntryPointGroup) -> dict[str, Any]:
    """Load entry points for a group; return mapping name -> loaded object.

    For slumber.units: only ez.Unit subclasses are stored (the class).
    For slumber.tasks: only Task subclasses are stored (the class).
    For slumber.ui_backends: classes are instantiated; other objects stored as-is.
    Invalid units/tasks are skipped with a warning.
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
        except Exception as error:
            logger.warning(
                "Failed to load plugin {}[{}]: {}",
                group.value,
                entry_point.name,
                error,
            )
    return result


class PluginRegistry:
    """Single registry for units, tasks, and UI backends loaded from entry points."""

    def __init__(self) -> None:
        self._units: dict[str, UnitClass] = {}
        self._tasks: dict[str, TaskClass] = {}
        self._ui_backends: dict[str, UIBackend] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load all three groups and coerce to expected types."""
        self._units = _load_entry_points(EntryPointGroup.UNITS)
        self._tasks = _load_entry_points(EntryPointGroup.TASKS)
        self._ui_backends = _load_entry_points(EntryPointGroup.UI_BACKENDS)

    def get_unit(self, unit_type: str) -> UnitClass:
        """Return the Unit class for the given type key.

        Args:
            unit_type: Entry-point name (e.g. 'ZMaxDataReceiver').

        Returns:
            Unit class; use build_unit_from_settings(unit_class, settings) to build instances.

        Raises:
            PluginNotFoundError: If no plugin is registered for unit_type.
        """
        if unit_type not in self._units:
            raise PluginNotFoundError(
                EntryPointGroup.UNITS.value,
                unit_type,
                list(self._units.keys()),
            )
        return self._units[unit_type]

    def get_task(self, task_type: str) -> TaskClass:
        """Return the Task class for the given task type key.

        Args:
            task_type: Entry-point name (e.g. 'instruction', 'survey').

        Returns:
            Task class; use build_task_from_settings to build instances.

        Raises:
            PluginNotFoundError: If no plugin is registered for task_type.
        """
        if task_type not in self._tasks:
            raise PluginNotFoundError(
                EntryPointGroup.TASKS.value,
                task_type,
                list(self._tasks.keys()),
            )
        return self._tasks[task_type]

    def get_ui_backend(self, key: str) -> UIBackend:
        """Return the UI backend for the given key.

        Args:
            key: Entry-point name (e.g. 'headless').

        Returns:
            UI backend implementing UIBackend protocol.

        Raises:
            PluginNotFoundError: If no plugin is registered for key.
        """
        if key not in self._ui_backends:
            raise PluginNotFoundError(
                EntryPointGroup.UI_BACKENDS.value,
                key,
                list(self._ui_backends.keys()),
            )
        return self._ui_backends[key]

    def list_unit_types(self) -> list[str]:
        """Return sorted list of registered unit type keys."""
        return sorted(self._units.keys())

    def list_task_types(self) -> list[str]:
        """Return sorted list of registered task type keys."""
        return sorted(self._tasks.keys())

    def list_ui_backend_keys(self) -> list[str]:
        """Return sorted list of registered UI backend keys."""
        return sorted(self._ui_backends.keys())


# Module-level default registry (lazy or at import).
_default_registry: PluginRegistry | None = None


def get_registry() -> PluginRegistry:
    """Return the default plugin registry (singleton)."""
    global _default_registry
    if _default_registry is None:
        _default_registry = PluginRegistry()
    return _default_registry
