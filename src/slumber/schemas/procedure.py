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
    title: str | None = Field(
        default=None,
        description="Display title for this step. Defaults to task_type titlecased.",
    )
    settings: dict[str, Any] | None = Field(
        default=None,
        description="Plugin-specific step settings.",
    )

    @property
    def display_title(self) -> str:
        """Return the title to show in the UI."""
        return self.title if self.title else self.task_type.replace("_", " ").title()


class Procedure(BaseModel):
    """A sequence of steps triggered by a session event.

    Procedures are defined within each condition. Each procedure declares
    a ``trigger`` event and an optional ``when`` guard that determines
    whether the procedure should run when that event fires.
    """

    steps: list[Step] = Field(..., min_length=1, description="Ordered list of steps.")
    title: str | None = Field(
        default=None,
        description="Display title for this procedure. Defaults to the procedure key titlecased.",
    )
    trigger: str | None = Field(
        default=None,
        description="Session event that starts this procedure (e.g. session_start, wake_up).",
    )
    when: dict[str, Any] | str | None = Field(
        default=None,
        description=(
            "Guard condition. Dict for declarative checks against SessionState "
            "(e.g. {awakening_count: 1} or {awakening_count: {gt: 1}}). "
            "String for a Python callable path "
            "(e.g. 'my_study.guards:is_rem_awakening') that receives SessionState "
            "and returns bool. None means always run on trigger."
        ),
    )
    show_task_list: bool = Field(
        default=True,
        description="Show step sidebar in UI.",
    )
    allow_skip: bool = Field(
        default=False,
        description="Allow skipping incomplete steps.",
    )

    @property
    def n_steps(self) -> int:
        """Return the number of steps in this procedure."""
        return len(self.steps)
