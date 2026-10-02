"""Built-in activity plugins."""

from slumber.ui.activities.base import Activity, ActivityHost
from slumber.ui.activities.instruction import (
    InstructionActivity,
    InstructionSettings,
    load_instruction_content,
)
from slumber.ui.activities.sleep import SleepActivity, SleepSettings

__all__ = [
    "Activity",
    "ActivityHost",
    "InstructionActivity",
    "InstructionSettings",
    "SleepActivity",
    "SleepSettings",
    "load_instruction_content",
]
