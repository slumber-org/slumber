"""Run directory layout: resolving placeholders and creating run directories."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slumber.schemas.study import Study


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


VALID_RUN_LAYOUT_KEYS: frozenset[str] = frozenset(
    f.name for f in dataclasses.fields(RunContext)
)


def run_context_as_dict(context: RunContext) -> dict[str, str]:
    return dataclasses.asdict(context)


def format_with_run_context(template: str, context: RunContext, **extra) -> str:
    """Format a string template using run context placeholders.

    Args:
        template: String with placeholders (e.g. ``"{run_id}.log"``).
        context: Run context values for placeholder expansion.
        **extra: Additional placeholders to inject.

    Returns:
        Formatted string with placeholders expanded.
    """
    return template.format(**run_context_as_dict(context), **extra)


def resolve_path_template(
    template: str,
    context: RunContext,
    *,
    base_dir: Path | None = None,
    **extra: str,
) -> Path:
    """Resolve a formatted path template relative to a base directory.

    This expands placeholders in *template* using :class:`RunContext` (and any
    *extra* placeholders), then resolves the resulting path relative to
    *base_dir* when it is not already absolute.

    Args:
        template: Path template string (may be relative or absolute).
        context: Run context values for placeholder expansion.
        base_dir: Directory used to resolve relative paths. Optional if *template* is absolute.
        **extra: Additional placeholders to inject for formatting.

    Returns:
        Resolved path (absolute if template is absolute, otherwise under base_dir).
    """
    expanded = format_with_run_context(template, context, **extra)
    path = Path(expanded)
    if not path.is_absolute():
        if base_dir is None:
            raise ValueError("base_dir is required when template is relative")
        path = base_dir / path
    return path.resolve()


def resolve_run_dir(study: Study, context: RunContext, study_dir: Path) -> Path:
    """Resolve the run directory path for a given run context.

    Substitutes placeholders in study.runs.layout using the run context and
    joins the result under study_dir / study.runs.base_directory. Does not
    create the directory.

    Args:
        study: Loaded study manifest.
        context: Run-specific values for placeholder expansion.
        study_dir: Path to the study folder.

    Returns:
        Resolved (absolute) path to the run directory.
    """
    base_dir = study_dir / study.runs.base_directory
    return resolve_path_template(study.runs.layout, context, base_dir=base_dir)


def create_run_dir(study: Study, context: RunContext, study_dir: Path) -> Path:
    """Create the run directory for a given run context.

    Calls resolve_run_dir() and creates the directory (including any parents).

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
