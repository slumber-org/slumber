"""Tests for :func:`slumber_supabase.utils.get_database_url`."""

from __future__ import annotations

import pytest

from slumber_supabase.utils import get_database_url


def test_get_database_url_raises_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_database_url raises ValueError when DATABASE_URL is not set."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValueError, match="DATABASE_URL is not set"):
        get_database_url()


def test_get_database_url_raises_when_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_database_url raises when DATABASE_URL is empty or whitespace."""
    monkeypatch.setenv("DATABASE_URL", "   ")
    with pytest.raises(ValueError, match="DATABASE_URL is not set"):
        get_database_url()


def test_get_database_url_returns_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_database_url returns the trimmed DATABASE_URL value."""
    url = "postgresql://user:pass@localhost:5432/slumber"
    monkeypatch.setenv("DATABASE_URL", f"  {url}  ")
    assert get_database_url() == url
