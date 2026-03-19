"""Study-related CLI commands."""

import shutil
from pathlib import Path

import typer
from pydantic import ValidationError

from slumber.auth import get_client
from slumber.backend import create_study
from slumber.constants import STUDY_DIR_ENV
from slumber.config import init_study, load_study, validate_study_plugins
from slumber.utils.errors import format_validation_error


DEFAULT_STUDY_ID = "new_study"
DEFAULT_BASE_DIR = Path(".")
DEFAULT_STUDY_NAME = "New Study"

study_app = typer.Typer(help="Study folder and manifest commands.")


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
    """Create a new study folder with manifest, conditions/, and assets/.

    Creates <base-dir>/<study-id>/ containing study.yaml, empty conditions/
    and assets/. Optionally creates .env (from config template) and .gitignore
    inside the study folder (for non-interactive use, pass --base-dir and --study-id).
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

    try:
        client = get_client(use_service_role=True)
        create_study(client, study_id, name)
        typer.echo(f"Registered study '{study_id}' in the database.")
    except ValueError as e:
        typer.echo(f"Database: {e}", err=True)
        _cleanup_study_dir(study_path)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Database: {e}", err=True)
        _cleanup_study_dir(study_path)
        raise typer.Exit(1) from e

    typer.echo(f"Created study at {study_path}")


def _cleanup_study_dir(study_path: Path) -> None:
    """Remove a newly created study directory after DB registration failure."""
    try:
        shutil.rmtree(study_path)
        typer.echo(
            "Database registration failed, so the created study folder was removed.",
            err=True,
        )
    except Exception as cleanup_error:
        typer.echo(
            "Database registration failed and automatic study-folder cleanup failed: "
            f"{cleanup_error}. Remove this folder manually: {study_path}",
            err=True,
        )


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

    typer.echo(f"Study: {study.name} ({study.study_id})")
    typer.echo(f"Conditions: {len(study.conditions)}")
    for c in study.conditions:
        typer.echo(f"  - {c.name}")
