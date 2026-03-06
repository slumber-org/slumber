"""Study folder: init, discovery, and load."""

from __future__ import annotations

from importlib.resources import as_file, files
from pathlib import Path

import yaml

from slumber.schemas.condition import load_conditions_from_dir
from slumber.schemas.study import Study
from slumber.utils.yaml import BlankLineDumper, load_and_validate

_TEMPLATES_PACKAGE = "slumber.config.templates"

_STUDY_MANIFEST_FILE = "study.yaml"
_ENV_EXAMPLE_FILENAME = "env.example"
_GITIGNORE_FILENAME = "gitignore"


def _load_template(template_name: str) -> str:
    """Load a template file from the package templates directory."""
    ref = files(_TEMPLATES_PACKAGE) / template_name
    with as_file(ref) as path:
        return path.read_text(encoding="utf-8")


def _create_file(file_path: Path, content: str) -> None:
    """Create a file at the given path with the given content."""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def create_template_file(file_path: Path, template_name: str) -> None:
    """Create a template file at the given path."""
    content = _load_template(template_name)
    _create_file(file_path, content)


def init_study(
    base_dir: Path,
    study_id: str,
    *,
    name: str | None = None,
    create_env_example: bool = True,
    create_gitignore: bool = True,
) -> Path:
    """Create a study folder with manifest, conditions/, and assets/.

    Creates <base_dir>/<study_id>/ with study.yaml, empty conditions/,
    assets/, and optionally .env.example and .gitignore.

    Args:
        base_dir: Project root; study folder will be base_dir / study_id.
        study_id: Unique study identifier (used as folder name).
        name: Human-readable study name; defaults to study_id.
        create_env_example: If True, create .env.example at study folder.
        create_gitignore: If True, create study folder .gitignore.

    Returns:
        Path to the created study directory.

    Raises:
        FileExistsError: If the study directory already exists.
    """
    project_root = base_dir.resolve()
    study_path = project_root / study_id
    if study_path.exists():
        raise FileExistsError(f"Study directory already exists: {study_path}")

    name = name if name is not None else study_id
    study = Study(
        study_id=study_id,
        name=name,
    )
    study_path.mkdir(parents=True)
    (study_path / study.conditions_dir).mkdir()
    (study_path / study.assets_dir).mkdir()

    with open(study_path / _STUDY_MANIFEST_FILE, "w", encoding="utf-8") as f:
        yaml.dump(
            study.model_dump(mode="json", exclude_computed_fields=True),
            f,
            Dumper=BlankLineDumper,
            sort_keys=False,
            allow_unicode=True,
        )

    if create_env_example:
        create_template_file(
            study_path / f".{_ENV_EXAMPLE_FILENAME}", _ENV_EXAMPLE_FILENAME
        )

    if create_gitignore:
        create_template_file(
            study_path / f".{_GITIGNORE_FILENAME}", _GITIGNORE_FILENAME
        )

    return study_path


def resolve_study_dir(
    study_dir: Path | None = None,
) -> Path:
    """Resolve the study directory from an explicit path or the current directory.

    When study_dir is given, it must be an existing directory containing
    study.yaml. When study_dir is None, the current working directory is
    checked for study.yaml; if present, it is the study dir.

    Args:
        study_dir: Optional path to the study folder. If None, uses Path.cwd().

    Returns:
        Path to the study directory if found.

    Raises:
        ValueError: If the study directory is not found or is not a directory.
        FileNotFoundError: If the study manifest is not found.
    """
    path = (study_dir if study_dir is not None else Path.cwd()).resolve()
    if not path.is_dir():
        raise ValueError(f"{path} is not a directory.")

    manifest = path / _STUDY_MANIFEST_FILE
    if not manifest.is_file():
        raise FileNotFoundError(
            f"Study manifest ({_STUDY_MANIFEST_FILE}) not found in {path}."
        )

    return path


def load_study(study_dir: Path) -> Study:
    """Load study manifest from a study directory.

    Sets the study's path so that study.conditions loads condition YAML files
    from that directory.

    Args:
        study_dir: Path to the study folder (must contain study.yaml).

    Returns:
        Study instance with path set; use study.conditions to load conditions.

    Raises:
        FileNotFoundError: If study.yaml is missing.
        pydantic.ValidationError: If the manifest is invalid.
    """
    manifest_path = (study_dir / _STUDY_MANIFEST_FILE).resolve()
    study = load_and_validate(manifest_path, Study)
    study._manifest_path = manifest_path
    study._conditions = load_conditions_from_dir(
        study_dir.resolve() / study.conditions_dir
    )
    return study
