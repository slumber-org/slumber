"""NiceGUI2 participant UI backend."""

from __future__ import annotations

from typing import Any

__all__ = ["NiceGUI2Backend"]


def __getattr__(name: str) -> Any:
    if name == "NiceGUI2Backend":
        from slumber.plugins.ui.nicegui2.backend import NiceGUI2Backend

        return NiceGUI2Backend
    raise AttributeError(name)
