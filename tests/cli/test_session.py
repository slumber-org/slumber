"""Tests for session CLI (slumber session create, list, update, delete)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from slumber.cli.main import app

pytestmark = pytest.mark.supabase


class TestSessionList:
    """Tests for slumber session list (researcher)."""

    def test_list_exits_without_service_role(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """session list exits 1 when SUPABASE_SERVICE_ROLE_KEY is not set."""
        monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
        runner = CliRunner()
        result = runner.invoke(app, ["session", "list"])
        assert result.exit_code == 1
        # Implementation may raise a config error before calling Supabase or
        # surface an HTTP error. Any non-zero exit with an error message is OK.
        assert result.output.strip() != ""

    def test_list_shows_sessions_when_authenticated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """session list prints rows when get_client(service_role) returns data."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [
            {
                "id": 1,
                "participant_id": "s1_sub-001",
                "earliest_start_at": "2025-03-12T22:00:00+00:00",
                "latest_start_at": "2025-03-13T06:00:00+00:00",
                "condition_id": None,
            },
        ]
        mock_table = MagicMock()
        mock_table.select.return_value.execute.return_value = mock_response
        mock_client.table.return_value = mock_table

        with patch(
            "slumber.supabase.auth.get_client",
            return_value=mock_client,
        ):
            runner = CliRunner()
            result = runner.invoke(app, ["session", "list"])
        assert result.exit_code == 0
        assert "2025-03-12" in result.output
        assert "earliest_start_at" in result.output


class TestSessionCreate:
    """Tests for slumber session create (researcher)."""

    def test_create_exits_without_service_role(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """session create exits 1 when SUPABASE_SERVICE_ROLE_KEY is not set."""
        monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "session",
                "create",
                "--participant-id",
                "1",
                "--earliest-start-at",
                "2025-03-12T22:00:00Z",
                "--latest-start-at",
                "2025-03-13T06:00:00Z",
            ],
        )
        assert result.exit_code == 1

    def test_create_succeeds_with_valid_args(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """session create prints success when backend returns row (with study_id)."""
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

        with patch(
            "slumber.supabase.auth.get_client",
            return_value=mock_client,
        ):
            runner = CliRunner()
            result = runner.invoke(
                app,
                [
                    "session",
                    "create",
                    "--study-id",
                    "s1",
                    "--participant-id",
                    "1",
                    "--earliest-start-at",
                    "2025-03-12T22:00:00Z",
                    "--latest-start-at",
                    "2025-03-13T06:00:00Z",
                ],
            )
        assert result.exit_code == 0
        assert "Created session" in result.output
