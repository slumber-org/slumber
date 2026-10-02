"""Tests for the plugin registry (EntryPointGroup, get_plugin, list_plugins)."""

from __future__ import annotations

import pytest

from slumber.plugins import (
    ConfiguredPlugin,
    EntryPointGroup,
    PluginNotFoundError,
    get_registry,
    reset_registry,
)


@pytest.fixture(autouse=True)
def _fresh_registry() -> None:
    """Reload entry points after pyproject changes within a session."""
    reset_registry()
    yield
    reset_registry()


class TestEntryPointGroup:
    """Entry-point group enum and string values."""

    def test_groups_defined(self) -> None:
        assert EntryPointGroup.ACTIVITIES.value == "slumber.activities"
        assert EntryPointGroup.UNITS.value == "slumber.units"

    def test_iteration(self) -> None:
        groups = list(EntryPointGroup)
        assert len(groups) == 2
        assert EntryPointGroup.ACTIVITIES in groups
        assert EntryPointGroup.UNITS in groups


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

    def test_get_plugin_activities_unknown_raises(self) -> None:
        registry = get_registry()
        with pytest.raises(PluginNotFoundError) as exc_info:
            registry.get_plugin(EntryPointGroup.ACTIVITIES, "nonexistent_activity")
        err = exc_info.value
        assert err.group == "slumber.activities"
        assert err.key == "nonexistent_activity"

    def test_get_plugin_instruction_activity_resolved(self) -> None:
        registry = get_registry()
        if "instruction" not in registry.list_plugins(EntryPointGroup.ACTIVITIES):
            pytest.skip(
                "instruction activity not loaded "
                "(entry-point load may have been skipped)"
            )
        activity_class = registry.get_plugin(EntryPointGroup.ACTIVITIES, "instruction")
        from slumber.ui.activities.instruction import InstructionActivity

        assert activity_class is InstructionActivity
        assert issubclass(activity_class, ConfiguredPlugin)

    def test_get_plugin_clock_unit_resolved(self) -> None:
        registry = get_registry()
        if "clock" not in registry.list_plugins(EntryPointGroup.UNITS):
            pytest.skip(
                "clock unit not loaded (entry-point load may have been skipped)"
            )
        unit_class = registry.get_plugin(EntryPointGroup.UNITS, "clock")
        from slumber.pipeline.units.clock import ClockUnit

        assert unit_class is ClockUnit


class TestPluginNotFoundError:
    """PluginNotFoundError attributes and message."""

    def test_subclass_of_lookup_error(self) -> None:
        assert issubclass(PluginNotFoundError, LookupError)

    def test_message_includes_group_key_available(self) -> None:
        err = PluginNotFoundError("slumber.activities", "foo", ["instruction", "sleep"])
        assert "slumber.activities" in str(err)
        assert "foo" in str(err)
        assert "instruction" in str(err) or "sleep" in str(err)

    def test_attributes(self) -> None:
        err = PluginNotFoundError("slumber.units", "Bar", [])
        assert err.group == "slumber.units"
        assert err.key == "Bar"
        assert err.available == []
