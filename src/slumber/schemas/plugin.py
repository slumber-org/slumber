"""Plugin specification schema (type + settings)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PluginSpec(BaseModel):
    """YAML reference to a typed implementation (UI, layout, activity, or unit).

    Schemas validate shape only. Config resolves ``type`` via the registry or
    built-in map and validates ``settings`` against the implementation.
    """

    type: str = Field(
        ...,
        min_length=1,
        description="Entry-point name or built-in key.",
    )
    settings: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional settings validated by the implementation's settings model.",
    )
