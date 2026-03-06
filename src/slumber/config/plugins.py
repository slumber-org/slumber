"""Validate condition DAG components and procedure tasks against the plugin registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slumber.plugins import EntryPointGroup, PluginNotFoundError, get_registry
from slumber.plugins.tasks import build_task_from_settings
from slumber.plugins.units import build_unit_from_settings

if TYPE_CHECKING:
    from slumber.plugins import PluginRegistry
    from slumber.schemas.condition import Condition
    from slumber.schemas.study import Study, UI


def _format_snippet(msg: str, max_len: int = 80) -> str:
    """One-line snippet for error message; truncate if long."""
    line = msg.replace("\n", " ").strip()
    return line if len(line) <= max_len else line[: max_len - 3] + "..."


def _validate_dag_components(
    condition: "Condition",
    registry: "PluginRegistry",
) -> list[str]:
    """Validate DAG components (unit_type + settings) against unit plugins."""
    errors: list[str] = []
    for comp in condition.dag.components:
        try:
            unit_class = registry.get_plugin(EntryPointGroup.UNITS, comp.unit_type)
            build_unit_from_settings(unit_class, comp.settings)
        except PluginNotFoundError as e:
            errors.append(
                f"Condition {condition.name!r}, DAG component {comp.name!r} "
                f"(unit_type {e.key!r}): plugin not found. Available: {e.available}."
            )
        except Exception as e:
            errors.append(
                f"Condition {condition.name!r}, DAG component {comp.name!r} "
                f"(unit_type {comp.unit_type!r}): {_format_snippet(str(e))}."
            )
    return errors


def _validate_procedure_steps(
    condition: "Condition",
    registry: "PluginRegistry",
) -> list[str]:
    """Validate procedure steps (task_type + settings) against task plugins."""
    errors: list[str] = []
    for proc_name, procedure in condition.procedures.items():
        for step in procedure.steps:
            try:
                task_class = registry.get_plugin(EntryPointGroup.TASKS, step.task_type)
                build_task_from_settings(task_class, step.settings)
            except PluginNotFoundError as e:
                errors.append(
                    f"Condition {condition.name!r}, procedure {proc_name!r}, "
                    f"step (task_type {e.key!r}): plugin not found. "
                    f"Available: {e.available}."
                )
            except Exception as e:
                errors.append(
                    f"Condition {condition.name!r}, procedure {proc_name!r}, "
                    f"step (task_type {step.task_type!r}): "
                    f"{_format_snippet(str(e))}."
                )
    return errors


def _validate_condition_plugins(
    condition: "Condition",
    registry: "PluginRegistry",
) -> list[str]:
    """Validate a condition's DAG unit settings and procedure steps via plugins.

    For each DAG component: resolves the unit plugin and builds an instance from
    settings (validating). For each procedure step: resolves the Task class and
    builds an instance from settings (validating). Collects all errors with context.

    Args:
        condition: Loaded condition (schema already validated).
        registry: Plugin registry.

    Returns:
        List of error strings (condition name, location, message). Empty if valid.
    """
    errors: list[str] = []
    errors.extend(_validate_dag_components(condition, registry))
    errors.extend(_validate_procedure_steps(condition, registry))
    return errors


def _validate_ui_backend(ui: "UI", registry: "PluginRegistry") -> list[str]:
    """Validate the UI backend key against the registry."""
    errors: list[str] = []
    try:
        registry.get_plugin(EntryPointGroup.UI_BACKENDS, ui.backend)
    except PluginNotFoundError as e:
        errors.append(
            f"UI backend {e.key!r}: plugin not found. Available: {e.available}."
        )
    return errors


def validate_study_plugins(
    study: "Study",
    registry: "PluginRegistry | None" = None,
) -> None:
    """Validate UI backend and all conditions' plugins for a study.

    Validates study.ui.backend (if set) and each condition's DAG and procedure
    steps. If any errors are collected, raises ValueError with one combined message.

    Args:
        study: Loaded study (with conditions and ui).
        registry: Plugin registry; uses get_registry() if None.

    Raises:
        ValueError: If UI backend or any DAG/task fails plugin validation.
    """
    reg = registry if registry is not None else get_registry()
    all_errors: list[str] = []
    all_errors.extend(_validate_ui_backend(study.ui, reg))
    for condition in study.conditions:
        all_errors.extend(_validate_condition_plugins(condition, reg))
    if all_errors:
        header = "Plugin validation failed:\n"
        raise ValueError(header + "\n".join(f"  - {e}" for e in all_errors))
