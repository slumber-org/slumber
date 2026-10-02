"""Sleep activity: wake / end buttons emit study events; never completes."""

from __future__ import annotations

from pydantic import BaseModel, Field

from slumber.ui.activities.base import Activity, ActivityHost


class SleepSettings(BaseModel):
    """Settings for :class:`SleepActivity`."""

    wake_button: str = Field(default="I'm Awake")
    end_button: str = Field(default="End Session")


class SleepActivity(Activity):
    """Open-ended sleep step; emits ``marked_awake`` / ``end_sleep`` only."""

    settings_model = SleepSettings

    def mount(self, activity_host: ActivityHost) -> None:
        """GUI waits on buttons; headless may emit ``end_sleep`` separately."""
