"""Typer application and top-level commands."""

from __future__ import annotations

from pathlib import Path

import typer
from dotenv.main import load_dotenv

from slumber.cli.doctor import doctor_command
from slumber.cli.logging import configure_cli_logging
from slumber.cli.study import study_app
from slumber.supabase.utils import is_supabase_extra_installed

app = typer.Typer(
    name="slumber",
    help="Sleep Logging and Unsupervised Monitoring through BioElectrical Recordings.",
)
app.add_typer(study_app, name="study")
app.command("doctor")(doctor_command)

# Supabase-backed commands only needed (and only appear in --help)
# when slumber[supabase] is installed.
if is_supabase_extra_installed():
    from slumber.cli.auth import auth_app
    from slumber.cli.condition import condition_app
    from slumber.cli.db import db_app
    from slumber.cli.participant import participant_app
    from slumber.cli.session import session_app

    app.add_typer(auth_app, name="auth")
    app.add_typer(condition_app, name="condition")
    app.add_typer(db_app, name="db")
    app.add_typer(participant_app, name="participant")
    app.add_typer(session_app, name="session")


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
