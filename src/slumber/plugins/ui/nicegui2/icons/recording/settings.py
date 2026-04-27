"""Settings for the recording icon."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RecordingIconSettings(BaseModel):
    """Settings for the recording status indicator."""

    recording_icon: str = "fiber_manual_record"
    not_recording_icon: str = "fiber_manual_record"
    recording_color: str = "negative"
    not_recording_color: str = "grey"
    recording_tooltip: str = "Recording now"
    not_recording_tooltip: str = "Not recording now"


__all__ = ["RecordingIconSettings"]
