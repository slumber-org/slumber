"""Run logging: apply study logging config when a run starts."""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from slumber.config.paths import expand_placeholders, resolve_path_string
from slumber.run.context import RunContext
from slumber.schemas.study import Study


def configure_run_logging(
    study: Study,
    context: RunContext,
    run_dir: Path,
    *,
    study_dir: Path,
    placeholders: dict[str, str],
) -> list[int]:
    """Add loguru handlers from ``study.logging`` for the current run.

    Iterates ``study.logging.handlers`` and calls ``logger.add(**kwargs)`` for
    each. For each handler:

    - Placeholders in the sink string are expanded using *placeholders*.
    - Relative sink paths resolve against the study root (authors typically
      use ``{run_dir}/…`` for run-scoped logs).
    - Absolute sinks stay absolute.
    - If the handler omits ``level``, ``study.logging.level`` is used.

    Args:
        study: Loaded study manifest with logging config.
        context: Run context (reserved for callers; placeholders carry values).
        run_dir: Path to the run directory (kept for API clarity / callers).
        study_dir: Study package root for relative path resolution.
        placeholders: Expanded placeholder map (includes ``run_dir``, ``run_id``).

    Returns:
        List of loguru handler IDs. Pass each to ``logger.remove()`` when the
        run ends.
    """
    del context, run_dir  # values are already in placeholders / study_dir
    handler_ids: list[int] = []

    for handler_config in study.logging.handlers:
        kwargs: dict = dict(handler_config)

        if "level" not in kwargs:
            kwargs["level"] = study.logging.level

        if "sink" in kwargs and isinstance(kwargs["sink"], str):
            expanded = expand_placeholders(kwargs["sink"], placeholders)
            kwargs["sink"] = Path(resolve_path_string(expanded, study_root=study_dir))

        handler_ids.append(logger.add(**kwargs))

    return handler_ids
