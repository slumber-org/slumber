"""Tests for backend session CRUD."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from slumber.backend.session import (
    create_session,
    delete_session,
    get_active_session,
    list_sessions,
    update_session,
)


def test_create_session_inserts_payload() -> None:
    """create_session builds payload and returns created row."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [
        {
            "id": 10,
            "participant_id": 1,
            "earliest_start_at": "2025-03-12T22:00:00+00:00",
        }
    ]
    mock_table = MagicMock()
    mock_table.insert.return_value.execute.return_value = mock_response
    mock_client.table.return_value = mock_table

    earliest = datetime(2025, 3, 12, 22, 0, 0, tzinfo=timezone.utc)
    latest = datetime(2025, 3, 13, 6, 0, 0, tzinfo=timezone.utc)
    result = create_session(
        mock_client,
        participant_id="p1",
        earliest_start_at=earliest,
        latest_start_at=latest,
    )

    call_args = mock_table.insert.call_args[0][0]
    assert call_args["participant_id"] == "p1"
    assert (
        "2025-03-12" in call_args["earliest_start_at"]
        and "22:00" in call_args["earliest_start_at"]
    )
    assert (
        "2025-03-13" in call_args["latest_start_at"]
        and "06:00" in call_args["latest_start_at"]
    )
    assert result["id"] == 10


def test_create_session_raises_when_overlap() -> None:
    """create_session raises ValueError when participant has overlapping session."""
    mock_client = MagicMock()
    existing_response = MagicMock()
    existing_response.data = [
        {
            "id": 1,
            "earliest_start_at": "2025-03-12T22:00:00+00:00",
            "latest_start_at": "2025-03-13T06:00:00+00:00",
        }
    ]
    mock_table = MagicMock()
    mock_table.select.return_value.eq.return_value.execute.return_value = (
        existing_response
    )
    mock_client.table.return_value = mock_table

    earliest = datetime(2025, 3, 12, 23, 0, 0, tzinfo=timezone.utc)
    latest = datetime(2025, 3, 13, 7, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="overlapping"):
        create_session(
            mock_client,
            participant_id="p1",
            earliest_start_at=earliest,
            latest_start_at=latest,
        )


def test_list_sessions_without_filter() -> None:
    """list_sessions returns all rows when participant_id is None."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [{"id": 1, "earliest_start_at": "2025-03-12T22:00:00+00:00"}]
    mock_table = MagicMock()
    mock_table.select.return_value.execute.return_value = mock_response
    mock_client.table.return_value = mock_table

    result = list_sessions(mock_client)

    assert len(result) == 1
    mock_table.select.assert_called_once_with("*")
    mock_table.select.return_value.execute.assert_called_once()


def test_list_sessions_with_participant_filter() -> None:
    """list_sessions applies eq filter when participant_id given."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = []
    mock_chain = MagicMock()
    mock_chain.execute.return_value = mock_response
    mock_chain.eq.return_value = mock_chain
    mock_table = MagicMock()
    mock_table.select.return_value = mock_chain
    mock_client.table.return_value = mock_table

    list_sessions(mock_client, participant_id="p3")

    mock_chain.eq.assert_called_once_with("participant_id", "p3")


def test_update_session_sends_only_provided_fields() -> None:
    """update_session builds update payload from non-None args; checks no overlap."""
    mock_client = MagicMock()
    # Overlap check: fetch current session (for participant_id and existing window)
    current_response = MagicMock()
    current_response.data = [
        {
            "participant_id": "p1",
            "earliest_start_at": "2025-03-14T22:00:00+00:00",
            "latest_start_at": "2025-03-15T06:00:00+00:00",
        }
    ]
    # Overlap check: fetch other sessions for participant (none overlapping)
    other_sessions_response = MagicMock()
    other_sessions_response.data = []
    update_response = MagicMock()
    update_response.data = [{"id": 5, "earliest_start_at": "2025-03-15T22:00:00+00:00"}]

    mock_table = MagicMock()
    select_chain = MagicMock()
    select_chain.eq.return_value = select_chain
    select_chain.execute.side_effect = [
        current_response,
        other_sessions_response,
    ]
    mock_table.select.return_value = select_chain
    update_chain = MagicMock()
    update_chain.eq.return_value.execute.return_value = update_response
    mock_table.update.return_value = update_chain
    mock_client.table.return_value = mock_table

    new_earliest = datetime(2025, 3, 15, 22, 0, 0, tzinfo=timezone.utc)
    result = update_session(
        mock_client,
        session_id=5,
        earliest_start_at=new_earliest,
    )

    call_args = mock_table.update.call_args[0][0]
    assert "earliest_start_at" in call_args
    assert "2025-03-15" in call_args["earliest_start_at"]
    update_chain.eq.assert_called_once_with("id", 5)
    assert result["id"] == 5


