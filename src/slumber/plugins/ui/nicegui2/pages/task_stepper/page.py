"""Task Stepper page - shows tasks in sequence with progress tracking."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Callable

from loguru import logger
from nicegui import ui

from slumber.plugins.ui.nicegui2.shell.shell import render_shell
from slumber.plugins.ui.nicegui2.shell.settings import ShellSettings
from slumber.plugins.ui.nicegui2.pages.task_stepper.settings import TaskStepperSettings
from slumber.plugins.ui.nicegui2.utils import load_config_class

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui2.state import PageGraphState


def cleanup_tasks(state: PageGraphState, page_cfg: TaskStepperSettings) -> None:
    """Call cleanup on all tasks in the current page.

    This is called when the task stepper page is reloaded (navigated to from another page)
    to ensure each task can clean up its specific state (e.g., JavaScript globals).

    Args:
        state: App state
        page_cfg: Task stepper configuration
    """
    page_id = state.get_current_page()
    for task_index, task_name in enumerate(page_cfg.tasks):
        try:
            module = importlib.import_module(
                f"slumber.plugins.ui.nicegui2.pages.task_stepper.tasks.{task_name}.task"
            )
            if hasattr(module, "cleanup"):
                # Generate instance_id using the task name (not hardcoded "survey")
                instance_id = f"{task_name}_{page_id}_{task_index}".replace("-", "_")
                cleanup_js = module.cleanup(instance_id)
                ui.run_javascript(cleanup_js)
        except Exception as e:
            # If cleanup fails, log but don't block page render
            logger.warning("Failed to cleanup task {}: {}", task_name, e)


def render(
    state: PageGraphState,
    refresh: Callable[[], None],
    shell_cfg: ShellSettings | None = None,
    page_cfg: TaskStepperSettings | None = None,
) -> None:
    """Render task stepper page with sequential tasks."""
    if shell_cfg is None:
        shell_cfg = ShellSettings()
    if page_cfg is None:
        page_cfg = TaskStepperSettings()

    # Clean up all task state when page is reloaded (navigated to from another page)
    cleanup_tasks(state, page_cfg)

    # Track state - use page_data to persist across refreshes but clear on navigation
    page_id = state.get_current_page()
    completion_key = f"{page_id}_completed_tasks"
    accessible_key = f"{page_id}_accessible_tasks"

    # Initialize or retrieve state from page_data
    if state.get_page_data(completion_key) is None:
        state.set_page_data(completion_key, set())
    if state.get_page_data(accessible_key) is None:
        state.set_page_data(accessible_key, {0})

    completed_tasks = [state.get_page_data(completion_key)]
    accessible_tasks = [state.get_page_data(accessible_key)]
    current_index = [0]  # Always start at first task when page renders

    def is_completed(index: int) -> bool:
        return index in completed_tasks[0]

    def is_accessible(index: int) -> bool:
        return index in accessible_tasks[0]

    def safe_refresh() -> None:
        """Safely refresh content only if client exists."""
        if ui.context.client is not None:
            content.refresh()

    def mark_completed(index: int) -> None:
        # Only refresh if task is newly completed (avoid infinite loop)
        is_newly_completed = index not in completed_tasks[0]
        completed_tasks[0].add(index)
        # Unlock next task when current is completed
        next_index = index + 1
        if next_index < len(page_cfg.tasks):
            accessible_tasks[0].add(next_index)
        if is_newly_completed:
            safe_refresh()

    def go_next() -> None:
        is_last = current_index[0] == len(page_cfg.tasks) - 1
        if is_last:
            state.fire_routing_event("finish")
            return
        if current_index[0] < len(page_cfg.tasks) - 1:
            current_index[0] += 1
            safe_refresh()

    def go_prev() -> None:
        if current_index[0] > 0:
            current_index[0] -= 1
            safe_refresh()

    def can_navigate_to(index: int) -> bool:
        """Check if user can navigate to a specific task.

        Allowed: accessible tasks (completed, current, or unlocked).
        Not allowed: future tasks that haven't been unlocked.
        """
        return is_accessible(index)

    def navigate_to(index: int) -> None:
        """Navigate to a specific task if allowed."""
        if can_navigate_to(index):
            current_index[0] = index
            safe_refresh()

    def render_task_list() -> None:
        """Render the progress list on the right."""
        with (
            ui.column()
            .classes("w-64 h-full p-4 gap-2 bg-surface border-l border-secondary")
            .style("min-width: 250px")
        ):
            ui.label("Progress").classes("text-h6 font-bold text-primary mb-4")

            for i, task_name in enumerate(page_cfg.tasks):
                is_current = i == current_index[0]
                is_done = is_completed(i)

                # Icon and color based on completion status
                if is_done:
                    icon = "check_circle"
                    color = page_cfg.completed_color
                elif is_current:
                    icon = "radio_button_checked"
                    color = page_cfg.current_color
                else:
                    icon = "radio_button_unchecked"
                    color = page_cfg.pending_color

                # Text style: always secondary color, bold if current
                text_class = f"text-secondary {'font-bold' if is_current else ''}"

                # Determine accessibility and clickability
                task_is_accessible = is_accessible(i)
                cursor_style = (
                    "cursor: pointer"
                    if task_is_accessible
                    else "cursor: not-allowed opacity-50"
                )

                # Task item
                with (
                    ui.row()
                    .classes(
                        f"items-center gap-3 p-2 rounded w-full {'bg-surface' if is_current else ''}"
                    )
                    .style(cursor_style)
                    .on(
                        "click",
                        lambda idx=i: navigate_to(idx) if is_accessible(idx) else None,
                    )
                ):
                    ui.icon(icon, size="24px").classes(f"text-{color}")
                    ui.label(f"{i + 1}. {task_name.replace('_', ' ').title()}").classes(
                        text_class
                    )

    def render_current_task() -> None:
        """Render the current task content."""
        task_name = page_cfg.tasks[current_index[0]]

        try:
            # Import the task module
            module = importlib.import_module(
                f"slumber.plugins.ui.nicegui2.pages.task_stepper.tasks.{task_name}.task"
            )

            if hasattr(module, "render"):
                # Get config class using naming convention: {TaskName}Config
                config_class = load_config_class(module, task_name)

                # Get task settings from page graph if available
                task_settings = {}
                if state.page_graph and state.current_page_id in state.page_graph.pages:
                    page = state.page_graph.pages[state.current_page_id]
                    if hasattr(page, "tasks") and current_index[0] < len(page.tasks):
                        task_step = page.tasks[current_index[0]]
                        if hasattr(task_step, "settings") and task_step.settings:
                            task_settings = task_step.settings

                # Create config with settings applied
                task_config = None
                if config_class:
                    if task_settings:
                        task_config = config_class(**task_settings)
                    else:
                        task_config = config_class()

                # Render the task with completion callback and task index
                module.render(
                    state,
                    lambda: mark_completed(current_index[0]),
                    task_config,
                    current_index[0],
                )
            else:
                ui.label(f"Task '{task_name}' has no render() function").classes(
                    "text-negative"
                )
        except Exception as e:
            ui.label(f"Error loading task '{task_name}': {e}").classes("text-negative")

    def render_navigation() -> None:
        """Render navigation buttons at bottom."""
        is_last = current_index[0] == len(page_cfg.tasks) - 1
        is_first = current_index[0] == 0
        can_proceed = is_completed(current_index[0])

        with ui.row().classes(
            "w-full items-center justify-between px-6 py-4 bg-surface border-t border-secondary"
        ):
            # Previous button
            prev_btn = (
                ui.button(
                    page_cfg.prev_button_text,
                    icon="arrow_back",
                    on_click=go_prev,
                )
                .props("unelevated rounded stack color=secondary text-color=primary")
                .classes("w-32")
            )
            if is_first:
                prev_btn.props("disable")

            # Progress indicator
            ui.label(f"Step {current_index[0] + 1} of {len(page_cfg.tasks)}").classes(
                "text-body2 text-secondary"
            )

            # Next/Finish button (only enabled if current task completed)
            next_text = (
                page_cfg.finish_button_text if is_last else page_cfg.next_button_text
            )
            next_icon = "check" if is_last else "arrow_forward"
            next_btn = (
                ui.button(
                    next_text,
                    icon=next_icon,
                    on_click=go_next,
                )
                .props(
                    f"unelevated rounded stack color={'secondary' if can_proceed else 'surface'} text-color=primary"
                )
                .classes("w-32")
            )
            if not can_proceed:
                next_btn.props("disable")

    @ui.refreshable
    def content() -> None:
        with (
            ui.row()
            .classes("w-full h-full")
            .style("flex-wrap: nowrap; align-items: stretch;")
        ):
            # Left side - task content area (scrollable) + fixed navigation bar
            with ui.column().classes("flex-grow h-full").style("min-width: 0;"):
                # Content area - let individual tasks handle their own scrolling
                with (
                    ui.column()
                    .classes("w-full h-full p-6 pb-20")
                    .style("min-width: 0;")
                ):
                    # Task title
                    ui.label(
                        page_cfg.tasks[current_index[0]].replace("_", " ").title()
                    ).classes("text-h4 font-bold text-primary mb-4")
                    render_current_task()

            # Right side - progress list
            render_task_list()

            # Navigation bar at bottom - outside columns so it spans full width
            with ui.row().classes("w-full fixed bottom-0 left-0 z-10"):
                render_navigation()

    render_shell(state, refresh, shell_cfg, content)  # type: ignore[arg-type]
