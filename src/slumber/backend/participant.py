"""Participant CRUD via Supabase table API (RLS applies)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from supabase import Client


def generate_participant_id(study_id: str, participant_id: str) -> str:
    """Generate a participant id for a given study and participant id."""
    return f"{study_id}_{participant_id}"


def _current_user_id(client: Client) -> str:
    """Return the current auth user's UUID as string."""
    session = client.auth.get_session()
    if not session or not session.user:
        raise ValueError("Not authenticated. Run 'slumber auth login'.")
    return str(session.user.id)


def create_participant(
    client: Client,
    study_id: str,
    participant_id: str,
) -> dict:
    """Create a participant row for the current user in the given study.

    RLS allows INSERT only when auth_user_id = auth.uid(). We set
    auth_user_id to the current user so the insert succeeds.

    Args:
        client: Authenticated Supabase client.
        study_id: Study id (must exist in study table).
        participant_id: Study-specific participant id (e.g. sub-001).

    Returns:
        Created row as dict (includes id, created_at, updated_at).

    Raises:
        ValueError: If not authenticated.
        Exception: On duplicate (study_id, participant_id) or FK violation.
    """
    auth_user_id = _current_user_id(client)
    payload = {
        "id": f"{study_id}_{participant_id}",
        "study_id": study_id,
        "participant_id": participant_id,
        "auth_user_id": auth_user_id,
    }
    response = client.table("participant").insert(payload).execute()
    if not response.data or len(response.data) == 0:
        raise RuntimeError("Participant insert returned no data")
    return response.data[0]


def create_participant_for_user(
    client: Client,
    study_id: str,
    participant_id: str,
    auth_user_id: str,
) -> dict:
    """Create a participant row for a given auth user (service role only).

    Use with get_client(use_service_role=True). Bypasses RLS so the
    researcher can create participants for any auth user.

    Args:
        client: Supabase client with service role.
        study_id: Study id (must exist in study table).
        participant_id: Study-specific participant id (e.g. sub-001).
        auth_user_id: Supabase auth user UUID (auth.users.id).

    Returns:
        Created row as dict.
    """
    payload = {
        "id": generate_participant_id(study_id, participant_id),
        "study_id": study_id,
        "participant_id": participant_id,
        "auth_user_id": auth_user_id,
    }
    response = client.table("participant").insert(payload).execute()
    if not response.data or len(response.data) == 0:
        raise RuntimeError("Participant insert returned no data")
    return response.data[0]


def get_participant_for_study(client: Client, study_id: str) -> dict:
    """Return the current user's participant record for the given study.

    Uses RLS — only the authenticated user's own participant row is visible.

    Args:
        client: Authenticated Supabase client.
        study_id: Study identifier.

    Returns:
        Participant row as dict.

    Raises:
        ValueError: If the current user is not a participant in the study.
    """
    response = (
        client.table("participant").select("*").eq("study_id", study_id).execute()
    )
    if not response.data:
        raise ValueError(
            f"Current user is not a participant in study {study_id!r}. "
            "Ask the researcher to add you as a participant."
        )
    return response.data[0]


def list_participants(
    client: Client,
    auth_user_id: str | None = None,
) -> list[dict]:
    """List participants (current user via RLS, or for auth_user_id with service role).

    When auth_user_id is None, uses RLS (current session). When auth_user_id
    is set, filters by that user (requires service role client).

    Args:
        client: Supabase client (anon for self, service role for researcher).
        auth_user_id: If set, list only participants for this auth user.

    Returns:
        List of participant rows.
    """
    query = client.table("participant").select("*")
    if auth_user_id is not None:
        query = query.eq("auth_user_id", auth_user_id)
    response = query.execute()
    return list(response.data) if response.data else []
