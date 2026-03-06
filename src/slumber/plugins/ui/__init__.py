"""Built-in and discovered UI backends (resolved via slumber.ui_backends entry point)."""

from slumber.plugins.ui.headless import HeadlessUIBackend

__all__ = ["HeadlessUIBackend"]
