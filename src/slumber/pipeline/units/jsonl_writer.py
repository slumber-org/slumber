"""Append pipeline messages to a JSONL file (demo / tests)."""

from __future__ import annotations

import ezmsg.core as ez
from pydantic import Field

from slumber.pipeline.units.utils import Settings


class JsonlWriterSettings(Settings):
    """Settings for :class:`JsonlWriterUnit`."""

    path: str = Field(..., min_length=1, description="Output JSONL path.")


class JsonlWriterUnit(ez.Unit):
    """Append each message to ``settings.path`` (implementation in run stack)."""

    SETTINGS = JsonlWriterSettings
