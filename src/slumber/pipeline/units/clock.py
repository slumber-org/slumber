"""Periodic dummy sample source (demo / tests)."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncGenerator
from typing import Any

import ezmsg.core as ez
from pydantic import Field

from slumber.pipeline.units.utils import Settings


class ClockSettings(Settings):
    """Settings for :class:`ClockUnit`."""

    rate: float = Field(default=1.0, gt=0, description="Samples per second.")


class ClockUnit(ez.Unit):
    """Emit periodic dummy samples at ``settings.rate`` on ``OUTPUT``."""

    SETTINGS = ClockSettings

    OUTPUT = ez.OutputStream(dict[str, Any])

    @ez.publisher(OUTPUT)
    async def tick(
        self,
    ) -> AsyncGenerator[tuple[ez.OutputStream, dict[str, Any]], None]:
        """Publish ``{"n", "t"}`` samples forever at the configured rate."""
        period = 1.0 / self.SETTINGS.rate
        n = 0
        while True:
            yield self.OUTPUT, {"n": n, "t": time.time()}
            n += 1
            await asyncio.sleep(period)
