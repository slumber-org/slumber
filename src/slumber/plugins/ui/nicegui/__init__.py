"""NiceGUI participant UI backend.

Provides a web-based participant app with login, procedure execution,
sleep monitoring, and session completion pages.
"""

from __future__ import annotations

from typing import Any

__all__ = ["NiceGUIBackend"]


def __getattr__(name: str) -> Any:
    if name == "NiceGUIBackend":
        from slumber.plugins.ui.nicegui.backend import NiceGUIBackend

        return NiceGUIBackend
    raise AttributeError(name)
