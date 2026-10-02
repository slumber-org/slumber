"""Condition schema: phases, activities, pipelines, and event actions."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from slumber.schemas.plugin import PluginSpec
from slumber.schemas.study import FrameSettings
from slumber.utils.errors import format_validation_error
from slumber.utils.yaml import EXTENSIONS, load_and_validate

_ACTION_FIELDS = ("start_phase", "start_pipeline", "stop_pipeline", "end_run")


def _remap_yaml_on_key(data: Any) -> Any:
    """Map YAML boolean key ``True`` (from bare ``on:``) to the string ``on``.

    PyYAML parses unquoted ``on`` as boolean ``True``, so condition YAML written
    as ``on:`` arrives as ``{True: [...]}`` unless quoted.
    """
    if isinstance(data, dict) and True in data and "on" not in data:
        remapped = dict(data)
        remapped["on"] = remapped.pop(True)
        return remapped
    return data


def _coerce_action(value: Any) -> Action:
    """Coerce YAML action forms into an :class:`Action`."""
    if isinstance(value, Action):
        return value
    if isinstance(value, str):
        if value == "end_run":
            return Action(end_run=True)
        raise ValueError(
            f"Unknown action string {value!r}; expected one of {_ACTION_FIELDS}."
        )
    if isinstance(value, set):
        if value == {"end_run"}:
            return Action(end_run=True)
        raise ValueError(
            f"Unknown action set {value!r}; only {{end_run}} is supported as a set."
        )
    if isinstance(value, dict):
        data = dict(value)
        if "end_run" in data and data["end_run"] is None:
            data["end_run"] = True
        return Action.model_validate(data)
    raise ValueError(
        "Each action must be a mapping (e.g. {start_phase: setup}), "
        "'end_run', or {end_run}."
    )


def _coerce_connection(
    value: Connection | tuple[str, str] | list[str] | dict[str, Any],
) -> Connection:
    """Coerce ``[output, input]`` or dict to :class:`Connection`."""
    if isinstance(value, Connection):
        return value
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return Connection(output=value[0], input=value[1])
    if isinstance(value, dict):
        return Connection.model_validate(value)
    raise ValueError("Each connection must be [output, input] or {output, input}.")


class Action(BaseModel):
    """One engine action from an event handler ``do`` list.

    Exactly one of ``start_phase``, ``start_pipeline``, ``stop_pipeline``, or
    ``end_run`` must be set.
    """

    model_config = ConfigDict(extra="forbid")

    start_phase: str | None = Field(
        default=None,
        min_length=1,
        description="Phase id to start.",
    )
    start_pipeline: str | None = Field(
        default=None,
        min_length=1,
        description="Pipeline id to start.",
    )
    stop_pipeline: str | None = Field(
        default=None,
        min_length=1,
        description="Pipeline id to stop.",
    )
    end_run: Literal[True] | None = Field(
        default=None,
        description="When True, end the run.",
    )

    @model_validator(mode="after")
    def exactly_one_action(self) -> Action:
        set_fields = [
            name for name in _ACTION_FIELDS if getattr(self, name) is not None
        ]
        if len(set_fields) != 1:
            raise ValueError(
                f"Action must set exactly one of {_ACTION_FIELDS}; "
                f"got {set_fields or 'none'}."
            )
        return self


class EventHandler(BaseModel):
    """Map a named study event to an ordered list of actions."""

    model_config = ConfigDict(extra="forbid")

    event: str = Field(..., min_length=1, description="Event name to handle.")
    do: list[Action] = Field(
        ...,
        min_length=1,
        description="Actions to run in order when the event fires.",
    )

    @field_validator("do", mode="before")
    @classmethod
    def coerce_actions(cls, value: Any) -> list[Action]:
        if not isinstance(value, list):
            raise TypeError("do must be a list of actions.")
        return [_coerce_action(item) for item in value]


class Activity(PluginSpec):
    """Activity instance in a phase (PluginSpec plus id, title, and handlers)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        ..., min_length=1, description="Unique activity id within the phase."
    )
    title: str | None = Field(
        default=None,
        description="Display title. Defaults to id when omitted.",
    )
    on: list[EventHandler] = Field(
        default_factory=list,
        description="Event handlers scoped to this activity.",
    )

    @model_validator(mode="before")
    @classmethod
    def coerce_yaml_on_key(cls, data: Any) -> Any:
        return _remap_yaml_on_key(data)

    @property
    def display_title(self) -> str:
        """Return the title to show in the UI."""
        return self.title if self.title is not None else self.id


class Connection(BaseModel):
    """A stream connection from one unit output to another unit input.

    Stream format is ``<unit_id>/<stream_name>`` (e.g. ``clock/OUTPUT``).
    """

    model_config = ConfigDict(extra="forbid")

    output: str = Field(
        ...,
        min_length=1,
        description="Output stream: unit_id/stream_name.",
    )
    input: str = Field(
        ...,
        min_length=1,
        description="Input stream: unit_id/stream_name.",
    )

    @model_validator(mode="after")
    def check_stream_format(self) -> Connection:
        for stream, label in [(self.output, "output"), (self.input, "input")]:
            if "/" not in stream or len(stream.split("/")) != 2:
                raise ValueError(
                    f"{label} must be in format '<unit_id>/<stream_name>', "
                    f"got: {stream!r}"
                )
        return self


