"""Built-in and discovered task plugins (resolved via slumber.tasks entry point)."""

from slumber.plugins.tasks.base import Task
from slumber.plugins.tasks.instruction import InstructionTask

__all__ = ["InstructionTask", "Task"]
