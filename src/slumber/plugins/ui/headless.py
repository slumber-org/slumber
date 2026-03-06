"""Headless UI backend: no display, logs procedure and tasks (for testing/CI)."""

from typing import Any

from loguru import logger

from slumber.schemas.procedure import Procedure


class HeadlessUIBackend:
    """UI backend that does not display a window; logs procedure and tasks.

    Entry-point key: ``headless``. Used when no GUI is needed (e.g. validate,
    automated runs, or when the UI backend is not yet implemented).
    """

    def run_procedure(
        self,
        procedure: Procedure,
        config: dict[str, Any],
    ) -> None:
        """Log the procedure step count; no user interaction."""
        logger.info(
            "headless UI running procedure with {} step(s)",
            procedure.n_steps,
        )
        for i, step in enumerate(procedure.steps):
            logger.debug("  step {}: task_type={!r}", i + 1, step.task_type)
