"""Tests for the NiceGUI UI backend."""

from __future__ import annotations

from slumber.ext.ui.nicegui import NiceGUIBackend
from slumber.plugins.types import UIBackend


class TestNiceGUIBackend:
    def test_implements_ui_backend_protocol(self) -> None:
        backend = NiceGUIBackend()
        assert isinstance(backend, UIBackend)

    def test_has_run_method(self) -> None:
        backend = NiceGUIBackend()
        assert hasattr(backend, "run")
        assert callable(backend.run)
