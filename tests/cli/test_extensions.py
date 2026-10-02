"""Tests for attaching Typer apps from the slumber.cli entry-point group."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import typer
from typer.testing import CliRunner

from slumber.cli.extensions import CLI_ENTRY_POINT_GROUP, load_cli_extensions


def test_load_cli_extensions_attaches_typer_apps() -> None:
    root = typer.Typer()
    extension = typer.Typer()

    @extension.command("ping")
    def ping() -> None:
        """Extension ping command."""
        typer.echo("pong")

    entry = MagicMock()
    entry.name = "extra"
    entry.load.return_value = extension

    with patch("slumber.cli.extensions.entry_points") as mock_eps:
        mock_eps.return_value.select.return_value = [entry]
        load_cli_extensions(root)

    mock_eps.return_value.select.assert_called_once_with(group=CLI_ENTRY_POINT_GROUP)
    result = CliRunner().invoke(root, ["extra", "ping"])
    assert result.exit_code == 0
    assert "pong" in result.output


def test_load_cli_extensions_skips_non_typer() -> None:
    root = typer.Typer()
    entry = MagicMock()
    entry.name = "bad"
    entry.load.return_value = object()

    with patch("slumber.cli.extensions.entry_points") as mock_eps:
        mock_eps.return_value.select.return_value = [entry]
        load_cli_extensions(root)

    group_names = {getattr(group, "name", None) for group in root.registered_groups}
    assert "bad" not in group_names
    assert root.registered_groups == []
