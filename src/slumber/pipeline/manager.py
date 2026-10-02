"""Pipeline lifecycle: start and stop named ezmsg graphs.

Full subprocess wiring lands with the pipelines workstream. This manager
tracks running pipeline ids so :class:`~slumber.run.engine.RunEngine` can
drive ``start_pipeline`` / ``stop_pipeline`` / ``end_run`` actions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from slumber.schemas.condition import Condition, Pipeline


class PipelineManager:
    """Start and stop pipelines by id for one condition run."""

    def __init__(self, condition: Condition) -> None:
        self._condition = condition
        self._running: set[str] = set()

    @property
    def running(self) -> frozenset[str]:
        """Ids of pipelines that have been started and not yet stopped."""
        return frozenset(self._running)

    def get_pipeline(self, pipeline_id: str) -> Pipeline:
        """Return the pipeline config for *pipeline_id*.

        Raises:
            KeyError: If the id is not in the condition.
        """
        try:
            return self._condition.pipelines_mapping[pipeline_id]
        except KeyError as e:
            available = sorted(self._condition.pipeline_ids)
            raise KeyError(
                f"Unknown pipeline {pipeline_id!r}. Available: {available}."
            ) from e

    def start(self, pipeline_id: str) -> None:
        """Mark *pipeline_id* as running (ezmsg subprocess TBD)."""
        pipeline = self.get_pipeline(pipeline_id)
        if pipeline_id in self._running:
            logger.warning(
                "Pipeline {!r} is already running; ignoring start.", pipeline_id
            )
            return
        # TODO: spawn ezmsg graph subprocess for pipeline.units / connections
        self._running.add(pipeline_id)
        logger.info(
            "Started pipeline {!r} ({} unit(s))",
            pipeline_id,
            len(pipeline.units),
        )

    def stop(self, pipeline_id: str) -> None:
        """Stop a running pipeline (no-op if not running)."""
        self.get_pipeline(pipeline_id)
        if pipeline_id not in self._running:
            logger.debug("Pipeline {!r} is not running; ignoring stop.", pipeline_id)
            return
        # TODO: terminate ezmsg graph subprocess
        self._running.discard(pipeline_id)
        logger.info("Stopped pipeline {!r}", pipeline_id)

    def stop_all(self) -> None:
        """Stop every running pipeline."""
        for pipeline_id in sorted(self._running):
            self.stop(pipeline_id)
