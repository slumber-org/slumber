"""Session commands: create, list, update, delete (researcher; use service role)."""

from __future__ import annotations

from datetime import datetime

import typer

from slumber.auth import get_client
from slumber.backend import (
    create_session as backend_create,
    list_sessions as backend_list,
    update_session as backend_update,
    delete_session as backend_delete,
)
from slumber.backend.participant import generate_participant_id
from slumber.constants import (
    PARTICIPANT_ID_ENV,
    STUDY_ID_ENV,
)

session_app = typer.Typer(
    name="session",
    help="Session CRUD for researchers (uses SUPABASE_SERVICE_ROLE_KEY).",
)


def _parse_datetime(value: str) -> datetime:
    """Parse ISO 8601 datetime (e.g. 2025-03-12T22:00:00Z or with +00:00)."""
    if not value:
        raise ValueError("Empty datetime")
    # fromisoformat handles +00:00 but not Z; normalize Z to +00:00
    normalized = value.strip().replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


@session_app.command("create")
def session_create(
    study_id: str = typer.Option(
        ...,
        "--study-id",
        envvar=STUDY_ID_ENV,
        prompt=True,
        help="Study ID. Validates participant belongs to study.",
    ),
    participant_id: str = typer.Option(
        ...,
        "--participant-id",
        envvar=PARTICIPANT_ID_ENV,
        prompt=True,
        help="Participant ID.",
    ),
    earliest_start_at: str = typer.Option(
        ...,
        "--earliest-start-at",
        prompt=True,
        help="Start of allowed start window (ISO 8601, e.g. 2025-03-12T22:00:00Z).",
    ),
    latest_start_at: str = typer.Option(
        ...,
        "--latest-start-at",
        prompt=True,
        help="End of allowed start window (ISO 8601, e.g. 2025-03-13T06:00:00Z).",
    ),
    condition_id: str | None = typer.Option(
        None, "--condition-id", help="Condition ID (e.g. condition_1)."
    ),
) -> None:
    """Create a session for a participant."""

    try:
        client = get_client(use_service_role=True)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e

    try:
        earliest = _parse_datetime(earliest_start_at)
        latest = _parse_datetime(latest_start_at)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e

    if earliest >= latest:
        typer.echo("Error: earliest-start-at must be before latest-start-at.", err=True)
        raise typer.Exit(1)

    try:
        row = backend_create(
            client,
            participant_id=generate_participant_id(study_id, participant_id),
            earliest_start_at=earliest,
            latest_start_at=latest,
            condition_id=condition_id,
        )
        typer.echo(f"Created session id={row.get('id')}.")
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Create failed: {e}", err=True)
        raise typer.Exit(1) from e


@session_app.command("list")
def session_list(
    study_id: str | None = typer.Option(
        None,
        "--study-id",
        envvar=STUDY_ID_ENV,
        help="Filter by study ID.",
    ),
    participant_id: str | None = typer.Option(
        None,
        "--participant-id",
        envvar=PARTICIPANT_ID_ENV,
        help="Filter by participant ID.",
    ),
) -> None:
    """List sessions (optionally filter by study or participant)."""

    try:
        client = get_client(use_service_role=True)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e

    try:
        rows = backend_list(
            client,
            participant_id=participant_id,
            study_id=study_id,
        )

        if not rows:
            typer.echo("No sessions.")
            return

        for r in rows:
            typer.echo(
                f"  id={r.get('id')}  participant_id={r.get('participant_id')}  "
                f"earliest_start_at={r.get('earliest_start_at')}  latest_start_at={r.get('latest_start_at')}  "
                f"condition_id={r.get('condition_id')}"
            )
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"List failed: {e}", err=True)
        raise typer.Exit(1) from e


@session_app.command("update")
def session_update(
    session_id: int = typer.Argument(..., help="Session ID to update."),
    condition_id: str | None = typer.Option(
        None, "--condition-id", help="New condition id (e.g. condition_1)."
    ),
    earliest_start_at: str | None = typer.Option(
        None,
        "--earliest-start-at",
        help="New start of allowed start window (ISO 8601).",
    ),
    latest_start_at: str | None = typer.Option(
        None, "--latest-start-at", help="New end of allowed start window (ISO 8601)."
    ),
) -> None:
    """Update a session (only provided options are changed)."""
    try:
        client = get_client(use_service_role=True)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e

    earliest: datetime | None = None
    latest: datetime | None = None
    if earliest_start_at is not None:
        try:
            earliest = _parse_datetime(earliest_start_at)
        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1) from e
    if latest_start_at is not None:
        try:
            latest = _parse_datetime(latest_start_at)
        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1) from e
    if earliest is not None and latest is not None and earliest >= latest:
        typer.echo("Error: earliest-start-at must be before latest-start-at.", err=True)
        raise typer.Exit(1)

    try:
        backend_update(
            client,
            session_id,
            condition_id=condition_id,
            earliest_start_at=earliest,
            latest_start_at=latest,
        )
        typer.echo(f"Updated session {session_id}.")
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Update failed: {e}", err=True)
        raise typer.Exit(1) from e


@session_app.command("delete")
def session_delete(
    session_id: int = typer.Argument(..., help="Session ID to delete."),
) -> None:
    """Delete a session."""
    try:
        client = get_client(use_service_role=True)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e

    try:
        backend_delete(client, session_id)
        typer.echo(f"Deleted session {session_id}.")
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Delete failed: {e}", err=True)
        raise typer.Exit(1) from e
