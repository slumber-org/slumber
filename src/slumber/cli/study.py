"""Study-related CLI commands."""

import os
import uuid
from pathlib import Path
from typing import Any

import typer
from loguru import logger
from pydantic import ValidationError

from slumber.config import (
    init_study,
    load_study,
    resolve_study_dir,
    validate_study_plugins,
)
from slumber.constants import PARTICIPANT_ID_ENV, STUDY_DIR_ENV
from slumber.runtime import RunContext, init_sentry, run_study
from slumber.schemas.study import Study
from slumber.supabase.utils import exit_unless_supabase_extra_installed
from slumber.utils.errors import format_validation_error
from slumber.utils.time import utc_now

DEFAULT_STUDY_ID = "new_study"
DEFAULT_BASE_DIR = Path(".")
DEFAULT_STUDY_NAME = "New Study"

study_app = typer.Typer(help="Study folder and manifest commands.")


def _execute_study_run(
    study: Study,
    condition_name: str,
    context: RunContext,
    resolved_dir: Path,
) -> Path:
    """Initialize Sentry and execute the study run; returns the run directory."""
    init_sentry(study.study_id)
    return run_study(study, condition_name, context, resolved_dir)


def _local_run_context(study: Study, condition_name: str) -> RunContext:
    """Build :class:`RunContext` for a local (file-based) run."""
    return RunContext(
        study_id=study.study_id,
        run_id=str(uuid.uuid4()),
        condition_id=condition_name,
        participant_id=os.environ.get(PARTICIPANT_ID_ENV),
    )


def _resolve_scheduled_run(study: Study) -> tuple[str, RunContext, Any, dict]:
    """Resolve active session, create run row, build context. May ``typer.Exit`` on failure."""
    exit_unless_supabase_extra_installed(
        reason="Scheduled study runs require the Supabase client."
    )
    from slumber.supabase.auth import get_authenticated_client
    from slumber.supabase.backend import (
        create_run,
        get_active_session,
        get_participant_for_study,
    )
    from slumber.supabase.backend.condition import generate_condition_id

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
    context = RunContext(
        study_id=study.study_id,
        run_id=run_id,
        condition_id=condition_name,
        participant_id=participant["participant_id"],
        session_id=str(session["id"]),
    )
    return condition_name, context, client, run_row


def _persist_scheduled_run_outcome(
    client: Any,
    run_row: dict,
    run_error: Exception | None,
    run_dir: Path | None,
) -> None:
    """Update Supabase Run row status and optional directory after orchestration."""
    from slumber.supabase.backend import RunStatus, update_run

    final_status = RunStatus.FAILED if run_error else RunStatus.COMPLETED
    update_kwargs: dict = {"status": final_status}
    if run_dir is not None:
        update_kwargs["run_directory"] = str(run_dir)
    try:
        update_run(client, run_row["id"], **update_kwargs)
    # TODO: [refactor] catch typed backend/network errors instead of Exception
    except Exception as update_exc:  # noqa: BLE001
        logger.warning(
            "Failed to record run {} status {!r}: {}",
            run_row["id"],
            final_status,
            update_exc,
        )


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
    register: bool = typer.Option(
        False,
        "--register",
        help=(
            "Register this study in the Supabase project (requires slumber[supabase], "
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)."
        ),
    ),
) -> None:
    """Create a new study folder with manifest, conditions/, and assets/.

    Creates <base-dir>/<study-id>/ containing study.yaml, empty conditions/
    and assets/. Optionally creates .env (from config template) and .gitignore
    inside the study folder (for non-interactive use, pass --base-dir and --study-id).

    Remote registration is opt-in: pass --register to insert a study row via the
    Supabase API (service role).
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

    if register:
        _register_study_in_supabase(study_id, name)


def _register_study_in_supabase(study_id: str, name: str) -> None:
    """Insert a study row in Supabase (lazy imports; needs slumber[supabase] + env)."""
    exit_unless_supabase_extra_installed(
        reason="Registering a study in the database requires the Supabase client."
    )
    from slumber.supabase.auth import get_client
    from slumber.supabase.backend.study import create_study

    try:
        client = get_client(use_service_role=True)
        create_study(client, study_id, name)
    except ValueError as e:
        typer.echo(f"Database: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Database: {e}", err=True)
        raise typer.Exit(1) from e

    typer.echo(f"Registered study '{study_id}' in the database.")


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
    condition_name: str | None = typer.Option(
        None,
        "--condition",
        "-c",
        help="Condition name from loaded YAML (required for a local run).",
    ),
    scheduled: bool = typer.Option(
        False,
        "--scheduled",
        help=(
            "Use the database session flow: active session window, create/update "
            "Run rows (requires slumber[supabase] and slumber auth login)."
        ),
    ),
) -> None:
    """Run a study condition from disk, or a scheduled session from the database.

    **Local (default):** pass ``--condition`` with a condition ``name`` from the
    study condition files. Creates a new run id (UUID). There are no participant or
    session flags for local runs; set ``PARTICIPANT_ID`` in the environment only if your run layout uses
    ``{participant_id}``. Does not contact the database.

    **Scheduled:** pass ``--scheduled`` to use the logged-in user's participant
    row, the active session window, and Run create/update (requires
    ``slumber[supabase]`` and ``slumber auth login``). Do not pass ``--condition``.

    Set ``SENTRY_DSN`` to enable Sentry error monitoring.
    """
    if scheduled and condition_name is not None:
        typer.echo(
            "Do not pass --condition together with --scheduled "
            "(the condition comes from the active session).",
            err=True,
        )
        raise typer.Exit(1)
    if not scheduled and condition_name is None:
        typer.echo(
            "Specify --condition <name> for a local run, or pass --scheduled "
            "for a database-backed scheduled session.",
            err=True,
        )
        raise typer.Exit(1)

    try:
        resolved_dir = resolve_study_dir(study_dir)
        study = load_study(resolved_dir)
    except (FileNotFoundError, ValueError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e
    except ValidationError as e:
        typer.echo(format_validation_error(e), err=True)
        raise typer.Exit(1) from e

    client = None
    run_row = None
    if scheduled:
        condition_name, context, client, run_row = _resolve_scheduled_run(study)
    else:
        context = _local_run_context(study, condition_name)

    run_error: Exception | None = None
    run_dir: Path | None = None
    try:
        run_dir = _execute_study_run(study, condition_name, context, resolved_dir)
    except Exception as e:  # noqa: BLE001 - persist FAILED for any run error
        run_error = e
    finally:
        if scheduled:
            _persist_scheduled_run_outcome(client, run_row, run_error, run_dir)

    if run_error is not None:
        typer.echo(f"Run failed: {run_error}", err=True)
        raise typer.Exit(1) from run_error

    typer.echo(f"Run complete: {run_dir}")
