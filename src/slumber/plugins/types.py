"""Lightweight protocols and types for plugin contracts (units, tasks, UI backends)."""

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from slumber.runtime.run import RunContext
    from slumber.schemas.condition import Condition
    from slumber.schemas.study import Study


@runtime_checkable
class UIBackend(Protocol):
    """Protocol for UI backend plugins.

    The entry point resolves to a backend that owns the full UI lifecycle
    for a condition (e.g. headless logger, NiceGUI app).
    """

    def run(
        self,
        study: "Study",
        condition: "Condition",
        context: "RunContext",
        config: dict[str, Any],
    ) -> None:
        """Run the full UI lifecycle for a condition.

        Args:
            study: Loaded study manifest.
            condition: The condition to run (procedures + DAG).
            context: Run context (study_id, participant_id, session_id, run_id).
            config: UI backend config from study manifest (``study.ui.config``).
        """
        ...
