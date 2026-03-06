"""Database migration commands (Alembic)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import typer

from slumber.cli.utils import StudyDirPath, require_study_dir

db_app = typer.Typer(
    name="db",
    help="Database schema migrations (Postgres / Supabase). Requires DATABASE_URL from study .env.",
)


@db_app.callback()
def _db_callback(
    study_dir: StudyDirPath = None,
) -> None:
    require_study_dir(study_dir)


def _alembic_cmd(args: list[str]) -> int:
    """Run alembic with framework root as cwd so alembic.ini is found."""
    root = Path(__file__).resolve().parent.parent.parent.parent
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.call(
        [sys.executable, "-m", "alembic", *args],
        cwd=root,
        env=env,
    )


@db_app.command("upgrade")
def db_upgrade(
    revision: str = typer.Argument("head", help="Target revision (default: head)."),
) -> None:
    """Apply migrations up to the given revision (default: head)."""
    raise typer.Exit(_alembic_cmd(["upgrade", revision]))


@db_app.command("downgrade")
def db_downgrade(
    revision: str = typer.Argument(
        "-1", help="Target revision (e.g. -1 for one step)."
    ),
) -> None:
    """Revert migrations to the given revision."""
    raise typer.Exit(_alembic_cmd(["downgrade", revision]))


@db_app.command("migrate")
def db_migrate() -> None:
    """Apply all pending migrations (alias for 'db upgrade head')."""
    raise typer.Exit(_alembic_cmd(["upgrade", "head"]))


@db_app.command("current")
def db_current() -> None:
    """Show current revision."""
    raise typer.Exit(_alembic_cmd(["current"]))


@db_app.command("history")
def db_history() -> None:
    """Show migration history."""
    raise typer.Exit(_alembic_cmd(["history"]))
