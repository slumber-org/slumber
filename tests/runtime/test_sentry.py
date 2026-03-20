"""Tests for init_sentry (no-op without DSN, initializes when DSN is set)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from slumber.runtime.sentry import init_sentry


class TestInitSentry:
    def test_returns_false_when_dsn_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("SENTRY_DSN", raising=False)
        assert init_sentry("my-study") is False

    def test_returns_false_when_dsn_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SENTRY_DSN", "")
        assert init_sentry("my-study") is False

    def test_returns_true_and_calls_sentry_init_when_dsn_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SENTRY_DSN", "https://key@sentry.io/123")
        mock_sdk = MagicMock()
        with patch.dict("sys.modules", {"sentry_sdk": mock_sdk}):
            result = init_sentry("my-study")
        assert result is True
        mock_sdk.init.assert_called_once_with(dsn="https://key@sentry.io/123")

    def test_sets_study_id_tag_when_dsn_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SENTRY_DSN", "https://key@sentry.io/123")
        mock_sdk = MagicMock()
        with patch.dict("sys.modules", {"sentry_sdk": mock_sdk}):
            init_sentry("my-study")
        mock_sdk.set_tag.assert_called_once_with("study_id", "my-study")

    def test_returns_false_when_sentry_sdk_not_installed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SENTRY_DSN", "https://key@sentry.io/123")
        with patch.dict("sys.modules", {"sentry_sdk": None}):
            result = init_sentry("my-study")
        assert result is False
