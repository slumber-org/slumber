"""Resolve PluginSpecs and validate study plugins against discovery maps."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

import ezmsg.core as ez
from pydantic import BaseModel, ValidationError

from slumber.config.paths import resolve_settings, study_root_placeholders
from slumber.pipeline.units import build_unit_from_settings
from slumber.plugins import (
    ConfiguredPlugin,
    EntryPointGroup,
    PluginNotFoundError,
    get_registry,
)
from slumber.plugins.registry import PluginRegistry
from slumber.schemas.condition import Action, Condition, EventHandler
from slumber.schemas.plugin import PluginSpec
from slumber.schemas.study import FrameSettings, Study
from slumber.ui.builtins import BUILT_IN_LAYOUTS, BUILT_IN_UI
from slumber.utils.mapping import deep_merge

BuiltInGroup = Literal["ui", "layouts"]


class PluginGroup(str, Enum):
    """Logical plugin groups for :func:`resolve_plugin_spec`."""

    ACTIVITIES = "slumber.activities"
    UNITS = "slumber.units"
    UI = "ui"
    LAYOUTS = "layouts"


def _format_snippet(msg: str, max_len: int = 80) -> str:
    """One-line snippet for error message; truncate if long."""
    line = msg.replace("\n", " ").strip()
    return line if len(line) <= max_len else line[: max_len - 3] + "..."


def deep_merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override onto base (public alias for config callers)."""
    return deep_merge(base, override)


def layout_defaults_for_type(study: Study, layout_type: str) -> dict[str, Any]:
    """Return ``ui.settings.layouts.<type>`` as a plain dict (or empty)."""
    layouts = study.ui.settings.get("layouts")
    if not isinstance(layouts, dict):
        return {}
    defaults = layouts.get(layout_type)
    if defaults is None:
        return {}
    if isinstance(defaults, BaseModel):
        return defaults.model_dump(exclude_none=True)
    if isinstance(defaults, dict):
        return dict(defaults)
    return {}


def merge_layout_settings(study: Study, layout_spec: PluginSpec) -> dict[str, Any]:
    """Deep-merge study layout defaults under phase ``layout.settings``."""
    defaults = layout_defaults_for_type(study, layout_spec.type)
    return deep_merge(defaults, dict(layout_spec.settings))


def merge_frame_settings(
    study_frame: dict[str, Any] | FrameSettings | None,
    phase_frame: FrameSettings | dict[str, Any] | None,
) -> dict[str, Any]:
    """Deep-merge phase ``frame`` over study ``ui.settings.frame``."""
    if isinstance(study_frame, FrameSettings):
        base = study_frame.model_dump(exclude_none=True)
    elif isinstance(study_frame, dict):
        base = dict(study_frame)
    else:
        base = {}

    if phase_frame is None:
        return base
    if isinstance(phase_frame, FrameSettings):
        override = phase_frame.model_dump(exclude_none=True)
    else:
        override = dict(phase_frame)
    return deep_merge(base, override)


def get_plugin_class(
    group: PluginGroup | EntryPointGroup | BuiltInGroup,
    key: str,
    *,
    registry: PluginRegistry | None = None,
) -> type:
    """Load a plugin class from entry points or the built-in UI/layout maps.

    Args:
        group: Entry-point group or built-in ``ui`` / ``layouts``.
        key: Plugin type key.
        registry: Plugin registry for activities/units; uses default if None.

    Returns:
        Plugin class.

    Raises:
        PluginNotFoundError: If the key is not registered for the group.
    """
    group_value = group.value if isinstance(group, Enum) else group

    if group_value == PluginGroup.UI.value:
        if key not in BUILT_IN_UI:
            raise PluginNotFoundError("ui", key, list(BUILT_IN_UI.keys()))
        return BUILT_IN_UI[key]

    if group_value == PluginGroup.LAYOUTS.value:
        if key not in BUILT_IN_LAYOUTS:
            raise PluginNotFoundError("layouts", key, list(BUILT_IN_LAYOUTS.keys()))
        return BUILT_IN_LAYOUTS[key]

    if group_value == EntryPointGroup.ACTIVITIES.value:
        entry_group = EntryPointGroup.ACTIVITIES
    elif group_value == EntryPointGroup.UNITS.value:
        entry_group = EntryPointGroup.UNITS
    else:
        raise ValueError(f"Unknown plugin group: {group_value!r}")

    reg = registry if registry is not None else get_registry()
    return reg.get_plugin(entry_group, key)


