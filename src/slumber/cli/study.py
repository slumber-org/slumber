"""Study-related CLI commands."""

from pathlib import Path
from typing import Annotated

from pydantic import ValidationError
import typer

from slumber.config import (
    discover_study_dir,
    format_validation_error,
    init_study,
    load_study,
    load_study_conditions,
)


DEFAULT_STUDY_ID = "new_study"

study_app = typer.Typer(help="Study folder and manifest commands.")


@study_app.command("init")
def initialize_study(
    base_dir: Annotated[
        Path,
        typer.Option(
            "--base-dir",
            "-b",
            show_default=True,
            file_okay=False,
            writable=True,
            resolve_path=True,
            prompt="Base directory (project root)",
            help="Base directory; study folder will be created as <base-dir>/<study-id>/.",
        ),
    ] = Path("."),
    study_id: Annotated[
        str,
        typer.Option(
            "--study-id",
            "-s",
            prompt="Study ID (folder name)",
            help="Study identifier (folder name). If omitted, prompt interactively.",
        ),
    ] = DEFAULT_STUDY_ID,
    name: Annotated[
        str,
        typer.Option(
            "--name",
            "-n",
            prompt="Study name (human-readable)",
            help="Human-readable study name; defaults to study_id.",
        ),
    ] = DEFAULT_STUDY_ID,
    no_env_example: bool = typer.Option(
        False,
        "--no-env-example",
        help="Do not create .env.example inside the study folder.",
    ),
    no_gitignore: bool = typer.Option(
        False,
        "--no-gitignore",
        help="Do not create .gitignore inside the study folder.",
    ),
) -> None:
    """Create a new study folder with manifest, conditions/, and assets/.

    Creates <base-dir>/<study-id>/ containing study.yaml, empty conditions/
    and assets/. Optionally creates .env.example and .gitignore inside the
    study folder (for non-interactive use, pass --base-dir and --study-id).
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
    typer.echo("Next: cd into the study folder and run 'slumber study validate'.")


@study_app.command("validate")
def validate_study(
    study_dir: Annotated[
        Path | None,
        typer.Option(
            "--study-dir",
            "-d",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
            help="Path to study folder. If omitted, current directory is used.",
        ),
    ] = None,
) -> None:
    """Validate study manifest and all condition files in the study folder.

    Discovers the study by looking for study.yaml in the current directory
    (or in --study-dir). Loads the manifest and every condition YAML in
    conditions_dir; reports validation errors with file paths.
    """
    found = discover_study_dir(study_dir=study_dir)
    if found is None:
        if study_dir is not None:
            hint = f" No study.yaml in {study_dir.resolve()}."
        else:
            hint = " No study.yaml in current directory."
        typer.echo(
            f"Study folder not found.{hint} Run from a study directory or pass --study-dir.",
            err=True,
        )
        raise typer.Exit(1)

    try:
        study = load_study(found)
    except ValidationError as e:
        typer.echo(
            format_validation_error(
                e, path=found / "study.yaml", prefix="Study manifest error"
            ),
            err=True,
        )
        raise typer.Exit(1) from e
    except FileNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e

    try:
        conditions = load_study_conditions(study, found)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e
    except FileNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e

    typer.echo(f"Study: {study.name} ({study.study_id})")
    typer.echo(f"Conditions: {len(conditions)}")
    for c in conditions:
        typer.echo(f"  - {c.name}")
