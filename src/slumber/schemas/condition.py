"""Condition schema: study-specific procedures and DAG."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from slumber.schemas.dag import DAG
from slumber.schemas.procedure import Procedure
from slumber.utils.errors import format_validation_error
from slumber.utils.yaml import EXTENSIONS, load_and_validate


class Condition(BaseModel):
    """A single condition: named procedures plus DAG."""

    name: str = Field(
        ..., min_length=1, description="Condition name (e.g. condition_1)."
    )
    procedures: dict[str, Procedure] = Field(
        ...,
        min_length=1,
        description="Mapping from procedure name to Procedure (e.g. pre_sleep, awakening, post_sleep, etc.).",
    )
    dag: DAG = Field(..., description="Processing DAG for this condition.")


def load_conditions_from_dir(conditions_dir: Path) -> list[Condition]:
    """Load and validate all condition YAML files from a conditions directory.

    Args:
        conditions_dir: Path to the directory containing condition YAML files.

    Returns:
        List of validated Condition instances, sorted by filename.

    Raises:
        FileNotFoundError: If the conditions directory does not exist.
        ValueError: If any condition file fails validation (message includes path).
    """
    if not conditions_dir.is_dir():
        raise FileNotFoundError(f"Conditions directory not found: {conditions_dir}")
    condition_files = sorted(
        f
        for f in conditions_dir.iterdir()
        if f.is_file() and f.suffix.lower() in EXTENSIONS
    )
    conditions: list[Condition] = []
    for file_path in condition_files:
        try:
            conditions.append(load_and_validate(file_path, Condition))
        except ValidationError as e:
            msg = format_validation_error(
                e, path=file_path, prefix="Condition file error"
            )
            raise ValueError(msg) from e
    return conditions
