"""Periodic dummy sample source (demo / tests)."""

from __future__ import annotations

import ezmsg.core as ez
from pydantic import Field

from slumber.pipeline.units.utils import Settings


class ClockSettings(Settings):
    """Settings for :class:`ClockUnit`."""

    rate: float = Field(default=1.0, gt=0, description="Samples per second.")


class ClockUnit(ez.Unit):
    """Emit periodic dummy samples at ``settings.rate`` (implementation in run stack)."""

    SETTINGS = ClockSettings
