"""Run directory layout: resolving placeholders and creating run directories."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING

from slumber.schemas.study import VALID_RUN_LAYOUT_KEYS

if TYPE_CHECKING:
    from slumber.schemas.study import Study

__all__ = [
    "VALID_RUN_LAYOUT_KEYS",
    "RunContext",
    "create_run_dir",
    "format_with_run_context",
    "resolve_run_dir",
    "run_context_as_dict",
]


@dataclasses.dataclass
class RunContext:
    """Values used to expand placeholders in run layout and log sink paths.

    Fields ``participant_id`` and ``session_id`` are optional.
    """

    study_id: str
    run_id: str
    condition_id: str
    participant_id: str | None = None
    session_id: str | None = None


def run_context_as_dict(context: RunContext) -> dict[str, str | None]:
    """Return run context fields as a plain dict."""
    return dataclasses.asdict(context)


def format_with_run_context(template: str, context: RunContext, **extra: object) -> str:
    """Format a string template using run context placeholders.

    Args:
        template: String with placeholders (e.g. ``"{run_id}.log"``).
        context: Run context values for placeholder expansion.
        **extra: Additional placeholders to inject.

    Returns:
        Formatted string with placeholders expanded.
    """
    return template.format(**run_context_as_dict(context), **extra)


def resolve_run_dir(study: Study, context: RunContext, study_dir: Path) -> Path:
    """Resolve the run directory path for a given run context.

    Substitutes placeholders in ``study.runs.layout`` using the run context and
    joins the result under ``study_dir / study.runs.directory``. Does not
    create the directory.

    Args:
        study: Loaded study manifest.
        context: Run-specific values for placeholder expansion.
        study_dir: Path to the study folder.

    Returns:
        Resolved (absolute) path to the run directory.
    """
    expanded = format_with_run_context(study.runs.layout, context)
    path = Path(expanded)
    if not path.is_absolute():
        path = study_dir / study.runs.directory / path
    return path.resolve()


def create_run_dir(study: Study, context: RunContext, study_dir: Path) -> Path:
    """Create the run directory for a given run context.

    Calls :func:`resolve_run_dir` and creates the directory (including parents).

    Args:
        study: Loaded study manifest.
        context: Run-specific values for placeholder expansion.
        study_dir: Path to the study folder.

    Returns:
        Path to the created run directory.
    """
    run_dir = resolve_run_dir(study, context, study_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir
