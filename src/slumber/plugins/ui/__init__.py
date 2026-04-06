"""Built-in and discovered UI backends (resolved via slumber.ui_backends entry point)."""

from slumber.plugins.ui.base import UIBackend
from slumber.plugins.ui.headless import HeadlessUIBackend
from slumber.plugins.ui.utils import build_ui_backend_from_settings

__all__ = [
    "HeadlessUIBackend",
    "UIBackend",
    "build_ui_backend_from_settings",
]
