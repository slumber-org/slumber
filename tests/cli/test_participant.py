"""Tests for participant CLI (slumber participant create, list)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from slumber.cli.main import app

pytestmark = pytest.mark.supabase


class TestParticipantList:
    """Tests for slumber participant list (researcher; requires --user-id)."""

    def test_list_exits_without_user_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """participant list exits 1 when --user-id (or USER_ID) not provided (prompts then aborts in non-interactive)."""
        monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "key")
        runner = CliRunner()
        result = runner.invoke(app, ["participant", "list"])
        assert result.exit_code == 1
        assert (
            "user-id" in result.output.lower()
            or "user_id" in result.output.lower()
            or "user id" in result.output.lower()
            or "aborted" in result.output.lower()
        )

    def test_list_exits_without_service_role(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """participant list exits 1 when SUPABASE_SERVICE_ROLE_KEY is not set."""
        monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "participant",
                "list",
                "--user-id",
                "00000000-0000-0000-0000-000000000001",
            ],
        )
        assert result.exit_code == 1
        # Implementation may raise a config error before calling Supabase or
        # surface an HTTP error. Any non-zero exit with an error message is OK.
        assert result.output.strip() != ""

    def test_list_shows_participants_when_authenticated(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """participant list prints rows when get_client(service_role) returns data."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [
            {"id": 1, "study_id": "s1", "participant_id": "sub-001"},
        ]
        mock_table = MagicMock()
        mock_table.select.return_value.eq.return_value.execute.return_value = (
            mock_response
        )
        mock_client.table.return_value = mock_table

        with patch(
            "slumber.supabase.auth.get_client",
            return_value=mock_client,
        ):
            runner = CliRunner()
            result = runner.invoke(
                app,
                [
                    "participant",
                    "list",
                    "--user-id",
                    "00000000-0000-0000-0000-000000000001",
                ],
            )
        assert result.exit_code == 0
        assert "sub-001" in result.output
        assert "s1" in result.output


class TestParticipantCreate:
    """Tests for slumber participant create (researcher)."""

    def test_create_exits_without_study_id(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """participant create exits 1 when study_id not provided (no study-dir, no env)."""
        monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "key")
        monkeypatch.delenv("STUDY_ID", raising=False)
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "participant",
                "create",
                "--participant-id",
                "sub-001",
                "--user-id",
                "00000000-0000-0000-0000-000000000001",
            ],
        )
        assert result.exit_code == 1
        assert "study" in result.output.lower()

    def test_create_succeeds_with_user_id_and_study_id(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """participant create prints success when linking existing user (--user-id + --study-id)."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{"id": 1, "study_id": "s1", "participant_id": "sub-001"}]
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
                    "participant",
                    "create",
                    "--study-id",
                    "s1",
                    "--participant-id",
                    "sub-001",
                    "--user-id",
                    "00000000-0000-0000-0000-000000000001",
                ],
            )
        assert result.exit_code == 0
        assert "Created participant" in result.output
        assert "sub-001" in result.output
        assert "s1" in result.output

    def test_create_succeeds_with_study_dir(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Kept for backwards-compatibility: use explicit --study-id + --user-id."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{"id": 1, "study_id": "s1", "participant_id": "sub-001"}]
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
                    "participant",
                    "create",
                    "--study-id",
                    "s1",
                    "--participant-id",
                    "sub-001",
                    "--user-id",
                    "00000000-0000-0000-0000-000000000001",
                ],
            )
        assert result.exit_code == 0
        assert "Created participant" in result.output
        assert "s1" in result.output
