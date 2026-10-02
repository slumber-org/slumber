"""CLI entry point and command groups.

Core commands: ``study`` and ``doctor``. Extra Typer apps are loaded from the
``slumber.cli`` entry-point group at import time.
"""

from slumber.cli.main import app

__all__ = ["app"]
