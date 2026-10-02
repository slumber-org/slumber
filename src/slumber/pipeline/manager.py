"""Pipeline lifecycle: start and stop named ezmsg graphs in subprocesses."""

from __future__ import annotations

from multiprocessing import Process
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from slumber.config.paths import resolve_settings
from slumber.pipeline.build import build_pipeline_graph
from slumber.pipeline.runner import run_pipeline_payload
from slumber.schemas.condition import Pipeline, Unit

if TYPE_CHECKING:
    from collections.abc import Mapping

    from slumber.plugins.registry import PluginRegistry
    from slumber.schemas.condition import Condition

_DEFAULT_TERMINATION_TIMEOUT_S = 5.0


class PipelineManager:
    """Start and stop pipelines by id for one condition run.

    Each ``start`` spawns a subprocess that builds the ezmsg graph and blocks
    in ``ez.run``. ``stop`` terminates that process. Unit settings are
    path-resolved (placeholders → study root) before the child is spawned.
    """

    def __init__(
        self,
        condition: Condition,
        *,
        study_root: Path | None = None,
        placeholders: Mapping[str, str] | None = None,
        registry: PluginRegistry | None = None,
        termination_timeout: float = _DEFAULT_TERMINATION_TIMEOUT_S,
    ) -> None:
        self._condition = condition
        self._study_root = study_root.resolve() if study_root is not None else None
        self._placeholders: dict[str, str] = (
            dict(placeholders) if placeholders is not None else {}
        )
        self._registry = registry
        self._termination_timeout = termination_timeout
        self._processes: dict[str, Process] = {}

    @property
    def running(self) -> frozenset[str]:
        """Ids of pipelines that have been started and not yet stopped."""
        return frozenset(self._processes)

    def configure(
        self,
        *,
        study_root: Path,
        placeholders: Mapping[str, str],
        registry: PluginRegistry | None = None,
    ) -> None:
        """Attach run-time path context used when resolving unit settings."""
        self._study_root = study_root.resolve()
        self._placeholders = dict(placeholders)
        if registry is not None:
            self._registry = registry

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
        """Spawn an ezmsg subprocess for *pipeline_id*."""
        pipeline = self.get_pipeline(pipeline_id)
        if pipeline_id in self._processes:
            logger.warning(
                "Pipeline {!r} is already running; ignoring start.", pipeline_id
            )
            return

        resolved = self._resolve_pipeline(pipeline)
        # Fail fast in the parent before spawning (settings / streams / types).
        build_pipeline_graph(resolved, registry=self._registry)

        units_payload = [
            {"id": unit.id, "type": unit.type, "settings": dict(unit.settings)}
            for unit in resolved.units
        ]
        connections_payload = [
            (connection.output, connection.input) for connection in resolved.connections
        ]

        process = Process(
            target=run_pipeline_payload,
            args=(pipeline_id, units_payload, connections_payload),
            name=f"pipeline-{pipeline_id}",
            daemon=True,
        )
        process.start()
        self._processes[pipeline_id] = process
        logger.info(
            "Started pipeline {!r} (pid={}, {} unit(s))",
            pipeline_id,
            process.pid,
            len(resolved.units),
        )

    def stop(self, pipeline_id: str) -> None:
        """Terminate a running pipeline process (no-op if not running)."""
        self.get_pipeline(pipeline_id)
        process = self._processes.pop(pipeline_id, None)
        if process is None:
            logger.debug("Pipeline {!r} is not running; ignoring stop.", pipeline_id)
            return
        self._terminate_process(pipeline_id, process)
        logger.info("Stopped pipeline {!r}", pipeline_id)

    def stop_all(self) -> None:
        """Stop every running pipeline."""
        for pipeline_id in sorted(self._processes):
            self.stop(pipeline_id)

    def _resolve_pipeline(self, pipeline: Pipeline) -> Pipeline:
        if self._study_root is None:
            raise RuntimeError(
                "PipelineManager has no study_root; call configure() before start()."
            )
        resolved_units: list[Unit] = []
        for unit in pipeline.units:
            settings = resolve_settings(
                dict(unit.settings),
                study_root=self._study_root,
                placeholders=self._placeholders,
            )
            resolved_units.append(Unit(id=unit.id, type=unit.type, settings=settings))
        return Pipeline(
            id=pipeline.id,
            units=resolved_units,
            connections=list(pipeline.connections),
        )

    def _terminate_process(self, pipeline_id: str, process: Process) -> None:
        if not process.is_alive():
            process.join(timeout=0)
            if process.exitcode not in (0, None):
                logger.warning(
                    "Pipeline {!r} process exited with code {}",
                    pipeline_id,
                    process.exitcode,
                )
            return

        process.terminate()
        process.join(timeout=self._termination_timeout)
        if process.is_alive():
            logger.warning(
                "Pipeline {!r} did not stop after terminate; killing.",
                pipeline_id,
            )
            process.kill()
            process.join(timeout=self._termination_timeout)
        if process.is_alive():
            logger.error(
                "Pipeline {!r} process remains alive (pid={})",
                pipeline_id,
                process.pid,
            )
