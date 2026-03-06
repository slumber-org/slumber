"""Study manifest schema: metadata, conditions dir, runs, logging, UI."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    field_validator,
    model_validator,
)

if TYPE_CHECKING:
    from slumber.schemas.condition import Condition


DEFAULT_CONDITIONS_DIR_NAME = "conditions"
DEFAULT_RUNS_DIR_NAME = "runs"
DEFAULT_ASSETS_DIR_NAME = "assets"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_RUN_LAYOUT = "sub-{participant_id}/ses-{session_id}/run-{run_id}"
VALID_RUN_LAYOUT_KEYS: ClassVar[frozenset[str]] = frozenset(
    {"study_id", "participant_id", "run_id", "condition_id", "session_id"}
)

# study_id must not contain path components so base_dir / study_id cannot escape base_dir
INVALID_STUDY_ID_SUBSTRINGS: ClassVar[tuple[str, ...]] = ("/", "\\", "..")

DEFAULT_UI_BACKEND = "headless"


class UI(BaseModel):
    """Selected UI backend and its configuration."""

    backend: str = Field(
        default=DEFAULT_UI_BACKEND,
        min_length=1,
        description="UI backend plugin key (e.g. 'headless').",
    )
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="UI backend-specific configuration.",
    )


class RunLayout(BaseModel):
    """Run output directory and path structure.

    Run directory is base_directory joined with layout formatted with run-context
    values. Use placeholders like {participant_id}, {run_id} (and any others
    the schema supports).
    """

    base_directory: str = Field(
        default=DEFAULT_RUNS_DIR_NAME,
        description="Base directory for run outputs.",
    )
    layout: str = Field(
        default=DEFAULT_RUN_LAYOUT,
        min_length=1,
        description="Path relative to base_directory with placeholders.",
    )

    @model_validator(mode="after")
    def validate_layout(self) -> "RunLayout":
        placeholders = re.findall(r"\{(\w+)\}", self.layout)
        unknown = set(placeholders) - VALID_RUN_LAYOUT_KEYS
        if unknown:
            raise ValueError(
                f"layout contains unknown placeholders: {sorted(unknown)}. "
                f"Allowed: {sorted(VALID_RUN_LAYOUT_KEYS)}."
            )
        return self


class RunLoggingConfig(BaseModel):
    """Logging configuration for study runs.

    Handlers are passed as kwargs to loguru logger.add(). Sink paths may
    contain placeholders (e.g. run_id) substituted at run start.
    """

    level: str = Field(
        default=DEFAULT_LOG_LEVEL,
        description="Default log level when a handler does not set level.",
    )
    handlers: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of handler configs; each is passed to loguru logger.add(**handler).",
    )


class Study(BaseModel):
    """Study manifest: metadata, conditions dir, runs, logging, UI.

    Loaded from study.yaml. When loaded via config.load_study(), path,
    manifest_path, and conditions are set from the study directory.
    """

    model_config = ConfigDict(extra="forbid")

    _manifest_path: Path | None = PrivateAttr(default=None)
    _conditions: list["Condition"] = PrivateAttr(default_factory=list)

    study_id: str = Field(..., min_length=1, description="Unique study identifier.")
    name: str = Field(..., min_length=1, description="Human-readable study name.")
    conditions_dir: str = Field(
        default=DEFAULT_CONDITIONS_DIR_NAME,
        description="Directory name (relative to study folder) containing condition YAML files.",
    )
    assets_dir: str = Field(
        default=DEFAULT_ASSETS_DIR_NAME,
        description="Directory name (relative to study folder) containing asset files.",
    )
    runs: RunLayout = Field(
        default_factory=RunLayout,
        description="Run output directory layout.",
    )
    logging: RunLoggingConfig = Field(
        default_factory=RunLoggingConfig,
        description="Logging config for runs (level + loguru handlers).",
    )
    ui: UI = Field(
        default_factory=UI,
        description="Selected UI backend and config.",
    )

    @field_validator("study_id")
    @classmethod
    def study_id_no_path_components(cls, v: str) -> str:
        """Reject study_id values that could escape base_dir (e.g. '/', '..')."""
        for invalid in INVALID_STUDY_ID_SUBSTRINGS:
            if invalid in v:
                raise ValueError(
                    f"study_id must not contain path components; got {v!r} "
                    f"(forbidden: {INVALID_STUDY_ID_SUBSTRINGS})."
                )
        return v

    @property
    def path(self) -> Path | None:
        """Study directory when loaded via load_study(); None otherwise."""
        return self._manifest_path.parent if self._manifest_path else None

    @property
    def manifest_path(self) -> Path | None:
        """Path to study.yaml when loaded via load_study(); None otherwise."""
        return self._manifest_path

    @property
    def conditions(self) -> list["Condition"]:
        """Conditions loaded from the study directory (set by load_study())."""
        return self._conditions