def build_configured_plugin(
    plugin_class: type[ConfiguredPlugin],
    settings: dict[str, Any] | None,
) -> ConfiguredPlugin:
    """Validate settings and instantiate a :class:`ConfiguredPlugin` subclass."""
    if settings is not None and not isinstance(settings, dict):
        raise ValueError(
            f"settings must be a dict or None, got {type(settings).__name__}."
        )
    settings_dict = settings or {}
    model = plugin_class.settings_model
    if model is None:
        if settings_dict:
            raise ValueError(
                f"{plugin_class.__name__} does not accept settings; "
                "remove settings from the PluginSpec."
            )
        return plugin_class()
    validated = model.model_validate(settings_dict)
    return plugin_class(validated)


def resolve_plugin_spec(
    spec: PluginSpec,
    group: PluginGroup | EntryPointGroup | BuiltInGroup,
    *,
    registry: PluginRegistry | None = None,
) -> ConfiguredPlugin | ez.Unit:
    """Load the plugin class for *spec* and build a validated instance.

    Activities, UI backends, and layouts use :class:`ConfiguredPlugin`
    ``settings_model``. Units use ezmsg ``SETTINGS`` via
    :func:`build_unit_from_settings`.

    Args:
        spec: Plugin type + settings from YAML.
        group: Which discovery map / entry-point group to use.
        registry: Optional registry override (activities/units).

    Returns:
        Configured plugin or unit instance.

    Raises:
        PluginNotFoundError: Unknown type key.
        ValidationError / ValueError: Invalid settings.
    """
    plugin_class = get_plugin_class(group, spec.type, registry=registry)
    group_value = group.value if isinstance(group, Enum) else group

    if group_value == EntryPointGroup.UNITS.value:
        return build_unit_from_settings(plugin_class, spec.settings)

    if not (
        isinstance(plugin_class, type) and issubclass(plugin_class, ConfiguredPlugin)
    ):
        raise TypeError(
            f"Plugin {spec.type!r} in group {group_value!r} must be a "
            f"ConfiguredPlugin subclass, got {plugin_class!r}."
        )
    return build_configured_plugin(plugin_class, spec.settings)


def _iter_handlers(condition: Condition) -> list[tuple[str, EventHandler]]:
    """Yield (location, handler) for all activity and phase handlers."""
    handlers: list[tuple[str, EventHandler]] = []
    for phase in condition.phases:
        for handler in phase.on:
            handlers.append((f"phase {phase.id!r}", handler))
        for activity in phase.activities:
            for handler in activity.on:
                handlers.append(
                    (f"phase {phase.id!r} activity {activity.id!r}", handler)
                )
    return handlers


def _validate_action_refs(
    condition: Condition,
    location: str,
    action: Action,
) -> list[str]:
    errors: list[str] = []
    if action.start_phase is not None and action.start_phase not in condition.phase_ids:
        errors.append(
            f"Condition {condition.name!r}, {location}: unknown start_phase "
            f"{action.start_phase!r}. Available: {sorted(condition.phase_ids)}."
        )
    if (
        action.start_pipeline is not None
        and action.start_pipeline not in condition.pipeline_ids
    ):
        errors.append(
            f"Condition {condition.name!r}, {location}: unknown start_pipeline "
            f"{action.start_pipeline!r}. Available: {sorted(condition.pipeline_ids)}."
        )
    if (
        action.stop_pipeline is not None
        and action.stop_pipeline not in condition.pipeline_ids
    ):
        errors.append(
            f"Condition {condition.name!r}, {location}: unknown stop_pipeline "
            f"{action.stop_pipeline!r}. Available: {sorted(condition.pipeline_ids)}."
        )
    return errors


