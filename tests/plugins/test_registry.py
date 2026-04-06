"""Tests for the plugin registry (EntryPointGroup, get_plugin, list_plugins)."""

from __future__ import annotations

import pytest

from slumber.plugins import (
    EntryPointGroup,
    PluginNotFoundError,
    get_registry,
)


class TestEntryPointGroup:
    """Entry-point group enum and string values."""

    def test_groups_defined(self) -> None:
        assert EntryPointGroup.UNITS.value == "slumber.units"
        assert EntryPointGroup.TASKS.value == "slumber.tasks"
        assert EntryPointGroup.UI_BACKENDS.value == "slumber.ui_backends"

    def test_iteration(self) -> None:
        groups = list(EntryPointGroup)
        assert len(groups) == 3
        assert EntryPointGroup.UNITS in groups
        assert EntryPointGroup.TASKS in groups
        assert EntryPointGroup.UI_BACKENDS in groups


class TestPluginRegistry:
    """PluginRegistry unified API: get_plugin(group, key), list_plugins(group)."""

    def test_get_registry_returns_singleton(self) -> None:
        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2

    def test_list_plugins_returns_list(self) -> None:
        registry = get_registry()
        for group in EntryPointGroup:
            keys = registry.list_plugins(group)
            assert isinstance(keys, list)
            assert all(isinstance(k, str) for k in keys)

    def test_get_plugin_units_unknown_raises(self) -> None:
        registry = get_registry()
        with pytest.raises(PluginNotFoundError) as exc_info:
            registry.get_plugin(EntryPointGroup.UNITS, "NonexistentUnitType")
        err = exc_info.value
        assert err.group == "slumber.units"
        assert err.key == "NonexistentUnitType"
        assert err.available is not None

    def test_get_plugin_tasks_unknown_raises(self) -> None:
        registry = get_registry()
        with pytest.raises(PluginNotFoundError) as exc_info:
            registry.get_plugin(EntryPointGroup.TASKS, "nonexistent_task")
        err = exc_info.value
        assert err.group == "slumber.tasks"
        assert err.key == "nonexistent_task"

    def test_get_plugin_ui_backends_unknown_raises(self) -> None:
        registry = get_registry()
        with pytest.raises(PluginNotFoundError) as exc_info:
            registry.get_plugin(EntryPointGroup.UI_BACKENDS, "nonexistent_ui")
        err = exc_info.value
        assert err.group == "slumber.ui_backends"
        assert err.key == "nonexistent_ui"

    def test_get_plugin_instruction_task_resolved(self) -> None:
        registry = get_registry()
        if "instruction" not in registry.list_plugins(EntryPointGroup.TASKS):
            pytest.skip(
                "instruction task not loaded (entry-point load may have been skipped)"
            )
        task_class = registry.get_plugin(EntryPointGroup.TASKS, "instruction")
        assert task_class is not None
        from slumber.plugins.tasks.instruction import InstructionTask

        assert task_class is InstructionTask

    def test_get_plugin_headless_ui_resolved(self) -> None:
        registry = get_registry()
        backend_class_or_obj = registry.get_plugin(
            EntryPointGroup.UI_BACKENDS, "headless"
        )
        backend = (
            backend_class_or_obj()
            if isinstance(backend_class_or_obj, type)
            else backend_class_or_obj
        )
        assert backend is not None
        assert hasattr(backend, "run")


class TestPluginNotFoundError:
    """PluginNotFoundError attributes and message."""

    def test_subclass_of_lookup_error(self) -> None:
        assert issubclass(PluginNotFoundError, LookupError)

    def test_message_includes_group_key_available(self) -> None:
        err = PluginNotFoundError("slumber.tasks", "foo", ["instruction", "survey"])
        assert "slumber.tasks" in str(err)
        assert "foo" in str(err)
        assert "instruction" in str(err) or "survey" in str(err)

    def test_attributes(self) -> None:
        err = PluginNotFoundError("slumber.units", "Bar", [])
        assert err.group == "slumber.units"
        assert err.key == "Bar"
        assert err.available == []
