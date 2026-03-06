"""Lightweight protocols and types for plugin contracts (units, tasks, UI backends)."""

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

import ezmsg.core as ez

from slumber.plugins.tasks.base import Task

if TYPE_CHECKING:
    from slumber.schemas.procedure import Procedure


# Unit plugins are ez.Unit subclasses
UnitClass = type[ez.Unit]


# Task plugins are Task subclasses
TaskClass = type[Task]


@runtime_checkable
class UIBackend(Protocol):
    """Protocol for UI backend plugins.

    The entry point resolves to a backend that can run procedures
    (e.g. headless logger, NiceGUI app).
    """

    def run_procedure(
        self,
        procedure: "Procedure",
        config: dict[str, Any],
    ) -> None:
        """Run a procedure: display/execute the given steps.

        Args:
            procedure: Procedure instance (steps with task_type and settings).
            config: UI backend config from study manifest.
        """
        ...
