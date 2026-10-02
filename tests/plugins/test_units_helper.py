"""Tests for unit helper utilities (settings validation + construction)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import ezmsg.core as ez
import pytest
from pydantic import BaseModel, Field, ValidationError

from slumber.pipeline.units import Settings, build_unit_from_settings


class _PydanticSettings(BaseModel):
    enabled: bool
    threshold: float


class _PydanticUnit:
    SETTINGS = _PydanticSettings

    def __init__(self, settings: _PydanticSettings) -> None:
        self.settings = settings


@dataclass(frozen=True)
class _DataclassSettings:
    enabled: bool = True
    count: int = 0


class _DataclassUnit:
    SETTINGS = _DataclassSettings

    def __init__(self, settings: _DataclassSettings) -> None:
        self.settings = settings


class _NoSettingsUnit:
    def __init__(self, _: Any) -> None:
        pass


class TestBuildUnitFromSettings:
    def test_pydantic_settings_validates(self) -> None:
        unit = build_unit_from_settings(
            _PydanticUnit, {"enabled": True, "threshold": 0.5}
        )
        assert isinstance(unit, _PydanticUnit)
        assert unit.settings.enabled is True
        assert unit.settings.threshold == 0.5

    def test_pydantic_settings_rejects_invalid(self) -> None:
        with pytest.raises(ValidationError):
            build_unit_from_settings(_PydanticUnit, {"enabled": "nope", "threshold": 1})

    def test_dataclass_settings_constructs(self) -> None:
        unit = build_unit_from_settings(_DataclassUnit, {"enabled": False, "count": 3})
        assert isinstance(unit, _DataclassUnit)
        assert unit.settings == _DataclassSettings(enabled=False, count=3)

    def test_dataclass_settings_rejects_unknown_field(self) -> None:
        with pytest.raises(TypeError):
            build_unit_from_settings(_DataclassUnit, {"unknown": 1})

    def test_none_settings_uses_defaults(self) -> None:
        unit = build_unit_from_settings(_DataclassUnit, None)
        assert unit.settings == _DataclassSettings()

    def test_missing_settings_attribute_rejected(self) -> None:
        with pytest.raises(AttributeError, match="SETTINGS"):
            build_unit_from_settings(_NoSettingsUnit, {})  # type: ignore[arg-type]

    def test_settings_must_be_dict_or_none(self) -> None:
        with pytest.raises(ValueError, match="settings must be a dict or None"):
            build_unit_from_settings(_DataclassUnit, ["not", "a", "dict"])  # type: ignore[arg-type]

    def test_settings_helper_is_ez_settings_and_validates(self) -> None:
        """Settings subclasses ez.Settings and validates via model_validate."""

        class _MyUnitSettings(Settings):
            enabled: bool = True
            count: int = Field(ge=0, le=100)

        class _MyUnit(ez.Unit):
            SETTINGS = _MyUnitSettings

            def __init__(self, settings: _MyUnitSettings) -> None:
                super().__init__(settings)
                self.settings = settings

        unit = build_unit_from_settings(_MyUnit, {"enabled": False, "count": 42})
        assert isinstance(unit, _MyUnit)
        assert isinstance(unit.settings, ez.Settings)
        assert unit.settings.enabled is False
        assert unit.settings.count == 42

        with pytest.raises(ValidationError):
            build_unit_from_settings(_MyUnit, {"count": 999})  # > 100
