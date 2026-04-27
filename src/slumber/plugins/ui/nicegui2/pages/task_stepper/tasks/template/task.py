"""Task Template - Quick Guide for Designing Tasks.

QUICK START:
1. Copy this folder to a new task (e.g., `my_task/`)
2. Edit the task logic below
3. Add your task to the task_stepper in condition.yaml

TASK STRUCTURE:
- Tasks are rendered within the task_stepper page
- Each task has a render() function that takes state, on_complete, task_cfg, task_index
- Call on_complete() when the task is finished
- Use task_cfg for configuration from YAML
- Optional: Add a cleanup() function to reset task state when page is reloaded

COMMON TASK PATTERNS:

1. DISPLAY CONTENT:
   with ui.card().classes("w-full bg-surface border border-secondary p-6"):
       ui.label("Task content").classes("text-h6")
       ui.label("Description").classes("text-body1")
   on_complete()

2. FORM INPUT:
   with ui.card().classes("w-full bg-surface border border-secondary p-6"):
       ui.input("Enter value").classes("w-full")
       ui.button("Submit", on_click=lambda: on_complete())

3. MARKDOWN CONTENT:
   from slumber.plugins.ui.nicegui2.utils import load_markdown_content
   _, _, full_md = load_markdown_content(task_cfg, Path(__file__).parent, state.study_assets_dir, parse=False)
   ui.markdown(full_md).classes("w-full")

CREATING A CUSTOM TASK SETTINGS:
1. Add a Pydantic model for your settings (e.g., `class MyTaskSettings`)
2. Include configuration fields from YAML settings
3. Use task_cfg.field_name to access values

Example settings class:
    class MyTaskSettings(BaseModel):
        title: str = "My Task"
        show_button: bool = True
        button_text: str = "Continue"

See other tasks (instructions, survey, audio_level_calibration) for examples.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from nicegui import ui

from slumber.plugins.ui.nicegui2.pages.task_stepper.tasks.template.settings import TemplateSettings

if TYPE_CHECKING:
    from slumber.plugins.ui.nicegui2.state import PageGraphState


def render(
    state: PageGraphState,
    on_complete: callable,
    task_cfg: TemplateSettings | None = None,
    task_index: int = 0,
) -> None:
    """Render the template task.

    Args:
        state: App state
        on_complete: Callback to call when task is completed
        task_cfg: Task configuration
        task_index: Index of this task within the page's task list.
    """
    if task_cfg is None:
        task_cfg = TemplateSettings()

    # ============================================================
    # YOUR TASK LAYOUT STARTS HERE
    # ============================================================

    with ui.card().classes("w-full bg-surface border border-secondary p-6"):
        # Task title
        ui.label(task_cfg.title).classes("text-h6 font-bold text-primary mb-4")

        # Task description
        ui.label(task_cfg.description).classes("text-body1 text-secondary mb-4")

        # Example: Add your task content here
        with ui.column().classes("gap-4"):
            ui.label("Your task content goes here").classes("text-body1 text-primary")
            
            # Example input
            ui.input("Enter value").classes("w-full text-primary")

        # Completion button
        if task_cfg.show_button:
            ui.button(
                task_cfg.button_text,
                icon="check",
                on_click=on_complete,
            ).props("rounded unelevated color=positive text-color=primary").classes("mt-4")
        else:
            # Auto-complete if no button
            on_complete()

    # ============================================================
    # YOUR TASK LAYOUT ENDS HERE
    # ============================================================


def cleanup(instance_id: str) -> str:
    """Optional cleanup function to reset task state when page is reloaded.

    This is called when the task stepper page is navigated to from another page.
    Use this to clear any JavaScript globals, timers, or other state that should
    be reset when the task is reloaded.

    Args:
        instance_id: The unique instance ID for this task (e.g., 'survey_page_0').

    Returns:
        JavaScript code to clean up task-specific state, or empty string if no cleanup needed.

    Example for tasks with JavaScript globals:
        return f"""
            delete window.myTaskState_{instance_id};
            delete window.myTaskData_{instance_id};
        """

    For tasks without JavaScript state, return empty string or omit this function entirely.
    """
    # No cleanup needed for this template task
    return ""
