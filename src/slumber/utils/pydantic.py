"""Pydantic helper utilities."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import TypeVar

EnumT = TypeVar("EnumT", bound=Enum)


def coerce_enum_by_name(enum_type: type[EnumT]) -> Callable[[str | EnumT], EnumT]:
    """Return a validator that coerces enum members by name.

    Args:
        enum_type: Enum subclass.

    Returns:
        Callable that accepts either an existing enum value or a string member name.

    Raises:
        TypeError: If the input is not a string or ``enum_type`` member.
        ValueError: If the string is not a valid member name.
    """

    def _coerce(value: str | EnumT) -> EnumT:
        if isinstance(value, enum_type):
            return value
        if not isinstance(value, str):
            raise TypeError(
                f"Expected {enum_type.__name__} or str, got {type(value).__name__}"
            )
        try:
            return enum_type[value]
        except KeyError as exc:
            raise ValueError(
                f"Unknown {enum_type.__name__} {value!r}. "
                f"Available: {sorted(enum_type.__members__.keys())}"
            ) from exc

    return _coerce

