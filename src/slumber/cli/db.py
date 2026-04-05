"""Database migration commands (Alembic) for Supabase/Postgres."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import typer

from slumber.supabase.utils import exit_unless_supabase_extra_installed

db_app = typer.Typer(
    name="db",
    help="Database schema migrations (Supabase / Postgres via Alembic).",
)


def _alembic_cmd(args: list[str]) -> int:
    """Run alembic with framework root as cwd so alembic.ini is found."""
    exit_unless_supabase_extra_installed()
    root = Path().cwd()
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.call(
        [sys.executable, "-m", "alembic", *args],
        cwd=root,
        env=env,
    )


def _compute_next_numeric_rev_id() -> str:
    """Compute the next numeric Alembic revision id.

    This assumes existing revision ids follow the `NNN_<slug>.py` filename
    convention (e.g. `001_initial_schema.py`).
    """
    pattern = re.compile(r"^(?P<num>\d+)_.*\.py$")
    nums: list[int] = []
    num_width = 3

    root = Path().cwd()
    versions_dir = root / "migrations" / "versions"

    if versions_dir.exists():
        for path in versions_dir.glob("*.py"):
            match = pattern.match(path.name)
            if not match:
                continue
            num_str = match.group("num")
            nums.append(int(num_str))
            num_width = max(num_width, len(num_str))

    next_num = (max(nums) + 1) if nums else 1
    return str(next_num).zfill(num_width)


@db_app.command("upgrade")
def db_upgrade(
    revision: str = typer.Argument("head", help="Target revision."),
) -> None:
    """Apply migrations up to the given revision."""
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


@db_app.command("revision")
def db_revision(
    message: str = typer.Option(
        ...,
        "--message",
        "-m",
        help="Migration message.",
    ),
    autogenerate: bool = typer.Option(
        True,
        "--autogenerate/--no-autogenerate",
        help=(
            "Autogenerate migration by comparing SQLModel metadata to the current "
            "database schema."
        ),
    ),
    rev_id: str | None = typer.Option(
        ...,
        "--rev-id",
        default_factory=_compute_next_numeric_rev_id,
        help="Alembic revision id override. Defaults to the next sequential numeric id.",
    ),
) -> None:
    """Create a new Alembic migration file."""

    args = ["revision", "--rev-id", rev_id]

    if autogenerate:
        args.append("--autogenerate")

    if message:
        args.extend(["-m", message])

    raise typer.Exit(_alembic_cmd(args))
