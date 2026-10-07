"""Tests for top-level slumber CLI options."""

from __future__ import annotations

from importlib import metadata

from typer.testing import CliRunner

from slumber.cli.main import app


class TestVersionOption:
    def test_prints_installed_version(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert result.output.strip() == f"slumber {metadata.version('slumber')}"

    def test_exits_before_running_subcommand(self, runner: CliRunner) -> None:
        """--version is eager: the subcommand after it is never invoked."""
        result = runner.invoke(app, ["--version", "doctor"])

        assert result.exit_code == 0
        assert result.output.strip() == f"slumber {metadata.version('slumber')}"
