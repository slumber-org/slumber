"""Tests for PluginRegistry: discovery, lookup, and missing-plugin errors."""

from dataclasses import dataclass
from unittest.mock import patch

import pytest

from slumber.plugins import (
    PluginNotFoundError,
    PluginRegistry,
    get_registry,
)
from slumber.plugins.registry import EntryPointGroup
from slumber.plugins.tasks.instruction import InstructionTask
from slumber.plugins.tasks.utils import build_task_from_settings
from slumber.plugins.ui.headless import HeadlessUIBackend


class TestEntryPointGroups:
    """Entry-point group names are part of the public API."""

    def test_groups_defined(self) -> None:
        groups = list(EntryPointGroup)
        assert EntryPointGroup.UNITS in groups
        assert EntryPointGroup.TASKS in groups
        assert EntryPointGroup.UI_BACKENDS in groups
        assert len(groups) == 3


class TestPluginRegistryDiscovery:
    """Registry discovers built-in plugins from entry points."""

    def test_list_task_types_includes_instruction(self) -> None:
        registry = PluginRegistry()
        assert "instruction" in registry.list_task_types()

    def test_list_ui_backend_keys_includes_headless(self) -> None:
        registry = PluginRegistry()
        assert "headless" in registry.list_ui_backend_keys()

    def test_list_unit_types_empty_without_extensions(self) -> None:
        registry = PluginRegistry()
        # No built-in units; list may be empty or populated by test env.
        keys = registry.list_unit_types()
        assert isinstance(keys, list)
        assert all(isinstance(k, str) for k in keys)

    def test_list_returns_sorted(self) -> None:
        registry = PluginRegistry()
        assert registry.list_task_types() == sorted(registry.list_task_types())
        assert registry.list_ui_backend_keys() == sorted(
            registry.list_ui_backend_keys()
        )


class TestGetTask:
    """get_task returns task class; build_task_from_settings validates and builds."""

    def test_get_instruction_returns_instruction_task_class(self) -> None:
        registry = PluginRegistry()
        task_class = registry.get_task("instruction")
        assert task_class is InstructionTask

    def test_build_instruction_empty_settings_ok(self) -> None:
        registry = PluginRegistry()
        task_class = registry.get_task("instruction")
        instance = build_task_from_settings(task_class, None)
        assert instance.text is None
        assert instance.content is None

    def test_build_instruction_with_text_ok(self) -> None:
        registry = PluginRegistry()
        task_class = registry.get_task("instruction")
        instance = build_task_from_settings(task_class, {"text": "Hello"})
        assert instance.text == "Hello"

    def test_build_instruction_with_content_ok(self) -> None:
        registry = PluginRegistry()
        task_class = registry.get_task("instruction")
        instance = build_task_from_settings(task_class, {"content": "Body"})
        assert instance.content == "Body"

    def test_build_instruction_rejects_unknown_field(self) -> None:
        registry = PluginRegistry()
        task_class = registry.get_task("instruction")
        with pytest.raises(ValueError):  # Pydantic ValidationError (subclass)
            build_task_from_settings(task_class, {"unknown": "x"})

    def test_get_task_missing_raises_plugin_not_found(self) -> None:
        registry = PluginRegistry()
        with pytest.raises(PluginNotFoundError) as exc_info:
            registry.get_task("nonexistent_task_type_xyz")
        assert exc_info.value.group == "slumber.tasks"
        assert exc_info.value.key == "nonexistent_task_type_xyz"
        assert "instruction" in exc_info.value.available


class TestGetUIBackend:
    """get_ui_backend resolves UI backends."""

    def test_get_headless_returns_headless_backend(self) -> None:
        registry = PluginRegistry()
        backend = registry.get_ui_backend("headless")
        assert isinstance(backend, HeadlessUIBackend)

    def test_headless_run_procedure_no_error(self) -> None:
        from slumber.schemas import Procedure, Step

        registry = PluginRegistry()
        backend = registry.get_ui_backend("headless")
        procedure = Procedure(steps=[Step(task_type="instruction")])
        backend.run_procedure(procedure, {})

    def test_get_ui_backend_missing_raises_plugin_not_found(self) -> None:
        registry = PluginRegistry()
        with pytest.raises(PluginNotFoundError) as exc_info:
            registry.get_ui_backend("nonexistent_backend_xyz")
        assert exc_info.value.group == "slumber.ui_backends"
        assert exc_info.value.key == "nonexistent_backend_xyz"
        assert "headless" in exc_info.value.available


class TestGetUnit:
    """get_unit raises when unit type is not registered."""

    def test_get_unit_missing_raises_plugin_not_found(self) -> None:
        registry = PluginRegistry()
        with pytest.raises(PluginNotFoundError) as exc_info:
            registry.get_unit("SomeUnitThatDoesNotExist")
        assert exc_info.value.group == "slumber.units"
        assert exc_info.value.key == "SomeUnitThatDoesNotExist"

    def test_get_unit_returns_unit_class_build_with_helper(self) -> None:
        """get_unit returns the Unit class; use build_unit_from_settings to build instances."""

        import ezmsg.core as ez

        @dataclass
        class _FakeSettings:
            x: int = 0

        class _FakeUnit(ez.Unit):
            SETTINGS = _FakeSettings

            def __init__(self, settings: _FakeSettings) -> None:
                super().__init__(settings)
                self.settings = settings

        from slumber.plugins import registry as reg_mod
        from slumber.plugins.units import build_unit_from_settings

        original_load = reg_mod._load_entry_points

        def _mock_load(group: EntryPointGroup):
            if group != EntryPointGroup.UNITS:
                return original_load(group)
            return {"FakeUnit": _FakeUnit}

        with patch.object(reg_mod, "_load_entry_points", side_effect=_mock_load):
            registry = PluginRegistry()
        unit_class = registry.get_unit("FakeUnit")
        assert unit_class is _FakeUnit
        unit = build_unit_from_settings(unit_class, {"x": 42})
        assert unit.settings.x == 42
        assert isinstance(unit, _FakeUnit)


class TestGetRegistry:
    """get_registry returns a singleton."""

    def test_returns_plugin_registry(self) -> None:
        reg = get_registry()
        assert isinstance(reg, PluginRegistry)
        assert get_registry() is reg
