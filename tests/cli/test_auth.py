"""Tests for auth CLI (slumber auth login, logout, status, etc.)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from slumber.cli.main import app

pytestmark = pytest.mark.supabase


class TestAuthLogout:
    """Tests for slumber auth logout."""

    def test_logout_clears_session_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """auth logout removes session file and exits 0."""
        session_file = tmp_path / "session.json"
        session_file.parent.mkdir(parents=True, exist_ok=True)
        session_file.write_text(
            json.dumps({"access_token": "a", "refresh_token": "r"}),
            encoding="utf-8",
        )
        monkeypatch.setenv("SLUMBER_SESSION_FILE", str(session_file))
        runner = CliRunner()
        result = runner.invoke(app, ["auth", "logout"])
        assert result.exit_code == 0
        assert "Signed out" in result.output
        assert not session_file.exists()

    def test_logout_succeeds_when_no_session_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """auth logout exits 0 even when no session file exists."""
        monkeypatch.setenv("SLUMBER_SESSION_FILE", str(tmp_path / "none.json"))
        runner = CliRunner()
        result = runner.invoke(app, ["auth", "logout"])
        assert result.exit_code == 0


class TestAuthStatus:
    """Tests for slumber auth status."""

    def test_status_not_signed_in_when_no_session(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """auth status prints Not signed in when no session file."""
        monkeypatch.setenv("SLUMBER_SESSION_FILE", str(tmp_path / "none.json"))
        monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "key")
        runner = CliRunner()
        result = runner.invoke(app, ["auth", "status"])
        assert result.exit_code == 0
        assert "Not signed in" in result.output

    def test_status_shows_email_when_session_valid(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """auth status prints email when session file exists and client returns user."""
        session_file = tmp_path / "sess.json"
        session_file.parent.mkdir(parents=True, exist_ok=True)
        session_file.write_text(
            json.dumps({"access_token": "at", "refresh_token": "rt"}),
            encoding="utf-8",
        )
        monkeypatch.setenv("SLUMBER_SESSION_FILE", str(session_file))
        monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
        monkeypatch.setenv("SUPABASE_ANON_KEY", "key")
        mock_user = type("User", (), {"email": "u@example.com"})()
        mock_session = type("Session", (), {"user": mock_user})()
        mock_auth = MagicMock()
        mock_auth.get_session.return_value = mock_session
        mock_client = MagicMock()
        mock_client.auth = mock_auth

        with patch(
            "slumber.supabase.auth.client.get_authenticated_client",
            return_value=mock_client,
        ):
            runner = CliRunner()
            result = runner.invoke(app, ["auth", "status"])
        assert result.exit_code == 0
        assert "u@example.com" in result.output


class TestAuthLogin:
    """Tests for slumber auth login (requires env + mock)."""

    def test_login_fails_without_supabase_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """auth login exits 1 when SUPABASE_URL is not set."""
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.setenv("SUPABASE_ANON_KEY", "key")
        runner = CliRunner()
        result = runner.invoke(
            app, ["auth", "login", "--email", "u@e.com", "--password", "secret"]
        )
        assert result.exit_code == 1
        assert "SUPABASE_URL" in result.output or "Login failed" in result.output
