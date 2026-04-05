"""Tests for auth operations (sign_in, sign_up, sign_out, update_password)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from slumber.supabase.auth.client import load_session
from slumber.supabase.auth.operations import sign_in, sign_out, sign_up, update_password


@pytest.fixture
def mock_session() -> MagicMock:
    """Fake session with tokens."""
    s = MagicMock()
    s.access_token = "access-token"
    s.refresh_token = "refresh-token"
    return s


@pytest.fixture
def mock_auth_response(mock_session: MagicMock) -> MagicMock:
    """Fake auth response with session."""
    r = MagicMock()
    r.session = mock_session
    return r


def test_sign_in_calls_client_and_saves_session(
    mock_auth_response: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: str,
) -> None:
    """sign_in calls sign_in_with_password and persists session."""
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")
    monkeypatch.setenv("SLUMBER_SESSION_FILE", str(tmp_path) + "/sess.json")
    mock_client = MagicMock()
    mock_client.auth.sign_in_with_password.return_value = mock_auth_response

    with patch("slumber.supabase.auth.operations.get_client", return_value=mock_client):
        sign_in("u@example.com", "secret")

    mock_client.auth.sign_in_with_password.assert_called_once_with(
        {"email": "u@example.com", "password": "secret"}
    )
    loaded = load_session()
    assert loaded == ("access-token", "refresh-token")


def test_sign_up_calls_client_and_saves_session(
    mock_auth_response: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: str,
) -> None:
    """sign_up calls sign_up and persists session when returned."""
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")
    monkeypatch.setenv("SLUMBER_SESSION_FILE", str(tmp_path) + "/sess.json")
    mock_client = MagicMock()
    mock_client.auth.sign_up.return_value = mock_auth_response

    with patch("slumber.supabase.auth.operations.get_client", return_value=mock_client):
        sign_up("new@example.com", "secret")

    mock_client.auth.sign_up.assert_called_once_with(
        {"email": "new@example.com", "password": "secret"}
    )
    loaded = load_session()
    assert loaded == ("access-token", "refresh-token")


def test_sign_out_clears_session_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """sign_out clears the session file."""
    session_file = tmp_path / "sess.json"
    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text(
        '{"access_token":"a","refresh_token":"r"}', encoding="utf-8"
    )
    monkeypatch.setenv("SLUMBER_SESSION_FILE", str(session_file))
    mock_client = MagicMock()

    with patch("slumber.supabase.auth.operations.get_client", return_value=mock_client):
        sign_out()

    assert not session_file.exists()


def test_update_password_calls_update_user(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """update_password uses authenticated client and calls update_user."""
    session_file = tmp_path / "sess.json"
    session_file.parent.mkdir(parents=True, exist_ok=True)
    session_file.write_text(
        '{"access_token":"access","refresh_token":"refresh"}',
        encoding="utf-8",
    )
    monkeypatch.setenv("SLUMBER_SESSION_FILE", str(session_file))
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")
    mock_client = MagicMock()

    with patch(
        "slumber.supabase.auth.operations.get_authenticated_client",
        return_value=mock_client,
    ):
        update_password("new-secret")

    mock_client.auth.update_user.assert_called_once_with({"password": "new-secret"})
