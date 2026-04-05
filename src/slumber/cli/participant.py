"""Participant commands: create, list (researcher; use service role)."""

from __future__ import annotations

from uuid import UUID

import typer

from slumber.constants import (
    PARTICIPANT_ID_ENV,
    STUDY_ID_ENV,
    USER_ID_ENV,
)
from slumber.supabase.utils import exit_unless_supabase_extra_installed

participant_app = typer.Typer(
    name="participant",
    help="Participant CRUD for researchers.",
)


@participant_app.command("create")
def participant_create(
    participant_id: str = typer.Option(
        ...,
        "--participant-id",
        envvar=PARTICIPANT_ID_ENV,
        prompt=True,
        help="Participant ID.",
    ),
    study_id: str = typer.Option(
        ...,
        "--study-id",
        envvar=STUDY_ID_ENV,
        prompt=True,
        help="Study ID.",
    ),
    user_id: str | None = typer.Option(
        None,
        "--user-id",
        envvar=USER_ID_ENV,
        prompt=True,
        help="Existing auth user UUID.",
    ),
) -> None:
    """Create a participant: link an existing user (--user-id)."""
    exit_unless_supabase_extra_installed()
    from slumber.supabase.auth import get_client
    from slumber.supabase.backend import create_participant_for_user

    try:
        client = get_client(use_service_role=True)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e

    try:
        UUID(user_id)
    except ValueError:
        typer.echo("Error: --user-id must be a valid UUID.", err=True)
        raise typer.Exit(1)

    try:
        row = create_participant_for_user(
            client,
            study_id=study_id,
            participant_id=participant_id,
            auth_user_id=user_id,
        )
        typer.echo(
            f"Created participant id={row.get('id')} ({study_id} / {participant_id})."
        )
    except Exception as e:
        typer.echo(f"Create failed: {e}", err=True)
        raise typer.Exit(1) from e


@participant_app.command("list")
def participant_list(
    user_id: str = typer.Option(
        ...,
        "--user-id",
        envvar=USER_ID_ENV,
        prompt=True,
        help="Auth user UUID.",
    ),
) -> None:
    """List participants for an auth user (researcher; uses service role)."""
    exit_unless_supabase_extra_installed()
    from slumber.supabase.auth import get_client
    from slumber.supabase.backend import list_participants

    try:
        UUID(user_id)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e

    try:
        client = get_client(use_service_role=True)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e

    try:
        rows = list_participants(client, auth_user_id=user_id)

        if not rows:
            typer.echo("No participants.")
            return

        for r in rows:
            typer.echo(
                f"  id={r.get('id')}  study_id={r.get('study_id')}  participant_id={r.get('participant_id')}"
            )
    except Exception as e:
        typer.echo(f"List failed: {e}", err=True)
        raise typer.Exit(1) from e
