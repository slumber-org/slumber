from __future__ import annotations

from typing import Any

from slumber.plugins.tasks.base import Task


def build_task_from_settings(
    task_class: type[Task],
    settings: dict[str, Any] | None,
) -> Task:
    """Build a Task instance from the plugin class and step settings.

    Args:
        task_class: Task subclass (the plugin class for this task_type).
        settings: Plugin-specific settings dict from the Step spec (or None).

    Returns:
        Validated Task instance.

    Raises:
        ValueError: If settings is not a dict or None.
        ValidationError: If the dict fails model validation.
    """
    if settings is not None and not isinstance(settings, dict):
        raise ValueError(
            f"settings must be a dict or None, got {type(settings).__name__}."
        )
    return task_class.model_validate(settings or {})
