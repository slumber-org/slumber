"""Run logging: apply study logging config when a run starts."""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from slumber.runtime.run import run_context_as_dict, RunContext
from slumber.schemas.study import Study


def configure_run_logging(
    study: Study,
    context: RunContext,
    run_dir: Path,
) -> list[int]:
    """Add loguru handlers from study.logging for the current run.

    Iterates study.logging.handlers and calls logger.add(**kwargs) for each.
    For each handler:

    - Placeholders (e.g. ``{run_id}``) in the sink string are expanded using
      the run context. ``{run_dir}`` is also available as the string form of
      run_dir.
    - If the expanded sink path is relative, it is resolved relative to run_dir.
    - If the handler does not include a ``level`` key, study.logging.level is used.

    Args:
        study: Loaded study manifest with logging config.
        context: Run-specific values for placeholder expansion in sink paths.
        run_dir: Path to the run directory (used for relative sink paths).

    Returns:
        List of loguru handler IDs. Pass each to ``logger.remove()`` to
        deregister handlers when the run ends.
    """
    handler_ids: list[int] = []
    ctx_dict = run_context_as_dict(context)

    for handler_config in study.logging.handlers:
        kwargs: dict = dict(handler_config)

        if "level" not in kwargs:
            kwargs["level"] = study.logging.level

        if "sink" in kwargs and isinstance(kwargs["sink"], str):
            sink_str = kwargs["sink"].format(**ctx_dict, run_dir=str(run_dir))
            sink_path = Path(sink_str)
            if not sink_path.is_absolute():
                sink_path = run_dir / sink_path
            kwargs["sink"] = sink_path

        handler_ids.append(logger.add(**kwargs))

    return handler_ids
