"""Sleep activity: wake / end buttons emit study events; never completes."""

from __future__ import annotations

from pydantic import BaseModel, Field

from slumber.ui.activities.base import Activity, ActivityHost
from slumber.ui.theme import BRAND_LIGHT, SECONDARY, TYPE_SCALE
from slumber.ui.widgets import confirm_dialog, logo_mark, outline_button, primary_button


class SleepSettings(BaseModel):
    """Settings for :class:`SleepActivity`."""

    wake_button: str = Field(default="I'm Awake")
    end_button: str = Field(default="End Session")


class SleepActivity(Activity):
    """Open-ended sleep step; emits ``marked_awake`` / ``end_sleep`` only."""

    settings_model = SleepSettings

    def __init__(self, settings: SleepSettings | None = None) -> None:
        super().__init__(settings or SleepSettings())
        self._host: ActivityHost | None = None

    def mount(self, activity_host: ActivityHost) -> None:
        """Render wake/end controls under GUI; headless leaves emit to the backend."""
        self._host = activity_host
        if activity_host.container is None:
            return

        from nicegui import ui

        settings = self.settings
        assert isinstance(settings, SleepSettings)

        with activity_host.container, ui.column().classes("items-center gap-4"):
            logo_mark(None, size="hub", fallback_icon="bedtime")
            ui.label("Sleep").classes(
                f"{TYPE_SCALE['display']} font-bold text-[{BRAND_LIGHT}]"
            )
            ui.label("Rest until you wake or end the session.").classes(
                f"{TYPE_SCALE['body']} text-[{SECONDARY}]"
            )
            with ui.column().classes("items-center gap-3 mt-6"):
                primary_button(
                    settings.wake_button,
                    icon="alarm",
                    on_click=self._on_wake,
                )
                outline_button(
                    settings.end_button,
                    icon="stop",
                    attention=True,
                    on_click=self._on_end,
                )

    def unmount(self) -> None:
        """Clear host reference."""
        self._host = None

    async def _on_wake(self) -> None:
        if self._host is None:
            return
        confirmed = await confirm_dialog(
            title="Mark awake?",
            message="Continue to the awakening activities?",
        )
        if confirmed and self._host is not None:
            self._host.emit("marked_awake")

    async def _on_end(self) -> None:
        if self._host is None:
            return
        confirmed = await confirm_dialog(
            title="End sleep?",
            message="Stop the sleep phase and continue the session?",
        )
        if confirmed and self._host is not None:
            self._host.emit("end_sleep")
