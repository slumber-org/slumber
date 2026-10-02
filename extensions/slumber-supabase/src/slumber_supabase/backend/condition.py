"""Condition sync via Supabase table API (service role required)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slumber.schemas.condition import Condition
    from supabase import Client


def generate_condition_id(study_id: str, condition_name: str) -> str:
    """Generate a condition row id from study id and condition name.

    Args:
        study_id: Study identifier.
        condition_name: Condition name (e.g. condition_1).

    Returns:
        Composite id string: ``{study_id}_{condition_name}``.
    """
    return f"{study_id}_{condition_name}"


def sync_conditions(
    client: Client,
    study_id: str,
    conditions: list[Condition],
) -> list[dict]:
    """Upsert conditions from a study folder into Supabase.

    Inserts or updates each condition row for the given study, keyed by
    ``{study_id}_{condition.name}``. Serializes ``entry``, ``phases``, and
    ``pipelines`` to JSON. Use with ``get_client(use_service_role=True)``; the
    condition table requires service role for writes.

    Args:
        client: Supabase client (service role).
        study_id: Study identifier (must exist in the study table).
        conditions: Validated Condition objects to sync.

    Returns:
        List of upserted condition rows (one dict per condition).

    Raises:
        RuntimeError: If a condition upsert returns no data.
    """
    results = []
    for condition in conditions:
        condition_id = generate_condition_id(study_id, condition.name)
        data = condition.model_dump(mode="json")
        payload = {
            "id": condition_id,
            "study_id": study_id,
            "entry": data["entry"],
            "phases": data["phases"],
            "pipelines": data["pipelines"],
        }
        response = client.table("condition").upsert(payload, on_conflict="id").execute()
        if not response.data or len(response.data) == 0:
            raise RuntimeError(
                f"Condition upsert returned no data for '{condition.name}'"
            )
        results.append(response.data[0])
    return results
