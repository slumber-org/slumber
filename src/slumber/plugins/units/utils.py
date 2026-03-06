"""Settings base and build_unit_from_settings for slumber.units plugins."""

from __future__ import annotations

from typing import Any

import ezmsg.core as ez
from pydantic import TypeAdapter


class Settings(ez.Settings):
    """ez.Settings subclass that adds Pydantic-style model_validate.

    Use this as the base for your unit's SETTINGS type so that config dicts
    are validated and coerced (e.g. Field(gt=0), nested models). Subclasses
    define fields with type annotations and optional pydantic Field().

    Example:

        from slumber.plugins.units import Settings
        from pydantic import Field

        class MyUnitSettings(Settings):
            enabled: bool = True
            count: int = Field(ge=0, le=100)

        class MyUnit(ez.Unit):
            SETTINGS = MyUnitSettings
            ...
    """

    @classmethod
    def model_validate(cls, obj: Any) -> Settings:
        """Validate and coerce a dict (or mapping) into a settings instance."""
        return TypeAdapter(cls).validate_python(obj)


def build_unit_from_settings(
    unit_cls: type[ez.Unit], settings: dict[str, Any] | None
) -> ez.Unit:
    """Instantiate a unit class using its `SETTINGS` attribute.

    This mirrors the legacy behavior:
    - If `unit_cls.SETTINGS` has `model_validate`, use it (Settings subclass).
    - Otherwise, assume `SETTINGS` is a dataclass/constructor and call `SETTINGS(**settings)`.
    - Instantiate the unit with the resulting settings object: `unit_cls(settings_obj)`.

    Args:
        unit_cls: The unit class to instantiate (ez.Unit subclass; defines SETTINGS).
        settings: Settings dict from config (or None).

    Returns:
        The instantiated ez.Unit.

    Raises:
        ValueError: If settings is not a dict or None, or if the unit has SETTINGS = None but settings were provided.
    """
    if settings is not None and not isinstance(settings, dict):
        raise ValueError(f"settings must be a dict or None, got {type(settings)}.")

    settings_type = getattr(unit_cls, "SETTINGS")

    if settings_type is None:
        if settings is not None:
            raise ValueError(
                f"Unit {unit_cls.__name__} has no SETTINGS (SETTINGS is None) but settings were provided."
            )
        return unit_cls()

    settings_dict = settings or {}

    if issubclass(settings_type, Settings):
        settings_obj = settings_type.model_validate(settings_dict)
    else:
        settings_obj = settings_type(**settings_dict)

    return unit_cls(settings_obj)
