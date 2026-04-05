"""Study CRUD via Supabase table API.

Study table has RLS with SELECT only; INSERT requires service role.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from supabase import Client


def create_study(
    client: Client,
    study_id: str,
    name: str,
) -> dict:
    """Create a study row in the database.

    Use with get_client(use_service_role=True). The study table has no
    INSERT policy for authenticated users, so service role is required.

    Args:
        client: Supabase client with service role.
        study_id: Study id (primary key, e.g. from study.yaml).
        name: Human-readable study name.

    Returns:
        Created row as dict (includes id, name, created_at, updated_at).

    Raises:
        Exception: On duplicate id or DB error.
    """
    payload = {
        "id": study_id,
        "name": name,
    }
    response = client.table("study").insert(payload).execute()
    if not response.data or len(response.data) == 0:
        raise RuntimeError("Study insert returned no data")
    return response.data[0]
