"""Condition config: load conditions from a directory."""

from pathlib import Path

from pydantic import ValidationError

from slumber.utils.validation import format_validation_error
from slumber.utils.yaml import load_and_validate
from slumber.schemas.condition import Condition
from slumber.schemas.study import Study
from slumber.utils.yaml import EXTENSIONS


def load_study_conditions(study: Study, study_dir: Path) -> list[Condition]:
    """Load and validate all condition YAML files for a study.

    Uses study.conditions_dir (relative to study_dir) to find condition files.

    Args:
        study: Study manifest (provides conditions_dir).
        study_dir: Path to the study folder.

    Returns:
        List of validated Condition instances, sorted by filename.

    Raises:
        FileNotFoundError: If the conditions directory does not exist.
        ValueError: If any condition file fails validation (message includes path).
    """
    conditions_path = study_dir / study.conditions_dir
    return load_conditions_from_dir(conditions_path)


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
