"""Built-in and discovered task plugins (resolved via slumber.tasks entry point)."""

from slumber.plugins.tasks.base import Task
from slumber.plugins.tasks.instruction import InstructionTask
from slumber.plugins.tasks.utils import build_task_from_settings

__all__ = ["InstructionTask", "Task", "build_task_from_settings"]
