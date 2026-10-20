"""Study manifest schema: metadata, runs, logging, and UI."""

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

from slumber.schemas.plugin import PluginSpec

if TYPE_CHECKING:
    from slumber.schemas.condition import Condition

DEFAULT_CONDITIONS_DIR_NAME = "conditions"
DEFAULT_RUNS_DIR_NAME = "runs"
DEFAULT_ASSETS_DIR_NAME = "assets"
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_RUN_LAYOUT = "run-{run_id}"
DEFAULT_UI_TYPE = "headless"

# Placeholders allowed in ``runs.layout`` (and related run path templates).
# Kept in schemas so Study validation does not import the run package.
VALID_RUN_LAYOUT_KEYS: frozenset[str] = frozenset(
    {
        "study_id",
        "run_id",
        "condition_id",
        "participant_id",
        "session_id",
    }
)

# study_id must not contain path components so base_dir / study_id cannot escape base_dir
INVALID_STUDY_ID_SUBSTRINGS: ClassVar[tuple[str, ...]] = ("/", "\\", "..")


class FrameHeaderSettings(BaseModel):
    """Optional header branding inside the AppFrame."""

    model_config = ConfigDict(extra="forbid")

    logo: str | None = Field(
        default=None,
        description="Logo path (placeholders expanded at resolve time).",
    )
    title: str | None = Field(
        default=None,
        description="Header title (e.g. '{study_name}').",
    )
    show_phase_title: bool | None = Field(
        default=None,
        description=(
            "Show the active phase's title centred in the header. Omit or leave "
            "null so phase frame merges keep the study value; missing after merge "
            "means off."
        ),
    )


class FrameSettings(BaseModel):
    """AppFrame chrome defaults or per-phase overrides.

    A region set to ``False`` hides it (typical phase override during sleep).
    A dict configures content; omitted fields keep the study default after merge.
    """

    model_config = ConfigDict(extra="forbid")

    header: FrameHeaderSettings | bool | None = Field(
        default=None,
        description="Header config, or False to hide.",
    )
    footer: bool | None = Field(
        default=None,
        description="Footer visibility (False hides).",
    )


class StepperLayoutDefaults(BaseModel):
    """Default labels and behaviour for the stepper layout."""

    model_config = ConfigDict(extra="forbid")

    previous_button: str = Field(
        default="Previous", description="Label of the Previous button."
    )
    next_button: str = Field(default="Next", description="Label of the Next button.")
    complete_button: str = Field(
        default="Complete",
        description="Label of the Complete button, shown on the last step.",
    )
    show_activity_list: bool = Field(
        default=True,
        description="Show the list of steps next to the activity (above it on "
        "narrow windows).",
    )
    show_progress_bar: bool = Field(
        default=True,
        description="Show the progress bar between the Previous and Next buttons.",
    )
    show_step_count: bool = Field(
        default=True,
        description="Show 'Step x of y' above the progress bar (needs the bar).",
    )
    show_step_name: bool = Field(
        default=False,
        description="Show the current step's title above the progress bar "
        "(needs the bar).",
    )
    number_steps: bool = Field(
        default=False, description="Number the steps in the list."
    )
    allow_skip: bool = Field(
        default=False,
        description="Let the participant open any step and complete the phase "
        "without finishing every step.",
    )


class LayoutDefaults(BaseModel):
    """Per-layout-type defaults under ``ui.settings.layouts``."""

    model_config = ConfigDict(extra="forbid")

    stepper: StepperLayoutDefaults | None = Field(
        default=None,
        description="Defaults merged under phase layout.settings for type stepper.",
    )


class GuiSettings(BaseModel):
    """Optional settings when ``study.ui.type`` is ``gui``.

    Stored as ``PluginSpec.settings``; config validates with this model when
    resolving the GUI backend. Phase ``layout.settings`` / ``frame`` merge in
    config, not here.
    """

    model_config = ConfigDict(extra="forbid")

    port: int | None = Field(default=None, description="NiceGUI listen port.")
    favicon: str | None = Field(
        default=None,
        description="Favicon path (placeholders expanded at resolve time).",
    )
    frame: FrameSettings | None = Field(
        default=None,
        description="Default AppFrame chrome for the run.",
    )
    layouts: LayoutDefaults | None = Field(
        default=None,
        description="Per-layout-type defaults (e.g. stepper button labels).",
    )


class RunLayout(BaseModel):
    """Run output directory and path structure.

    Run directory is ``directory`` joined with ``layout`` formatted with
    run-context values (see :data:`VALID_RUN_LAYOUT_KEYS`).
    """

    directory: str = Field(
        default=DEFAULT_RUNS_DIR_NAME,
        description="Base directory for run outputs.",
    )
    layout: str = Field(
        default=DEFAULT_RUN_LAYOUT,
        min_length=1,
        description="Path relative to directory with placeholders.",
    )

    @model_validator(mode="after")
    def validate_layout(self) -> RunLayout:
        placeholders = re.findall(r"\{(\w+)\}", self.layout)
        unknown = set(placeholders) - VALID_RUN_LAYOUT_KEYS
        if unknown:
            raise ValueError(
                f"layout contains unknown placeholders: {sorted(unknown)}. "
                f"Allowed: {sorted(VALID_RUN_LAYOUT_KEYS)}."
            )
        return self


class LoggingConfig(BaseModel):
    """Logging configuration.

    Handlers are passed as kwargs to loguru ``logger.add()``. Sink paths may
    contain placeholders (e.g. ``run_id``) substituted at run start.
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
    _conditions: list[Condition] = PrivateAttr(default_factory=list)

    study_id: str = Field(..., min_length=1, description="Unique study identifier.")
    study_name: str = Field(..., min_length=1, description="Human-readable study name.")
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
    ui: PluginSpec = Field(
        default_factory=lambda: PluginSpec(type=DEFAULT_UI_TYPE),
        description="UI backend plugin spec (gui or headless).",
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="Logging configuration.",
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
    def conditions(self) -> list[Condition]:
        """Conditions loaded from the study directory (set by load_study())."""
        return self._conditions
