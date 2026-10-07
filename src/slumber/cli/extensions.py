"""Discover and attach optional Typer apps from the ``slumber.cli`` group."""

from __future__ import annotations

try:
    from importlib.metadata import entry_points
except ImportError:
    from importlib_metadata import entry_points  # type: ignore[import-untyped]

import typer
from loguru import logger

CLI_ENTRY_POINT_GROUP = "slumber.cli"


def load_cli_extensions(app: typer.Typer) -> None:
    """Attach Typer apps registered under the ``slumber.cli`` entry-point group.

    Each entry point name becomes a subcommand group on *app*. Invalid or
    unloadable extensions are skipped with a warning so core CLI still starts.

    Args:
        app: Root Typer application to extend.
    """
    all_entry_points = entry_points()
    group_entry_points = (
        all_entry_points.select(group=CLI_ENTRY_POINT_GROUP)
        if hasattr(all_entry_points, "select")
        else all_entry_points.get(CLI_ENTRY_POINT_GROUP, [])
    )

    for entry_point in group_entry_points:
        try:
            loaded = entry_point.load()
        except Exception as error:  # noqa: BLE001
            logger.warning(
                "Failed to load CLI extension {!r}: {}",
                entry_point.name,
                error,
            )
            continue

        if not isinstance(loaded, typer.Typer):
            logger.warning(
                "Skipping CLI extension {!r}: expected typer.Typer, got {!r}.",
                entry_point.name,
                type(loaded).__name__,
            )
            continue

        app.add_typer(loaded, name=entry_point.name)
