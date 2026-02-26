"""Study manifest schema: metadata, conditions dir, runs, logging, UI."""

import re
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UI(BaseModel):
    """Selected UI backend and its configuration."""

    backend: str = Field(
        ...,
        min_length=1,
        description="UI backend plugin key (e.g. 'headless', 'nicegui').",
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

    LAYOUT_KEYS: ClassVar[frozenset[str]] = frozenset(
        {"study_id", "participant_id", "run_id", "condition_id", "session_id"}
    )

    base_directory: str = Field(
        default="runs",
        description="Base directory for run outputs.",
    )
    layout: str = Field(
        default="sub-{participant_id}/ses-{session_id}/run-{run_id}",
        min_length=1,
        description="Path relative to base_directory with placeholders.",
    )

    @model_validator(mode="after")
    def validate_layout(self) -> "RunLayout":
        placeholders = re.findall(r"\{(\w+)\}", self.layout)
        unknown = set(placeholders) - self.LAYOUT_KEYS
        if unknown:
            raise ValueError(
                f"layout contains unknown placeholders: {sorted(unknown)}. "
                f"Allowed: {sorted(self.LAYOUT_KEYS)}."
            )
        return self


class RunLoggingConfig(BaseModel):
    """Logging configuration for study runs.

    Handlers are passed as kwargs to loguru logger.add(). Sink paths may
    contain placeholders (e.g. run_id) substituted at run start.
    """

    level: str = Field(
        default="INFO",
        description="Default log level when a handler does not set level.",
    )
    handlers: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of handler configs; each is passed to loguru logger.add(**handler).",
    )


class Study(BaseModel):
    """Study manifest: metadata, conditions dir, runs, logging, UI.

    Loaded from study.yaml. Conditions are loaded from the directory named
    by conditions_dir (default conditions/). Run layout and run-time logging
    come from runs and logging. Participant list lives in participants.yaml
    or database, not in the study manifest.
    """

    model_config = ConfigDict(extra="forbid")

    study_id: str = Field(..., min_length=1, description="Unique study identifier.")
    name: str = Field(..., min_length=1, description="Human-readable study name.")
    conditions_dir: str = Field(
        default="conditions",
        description="Directory name (relative to study folder) containing condition YAML files.",
    )
    runs: RunLayout = Field(
        default_factory=RunLayout,
        description="Run output directory layout.",
    )
    logging: RunLoggingConfig = Field(
        default_factory=RunLoggingConfig,
        description="Logging config for runs (level + loguru handlers).",
    )
    ui: UI = Field(..., description="Selected UI backend and config.")
