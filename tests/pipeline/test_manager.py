"""Tests for pipeline units, graph build, and PipelineManager."""

from __future__ import annotations

import json
import time
from pathlib import Path

import ezmsg.core as ez
import pytest
from pydantic import ValidationError

from slumber.pipeline.build import build_pipeline_graph
from slumber.pipeline.manager import PipelineManager
from slumber.pipeline.units import (
    ClockSettings,
    ClockUnit,
    JsonlWriterSettings,
    JsonlWriterUnit,
    build_unit_from_settings,
)
from slumber.schemas.condition import Condition, Connection, Pipeline, Unit


def _condition_with_pipeline(pipeline: Pipeline) -> Condition:
    return Condition(
        name="ctrl",
        entry="setup",
        phases=[
            {
                "id": "setup",
                "layout": {"type": "stepper"},
                "activities": [
                    {
                        "id": "welcome",
                        "type": "instruction",
                        "settings": {"content": "hi"},
                    }
                ],
            }
        ],
        pipelines=[pipeline],
    )


class TestClockUnit:
    def test_settings_require_positive_rate(self) -> None:
        with pytest.raises(ValidationError):
            ClockSettings.model_validate({"rate": 0})

    def test_build_from_settings(self) -> None:
        unit = build_unit_from_settings(ClockUnit, {"rate": 2.5})
        assert isinstance(unit, ClockUnit)
        assert unit.SETTINGS.rate == 2.5
        assert isinstance(ClockUnit.OUTPUT, ez.OutputStream)


class TestJsonlWriterUnit:
    def test_settings_require_path(self) -> None:
        with pytest.raises(ValidationError):
            JsonlWriterSettings.model_validate({})

    def test_build_from_settings(self) -> None:
        unit = build_unit_from_settings(JsonlWriterUnit, {"path": "/tmp/clock.jsonl"})
        assert isinstance(unit, JsonlWriterUnit)
        assert unit.SETTINGS.path == "/tmp/clock.jsonl"
        assert isinstance(JsonlWriterUnit.INPUT, ez.InputStream)


class TestBuildPipelineGraph:
    def test_wires_clock_to_jsonl_writer(self, tmp_path: Path) -> None:
        out = tmp_path / "clock.jsonl"
        pipeline = Pipeline(
            id="main",
            units=[
                Unit(id="clock", type="clock", settings={"rate": 5.0}),
                Unit(
                    id="store",
                    type="jsonl_writer",
                    settings={"path": str(out)},
                ),
            ],
            connections=[Connection(output="clock/OUTPUT", input="store/INPUT")],
        )
        components, connections = build_pipeline_graph(pipeline)
        assert set(components) == {"clock", "store"}
        assert isinstance(components["clock"], ClockUnit)
        assert isinstance(components["store"], JsonlWriterUnit)
        assert len(connections) == 1
        assert connections[0][0] is components["clock"].OUTPUT
        assert connections[0][1] is components["store"].INPUT

    def test_unknown_stream_raises(self) -> None:
        pipeline = Pipeline(
            id="main",
            units=[Unit(id="clock", type="clock", settings={"rate": 1.0})],
            connections=[
                Connection(output="clock/MISSING", input="clock/OUTPUT"),
            ],
        )
        with pytest.raises(AttributeError, match="MISSING"):
            build_pipeline_graph(pipeline)


class TestPipelineManager:
    def test_start_stop_writes_jsonl(self, tmp_path: Path) -> None:
        out = tmp_path / "clock.jsonl"
        pipeline = Pipeline(
            id="main",
            units=[
                Unit(id="clock", type="clock", settings={"rate": 20.0}),
                Unit(
                    id="store",
                    type="jsonl_writer",
                    settings={"path": "{run_dir}/clock.jsonl"},
                ),
            ],
            connections=[["clock/OUTPUT", "store/INPUT"]],
        )
        condition = _condition_with_pipeline(pipeline)
        manager = PipelineManager(
            condition,
            study_root=tmp_path,
            placeholders={"run_dir": str(tmp_path)},
        )

        manager.start("main")
        assert manager.running == frozenset({"main"})
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            if out.is_file() and out.stat().st_size > 0:
                break
            time.sleep(0.05)
        manager.stop("main")
        assert manager.running == frozenset()

        assert out.is_file()
        lines = [line for line in out.read_text(encoding="utf-8").splitlines() if line]
        assert len(lines) >= 1
        sample = json.loads(lines[0])
        assert "n" in sample
        assert "t" in sample

    def test_start_requires_configure(self, tmp_path: Path) -> None:
        pipeline = Pipeline(
            id="main",
            units=[Unit(id="clock", type="clock", settings={"rate": 1.0})],
            connections=[],
        )
        manager = PipelineManager(_condition_with_pipeline(pipeline))
        with pytest.raises(RuntimeError, match="study_root"):
            manager.start("main")

    def test_unknown_pipeline_raises(self, tmp_path: Path) -> None:
        pipeline = Pipeline(
            id="main",
            units=[Unit(id="clock", type="clock", settings={"rate": 1.0})],
            connections=[],
        )
        manager = PipelineManager(
            _condition_with_pipeline(pipeline),
            study_root=tmp_path,
            placeholders={},
        )
        with pytest.raises(KeyError, match="missing"):
            manager.start("missing")

    def test_stop_all(self, tmp_path: Path) -> None:
        pipeline = Pipeline(
            id="main",
            units=[Unit(id="clock", type="clock", settings={"rate": 10.0})],
            connections=[],
        )
        manager = PipelineManager(
            _condition_with_pipeline(pipeline),
            study_root=tmp_path,
            placeholders={},
        )
        manager.start("main")
        manager.stop_all()
        assert manager.running == frozenset()
