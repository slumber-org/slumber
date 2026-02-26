"""Study folder initialization: layout, manifest from schema, .gitignore, .env.example."""

from importlib.resources import as_file, files
from pathlib import Path

import yaml

from slumber.schemas.study import Study
from slumber.utils.yaml import BlankLineDumper

_TEMPLATES_PACKAGE = "slumber.study.templates"

STUDY_YAML_FILENAME = "study.yaml"
ENV_EXAMPLE_FILENAME = "env.example"
GITIGNORE_FILENAME = "gitignore"


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

    with open(study_path / STUDY_YAML_FILENAME, "w", encoding="utf-8") as f:
        yaml.dump(
            study.model_dump(mode="json"),
            f,
            Dumper=BlankLineDumper,
            sort_keys=False,
            allow_unicode=True,
        )

    if create_env_example:
        create_template_file(
            study_path / f".{ENV_EXAMPLE_FILENAME}", ENV_EXAMPLE_FILENAME
        )

    if create_gitignore:
        create_template_file(study_path / f".{GITIGNORE_FILENAME}", GITIGNORE_FILENAME)

    return study_path
