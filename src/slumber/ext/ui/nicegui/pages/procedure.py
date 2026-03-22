"""Procedure runner page: step execution with sidebar and navigation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nicegui import ui

from slumber.ext.ui.nicegui.renderers import get_renderer
from slumber.ext.ui.nicegui.theme import (
    ACCENT_LAVENDER,
    POSITIVE,
    PRIMARY,
    SURFACE,
    SURFACE_LIGHT,
    TEXT_SECONDARY,
)

if TYPE_CHECKING:
    from slumber.ext.ui.nicegui.state import AppState


def render_procedure_page(state: AppState, refresh: object) -> None:
    """Render the procedure runner page.

    Args:
        state: App state (must have active_procedures set).
        refresh: Callable to refresh the UI after state changes.
    """
    cfg = state.ui_config.procedure
    procedure = state.current_procedure
    proc_title = state.current_procedure_title
    step = state.current_step
    step_num = state.current_step_index + 1
    total_steps = procedure.n_steps
    is_completed = state.current_step_index in state.completed_steps

    with ui.column().classes("w-full h-screen"):
        with ui.row().classes(
            f"w-full items-center justify-between px-6 py-3 bg-[{SURFACE}] "
            f"border-b border-[{SURFACE_LIGHT}]"
        ):
            with ui.row().classes("items-center gap-3"):
                ui.icon("assignment", size="sm").classes(f"text-[{ACCENT_LAVENDER}]")
                ui.label(proc_title).classes("text-h6 font-bold")
            with ui.row().classes("items-center gap-4"):
                ui.label(f"Step {step_num} of {total_steps}").classes(
                    f"text-body2 text-[{TEXT_SECONDARY}]"
                )
                with ui.row().classes("gap-1"):
                    for i in range(total_steps):
                        done = i in state.completed_steps
                        current = i == state.current_step_index
                        color = (
                            POSITIVE
                            if done
                            else (PRIMARY if current else SURFACE_LIGHT)
                        )
                        ui.element("div").style(
                            f"width: 24px; height: 4px; border-radius: 2px; "
                            f"background-color: {color}; "
                            f"transition: background-color 0.3s"
                        )

        with ui.row().classes("w-full flex-grow no-wrap"):
            content_container = ui.column().classes("flex-grow p-6")
            get_renderer(step.task_type)(step, content_container)

            if procedure.show_task_list:
                with ui.column().classes(
                    f"w-64 p-4 bg-[{SURFACE}] border-l border-[{SURFACE_LIGHT}]"
                ):
                    ui.label(cfg.steps_label).classes(
                        f"text-overline text-[{TEXT_SECONDARY}] mb-3"
                    )
                    for i, s in enumerate(procedure.steps):
                        is_current = i == state.current_step_index
                        is_done = i in state.completed_steps
                        icon = (
                            "check_circle"
                            if is_done
                            else ("play_circle" if is_current else "circle")
                        )
                        icon_color = (
                            POSITIVE
                            if is_done
                            else (PRIMARY if is_current else SURFACE_LIGHT)
                        )
                        text_cls = (
                            "font-bold" if is_current else f"text-[{TEXT_SECONDARY}]"
                        )
                        with ui.row().classes("items-center gap-2 py-1"):
                            ui.icon(icon, size="xs").style(f"color: {icon_color}")
                            ui.label(s.display_title).classes(f"text-body2 {text_cls}")

        with ui.row().classes(
            f"w-full items-center justify-center gap-3 px-6 py-3 "
            f"bg-[{SURFACE}] border-t border-[{SURFACE_LIGHT}]"
        ):
            ui.button(
                cfg.previous_button,
                icon="arrow_back",
                on_click=lambda: (_prev(state), refresh()),  # type: ignore[operator]
            ).props("flat rounded").set_enabled(state.current_step_index > 0)

            can_advance = is_completed or procedure.allow_skip
            if not state.is_last_step:
                ui.button(
                    cfg.next_button,
                    icon="arrow_forward",
                    on_click=lambda: (_next(state), refresh()),  # type: ignore[operator]
                ).props("rounded unelevated color=primary").set_enabled(can_advance)
            else:
                all_done = state.all_steps_completed or procedure.allow_skip
                ui.button(
                    cfg.complete_button,
                    icon="check",
                    on_click=lambda: (_complete(state), refresh()),  # type: ignore[operator]
                ).props("rounded unelevated color=positive").set_enabled(all_done)

            if not is_completed:
                ui.button(
                    cfg.mark_done_button,
                    icon="done",
                    on_click=lambda: (state.complete_current_step(), refresh()),  # type: ignore[operator]
                ).props("flat rounded color=accent")


def _prev(state: AppState) -> None:
    state.prev_step()


def _next(state: AppState) -> None:
    state.complete_current_step()
    if state.is_last_step:
        state.advance_to_next_procedure()
    else:
        state.current_step_index += 1


def _complete(state: AppState) -> None:
    state.complete_current_step()
    state.advance_to_next_procedure()
