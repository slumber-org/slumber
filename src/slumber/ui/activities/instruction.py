"""Instruction activity: show markdown/text and complete on mount."""

from __future__ import annotations

from pydantic import BaseModel, Field

from slumber.ui.activities.base import Activity, ActivityHost


class InstructionSettings(BaseModel):
    """Settings for :class:`InstructionActivity`."""

    content: str = Field(
        default="",
        description="Inline text/markdown or a path to a content file.",
    )


class InstructionActivity(Activity):
    """Render instruction content; calls ``host.complete()`` on mount."""

    settings_model = InstructionSettings

    def mount(self, activity_host: ActivityHost) -> None:
        """Headless-friendly: finish immediately so steppers can advance."""
        activity_host.complete()
