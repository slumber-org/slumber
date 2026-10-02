"""Typer application and top-level commands."""

from __future__ import annotations

from pathlib import Path

import typer
from dotenv.main import load_dotenv

from slumber.cli.doctor import doctor_command
from slumber.cli.extensions import load_cli_extensions
from slumber.cli.logging import configure_cli_logging
from slumber.cli.study import study_app

app = typer.Typer(
    name="slumber",
    help="Sleep Logging and Unsupervised Monitoring through BioElectrical Recordings.",
)
app.add_typer(study_app, name="study")
app.command("doctor")(doctor_command)
load_cli_extensions(app)


@app.callback()
def _callback(
    env: Path | None = typer.Option(
        None,
        "--env",
        "-e",
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
        help="Path to an environment file to load (overrides auto-discovered .env).",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging (DEBUG level).",
    ),
) -> None:
    """SLUMBER — Sleep Logging and Unsupervised Monitoring through BioElectrical Recordings."""
    load_dotenv(dotenv_path=env)
    configure_cli_logging(verbose=verbose)
