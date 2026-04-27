"""Instructions task - displays markdown content with a completion button."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from nicegui import ui

from slumber.plugins.ui.nicegui2.utils import load_markdown_content

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui2.state import PageGraphState


@dataclass
class InstructionsConfig:
    """Configuration for the instructions task."""

    markdown_path: str | None = None
    show_complete_button: bool = False
    complete_button_text: str = "I Understand"
    complete_button_icon: str = "check"


def render(
    state: PageGraphState,
    on_complete: callable,
    task_cfg: InstructionsConfig | None = None,
    task_index: int = 0,
) -> None:
    """Render the instructions task.

    Args:
        state: App state
        on_complete: Callback to call when task is completed
        task_cfg: Task configuration
        task_index: Index of this task within the page's task list.
    """
    if task_cfg is None:
        task_cfg = InstructionsConfig()

    # Show error if no markdown file specified
    if task_cfg.markdown_path is None:
        ui.label("No markdown file specified in task settings").classes("text-negative")
        on_complete()
        return

    # Load markdown content using utility (handles study assets → plugin fallback)
    _, _, full_md = load_markdown_content(
        task_cfg,
        Path(__file__).parent,
        state.study_assets_dir,
        parse=False,
    )

    # Render all content within a card with constrained height
    with (
        ui.card()
        .classes("w-full bg-surface border border-secondary p-6 overflow-y-auto")
        .style("max-height: 60vh;")
    ):
        ui.markdown(full_md).classes("w-full text-body1 text-primary overflow-x-hidden")

    # Completion button (optional)
    if task_cfg.show_complete_button:
        ui.button(
            task_cfg.complete_button_text,
            icon=task_cfg.complete_button_icon,
            on_click=on_complete,
        ).props("size=lg rounded unelevated color=positive text-color=primary").classes(
            "mt-6"
        )
    else:
        # Auto-complete when button is disabled
        on_complete()
