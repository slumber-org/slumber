"""Instruction activity: show markdown/text and complete on mount."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from slumber.ui.activities.base import Activity, ActivityHost
from slumber.ui.theme import SECONDARY, TYPE_SCALE


class InstructionSettings(BaseModel):
    """Settings for :class:`InstructionActivity`."""

    content: str = Field(
        default="",
        description="Inline text/markdown or a resolved path to a content file.",
    )


def load_instruction_content(content: str) -> str:
    """Return file contents when *content* is an existing path, else the string."""
    if not content:
        return ""
    path = Path(content)
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return content


class InstructionActivity(Activity):
    """Render instruction content; calls ``host.complete()`` on mount."""

    settings_model = InstructionSettings

    def mount(self, activity_host: ActivityHost) -> None:
        """Render when a GUI container is present; always complete as a step."""
        settings = self.settings
        assert isinstance(settings, InstructionSettings)
        body = load_instruction_content(settings.content)

        if activity_host.container is not None:
            from nicegui import ui

            with activity_host.container:
                if body.strip():
                    ui.markdown(body).classes(TYPE_SCALE["body"])
                else:
                    ui.label("No instruction content.").classes(
                        f"{TYPE_SCALE['body']} text-[{SECONDARY}] italic"
                    )

        activity_host.complete()
