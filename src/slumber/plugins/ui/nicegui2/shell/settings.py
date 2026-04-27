"""Settings for the shell (menu bar, indicators)."""

from __future__ import annotations

from typing import Any, Union

from pydantic import BaseModel, Field, field_validator


class PluginInstanceSettings(BaseModel):
    """One configured menu/icon plugin instance."""

    type: str = Field(..., min_length=1, description="Plugin key.")
    items: list[dict[str, Any]] | None = Field(
        default=None,
        description="List of items for menus.",
    )
    settings: dict[str, Any] = Field(
        default_factory=dict,
        description="Plugin-instance settings.",
    )


class ShellSettings(BaseModel):
    """Settings for the shell (menu bar, indicators)."""

    brand_text: str = Field(default="SLUMBER", min_length=1)
    show_logo: bool = Field(default=True)
    theme: str = Field(default="dark", description="Theme key (e.g. dark/light).")
    icons: list[Union[PluginInstanceSettings, str]] = Field(
        default_factory=list,
    )
    menus: list[Union[PluginInstanceSettings, str]] = Field(
        default_factory=list,
    )

    @field_validator("icons", mode="before")
    @classmethod
    def normalize_icons(cls, v: list) -> list[PluginInstanceSettings]:
        """Convert string icons to PluginInstanceSettings."""
        result = []
        for item in v:
            if isinstance(item, str):
                result.append(PluginInstanceSettings(type=item))
            else:
                result.append(item)
        return result

    @field_validator("menus", mode="before")
    @classmethod
    def normalize_menus(cls, v: list) -> list[PluginInstanceSettings]:
        """Convert string menus to PluginInstanceSettings."""
        result = []
        for item in v:
            if isinstance(item, str):
                result.append(PluginInstanceSettings(type=item))
            else:
                result.append(item)
        return result


__all__ = ["ShellSettings", "PluginInstanceSettings"]
