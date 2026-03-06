from pydantic import ConfigDict, Field

from slumber.plugins.tasks.base import Task


class InstructionTask(Task):
    """Task model for displaying instructions to the participant.

    The instruction body is displayed to the participant.
    """

    model_config = ConfigDict(extra="forbid")

    text: str | None = Field(default=None, description="Instruction body (plain text).")
    content: str | None = Field(
        default=None, description="Instruction body (alternative to text)."
    )