def test_update_session_raises_when_overlap() -> None:
    """update_session raises ValueError when new window overlaps another session."""
    mock_client = MagicMock()
    current_response = MagicMock()
    current_response.data = [
        {
            "participant_id": "p1",
            "earliest_start_at": "2025-03-14T22:00:00+00:00",
            "latest_start_at": "2025-03-15T06:00:00+00:00",
        }
    ]
    other_response = MagicMock()
    other_response.data = [
        {
            "id": "sess-99",
            "earliest_start_at": "2025-03-15T22:00:00+00:00",
            "latest_start_at": "2025-03-16T06:00:00+00:00",
        }
    ]
    mock_table = MagicMock()
    select_chain = MagicMock()
    select_chain.eq.return_value = select_chain
    select_chain.execute.side_effect = [current_response, other_response]
    mock_table.select.return_value = select_chain
    mock_client.table.return_value = mock_table

    new_earliest = datetime(2025, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
    new_latest = datetime(2025, 3, 16, 8, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="overlapping"):
        update_session(
            mock_client,
            session_id=5,
            earliest_start_at=new_earliest,
            latest_start_at=new_latest,
        )


def test_update_session_raises_when_not_found() -> None:
    """update_session raises when response has no data."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = []
    mock_chain = MagicMock()
    mock_chain.execute.return_value = mock_response
    mock_chain.eq.return_value = mock_chain
    mock_table = MagicMock()
    mock_table.update.return_value = mock_chain
    mock_client.table.return_value = mock_table

    with pytest.raises(ValueError, match="Session 99 not found"):
        update_session(mock_client, 99, condition_id="condition_1")


def test_delete_session_raises_when_not_found() -> None:
    """delete_session raises when no row deleted."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = []
    mock_chain = MagicMock()
    mock_chain.execute.return_value = mock_response
    mock_chain.eq.return_value = mock_chain
    mock_table = MagicMock()
    mock_table.delete.return_value = mock_chain
    mock_client.table.return_value = mock_table

    with pytest.raises(ValueError, match="Session 7 not found"):
        delete_session(mock_client, 7)


def test_list_sessions_with_study_id_filters_by_participant_ids() -> None:
    """list_sessions with study_id fetches participant ids then filters sessions."""
    mock_client = MagicMock()
    part_response = MagicMock()
    part_response.data = [{"id": "s1_sub-001"}, {"id": "s1_sub-002"}]
    sess_response = MagicMock()
    sess_response.data = [
        {"id": 10, "participant_id": "s1_sub-001"},
        {"id": 11, "participant_id": "s1_sub-002"},
    ]
    part_table = MagicMock()
    part_table.select.return_value.eq.return_value.execute.return_value = part_response
    sess_chain = MagicMock()
    sess_chain.in_.return_value.execute.return_value = sess_response
    sess_table = MagicMock()
    sess_table.select.return_value = sess_chain
    mock_client.table.side_effect = (
        lambda name: part_table if name == "participant" else sess_table
    )

    result = list_sessions(mock_client, study_id="s1")

    assert len(result) == 2
    part_table.select.assert_called_once_with("id")
    part_table.select.return_value.eq.assert_called_once_with("study_id", "s1")
    sess_chain.in_.assert_called_once_with(
        "participant_id", ["s1_sub-001", "s1_sub-002"]
    )


def test_list_sessions_with_study_id_returns_empty_when_no_participants() -> None:
    """list_sessions with study_id returns [] when no participants in study."""
    mock_client = MagicMock()
    part_response = MagicMock()
    part_response.data = []
    part_table = MagicMock()
    part_table.select.return_value.eq.return_value.execute.return_value = part_response
    mock_client.table.return_value = part_table

    result = list_sessions(mock_client, study_id="s1")

    assert result == []


def test_delete_session_succeeds_when_row_deleted() -> None:
    """delete_session returns None when row is deleted."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [{"id": 7}]
    mock_chain = MagicMock()
    mock_chain.execute.return_value = mock_response
    mock_chain.eq.return_value = mock_chain
    mock_table = MagicMock()
    mock_table.delete.return_value = mock_chain
    mock_client.table.return_value = mock_table

    delete_session(mock_client, 7)  # no raise


def test_get_active_session_returns_row() -> None:
    """get_active_session returns first row within the start window."""
    now = datetime(2025, 10, 1, 23, 0, 0, tzinfo=timezone.utc)
    row = {"id": 99, "participant_id": "s1_sub-001", "condition_id": "s1_ctrl"}
    mock_chain = MagicMock()
    mock_chain.eq.return_value = mock_chain
    mock_chain.lte.return_value = mock_chain
    mock_chain.gte.return_value.execute.return_value = MagicMock(data=[row])
    mock_table = MagicMock()
    mock_table.select.return_value = mock_chain
    mock_client = MagicMock()
    mock_client.table.return_value = mock_table

    result = get_active_session(mock_client, "s1_sub-001", now)

    assert result == row
    mock_chain.eq.assert_called_once_with("participant_id", "s1_sub-001")


def test_get_active_session_raises_when_no_session() -> None:
    """get_active_session raises ValueError when no session is within window."""
    now = datetime(2025, 10, 1, 23, 0, 0, tzinfo=timezone.utc)
    mock_chain = MagicMock()
    mock_chain.eq.return_value = mock_chain
    mock_chain.lte.return_value = mock_chain
    mock_chain.gte.return_value.execute.return_value = MagicMock(data=[])
    mock_table = MagicMock()
    mock_table.select.return_value = mock_chain
    mock_client = MagicMock()
    mock_client.table.return_value = mock_table

    with pytest.raises(ValueError, match="No session"):
        get_active_session(mock_client, "s1_sub-001", now)
