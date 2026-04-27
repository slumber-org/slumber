"""Settings for the internet icon."""

from __future__ import annotations

from pydantic import BaseModel, Field


class InternetIconSettings(BaseModel):
    """Settings for the internet status indicator."""

    connected_icon: str = "wifi"
    disconnected_icon: str = "wifi_off"
    connected_color: str = "secondary"
    disconnected_color: str = "warning"
    connected_tooltip: str = "Connected"
    disconnected_tooltip: str = "No internet"


__all__ = ["InternetIconSettings"]
