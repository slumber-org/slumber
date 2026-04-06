"""Headless UI backend: no display, logs procedures and tasks (for testing/CI)."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from loguru import logger
from pydantic import BaseModel

from slumber.plugins.ui.base import UIBackend

if TYPE_CHECKING:
    from slumber.runtime.run import RunContext
    from slumber.schemas.condition import Condition
    from slumber.schemas.study import Study


class HeadlessUIBackend(UIBackend):
    """UI backend that does not display a window; logs procedures and tasks.

    Entry-point key: ``headless``. Ignores triggers and guards — runs all
    procedures in the condition sequentially. Used when no GUI is needed
    (e.g. validate, automated runs, CI).
    """

    ui_settings_model: ClassVar[type[BaseModel] | None] = None

    def run(
        self,
        study: "Study",
        condition: "Condition",
        context: "RunContext",
    ) -> None:
        """Log all procedures and their steps; no user interaction."""
        logger.info(
            "headless: condition={!r} ({} procedure(s))",
            condition.name,
            len(condition.procedures),
        )
        for proc_name, procedure in condition.procedures.items():
            logger.info("  procedure {!r} ({} step(s))", proc_name, procedure.n_steps)
            for i, step in enumerate(procedure.steps):
                logger.debug("    step {}: task_type={!r}", i + 1, step.task_type)
