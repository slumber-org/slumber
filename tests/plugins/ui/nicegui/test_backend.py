"""Tests for the NiceGUI UI backend."""

from __future__ import annotations

from slumber.plugins.ui.base import UIBackend
from slumber.plugins.ui.nicegui import NiceGUIBackend


class TestNiceGUIBackend:
    def test_is_ui_backend(self) -> None:
        backend = NiceGUIBackend()
        assert isinstance(backend, UIBackend)

    def test_has_required_methods(self) -> None:
        backend = NiceGUIBackend()
        assert hasattr(backend, "configure")
        assert callable(backend.configure)
        assert hasattr(backend, "run")
        assert callable(backend.run)
