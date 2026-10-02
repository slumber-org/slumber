"""Tests for backend participant CRUD."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from slumber_supabase.backend.participant import (
    create_participant,
    create_participant_for_user,
    get_participant_for_study,
    list_participants,
)


def test_create_participant_inserts_with_current_user_id() -> None:
    """create_participant uses current user id and returns created row."""
    mock_client = MagicMock()
    mock_user = MagicMock()
    mock_user.id = "auth-uuid-123"
    mock_session = MagicMock()
    mock_session.user = mock_user
    mock_client.auth.get_session.return_value = mock_session

    mock_response = MagicMock()
    mock_response.data = [
        {
            "id": 1,
            "study_id": "s1",
            "participant_id": "sub-001",
            "auth_user_id": "auth-uuid-123",
        }
    ]
    mock_table = MagicMock()
    mock_table.insert.return_value.execute.return_value = mock_response
    mock_client.table.return_value = mock_table

    result = create_participant(mock_client, study_id="s1", participant_id="sub-001")

    mock_client.table.assert_called_once_with("participant")
    mock_table.insert.assert_called_once()
    call_args = mock_table.insert.call_args[0][0]
    assert call_args["study_id"] == "s1"
    assert call_args["participant_id"] == "sub-001"
    assert call_args["auth_user_id"] == "auth-uuid-123"
    assert result["id"] == 1
    assert result["participant_id"] == "sub-001"


def test_create_participant_raises_when_not_authenticated() -> None:
    """create_participant raises when client has no session user."""
    mock_client = MagicMock()
    mock_client.auth.get_session.return_value = None

    with pytest.raises(ValueError, match="Not authenticated"):
        create_participant(mock_client, study_id="s1", participant_id="sub-001")


def test_list_participants_returns_data() -> None:
    """list_participants returns list of rows from table select."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [
        {"id": 1, "study_id": "s1", "participant_id": "sub-001"},
        {"id": 2, "study_id": "s2", "participant_id": "sub-002"},
    ]
    mock_table = MagicMock()
    mock_table.select.return_value.execute.return_value = mock_response
    mock_client.table.return_value = mock_table

    result = list_participants(mock_client)

    assert len(result) == 2
    assert result[0]["participant_id"] == "sub-001"
    assert result[1]["study_id"] == "s2"


def test_list_participants_returns_empty_list_when_no_data() -> None:
    """list_participants returns empty list when response has no data."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = None
    mock_table = MagicMock()
    mock_table.select.return_value.execute.return_value = mock_response
    mock_client.table.return_value = mock_table

    result = list_participants(mock_client)

    assert result == []


def test_create_participant_for_user_inserts_with_given_auth_user_id() -> None:
    """create_participant_for_user inserts row with given auth_user_id (service role)."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [
        {
            "id": 1,
            "study_id": "s1",
            "participant_id": "sub-001",
            "auth_user_id": "uuid-1",
        },
    ]
    mock_table = MagicMock()
    mock_table.insert.return_value.execute.return_value = mock_response
    mock_client.table.return_value = mock_table

    result = create_participant_for_user(
        mock_client,
        study_id="s1",
        participant_id="sub-001",
        auth_user_id="uuid-1",
    )

    call_args = mock_table.insert.call_args[0][0]
    assert call_args["auth_user_id"] == "uuid-1"
    assert result["id"] == 1


def test_list_participants_with_auth_user_id_filters() -> None:
    """list_participants with auth_user_id applies eq filter."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [{"id": 1, "study_id": "s1", "participant_id": "sub-001"}]
    mock_chain = MagicMock()
    mock_chain.eq.return_value.execute.return_value = mock_response
    mock_table = MagicMock()
    mock_table.select.return_value = mock_chain
    mock_client.table.return_value = mock_table

    result = list_participants(mock_client, auth_user_id="uuid-1")

    assert len(result) == 1
    mock_chain.eq.assert_called_once_with("auth_user_id", "uuid-1")


def test_get_participant_for_study_returns_row() -> None:
    """get_participant_for_study returns first row filtered by study_id."""
    row = {"id": "s1_sub-001", "study_id": "s1", "participant_id": "sub-001"}
    mock_chain = MagicMock()
    mock_chain.eq.return_value.execute.return_value = MagicMock(data=[row])
    mock_table = MagicMock()
    mock_table.select.return_value = mock_chain
    mock_client = MagicMock()
    mock_client.table.return_value = mock_table

    result = get_participant_for_study(mock_client, "s1")

    assert result == row
    mock_chain.eq.assert_called_once_with("study_id", "s1")


def test_get_participant_for_study_raises_when_not_found() -> None:
    """get_participant_for_study raises ValueError when no row returned."""
    mock_chain = MagicMock()
    mock_chain.eq.return_value.execute.return_value = MagicMock(data=[])
    mock_table = MagicMock()
    mock_table.select.return_value = mock_chain
    mock_client = MagicMock()
    mock_client.table.return_value = mock_table

    with pytest.raises(ValueError, match="not a participant"):
        get_participant_for_study(mock_client, "s1")
