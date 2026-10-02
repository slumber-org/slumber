"""Tests for auth client (session path, env, save/load session)."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

from slumber_supabase.auth.client import (
    _PACKAGE_NAME,
    SESSION_FILENAME,
    _save_session,
    clear_saved_session,
    get_client,
    get_session_path,
    load_session,
)


def test_get_session_path_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default session path is ~/.config/<package>/session.json."""
    monkeypatch.delenv("SLUMBER_SESSION_FILE", raising=False)
    path = get_session_path()
    assert path == Path.home() / ".config" / _PACKAGE_NAME / SESSION_FILENAME


def test_get_session_path_from_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Session path can be overridden via SLUMBER_SESSION_FILE."""
    custom = tmp_path / "custom_session.json"
    monkeypatch.setenv("SLUMBER_SESSION_FILE", str(custom))
    assert get_session_path() == custom


def test_get_client_raises_when_supabase_url_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_client raises when SUPABASE_URL is not set."""
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")
    with pytest.raises(ValueError, match="SUPABASE_URL"):
        get_client()


def test_get_client_raises_when_anon_key_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_client raises when SUPABASE_ANON_KEY is not set."""
    monkeypatch.setenv("SUPABASE_URL", "https://xxx.supabase.co")
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    with pytest.raises(ValueError, match="SUPABASE_ANON_KEY"):
        get_client()


def test_get_client_returns_client_with_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_client returns a Supabase client when env is set."""
    monkeypatch.setenv("SUPABASE_URL", "https://xxx.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")
    client = get_client()
    assert client is not None
    assert hasattr(client, "auth")
    assert hasattr(client, "table")


def test_save_and_load_session_roundtrip(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """_save_session and load_session roundtrip tokens."""
    monkeypatch.setenv("SLUMBER_SESSION_FILE", str(tmp_path / "sess.json"))
    _save_session("access-123", "refresh-456")
    loaded = load_session()
    assert loaded == ("access-123", "refresh-456")


@pytest.mark.skipif(os.name == "nt", reason="POSIX-style file permissions")
def test_save_session_sets_restrictive_file_permissions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """_save_session writes session file with owner-only permissions."""
    path = tmp_path / "sess.json"
    monkeypatch.setenv("SLUMBER_SESSION_FILE", str(path))

    _save_session("access-123", "refresh-456")

    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_load_session_returns_none_when_file_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """load_session returns None when file does not exist."""
    monkeypatch.setenv("SLUMBER_SESSION_FILE", str(tmp_path / "nonexistent.json"))
    assert load_session() is None


def test_load_session_returns_none_when_invalid_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """load_session returns None when file is invalid JSON."""
    path = tmp_path / "bad.json"
    path.write_text("not json")
    monkeypatch.setenv("SLUMBER_SESSION_FILE", str(path))
    assert load_session() is None


def test_clear_saved_session_removes_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """clear_saved_session removes the session file if present."""
    path = tmp_path / "sess.json"
    path.write_text(
        json.dumps({"access_token": "a", "refresh_token": "r"}), encoding="utf-8"
    )
    monkeypatch.setenv("SLUMBER_SESSION_FILE", str(path))
    assert path.is_file()
    clear_saved_session()
    assert not path.is_file()


def test_get_authenticated_client_raises_when_no_session(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """get_authenticated_client raises when session file is missing."""
    monkeypatch.setenv("SLUMBER_SESSION_FILE", str(tmp_path / "none.json"))
    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "key")
    from slumber_supabase.auth.client import get_authenticated_client

    with pytest.raises(ValueError, match="Not logged in"):
        get_authenticated_client()
