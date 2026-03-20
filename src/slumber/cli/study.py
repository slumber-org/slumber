"""Study-related CLI commands."""

import shutil
from pathlib import Path

import typer
from loguru import logger
from pydantic import ValidationError

from slumber.auth import get_authenticated_client, get_client
from slumber.backend import (
    RunStatus,
    create_run,
    create_study,
    get_active_session,
    get_participant_for_study,
    update_run,
)
from slumber.backend.condition import generate_condition_id
from slumber.config import (
    init_study,
    load_study,
    resolve_study_dir,
    validate_study_plugins,
)
from slumber.constants import STUDY_DIR_ENV
from slumber.runtime import RunContext, init_sentry, run_study
from slumber.utils.errors import format_validation_error
from slumber.utils.time import utc_now


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
) -> None:
    """Run the scheduled session for the current user.

    Looks up the current user's participant record in the study, finds the
    session whose start window contains now, creates a Run record in the
    database, and runs that session's condition via the study's UI backend
    (headless by default).

    Requires 'slumber auth login' before running. Set SENTRY_DSN to enable
    Sentry error monitoring.
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

    try:
        client = get_authenticated_client()
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e

    now = utc_now()
    try:
        participant = get_participant_for_study(client, study.study_id)
        session = get_active_session(client, participant["id"], now)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e

    condition_id = session.get("condition_id")
    if not condition_id:
        typer.echo(
            f"Session {session['id']} has no condition assigned. "
            "Ask the researcher to update the session with a condition.",
            err=True,
        )
        raise typer.Exit(1)

    condition_name = condition_id.removeprefix(
        generate_condition_id(study.study_id, "")
    )

    try:
        run_row = create_run(client, session["id"])
    except Exception as e:
        typer.echo(f"Failed to create run record: {e}", err=True)
        raise typer.Exit(1) from e

    run_id = str(run_row["id"])
    init_sentry(study.study_id)

    context = RunContext(
        study_id=study.study_id,
        participant_id=participant["participant_id"],
        session_id=str(session["id"]),
        run_id=run_id,
        condition_id=condition_name,
    )

    run_error: Exception | None = None
    run_dir: Path | None = None
    try:
        run_dir = run_study(study, condition_name, context, resolved_dir)
    except Exception as e:
        run_error = e
    finally:
        final_status = RunStatus.FAILED if run_error else RunStatus.COMPLETED
        update_kwargs: dict = {"status": final_status}
        if run_dir is not None:
            update_kwargs["run_directory"] = str(run_dir)
        try:
            update_run(client, run_row["id"], **update_kwargs)
        except Exception as update_exc:
            logger.warning(
                "Failed to record run {} status {!r}: {}",
                run_row["id"],
                final_status,
                update_exc,
            )

    if run_error is not None:
        typer.echo(f"Run failed: {run_error}", err=True)
        raise typer.Exit(1) from run_error

    typer.echo(f"Run complete: {run_dir}")
