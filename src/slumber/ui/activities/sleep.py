"""Sleep activity: a sleep / wake toggle button and an end button; never completes."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from slumber.ui.activities.base import Activity, ActivityHost
from slumber.ui.widgets import (
    ButtonSettings,
    action_button,
    logo_mark,
    merge_button_defaults,
    toggle_button,
    with_confirmation,
)

WAKE_EVENT = "marked_awake"
SLEEP_EVENT = "marked_asleep"
END_EVENT = "end_sleep"

SLEEP_CSS = """
.slumber-sleep {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
  text-align: center;
}
.slumber-sleep-title {
  font-size: clamp(28px, 5vh, 40px);
  line-height: 1.15;
  font-weight: 700;
}
.slumber-sleep-message {
  max-width: 52ch;
  color: var(--slumber-secondary);
  white-space: pre-line;
}
.slumber-sleep-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 48px;
  margin-top: 12px;
}
@media (max-height: 640px) {
  .slumber-sleep { gap: 10px; }
  .slumber-sleep-actions { gap: 24px; margin-top: 4px; }
}
"""


# Only the end button asks first: the other two are pressed during the night and
# are easy to undo.
_BUTTON_DEFAULTS: dict[str, dict[str, Any]] = {
    "wake_button": {"label": "I'm Awake", "style": "primary", "confirm": False},
    "sleep_button": {"label": "Going to Sleep", "style": "primary", "confirm": False},
    "end_button": {"label": "End Session", "style": "attention", "confirm": True},
}


class SleepSettings(BaseModel):
    """Settings for :class:`SleepActivity`."""

    title: str | Literal[False] = Field(
        default="Sleep well",
        description="Heading, or false (or empty) to leave it out.",
    )
    message: str | None = Field(
        default=None, description="Text under the heading. Unset shows none."
    )
    sleep_button: ButtonSettings = Field(
        default_factory=lambda: ButtonSettings(**_BUTTON_DEFAULTS["sleep_button"]),
        description="The main button while the participant is awake (the start): "
        f"emits {SLEEP_EVENT}. A label, or a mapping with label, style and confirm.",
    )
    wake_button: ButtonSettings = Field(
        default_factory=lambda: ButtonSettings(**_BUTTON_DEFAULTS["wake_button"]),
        description="The main button once the participant has marked themselves "
        f"asleep: emits {WAKE_EVENT}. A label, or a mapping with label, style and "
        "confirm.",
    )
    end_button: ButtonSettings = Field(
        default_factory=lambda: ButtonSettings(**_BUTTON_DEFAULTS["end_button"]),
        description=f"The button that emits {END_EVENT}: a label, or a mapping "
        "with label, style and confirm.",
    )

    @field_validator("wake_button", "sleep_button", "end_button", mode="before")
    @classmethod
    def _fill_button_defaults(cls, value: object, info: ValidationInfo) -> object:
        """Let a label or a partial mapping keep the button's default look."""
        if info.field_name is None:
            return value
        return merge_button_defaults(value, _BUTTON_DEFAULTS[info.field_name])


class SleepActivity(Activity):
    """Open-ended sleep step: the main button toggles between awake and asleep.

    Emits ``marked_awake`` / ``marked_asleep`` from the main button and
    ``end_sleep`` from the end button. Never completes.
    """

    settings_model = SleepSettings
    css = SLEEP_CSS

    def __init__(self, settings: SleepSettings | None = None) -> None:
        super().__init__(settings or SleepSettings())
        self._host: ActivityHost | None = None

    def mount(self, activity_host: ActivityHost) -> None:
        """Render the buttons under GUI; headless leaves emitting to the backend."""
        self._host = activity_host
        if activity_host.container is None:
            return

        from nicegui import ui

        settings = self.settings
        assert isinstance(settings, SleepSettings)

        with activity_host.container, ui.element("div").classes("slumber-sleep"):
            logo_mark(None, size="hub", fallback_icon="bedtime")
            if settings.title:
                ui.label(settings.title).classes("slumber-sleep-title").props(
                    'role="heading" aria-level="1"'
                )
            if settings.message:
                ui.label(settings.message).classes("slumber-sleep-message")
            with ui.element("div").classes("slumber-sleep-actions"):
                toggle_button(
                    settings.sleep_button,
                    settings.wake_button,
                    on_first=self._confirmed(settings.sleep_button, SLEEP_EVENT),
                    on_second=self._confirmed(settings.wake_button, WAKE_EVENT),
                    large=True,
                )
                action_button(
                    settings.end_button,
                    self._confirmed(settings.end_button, END_EVENT),
                    large=True,
                )

    def unmount(self) -> None:
        """Clear host reference."""
        self._host = None

    def _confirmed(self, button: ButtonSettings, event: str) -> Callable[[], Any]:
        """The button's action: emit *event*, after its question if it has one."""
        return with_confirmation(button, partial(self._emit, event))

    def _emit(self, event: str) -> None:
        if self._host is not None:
            self._host.emit(event)
