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
    layout = study.runs.layout.format(**run_context_as_dict(context))
    return (study_dir / study.runs.base_directory / layout).resolve()


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
