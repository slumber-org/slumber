"""Helpers for UI backend plugins."""

from __future__ import annotations

from typing import Any

from slumber.plugins.ui.base import UIBackend


def build_ui_backend_from_settings(
    backend_class: type[UIBackend],
    settings: dict[str, Any],
) -> UIBackend:
    """Instantiate a UI backend class and apply manifest settings.

    Args:
        backend_class: ``UIBackend`` subclass (registry value for ``slumber.ui_backends``).
        settings: ``study.ui.settings`` dict from the manifest.

    Returns:
        Backend instance after ``configure(settings)``.
    """
    backend = backend_class()
    backend.configure(settings)
    return backend
