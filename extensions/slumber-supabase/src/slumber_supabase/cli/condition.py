"""Condition commands: sync conditions from study folder to Supabase."""

from __future__ import annotations

from pathlib import Path

import typer
from pydantic import ValidationError
from slumber.config import load_study
from slumber.constants import STUDY_DIR_ENV
from slumber.utils.errors import format_validation_error

from slumber_supabase.utils import exit_unless_supabase_extra_installed

condition_app = typer.Typer(
    name="condition",
    help="Condition commands.",
)


@condition_app.command("sync")
def condition_sync(
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
    conditions: list[str] | None = typer.Option(
        None,
        "--conditions",
        "-c",
        help=(
            "Condition names to sync (repeat or space-separate). "
            "Defaults to all conditions in the study folder."
        ),
    ),
) -> None:
    """Push conditions from the study folder into Supabase.

    Loads condition YAML files from the study's conditions directory,
    validates them, and upserts each into the Supabase condition table.
    Pass --conditions to sync a subset by name; omit to sync all.

    Requires SUPABASE_SERVICE_ROLE_KEY in the environment.
    """
    exit_unless_supabase_extra_installed()
    from slumber_supabase.auth import get_client
    from slumber_supabase.backend import sync_conditions

    try:
        study = load_study(study_dir)
    except ValidationError as e:
        typer.echo(format_validation_error(e), err=True)
        raise typer.Exit(1) from e
    except (ValueError, FileNotFoundError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e

    all_conditions = study.conditions
    if not all_conditions:
        typer.echo("No conditions found in study folder.")
        raise typer.Exit(0)

    available_names = {c.name for c in all_conditions}

    if conditions:
        invalid = set(conditions) - available_names
        if invalid:
            typer.echo(
                f"Unknown condition(s): {sorted(invalid)}. "
                f"Available: {sorted(available_names)}",
                err=True,
            )
            raise typer.Exit(1)
        to_sync = [c for c in all_conditions if c.name in set(conditions)]
    else:
        to_sync = all_conditions

    try:
        client = get_client(use_service_role=True)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e

    synced = 0
    for condition in to_sync:
        try:
            sync_conditions(client, study.study_id, [condition])
            typer.echo(f"  synced: {condition.name}")
            synced += 1
        except Exception as e:
            typer.echo(f"  failed: {condition.name} — {e}", err=True)
            raise typer.Exit(1) from e

    typer.echo(f"Synced {synced} condition(s) for study '{study.study_id}'.")
