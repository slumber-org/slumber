from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

from dotenv import find_dotenv, load_dotenv
import typer

from slumber.config import resolve_study_dir


STUDY_DIR_OPTION = typer.Option(
    "--study-dir",
    "-d",
    file_okay=False,
    dir_okay=True,
    resolve_path=True,
    help="Path to study folder. Default: current directory.",
)

StudyDirPath = Annotated[Path | None, STUDY_DIR_OPTION]


def require_study_dir(study_dir: Path | None = None) -> Path:
    """Resolve study dir, prepare cwd and .env; on failure echo error and exit 1."""
    try:
        resolved = resolve_study_dir(study_dir=study_dir)
        os.chdir(resolved)

        env_path = find_dotenv(usecwd=True)
        if env_path:
            load_dotenv(dotenv_path=env_path)

        return resolved
    except (ValueError, FileNotFoundError) as e:
        typer.echo(
            f"Error resolving study directory: {e}"
            "\nRun this command from a study folder or use --study-dir.",
            err=True,
        )
        raise typer.Exit(1) from e
