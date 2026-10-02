"""Tests for backend run CRUD."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from slumber_supabase.backend.run import RunStatus, create_run, update_run


def test_create_run_inserts_and_returns_row() -> None:
    row = {"id": 7, "session_id": 42, "status": "running", "run_directory": ""}
    mock_client = MagicMock()
    mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[row]
    )

    result = create_run(mock_client, 42)

    assert result == row
    payload = mock_client.table.return_value.insert.call_args.args[0]
    assert payload["session_id"] == 42
    assert payload["status"] == RunStatus.RUNNING
    assert payload["run_directory"] == ""


def test_create_run_raises_when_no_data() -> None:
    mock_client = MagicMock()
    mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[]
    )
    with pytest.raises(RuntimeError, match="no data"):
        create_run(mock_client, 1)


def test_update_run_sets_status() -> None:
    row = {"id": 7, "status": "completed", "run_directory": "/tmp/run"}
    mock_chain = MagicMock()
    mock_chain.eq.return_value.execute.return_value = MagicMock(data=[row])
    mock_client = MagicMock()
    mock_client.table.return_value.update.return_value = mock_chain

    result = update_run(
        mock_client, 7, status=RunStatus.COMPLETED, run_directory="/tmp/run"
    )

    assert result == row
    payload = mock_client.table.return_value.update.call_args.args[0]
    assert payload["status"] == RunStatus.COMPLETED
    assert payload["run_directory"] == "/tmp/run"
    assert "end_time" in payload


def test_update_run_omits_run_directory_when_not_provided() -> None:
    mock_chain = MagicMock()
    mock_chain.eq.return_value.execute.return_value = MagicMock(data=[{"id": 7}])
    mock_client = MagicMock()
    mock_client.table.return_value.update.return_value = mock_chain

    update_run(mock_client, 7, status=RunStatus.FAILED)

    payload = mock_client.table.return_value.update.call_args.args[0]
    assert "run_directory" not in payload
    assert "end_time" in payload


def test_update_run_raises_when_not_found() -> None:
    mock_chain = MagicMock()
    mock_chain.eq.return_value.execute.return_value = MagicMock(data=[])
    mock_client = MagicMock()
    mock_client.table.return_value.update.return_value = mock_chain

    with pytest.raises(ValueError, match="Run 7 not found"):
        update_run(mock_client, 7, status=RunStatus.COMPLETED)