def _validate_connection_endpoints(condition: Condition) -> list[str]:
    errors: list[str] = []
    for pipeline in condition.pipelines:
        unit_ids = pipeline.unit_ids
        for connection in pipeline.connections:
            for stream, label in (
                (connection.output, "output"),
                (connection.input, "input"),
            ):
                unit_id = stream.split("/", 1)[0]
                if unit_id not in unit_ids:
                    errors.append(
                        f"Condition {condition.name!r}, pipeline {pipeline.id!r}: "
                        f"connection {label} references unknown unit {unit_id!r} "
                        f"in {stream!r}. Available: {sorted(unit_ids)}."
                    )
    return errors


def _validate_condition_structure(condition: Condition) -> list[str]:
    errors: list[str] = []
    if condition.entry not in condition.phase_ids:
        errors.append(
            f"Condition {condition.name!r}: entry {condition.entry!r} is not a "
            f"phase id. Available: {sorted(condition.phase_ids)}."
        )
    for location, handler in _iter_handlers(condition):
        for action in handler.do:
            errors.extend(
                _validate_action_refs(
                    condition,
                    f"{location} on {handler.event!r}",
                    action,
                )
            )
    errors.extend(_validate_connection_endpoints(condition))
    return errors


def _validate_condition_plugins(
    study: Study,
    condition: Condition,
    registry: PluginRegistry,
    *,
    resolved_settings: bool,
    placeholders: dict[str, str] | None,
) -> list[str]:
    errors: list[str] = []
    study_root = study.path

    for phase in condition.phases:
        layout_settings = merge_layout_settings(study, phase.layout)
        if resolved_settings and study_root is not None and placeholders is not None:
            layout_settings = resolve_settings(
                layout_settings,
                study_root=study_root,
                placeholders=placeholders,
            )
        layout_spec = PluginSpec(type=phase.layout.type, settings=layout_settings)
        try:
            resolve_plugin_spec(layout_spec, PluginGroup.LAYOUTS, registry=registry)
        except PluginNotFoundError as e:
            errors.append(
                f"Condition {condition.name!r}, phase {phase.id!r} layout "
                f"{e.key!r}: plugin not found. Available: {e.available}."
            )
        except (ValidationError, ValueError, TypeError) as e:
            errors.append(
                f"Condition {condition.name!r}, phase {phase.id!r} layout "
                f"{phase.layout.type!r}: {_format_snippet(str(e))}."
            )

        for activity in phase.activities:
            activity_settings = dict(activity.settings)
            if (
                resolved_settings
                and study_root is not None
                and placeholders is not None
            ):
                activity_settings = resolve_settings(
                    activity_settings,
                    study_root=study_root,
                    placeholders=placeholders,
                )
            activity_spec = PluginSpec(type=activity.type, settings=activity_settings)
            try:
                resolve_plugin_spec(
                    activity_spec, PluginGroup.ACTIVITIES, registry=registry
                )
            except PluginNotFoundError as e:
                errors.append(
                    f"Condition {condition.name!r}, phase {phase.id!r} activity "
                    f"{activity.id!r} (type {e.key!r}): plugin not found. "
                    f"Available: {e.available}."
                )
            except (ValidationError, ValueError, TypeError) as e:
                errors.append(
                    f"Condition {condition.name!r}, phase {phase.id!r} activity "
                    f"{activity.id!r} (type {activity.type!r}): "
                    f"{_format_snippet(str(e))}."
                )

    for pipeline in condition.pipelines:
        for unit in pipeline.units:
            unit_settings = dict(unit.settings)
            if (
                resolved_settings
                and study_root is not None
                and placeholders is not None
            ):
                unit_settings = resolve_settings(
                    unit_settings,
                    study_root=study_root,
                    placeholders=placeholders,
                )
            unit_spec = PluginSpec(type=unit.type, settings=unit_settings)
            try:
                resolve_plugin_spec(unit_spec, PluginGroup.UNITS, registry=registry)
            except PluginNotFoundError as e:
                errors.append(
                    f"Condition {condition.name!r}, pipeline {pipeline.id!r} unit "
                    f"{unit.id!r} (type {e.key!r}): plugin not found. "
                    f"Available: {e.available}."
                )
            except (ValidationError, ValueError, TypeError) as e:
                errors.append(
                    f"Condition {condition.name!r}, pipeline {pipeline.id!r} unit "
                    f"{unit.id!r} (type {unit.type!r}): "
                    f"{_format_snippet(str(e))}."
                )

    return errors


