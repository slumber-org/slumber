"""Run orchestration: create run directory, apply logging, execute procedures."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from slumber.config.plugins import resolve_ui_backend_from_ui
from slumber.plugins import get_registry
from slumber.runtime.logging import configure_run_logging
from slumber.runtime.run import RunContext, create_run_dir

if TYPE_CHECKING:
    from slumber.plugins.registry import PluginRegistry
    from slumber.schemas.study import Study

_RUN_METADATA_FILE = "run.json"


def _write_run_metadata(
    run_dir: Path,
    context: RunContext,
    condition_name: str,
    started_at: datetime,
) -> None:
    """Write run.json with run context and start timestamp."""
    metadata = {
        "study_id": context.study_id,
        "condition_name": condition_name,
        "participant_id": context.participant_id,
        "session_id": context.session_id,
        "run_id": context.run_id,
        "started_at": started_at.isoformat(),
    }
    (run_dir / _RUN_METADATA_FILE).write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )


def run_study(
    study: Study,
    condition_name: str,
    context: RunContext,
    study_dir: Path,
    registry: PluginRegistry | None = None,
) -> Path:
    """Run a study condition: set up the run directory and execute all procedures.

    Creates the run directory, writes run metadata, configures run logging,
    resolves the UI backend, and runs each procedure in the condition in order.
    Logging handlers are removed when the run finishes (even on error).

    Note: DAG startup (data acquisition) is not yet wired here; it will be
    added in the extension layer once ezmsg integration is complete.

    Args:
        study: Loaded study manifest (with conditions).
        condition_name: Name of the condition to run (must exist in the study).
        context: Run context (participant_id, session_id, run_id, etc.).
        study_dir: Absolute path to the study folder.
        registry: Plugin registry; uses the default registry when None.

    Returns:
        Path to the created run directory.

    Raises:
        ValueError: If condition_name is not found in the study, or plugin
            resolution fails.
    """
    reg = registry if registry is not None else get_registry()

    conditions_by_name = {c.name: c for c in study.conditions}
    if condition_name not in conditions_by_name:
        available = sorted(conditions_by_name)
        raise ValueError(
            f"Condition {condition_name!r} not found in study {study.study_id!r}. "
            f"Available: {available}."
        )
    condition = conditions_by_name[condition_name]

    run_dir = create_run_dir(study, context, study_dir)
    started_at = datetime.now(tz=timezone.utc)
    _write_run_metadata(run_dir, context, condition_name, started_at)

    handler_ids = configure_run_logging(study, context, run_dir)
    try:
        logger.info(
            "Run started  study={!r} condition={!r} run_id={!r}",
            study.study_id,
            condition_name,
            context.run_id,
        )

        ui_backend = resolve_ui_backend_from_ui(study.ui, reg)
        ui_backend.run(study, condition, context)

        logger.info("Run completed  run_id={!r}  dir={}", context.run_id, run_dir)
    finally:
        for hid in handler_ids:
            logger.remove(hid)

    return run_dir
