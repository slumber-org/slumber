"""Study-related CLI commands."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import typer
from pydantic import ValidationError

from slumber.config import (
    init_study,
    load_study,
    resolve_study_dir,
    validate_study_plugins,
)
from slumber.constants import PARTICIPANT_ID_ENV, STUDY_DIR_ENV
from slumber.run import RunContext, run_study
from slumber.schemas.plugin import PluginSpec
from slumber.schemas.study import Study
from slumber.utils.errors import format_validation_error

DEFAULT_STUDY_ID = "new_study"
DEFAULT_BASE_DIR = Path(".")
DEFAULT_STUDY_NAME = "New Study"
_UI_CHOICES = ("gui", "headless")

study_app = typer.Typer(help="Study folder and manifest commands.")


def _local_run_context(study: Study, condition_name: str) -> RunContext:
    """Build :class:`RunContext` for a local (file-based) run."""
    return RunContext(
        study_id=study.study_id,
        run_id=str(uuid.uuid4()),
        condition_id=condition_name,
        participant_id=os.environ.get(PARTICIPANT_ID_ENV),
    )


def _apply_ui_override(study: Study, ui_type: str | None) -> None:
    """Replace ``study.ui.type`` when the CLI requests a UI override.

    Headless forbids GUI-only settings (frame, layouts, port, …), so switching
    to headless clears ``settings``. Switching to gui keeps existing settings.
    """
    if ui_type is None:
        return
    if ui_type not in _UI_CHOICES:
        typer.echo(
            f"Invalid --ui {ui_type!r}. Choose one of: {', '.join(_UI_CHOICES)}.",
            err=True,
        )
        raise typer.Exit(1)
    settings = {} if ui_type == "headless" else dict(study.ui.settings)
    study.ui = PluginSpec(type=ui_type, settings=settings)


@study_app.command("init")
def initialize_study(
    base_dir: Path = typer.Option(
        DEFAULT_BASE_DIR,
        "--base-dir",
        "-b",
        show_default=True,
        file_okay=False,
        writable=True,
        resolve_path=True,
        prompt=True,
        help="Base directory (study folder will be created as <base-dir>/<study-id>).",
    ),
    study_id: str = typer.Option(
        DEFAULT_STUDY_ID,
        "--study-id",
        "-s",
        prompt=True,
        help="Study ID.",
    ),
    name: str = typer.Option(
        DEFAULT_STUDY_NAME,
        "--name",
        "-n",
        prompt=True,
        help="Human-readable study name.",
    ),
    no_env_example: bool = typer.Option(
        False,
        "--no-env-example",
        help="Do not create .env inside the study folder.",
    ),
    no_gitignore: bool = typer.Option(
        False,
        "--no-gitignore",
        help="Do not create .gitignore inside the study folder.",
    ),
) -> None:
    """Create a new study folder with manifest, conditions/, assets/, and runs/.

    Creates ``<base-dir>/<study-id>/`` containing ``study.yaml``, empty
    ``conditions/``, ``assets/``, and ``runs/``. Optionally creates ``.env``
    and ``.gitignore`` inside the study folder.
    """
    try:
        study_path = init_study(
            base_dir,
            study_id,
            name=name,
            create_env_example=not no_env_example,
            create_gitignore=not no_gitignore,
        )
    except (FileExistsError, ValidationError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e

    typer.echo(f"Created study at {study_path}")


@study_app.command("validate")
def validate_study(
    study_dir: Path = typer.Option(
        ...,
        "--study-dir",
        "-d",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        envvar=STUDY_DIR_ENV,
        prompt=True,
        help="Path to study folder.",
    ),
) -> None:
    """Validate study manifest and all condition files in the study folder."""
    try:
        study = load_study(study_dir)
    except ValidationError as e:
        typer.echo(
            format_validation_error(e),
            err=True,
        )
        raise typer.Exit(1) from e
    except (ValueError, FileNotFoundError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e

    try:
        validate_study_plugins(study)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e

    typer.echo(f"Study: {study.study_name} ({study.study_id})")
    typer.echo(f"Conditions: {len(study.conditions)}")
    for condition in study.conditions:
        typer.echo(f"  - {condition.name}")


@study_app.command("run")
def run_study_command(
    study_dir: Path = typer.Option(
        ...,
        "--study-dir",
        "-d",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        envvar=STUDY_DIR_ENV,
        prompt=True,
        help="Path to study folder.",
    ),
    condition_name: str = typer.Option(
        ...,
        "--condition",
        "-c",
        help="Condition name from loaded YAML.",
    ),
    ui: str | None = typer.Option(
        None,
        "--ui",
        help="Override study.ui.type for this run (gui or headless).",
    ),
) -> None:
    """Run a study condition from disk (local only).

    Creates a new run id (UUID). There are no participant or session flags;
    set ``PARTICIPANT_ID`` in the environment only if your run layout uses
    ``{participant_id}``. Does not contact a remote backend.
    """
    try:
        resolved_dir = resolve_study_dir(study_dir)
        study = load_study(resolved_dir)
    except (FileNotFoundError, ValueError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e
    except ValidationError as e:
        typer.echo(format_validation_error(e), err=True)
        raise typer.Exit(1) from e

    _apply_ui_override(study, ui)
    context = _local_run_context(study, condition_name)

    try:
        run_dir = run_study(study, condition_name, context, resolved_dir)
    except Exception as e:
        typer.echo(f"Run failed: {e}", err=True)
        raise typer.Exit(1) from e

    typer.echo(f"Run complete: {run_dir}")
