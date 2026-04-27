"""Shared utilities for nicegui2."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dataclasses import dataclass


def load_markdown_content(
    config: dataclass,
    base_path: Path | None = None,
    study_assets_dir: Path | None = None,
    parse: bool = True,
) -> tuple[str, str, str]:
    """Load title, subtitle, and body from markdown file.

    Args:
        config: A config dataclass with a `markdown_path` attribute
        base_path: Optional base directory for resolving markdown_path.
                   Defaults to the directory containing this utils.py file.
        study_assets_dir: Study assets directory to check for the file.
        parse: If True, parse into title/subtitle/body. If False, return raw content.

    Returns:
        Tuple of (title, subtitle, body_markdown) or ("", "", raw_content) if parse=False
    """
    md_path = getattr(config, "markdown_path", None)
    if not md_path:
        return "Untitled", "", "No content"

    if base_path is None:
        base_path = Path(__file__).parent

    # Check study assets directory if provided
    if study_assets_dir is not None:
        md_file = study_assets_dir / md_path
        if md_file.exists():
            content = md_file.read_text(encoding="utf-8").strip()
            if parse:
                return _parse_markdown(content)
            else:
                return "", "", content
        else:
            return (
                "Error",
                "",
                f"Error: File '{md_path}' not found in study assets at '{study_assets_dir}'",
            )

    # If no study assets dir provided, check base path
    md_file = base_path / md_path
    if not md_file.exists():
        return "Error", "", f"Error: File '{md_path}' not found at '{base_path}'"

    content = md_file.read_text(encoding="utf-8").strip()
    if parse:
        return _parse_markdown(content)
    else:
        return "", "", content


def _parse_markdown(content: str) -> tuple[str, str, str]:
    """Parse markdown content into title, subtitle, and body.

    Args:
        content: Raw markdown content

    Returns:
        Tuple of (title, subtitle, body_markdown)
    """
    lines = content.split("\n")

    title = "Untitled"
    subtitle = ""
    body_lines = []

    in_body = False
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            subtitle = line[3:].strip()
        elif line.strip() and not line.startswith("#"):
            in_body = True
            body_lines.append(line)
        elif in_body:
            body_lines.append(line)

    body_markdown = "\n".join(body_lines).strip()
    return title, subtitle, body_markdown


def to_pascal_case(snake_str: str) -> str:
    """Convert snake_case string to PascalCase.

    Args:
        snake_str: Snake_case string (e.g., "wakeup_procedure")

    Returns:
        PascalCase string (e.g., "WakeupProcedure")

    Example:
        >>> to_pascal_case("task_stepper")
        'TaskStepper'
        >>> to_pascal_case("audio_level_calibration")
        'AudioLevelCalibration'
    """
    return "".join(word.capitalize() for word in snake_str.split("_"))


def load_settings_class(
    module_path: str,
    class_name: str,
    fallback_class_name: str | None = None,
) -> type[Any] | None:
    """Dynamically load a settings class from a module.

    Args:
        module_path: Full Python module path (e.g., "slumber.plugins.ui.nicegui2.pages.sleep.settings")
        class_name: Expected class name (e.g., "SleepSettings")
        fallback_class_name: Optional fallback class name to try if primary not found

    Returns:
        The settings class if found, None otherwise
    """
    try:
        module = importlib.import_module(module_path)
        settings_class = getattr(module, class_name, None)
        if settings_class is None and fallback_class_name:
            settings_class = getattr(module, fallback_class_name, None)
        return settings_class
    except ImportError:
        return None


def load_config_class(
    task_module: Any,
    task_name: str,
) -> type[Any] | None:
    """Load a task's config class using naming convention.

    Looks for a class named {TaskName}Config in the task module.

    Args:
        task_module: The imported task module
        task_name: Snake_case task name (e.g., "audio_level_calibration")

    Returns:
        The config class if found, None otherwise
    """
    config_class_name = f"{to_pascal_case(task_name)}Config"
    return getattr(task_module, config_class_name, None)