class Unit(PluginSpec):
    """Pipeline unit instance (PluginSpec plus id)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        ..., min_length=1, description="Unique unit id within the pipeline."
    )


class Pipeline(BaseModel):
    """Named processing graph: units and stream connections."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1, description="Unique pipeline id.")
    units: list[Unit] = Field(..., min_length=1, description="Pipeline units.")
    connections: list[Connection] = Field(
        default_factory=list,
        description="Stream connections (output -> input).",
    )

    @field_validator("connections", mode="before")
    @classmethod
    def coerce_connections(cls, value: list[Any]) -> list[Connection]:
        if not value:
            return []
        return [_coerce_connection(item) for item in value]

    @model_validator(mode="after")
    def validate_unique_unit_ids(self) -> Pipeline:
        ids = [unit.id for unit in self.units]
        if len(ids) != len(set(ids)):
            raise ValueError("Unit ids must be unique within a pipeline.")
        return self

    @property
    def unit_ids(self) -> set[str]:
        """Set of unit ids in this pipeline."""
        return {unit.id for unit in self.units}

    @property
    def units_mapping(self) -> dict[str, Unit]:
        """Map unit id -> Unit."""
        return {unit.id: unit for unit in self.units}


class Phase(BaseModel):
    """Named stage of a condition: layout, activities, and optional handlers."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=1, description="Unique phase id.")
    title: str | None = Field(
        default=None,
        description="Display title. Defaults to id when omitted.",
    )
    layout: PluginSpec = Field(
        ..., description="Layout plugin spec (e.g. stepper, hub)."
    )
    activities: list[Activity] = Field(
        ...,
        min_length=1,
        description="Ordered activities hosted by the layout.",
    )
    frame: FrameSettings | None = Field(
        default=None,
        description="Optional AppFrame override merged over study ui.settings.frame.",
    )
    on: list[EventHandler] = Field(
        default_factory=list,
        description="Event handlers scoped to this phase.",
    )

    @model_validator(mode="before")
    @classmethod
    def coerce_yaml_on_key(cls, data: Any) -> Any:
        return _remap_yaml_on_key(data)

    @model_validator(mode="after")
    def validate_unique_activity_ids(self) -> Phase:
        ids = [activity.id for activity in self.activities]
        if len(ids) != len(set(ids)):
            raise ValueError("Activity ids must be unique within a phase.")
        return self

    @property
    def display_title(self) -> str:
        """Return the title to show in the UI."""
        return self.title if self.title is not None else self.id


class Condition(BaseModel):
    """A single condition: entry phase, phases, and pipelines."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, description="Condition name.")
    entry: str = Field(..., min_length=1, description="Id of the phase to start.")
    phases: list[Phase] = Field(..., min_length=1, description="Condition phases.")
    pipelines: list[Pipeline] = Field(
        default_factory=list,
        description="Named processing pipelines.",
    )

    @model_validator(mode="after")
    def validate_unique_phase_ids(self) -> Condition:
        ids = [phase.id for phase in self.phases]
        if len(ids) != len(set(ids)):
            raise ValueError("Phase ids must be unique.")
        return self

    @model_validator(mode="after")
    def validate_unique_pipeline_ids(self) -> Condition:
        ids = [pipeline.id for pipeline in self.pipelines]
        if len(ids) != len(set(ids)):
            raise ValueError("Pipeline ids must be unique.")
        return self

    @property
    def phase_ids(self) -> set[str]:
        """Set of phase ids in this condition."""
        return {phase.id for phase in self.phases}

    @property
    def pipeline_ids(self) -> set[str]:
        """Set of pipeline ids in this condition."""
        return {pipeline.id for pipeline in self.pipelines}

    @property
    def phases_mapping(self) -> dict[str, Phase]:
        """Map phase id -> Phase."""
        return {phase.id: phase for phase in self.phases}

    @property
    def pipelines_mapping(self) -> dict[str, Pipeline]:
        """Map pipeline id -> Pipeline."""
        return {pipeline.id: pipeline for pipeline in self.pipelines}


def load_conditions_from_dir(conditions_dir: Path) -> list[Condition]:
    """Load and validate all condition YAML files from a conditions directory.

    Args:
        conditions_dir: Path to the directory containing condition YAML files.

    Returns:
        List of validated Condition instances, sorted by filename.

    Raises:
        FileNotFoundError: If the conditions directory does not exist.
        ValueError: If any condition file fails validation, or its ``name`` does
            not match the file stem (message includes path).
    """
    if not conditions_dir.is_dir():
        raise FileNotFoundError(f"Conditions directory not found: {conditions_dir}")
    condition_files = sorted(
        file_path
        for file_path in conditions_dir.iterdir()
        if file_path.is_file() and file_path.suffix.lower() in EXTENSIONS
    )
    conditions: list[Condition] = []
    for file_path in condition_files:
        try:
            condition = load_and_validate(file_path, Condition)
        except ValidationError as e:
            msg = format_validation_error(
                e, path=file_path, prefix="Condition file error"
            )
            raise ValueError(msg) from e
        if condition.name != file_path.stem:
            raise ValueError(
                f"Condition file error: {file_path}\n"
                f"  name: '{condition.name}' does not match the file name "
                f"'{file_path.stem}'"
            )
        conditions.append(condition)
    return conditions
