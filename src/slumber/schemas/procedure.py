"""Procedure and step schemas (UI-agnostic, plugin-keyed).

Component -> Unit (DAG); Step -> Task (procedure). A Step is the spec
resolved via slumber.tasks to a Task (plugin) class.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Step(BaseModel):
    """Procedure step specification (like Component: plugin key + settings).

    The `task_type` field is a string key resolved via the slumber.tasks
    entry point; the plugin is a Task class (in slumber.plugins.tasks.base)
    that validates settings.
    """

    model_config = ConfigDict(populate_by_name=True)

    task_type: str = Field(
        ...,
        min_length=1,
        alias="task",
        description="Task plugin key.",
    )
    settings: dict[str, Any] | None = Field(
        default=None,
        description="Plugin-specific step settings.",
    )


class Procedure(BaseModel):
    """A sequence of steps for one phase (e.g. pre_sleep, awakening).

    Procedures are study-specific and defined within each condition.
    """

    steps: list[Step] = Field(..., min_length=1, description="Ordered list of steps.")

    @property
    def n_steps(self) -> int:
        """Return the number of steps in this procedure."""
        return len(self.steps)
