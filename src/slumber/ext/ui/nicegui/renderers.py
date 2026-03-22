"""Task renderer dispatch for the NiceGUI UI backend.

Maps ``task_type`` strings to render functions. In Stage 2, all task types
use the placeholder renderer. Stage 3 registers concrete renderers
(instruction, survey, device widgets, etc.).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from slumber.schemas.procedure import Step

RenderFunc = Callable[["Step", Any], None]

_RENDERERS: dict[str, RenderFunc] = {}


def register_renderer(task_type: str, renderer: RenderFunc) -> None:
    """Register a render function for a task type.

    Args:
        task_type: The task type key (matching ``Step.task_type``).
        renderer: A callable ``(step, container) -> None`` that renders
            the task UI inside *container*.
    """
    _RENDERERS[task_type] = renderer


def get_renderer(task_type: str) -> RenderFunc:
    """Return the renderer for *task_type*, falling back to the placeholder."""
    return _RENDERERS.get(task_type, render_placeholder)


def render_placeholder(step: "Step", container: Any) -> None:
    """Default placeholder renderer: show task type and settings.

    Args:
        step: The procedure step to render.
        container: A NiceGUI container element to render into.
    """
    from nicegui import ui

    from slumber.ext.ui.nicegui.theme import SURFACE, SURFACE_LIGHT, TEXT_SECONDARY

    with container:
        with ui.row().classes("items-center gap-2 mb-2"):
            ui.icon("widgets", size="sm").classes("text-[#7B7FC4]")
            ui.label(step.display_title).classes("text-h5 font-bold")
        if step.settings:
            with (
                ui.card()
                .classes(f"w-full bg-[{SURFACE}] border border-[{SURFACE_LIGHT}]")
                .props("flat bordered")
            ):
                ui.code(
                    json.dumps(step.settings, indent=2, default=str),
                    language="json",
                ).classes("w-full")
        ui.label("Widget not yet implemented").classes(
            f"text-body2 text-[{TEXT_SECONDARY}] italic mt-1"
        )
