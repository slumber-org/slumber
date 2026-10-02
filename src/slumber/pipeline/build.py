"""Build ezmsg component graphs from resolved pipeline configs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import ezmsg.core as ez

from slumber.config.plugins import PluginGroup, resolve_plugin_spec
from slumber.schemas.plugin import PluginSpec

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from slumber.plugins.registry import PluginRegistry
    from slumber.schemas.condition import Connection, Pipeline, Unit


def _resolve_stream(components: Mapping[str, ez.Unit], endpoint: str) -> ez.Stream:
    """Resolve ``unit_id/STREAM`` to an ezmsg stream object."""
    unit_id, stream_name = endpoint.split("/", 1)
    try:
        unit = components[unit_id]
    except KeyError as e:
        available = sorted(components)
        raise KeyError(
            f"Unknown unit {unit_id!r} in connection endpoint {endpoint!r}. "
            f"Available: {available}."
        ) from e
    try:
        stream = getattr(unit, stream_name)
    except AttributeError as e:
        raise AttributeError(
            f"Unit {unit_id!r} has no stream {stream_name!r} (endpoint {endpoint!r})."
        ) from e
    return stream


def build_units(
    units: Sequence[Unit],
    *,
    registry: PluginRegistry | None = None,
) -> dict[str, ez.Unit]:
    """Instantiate pipeline units from already-resolved settings.

    Args:
        units: Unit configs whose ``settings`` paths are already resolved.
        registry: Optional plugin registry override.

    Returns:
        Mapping of unit id to ezmsg Unit instance.
    """
    components: dict[str, ez.Unit] = {}
    for unit in units:
        spec = PluginSpec(type=unit.type, settings=dict(unit.settings))
        instance = resolve_plugin_spec(spec, PluginGroup.UNITS, registry=registry)
        if not isinstance(instance, ez.Unit):
            raise TypeError(
                f"Unit {unit.id!r} type {unit.type!r} must be an ez.Unit, "
                f"got {type(instance).__name__}."
            )
        components[unit.id] = instance
    return components


def build_connections(
    components: Mapping[str, ez.Unit],
    connections: Sequence[Connection],
) -> list[tuple[Any, Any]]:
    """Resolve connection endpoints to ``(output_stream, input_stream)`` pairs."""
    return [
        (
            _resolve_stream(components, connection.output),
            _resolve_stream(components, connection.input),
        )
        for connection in connections
    ]


def build_pipeline_graph(
    pipeline: Pipeline,
    *,
    registry: PluginRegistry | None = None,
) -> tuple[dict[str, ez.Unit], list[tuple[Any, Any]]]:
    """Build components and wired connections for a pipeline config.

    Args:
        pipeline: Pipeline whose unit settings are already path-resolved.
        registry: Optional plugin registry override.

    Returns:
        ``(components, connections)`` suitable for :func:`ezmsg.core.run`.
    """
    components = build_units(pipeline.units, registry=registry)
    connections = build_connections(components, pipeline.connections)
    return components, connections