def _validate_ui(study: Study, registry: PluginRegistry) -> list[str]:
    errors: list[str] = []
    ui_settings = dict(study.ui.settings)
    if study.path is not None:
        placeholders = study_root_placeholders(
            study.path,
            study_id=study.study_id,
            study_name=study.study_name,
            assets_dir=study.assets_dir,
        )
        ui_settings = resolve_settings(
            ui_settings,
            study_root=study.path,
            placeholders=placeholders,
        )
    ui_spec = PluginSpec(type=study.ui.type, settings=ui_settings)
    try:
        resolve_plugin_spec(ui_spec, PluginGroup.UI, registry=registry)
    except PluginNotFoundError as e:
        errors.append(f"UI type {e.key!r}: plugin not found. Available: {e.available}.")
    except (ValidationError, ValueError, TypeError) as e:
        errors.append(
            f"UI type {study.ui.type!r} settings invalid: {_format_snippet(str(e))}."
        )
    return errors


def resolve_ui_backend_from_ui(ui: PluginSpec, registry: PluginRegistry) -> Any:
    """Legacy orchestrator hook (pre-0.1 UIBackend entry points).

    Kept so ``slumber.runtime`` can still import while RunEngine lands. New
    code should use :func:`resolve_plugin_spec` with :attr:`PluginGroup.UI`.

    Raises:
        NotImplementedError: Always; legacy backends are no longer registered.
    """
    del registry  # unused; signature preserved for callers
    raise NotImplementedError(
        f"Legacy UI backend resolution for type {ui.type!r} was removed. "
        "Use resolve_plugin_spec(..., PluginGroup.UI) and the 0.1 RunEngine."
    )


def validate_study_plugins(
    study: Study,
    registry: PluginRegistry | None = None,
) -> None:
    """Validate UI, layouts, activities, units, and condition cross-references.

    Checks ``study.ui``, every phase layout (after merging study layout
    defaults), every activity and unit, ``entry`` / action phase and pipeline
    ids, and connection endpoints. When the study was loaded from disk,
    study-root path placeholders in settings are expanded before validation.

    Args:
        study: Loaded study (with conditions and ui).
        registry: Plugin registry; uses :func:`get_registry` if None.

    Raises:
        ValueError: If any check fails (combined message).
    """
    reg = registry if registry is not None else get_registry()
    all_errors: list[str] = []
    all_errors.extend(_validate_ui(study, reg))

    placeholders: dict[str, str] | None = None
    resolve_paths = study.path is not None
    if resolve_paths:
        placeholders = study_root_placeholders(
            study.path,
            study_id=study.study_id,
            study_name=study.study_name,
            assets_dir=study.assets_dir,
        )

    for condition in study.conditions:
        all_errors.extend(_validate_condition_structure(condition))
        all_errors.extend(
            _validate_condition_plugins(
                study,
                condition,
                reg,
                resolved_settings=resolve_paths,
                placeholders=placeholders,
            )
        )

    if all_errors:
        header = "Plugin validation failed:\n"
        raise ValueError(header + "\n".join(f"  - {e}" for e in all_errors))
