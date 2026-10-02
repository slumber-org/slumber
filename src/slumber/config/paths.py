"""Path and placeholder resolution for plugin settings."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

# Placeholders authors may use in settings strings (paths, titles, sinks).
SETTINGS_PLACEHOLDERS: frozenset[str] = frozenset(
    {
        "assets_dir",
        "run_dir",
        "run_id",
        "study_id",
        "study_name",
        "condition_id",
        "participant_id",
        "session_id",
    }
)


def study_root_placeholders(
    study_root: Path,
    *,
    study_id: str,
    study_name: str,
    assets_dir: str,
) -> dict[str, str]:
    """Build placeholders available before a run directory exists."""
    root = study_root.resolve()
    return {
        "assets_dir": str((root / assets_dir).resolve()),
        "study_id": study_id,
        "study_name": study_name,
    }


def run_placeholders(
    study_root: Path,
    *,
    study_id: str,
    study_name: str,
    assets_dir: str,
    run_dir: Path,
    run_id: str,
    condition_id: str,
    participant_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, str]:
    """Build the full placeholder map once a run directory exists."""
    placeholders = study_root_placeholders(
        study_root,
        study_id=study_id,
        study_name=study_name,
        assets_dir=assets_dir,
    )
    placeholders.update(
        {
            "run_dir": str(run_dir.resolve()),
            "run_id": run_id,
            "condition_id": condition_id,
        }
    )
    if participant_id is not None:
        placeholders["participant_id"] = participant_id
    if session_id is not None:
        placeholders["session_id"] = session_id
    return placeholders


class _PartialFormatMap(dict[str, str]):
    """``str.format_map`` helper that leaves unknown ``{keys}`` intact."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def expand_placeholders(text: str, placeholders: Mapping[str, str]) -> str:
    """Expand known placeholders in *text*; leave missing keys as ``{name}``."""
    if "{" not in text:
        return text
    return text.format_map(_PartialFormatMap(placeholders))


def _looks_like_path(value: str) -> bool:
    """Heuristic: treat strings with path separators as filesystem paths."""
    return "/" in value or "\\" in value


def resolve_path_string(value: str, *, study_root: Path) -> str:
    """Resolve a path string against the study root when relative.

    Absolute paths are unchanged. Relative paths join under *study_root*.
    """
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str((study_root / path).resolve())


def resolve_settings(
    settings: dict[str, Any],
    *,
    study_root: Path,
    placeholders: Mapping[str, str],
) -> dict[str, Any]:
    """Expand placeholders in settings, then resolve relative path-like strings.

    Placeholders expand first. Strings that still contain ``{...}`` are left
    as-is (e.g. ``{run_dir}`` at validate time). Other strings that look like
    paths are resolved against *study_root* when relative; absolute paths stay
    absolute. Non-path strings (labels, etc.) are only placeholder-expanded.

    Args:
        settings: Plugin settings dict (possibly nested).
        study_root: Study package root for relative path resolution.
        placeholders: Mapping of placeholder name -> expanded value.

    Returns:
        New settings structure with strings resolved.
    """
    root = study_root.resolve()
    return _resolve_value(settings, study_root=root, placeholders=placeholders)


def _resolve_value(
    value: Any,
    *,
    study_root: Path,
    placeholders: Mapping[str, str],
) -> Any:
    if isinstance(value, dict):
        return {
            key: _resolve_value(item, study_root=study_root, placeholders=placeholders)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            _resolve_value(item, study_root=study_root, placeholders=placeholders)
            for item in value
        ]
    if isinstance(value, str):
        expanded = expand_placeholders(value, placeholders)
        if "{" in expanded:
            return expanded
        if _looks_like_path(expanded):
            return resolve_path_string(expanded, study_root=study_root)
        return expanded
    return value
