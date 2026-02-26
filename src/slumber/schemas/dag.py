"""DAG schema: components, connections, and process groups (plugin-keyed)."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _coerce_connection(
    v: "Connection | tuple[str, str] | list[str] | dict[str, Any]",
) -> "Connection":
    """Coerce tuple/list [output, input] or dict to Connection."""
    if isinstance(v, Connection):
        return v
    if isinstance(v, (list, tuple)) and len(v) == 2:
        return Connection(output_stream=v[0], input_stream=v[1])
    if isinstance(v, dict):
        return Connection.model_validate(v)
    raise ValueError(
        "Each connection must be (output_stream, input_stream) or Connection."
    )


class Component(BaseModel):
    """DAG component specified by plugin key (unit_type).

    The `unit_type` field is a string key resolved via the slumber.units
    entry point; settings are passed to the unit at runtime.
    """

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...,
        min_length=1,
        pattern=r"[A-Z]+(?:_[A-Z0-9]+)*",
        description="Unique component name (uppercase with underscores).",
    )
    unit_type: str = Field(
        ...,
        min_length=1,
        alias="unit",
        description="Unit plugin key (e.g. 'ZMaxDataReceiver', 'CountQueue').",
    )
    settings: dict[str, Any] | None = Field(
        default=None,
        description="Plugin-specific unit settings.",
    )


class Connection(BaseModel):
    """A stream connection from one component output to another component input.

    Stream format is '<component_name>/<stream_name>' (e.g. 'ZMAX/OUTPUT_SAMPLE').
    """

    output_stream: str = Field(
        ..., min_length=1, description="Output stream: component_name/stream_name."
    )
    input_stream: str = Field(
        ..., min_length=1, description="Input stream: component_name/stream_name."
    )

    @model_validator(mode="after")
    def check_stream_format(self) -> "Connection":
        for stream, label in [
            (self.output_stream, "output_stream"),
            (self.input_stream, "input_stream"),
        ]:
            if "/" not in stream or len(stream.split("/")) != 2:
                raise ValueError(
                    f"{label} must be in format '<component_name>/<stream_name>', got: {stream!r}"
                )
        return self


class DAG(BaseModel):
    """Processing DAG: components, stream connections, and process component names.

    Component names must be unique. Connections reference components by the
    first segment of the stream name (before '/'); validation that stream names
    exist on the actual unit is done at runtime via the plugin registry.
    """

    components: list[Component] = Field(
        ..., min_length=1, description="DAG components."
    )
    connections: list[Connection] = Field(
        default_factory=list,
        description="Stream connections (output -> input).",
    )
    process_components: list[str] = Field(
        default_factory=list,
        description="Component names that run as separate processes.",
    )

    @field_validator("connections", mode="before")
    @classmethod
    def coerce_connections(cls, v: list[Any]) -> list[Connection]:
        if not v:
            return []
        return [_coerce_connection(c) for c in v]

    @model_validator(mode="after")
    def validate_unique_components(self) -> "DAG":
        names = [c.name for c in self.components]
        if len(names) != len(set(names)):
            raise ValueError("Component names must be unique.")
        return self

    @model_validator(mode="after")
    def validate_connections_reference_components(self) -> "DAG":
        for spec in self.connections:
            out_component = spec.output_stream.split("/", 1)[0]
            in_component = spec.input_stream.split("/", 1)[0]
            if out_component not in self.component_names:
                raise ValueError(
                    f"Connection output stream references unknown component {out_component!r}. "
                    f"Available: {', '.join(sorted(self.component_names))}."
                )
            if in_component not in self.component_names:
                raise ValueError(
                    f"Connection input stream references unknown component {in_component!r}. "
                    f"Available: {', '.join(sorted(self.component_names))}."
                )
        return self

    @model_validator(mode="after")
    def validate_process_components(self) -> "DAG":
        if unknown := set(self.process_components) - self.component_names:
            raise ValueError(
                f"process_components contains unknown components: {sorted(unknown)}. "
                f"Available: {sorted(self.component_names)}."
            )
        return self

    @property
    def components_mapping(self) -> dict[str, Component]:
        """Map component name -> Component."""
        return {c.name: c for c in self.components}

    @property
    def component_names(self) -> set[str]:
        """Set of component names in this DAG."""
        return set(self.components_mapping.keys())

    def has_component(self, name: str) -> bool:
        """Return True if a component with the given name exists."""
        return name in self.components_mapping
