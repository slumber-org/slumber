"""Typer application and top-level commands."""

import typer

from slumber.cli.db import db_app
from slumber.cli.study import study_app

app = typer.Typer(
    name="slumber",
    help="Sleep Logging and Unsupervised Monitoring through BioElectrical Recordings.",
)
app.add_typer(study_app, name="study")
app.add_typer(db_app, name="db")
