"""Run CRUD via Supabase table API."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from slumber.utils.time import utc_now

if TYPE_CHECKING:
    from supabase import Client


class RunStatus(StrEnum):
    """Possible status values for a Run row."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


def create_run(client: "Client", session_id: int) -> dict:
    """Insert a new run row with status 'running' and return it.

    The run_directory is initially empty and updated once the local directory
    is created (call update_run after run_study returns).

    Args:
        client: Authenticated Supabase client.
        session_id: Session this run belongs to.

    Returns:
        Created run row as dict (includes ``id`` — the integer primary key).

    Raises:
        RuntimeError: If the insert returns no data.
    """
    payload = {
        "session_id": session_id,
        "status": RunStatus.RUNNING,
        "run_directory": "",
    }
    response = client.table("run").insert(payload).execute()
    if not response.data:
        raise RuntimeError("Run insert returned no data")
    return response.data[0]


def update_run(
    client: "Client",
    run_id: int,
    *,
    status: RunStatus,
    run_directory: str | None = None,
    end_time: str | None = None,
) -> dict:
    """Update status (and optionally run_directory) for a run row.

    Args:
        client: Authenticated Supabase client.
        run_id: Run table primary key.
        status: New run status.
        run_directory: Absolute path to the run directory; omit to leave unchanged.
        end_time: Optional ISO8601 end time override. If omitted and status is
            terminal (completed/failed), now() is used.

    Returns:
        Updated run row as dict.

    Raises:
        ValueError: If the run row is not found.
    """
    payload: dict = {"status": status}
    if run_directory is not None:
        payload["run_directory"] = run_directory
    if end_time is not None:
        payload["end_time"] = end_time
    elif status in {RunStatus.COMPLETED, RunStatus.FAILED}:
        payload["end_time"] = utc_now().isoformat()

    response = client.table("run").update(payload).eq("id", run_id).execute()
    if not response.data:
        raise ValueError(f"Run {run_id} not found")
    return response.data[0]
