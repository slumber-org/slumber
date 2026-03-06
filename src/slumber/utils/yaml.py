from __future__ import annotations

from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

EXTENSIONS = (".yaml", ".yml")

T = TypeVar("T", bound=BaseModel)


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file from disk and return the parsed dict.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed YAML as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the file is invalid YAML.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text) or {}


def load_and_validate(path: Path, model: type[T]) -> T:
    """Load YAML from a file and validate as the given Pydantic model.

    Args:
        path: Path to the YAML file.
        model: Pydantic model class to validate against (e.g. Study, Condition).

    Returns:
        Validated instance of the model.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the file is invalid YAML.
        pydantic.ValidationError: If the content does not match the model schema.
    """
    data = load_yaml(path)
    return model.model_validate(data)


class BlankLineDumper(yaml.SafeDumper):
    """Dumper that inserts blank lines between top-level objects."""

    def write_line_break(self, data: Any = None) -> None:
        super().write_line_break(data)

        if len(self.indents) == 1:
            super().write_line_break()
