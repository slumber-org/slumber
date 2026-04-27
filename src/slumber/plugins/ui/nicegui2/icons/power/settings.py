"""Settings for the power icon."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PowerIconSettings(BaseModel):
    """Settings for the power status indicator."""

    plugged_icon: str = "power"
    battery_icon: str = "battery_full"
    plugged_color: str = "secondary"
    battery_color: str = "warning"
    plugged_tooltip: str = "Plugged in"
    battery_tooltip: str = "Battery"


__all__ = ["PowerIconSettings"]
