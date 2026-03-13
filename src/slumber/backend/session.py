"""Session CRUD via Supabase table API (RLS applies)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from slumber.utils.time import utc_now

if TYPE_CHECKING:
    from supabase import Client


def _datetime_to_iso(dt: datetime) -> str:
    """Format timezone-aware datetime for PostgREST (ISO 8601)."""
    return dt.isoformat()


def _ranges_overlap(
    start_a: datetime,
    end_a: datetime,
    start_b: datetime,
    end_b: datetime,
) -> bool:
    """True if [start_a, end_a] and [start_b, end_b] overlap (inclusive ends)."""
    return start_a <= end_b and start_b <= end_a


def _check_no_overlap(
    client: Client,
    participant_id: str,
    earliest_start_at: datetime,
    latest_start_at: datetime,
    *,
    exclude_session_id: int | None = None,
) -> None:
    """Raise ValueError if participant already has a session with overlapping start window."""
    response = (
        client.table("session")
        .select("id,earliest_start_at,latest_start_at")
        .eq("participant_id", participant_id)
        .execute()
    )
    for row in response.data or []:
        if exclude_session_id is not None and row.get("id") == exclude_session_id:
            continue
        ea = row.get("earliest_start_at")
        la = row.get("latest_start_at")
        if ea is None or la is None:
            continue
        # Supabase returns ISO strings; parse to datetime for comparison
        if isinstance(ea, str):
            ea = datetime.fromisoformat(ea.replace("Z", "+00:00"))
        if isinstance(la, str):
            la = datetime.fromisoformat(la.replace("Z", "+00:00"))
        if _ranges_overlap(earliest_start_at, latest_start_at, ea, la):
            raise ValueError(
                f"Participant {participant_id} already has a session with overlapping "
                f"start window (existing: {ea}–{la}; requested: {earliest_start_at}–{latest_start_at})."
            )


def create_session(
    client: Client,
    participant_id: str,
    earliest_start_at: datetime,
    latest_start_at: datetime,
    *,
    condition_id: str | None = None,
) -> dict:
    """Create a session for a participant (must belong to current user).

    RLS allows insert only when the participant's auth_user_id = auth.uid().
    The DB enforces no overlapping (earliest_start_at, latest_start_at) per
    participant via an exclusion constraint.

    Args:
        client: Authenticated Supabase client.
        study_id: Study id.
        participant_id: Participant id.
        earliest_start_at: Start of allowed start window (timestamptz).
        latest_start_at: End of allowed start window (timestamptz).
        condition_id: Optional condition id.

    Returns:
        Created session row as dict.

    Raises:
        ValueError: If the participant already has a session with an overlapping
            (earliest_start_at, latest_start_at) window.
    """
    _check_no_overlap(client, participant_id, earliest_start_at, latest_start_at)
    now = utc_now()
    payload = {
        "participant_id": participant_id,
        "earliest_start_at": _datetime_to_iso(earliest_start_at),
        "latest_start_at": _datetime_to_iso(latest_start_at),
        "condition_id": condition_id,
        "created_at": _datetime_to_iso(now),
        "updated_at": _datetime_to_iso(now),
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    response = client.table("session").insert(payload).execute()
    if not response.data or len(response.data) == 0:
        raise RuntimeError("Session insert returned no data")
    return response.data[0]


def list_sessions(
    client: Client,
    *,
    participant_id: str | None = None,
    study_id: str | None = None,
) -> list[dict]:
    """List sessions (RLS filters by participant ownership).

    Args:
        client: Authenticated Supabase client.
        participant_id: If set, filter to this participant's sessions.
        study_id: If set, filter to sessions whose participant is in this study.
            Fetches participant ids for the study first, then filters sessions.
    """
    if study_id is not None:
        participants = (
            client.table("participant").select("id").eq("study_id", study_id).execute()
        )
        if not participants.data:
            return []
        participant_ids = [p["id"] for p in participants.data]
        query = (
            client.table("session").select("*").in_("participant_id", participant_ids)
        )
    else:
        query = client.table("session").select("*")
        if participant_id is not None:
            query = query.eq("participant_id", participant_id)
    response = query.execute()
    return list(response.data) if response.data else []


def update_session(
    client: Client,
    session_id: int,
    *,
    condition_id: str | None = None,
    earliest_start_at: datetime | None = None,
    latest_start_at: datetime | None = None,
) -> dict:
    """Update a session by id (must belong to current user via RLS).

    Only provided fields are updated. Pass None for a field to leave it unchanged.
    Updating the start window is subject to the same no-overlap constraint.

    Args:
        client: Authenticated Supabase client.
        session_id: Session table id.
        condition_id: New condition id (or None to leave unchanged).
        earliest_start_at: New start of allowed start window.
        latest_start_at: New end of allowed start window.

    Returns:
        Updated session row as dict.

    Raises:
        ValueError: If updating the window would overlap another session for the
            same participant.
    """
    payload: dict[str, object] = {}
    if condition_id is not None:
        payload["condition_id"] = condition_id
    if earliest_start_at is not None:
        payload["earliest_start_at"] = _datetime_to_iso(earliest_start_at)
    if latest_start_at is not None:
        payload["latest_start_at"] = _datetime_to_iso(latest_start_at)
    if not payload:
        # Fetch current row and return it
        response = client.table("session").select("*").eq("id", session_id).execute()
        if not response.data or len(response.data) == 0:
            raise ValueError(f"Session {session_id} not found")
        return response.data[0]

    # If we're changing the start window, enforce no overlap with other sessions
    if "earliest_start_at" in payload or "latest_start_at" in payload:
        current = (
            client.table("session")
            .select("participant_id,earliest_start_at,latest_start_at")
            .eq("id", session_id)
            .execute()
        )
        if not current.data or len(current.data) == 0:
            raise ValueError(f"Session {session_id} not found")
        row = current.data[0]
        participant_id = row["participant_id"]
        ea = earliest_start_at
        la = latest_start_at
        if ea is None:
            raw = row.get("earliest_start_at")
            ea = (
                datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if isinstance(raw, str)
                else raw
            )
        if la is None:
            raw = row.get("latest_start_at")
            la = (
                datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if isinstance(raw, str)
                else raw
            )
        _check_no_overlap(
            client,
            participant_id,
            ea,
            la,
            exclude_session_id=session_id,
        )

    response = client.table("session").update(payload).eq("id", session_id).execute()
    if not response.data or len(response.data) == 0:
        raise ValueError(f"Session {session_id} not found")
    return response.data[0]


def delete_session(client: Client, session_id: int) -> None:
    """Delete a session by id (must belong to current user via RLS).

    Args:
        client: Authenticated Supabase client.
        session_id: Session table id.

    Raises:
        ValueError: If session not found (or not owned).
    """
    response = client.table("session").delete().eq("id", session_id).execute()
    if response.data is None or len(response.data) == 0:
        raise ValueError(f"Session {session_id} not found")
