"""Subprocess entry point for running one ezmsg pipeline graph."""

from __future__ import annotations

from typing import Any

import ezmsg.core as ez
from loguru import logger

from slumber.pipeline.build import build_pipeline_graph
from slumber.schemas.condition import Pipeline


def run_pipeline_graph(pipeline: Pipeline) -> None:
    """Build and run an ezmsg graph for *pipeline* (blocks until terminated).

    Intended as a :class:`multiprocessing.Process` target. Unit settings must
    already be path-resolved. The parent stops the graph by terminating the
    process; there is no pipeline→engine channel.
    """
    components, connections = build_pipeline_graph(pipeline)
    logger.info(
        "Running pipeline {!r} with {} unit(s) and {} connection(s)",
        pipeline.id,
        len(components),
        len(connections),
    )
    ez.run(components=components, connections=connections)


def run_pipeline_payload(
    pipeline_id: str,
    units: list[dict[str, Any]],
    connections: list[tuple[str, str]],
) -> None:
    """Rebuild a :class:`Pipeline` from a picklable payload and run it.

    Args:
        pipeline_id: Pipeline id (for logging / Process naming).
        units: List of ``{"id", "type", "settings"}`` dicts.
        connections: List of ``(output, input)`` endpoint strings.
    """
    pipeline = Pipeline.model_validate(
        {
            "id": pipeline_id,
            "units": units,
            "connections": [{"output": out, "input": inp} for out, inp in connections],
        }
    )
    run_pipeline_graph(pipeline)
