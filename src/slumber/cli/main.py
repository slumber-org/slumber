"""Typer application and top-level commands."""

from pathlib import Path
from dotenv.main import load_dotenv
import typer

from slumber.cli.auth import auth_app
from slumber.cli.condition import condition_app
from slumber.cli.db import db_app
from slumber.cli.participant import participant_app
from slumber.cli.session import session_app
from slumber.cli.study import study_app

app = typer.Typer(
    name="slumber",
    help="Sleep Logging and Unsupervised Monitoring through BioElectrical Recordings.",
)
app.add_typer(auth_app, name="auth")
app.add_typer(study_app, name="study")
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
        help="Environment file.",
    ),
) -> None:
    """Load .env file."""
    load_dotenv(dotenv_path=env)
