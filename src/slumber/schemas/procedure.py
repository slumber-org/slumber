"""Procedure and task schemas (UI-agnostic, plugin-keyed)."""

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class Task(BaseModel):
    """UI-agnostic task specification keyed by plugin type.

    The `type` field is a string key resolved via the slumber.tasks entry
    point; each task plugin may validate `kwargs` when the config is loaded.
    """

    type: str = Field(
        ..., min_length=1, description="Task plugin key (e.g. 'instruction', 'survey')."
    )
    title: str = Field(..., min_length=1, description="Human-readable task title.")
    kwargs: dict[str, Any] = Field(
        default_factory=dict, description="Plugin-specific task options."
    )


class Procedure(BaseModel):
    """A sequence of tasks for one phase (e.g. pre_sleep, awakening).

    Procedures are study-specific and defined within each condition.
    """

    model_config = ConfigDict(populate_by_name=True)

    tasks: list[Task] = Field(..., min_length=1, description="Ordered list of tasks.")
    show_task_list: bool = Field(
        default=True,
        validation_alias=AliasChoices("show_task_list", "show_item_list"),
        description="Whether to show a list of tasks in the UI.",
    )
    allow_skip_tasks: bool = Field(
        default=False,
        description="When true, the current task can be skipped (marked done).",
    )

    @property
    def n_tasks(self) -> int:
        """Return the number of tasks in this procedure."""
        return len(self.tasks)
