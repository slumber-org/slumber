"""Tests for backend condition sync."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from slumber.backend.condition import generate_condition_id, sync_conditions
from slumber.schemas.condition import Condition


def _make_condition(name: str = "condition_1") -> Condition:
    """Return a minimal valid Condition for testing."""
    return Condition.model_validate(
        {
            "name": name,
            "procedures": {
                "pre_sleep": {"steps": [{"task": "instruction"}]},
            },
            "dag": {
                "components": [{"name": "MASTER", "unit_type": "Master"}],
                "connections": [],
                "process_components": [],
            },
        }
    )


def _mock_client_with_upsert_response(data: list[dict]) -> MagicMock:
    """Return a mock Supabase client whose table().upsert().execute() returns data."""
    mock_response = MagicMock()
    mock_response.data = data
    mock_table = MagicMock()
    mock_table.upsert.return_value.execute.return_value = mock_response
    mock_client = MagicMock()
    mock_client.table.return_value = mock_table
    return mock_client


class TestGenerateConditionId:
    def test_combines_study_and_condition_name(self) -> None:
        assert generate_condition_id("study-1", "condition_2") == "study-1_condition_2"

    def test_preserves_hyphens_and_underscores(self) -> None:
        assert generate_condition_id("ld-2025", "pilot_3") == "ld-2025_pilot_3"


class TestSyncConditions:
    def test_upserts_each_condition(self) -> None:
        """sync_conditions calls upsert once per condition."""
        c1 = _make_condition("condition_1")
        c2 = _make_condition("condition_2")
        mock_client = _mock_client_with_upsert_response([{"id": "s1_condition_1"}])
        # Override to return different data per call
        mock_response_1 = MagicMock()
        mock_response_1.data = [{"id": "s1_condition_1"}]
        mock_response_2 = MagicMock()
        mock_response_2.data = [{"id": "s1_condition_2"}]
        mock_client.table.return_value.upsert.return_value.execute.side_effect = [
            mock_response_1,
            mock_response_2,
        ]

        results = sync_conditions(mock_client, "s1", [c1, c2])

        assert mock_client.table.return_value.upsert.call_count == 2
        assert len(results) == 2

    def test_sets_correct_id_and_study_id(self) -> None:
        """Upsert payload has id={study_id}_{condition.name} and study_id."""
        condition = _make_condition("condition_1")
        mock_client = _mock_client_with_upsert_response([{"id": "s1_condition_1"}])

        sync_conditions(mock_client, "s1", [condition])

        payload = mock_client.table.return_value.upsert.call_args[0][0]
        assert payload["id"] == "s1_condition_1"
        assert payload["study_id"] == "s1"

    def test_payload_contains_procedures_and_dag(self) -> None:
        """Upsert payload includes serialized procedures and dag."""
        condition = _make_condition("condition_1")
        mock_client = _mock_client_with_upsert_response([{"id": "s1_condition_1"}])

        sync_conditions(mock_client, "s1", [condition])

        payload = mock_client.table.return_value.upsert.call_args[0][0]
        assert "procedures" in payload
        assert "dag" in payload
        assert "created_at" not in payload
        assert "updated_at" not in payload
        assert isinstance(payload["procedures"], dict)
        assert isinstance(payload["dag"], dict)

    def test_uses_on_conflict_id(self) -> None:
        """Upsert is called with on_conflict='id' for upsert semantics."""
        condition = _make_condition("condition_1")
        mock_client = _mock_client_with_upsert_response([{"id": "s1_condition_1"}])

        sync_conditions(mock_client, "s1", [condition])

        mock_client.table.return_value.upsert.assert_called_once_with(
            mock_client.table.return_value.upsert.call_args[0][0],
            on_conflict="id",
        )

    def test_returns_upserted_rows(self) -> None:
        """sync_conditions returns the list of rows returned by Supabase."""
        condition = _make_condition("condition_1")
        expected_row = {"id": "s1_condition_1", "study_id": "s1"}
        mock_client = _mock_client_with_upsert_response([expected_row])

        results = sync_conditions(mock_client, "s1", [condition])

        assert results == [expected_row]

    def test_raises_when_upsert_returns_no_data(self) -> None:
        """RuntimeError when upsert returns empty data."""
        condition = _make_condition("condition_1")
        mock_client = _mock_client_with_upsert_response([])

        with pytest.raises(RuntimeError, match="condition_1"):
            sync_conditions(mock_client, "s1", [condition])

    def test_empty_conditions_list_returns_empty(self) -> None:
        """sync_conditions with empty list returns [] without any upsert calls."""
        mock_client = MagicMock()

        results = sync_conditions(mock_client, "s1", [])

        mock_client.table.assert_not_called()
        assert results == []
