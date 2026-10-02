"""Tests for Condition, Phase, Activity, Pipeline, Action, and loaders."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from slumber.schemas import (
    Action,
    Activity,
    Condition,
    Connection,
    EventHandler,
    Phase,
    Pipeline,
    PluginSpec,
    Unit,
    load_conditions_from_dir,
)


def _minimal_activity(**overrides: object) -> dict:
    data: dict = {
        "id": "welcome",
        "type": "instruction",
        "settings": {"content": "Hello"},
    }
    data.update(overrides)
    return data


def _minimal_phase(**overrides: object) -> dict:
    data: dict = {
        "id": "setup",
        "layout": {"type": "stepper"},
        "activities": [_minimal_activity()],
    }
    data.update(overrides)
    return data


def _minimal_pipeline(**overrides: object) -> dict:
    data: dict = {
        "id": "main",
        "units": [
            {"id": "clock", "type": "clock", "settings": {"rate": 1.0}},
            {"id": "store", "type": "jsonl_writer", "settings": {"path": "out.jsonl"}},
        ],
        "connections": [["clock/OUTPUT", "store/INPUT"]],
    }
    data.update(overrides)
    return data


class TestAction:
    """Tests for Action schema."""

    def test_start_phase(self) -> None:
        action = Action(start_phase="sleep")
        assert action.start_phase == "sleep"
        assert action.end_run is None

    def test_end_run(self) -> None:
        action = Action(end_run=True)
        assert action.end_run is True

    def test_rejects_multiple_fields(self) -> None:
        with pytest.raises(ValidationError):
            Action(start_phase="a", end_run=True)

    def test_rejects_empty(self) -> None:
        with pytest.raises(ValidationError):
            Action()

    def test_coerce_end_run_string(self) -> None:
        handler = EventHandler(event="phase_completed", do=["end_run"])
        assert handler.do[0].end_run is True

    def test_coerce_end_run_set(self) -> None:
        handler = EventHandler(event="phase_completed", do=[{"end_run"}])
        assert handler.do[0].end_run is True

    def test_coerce_end_run_null_mapping(self) -> None:
        handler = EventHandler(event="phase_completed", do=[{"end_run": None}])
        assert handler.do[0].end_run is True


class TestActivity:
    """Tests for Activity schema."""

    def test_valid_minimal(self) -> None:
        activity = Activity(id="welcome", type="instruction")
        assert activity.id == "welcome"
        assert activity.type == "instruction"
        assert activity.settings == {}
        assert activity.display_title == "welcome"
        assert activity.on == []

    def test_title_and_handlers(self) -> None:
        activity = Activity(
            id="sleep",
            title="Sleep",
            type="sleep",
            on=[
                EventHandler(
                    event="marked_awake",
                    do=[Action(start_phase="awakening")],
                )
            ],
        )
        assert activity.display_title == "Sleep"
        assert activity.on[0].event == "marked_awake"


class TestConnection:
    """Tests for Connection schema."""

    def test_valid(self) -> None:
        conn = Connection(output="clock/OUTPUT", input="store/INPUT")
        assert conn.output == "clock/OUTPUT"
        assert conn.input == "store/INPUT"

    def test_invalid_stream_format_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Connection(output="no_slash", input="a/b")
        with pytest.raises(ValidationError):
            Connection(output="a/b", input="a/b/c")


class TestPipeline:
    """Tests for Pipeline schema."""

    def test_valid_with_shorthand_connections(self) -> None:
        pipeline = Pipeline.model_validate(_minimal_pipeline())
        assert pipeline.id == "main"
        assert len(pipeline.units) == 2
        assert pipeline.connections[0].output == "clock/OUTPUT"
        assert pipeline.connections[0].input == "store/INPUT"

    def test_long_form_connections(self) -> None:
        pipeline = Pipeline.model_validate(
            {
                "id": "main",
                "units": [
                    {"id": "clock", "type": "clock"},
                    {"id": "store", "type": "jsonl_writer"},
                ],
                "connections": [
                    {"output": "clock/OUTPUT", "input": "store/INPUT"},
                ],
            }
        )
        assert pipeline.connections[0].output == "clock/OUTPUT"

    def test_duplicate_unit_ids_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Pipeline.model_validate(
                {
                    "id": "main",
                    "units": [
                        {"id": "clock", "type": "clock"},
                        {"id": "clock", "type": "jsonl_writer"},
                    ],
                }
            )
        assert "unique" in str(exc_info.value).lower()

    def test_units_min_length(self) -> None:
        with pytest.raises(ValidationError):
            Pipeline(id="main", units=[])


class TestPhase:
    """Tests for Phase schema."""

    def test_valid_minimal(self) -> None:
        phase = Phase.model_validate(_minimal_phase())
        assert phase.id == "setup"
        assert phase.display_title == "setup"
        assert phase.layout.type == "stepper"
        assert len(phase.activities) == 1

    def test_title_and_frame(self) -> None:
        phase = Phase.model_validate(
            _minimal_phase(
                title="Setup",
                frame={"header": False, "footer": False},
            )
        )
        assert phase.display_title == "Setup"
        assert phase.frame is not None
        assert phase.frame.header is False

    def test_duplicate_activity_ids_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Phase.model_validate(
                _minimal_phase(
                    activities=[
                        _minimal_activity(id="a"),
                        _minimal_activity(id="a", type="sleep"),
                    ]
                )
            )
        assert "unique" in str(exc_info.value).lower()


class TestCondition:
    """Tests for Condition schema."""

    def test_valid_minimal(self) -> None:
        cond = Condition.model_validate(
            {
                "name": "demo",
                "entry": "setup",
                "phases": [_minimal_phase()],
            }
        )
        assert cond.name == "demo"
        assert cond.entry == "setup"
        assert cond.pipelines == []
        assert "setup" in cond.phase_ids

    def test_valid_with_pipelines_and_handlers(self) -> None:
        cond = Condition.model_validate(
            {
                "name": "demo",
                "entry": "setup",
                "phases": [
                    {
                        "id": "setup",
                        "title": "Setup",
                        "layout": {"type": "stepper", "settings": {"allow_skip": True}},
                        "activities": [
                            {
                                "id": "welcome",
                                "title": "Welcome",
                                "type": "instruction",
                                "settings": {
                                    "content": "{assets_dir}/instructions/intro.md"
                                },
                            }
                        ],
                        "on": [
                            {
                                "event": "phase_completed",
                                "do": [
                                    {"start_pipeline": "main"},
                                    {"start_phase": "sleep"},
                                ],
                            }
                        ],
                    },
                    {
                        "id": "sleep",
                        "layout": {"type": "hub"},
                        "frame": {"header": False, "footer": False},
                        "activities": [
                            {
                                "id": "sleep",
                                "type": "sleep",
                                "on": [
                                    {
                                        "event": "end_sleep",
                                        "do": [
                                            {"stop_pipeline": "main"},
                                            {"end_run": True},
                                        ],
                                    }
                                ],
                            }
                        ],
                    },
                ],
                "pipelines": [_minimal_pipeline()],
            }
        )
        assert cond.phases_mapping["setup"].on[0].do[0].start_pipeline == "main"
        assert cond.pipelines_mapping["main"].unit_ids == {"clock", "store"}

    def test_name_required(self) -> None:
        with pytest.raises(ValidationError):
            Condition.model_validate(
                {"name": "", "entry": "setup", "phases": [_minimal_phase()]}
            )

    def test_phases_min_length(self) -> None:
        with pytest.raises(ValidationError):
            Condition.model_validate({"name": "demo", "entry": "setup", "phases": []})

    def test_duplicate_phase_ids_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Condition.model_validate(
                {
                    "name": "demo",
                    "entry": "setup",
                    "phases": [
                        _minimal_phase(id="setup"),
                        _minimal_phase(id="setup"),
                    ],
                }
            )
        assert "unique" in str(exc_info.value).lower()

    def test_duplicate_pipeline_ids_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            Condition.model_validate(
                {
                    "name": "demo",
                    "entry": "setup",
                    "phases": [_minimal_phase()],
                    "pipelines": [
                        _minimal_pipeline(id="main"),
                        _minimal_pipeline(id="main"),
                    ],
                }
            )
        assert "unique" in str(exc_info.value).lower()

    def test_rejects_legacy_procedures_and_dag(self) -> None:
        with pytest.raises(ValidationError):
            Condition.model_validate(
                {
                    "name": "legacy",
                    "procedures": {"pre_sleep": {"steps": [{"task": "instruction"}]}},
                    "dag": {"components": [{"name": "MASTER", "unit": "Master"}]},
                }
            )


def _minimal_condition_yaml(name: str = "demo") -> str:
    """Minimal valid condition YAML for load_conditions_from_dir tests."""
    return f"""
name: {name}
entry: setup
phases:
  - id: setup
    layout:
      type: stepper
    activities:
      - id: welcome
        type: instruction
        settings:
          content: Hello
pipelines: []
"""


class TestLoadConditionsFromDir:
    """Tests for load_conditions_from_dir."""

    def test_loads_conditions_from_directory(self, tmp_path: Path) -> None:
        (tmp_path / "control.yaml").write_text(
            _minimal_condition_yaml("condition_1"), encoding="utf-8"
        )
        (tmp_path / "other.yaml").write_text(
            _minimal_condition_yaml("condition_2"), encoding="utf-8"
        )
        conditions = load_conditions_from_dir(tmp_path)
        names = [c.name for c in conditions]
        assert "condition_1" in names
        assert "condition_2" in names
        assert len(conditions) == 2

    def test_returns_empty_list_for_empty_dir(self, tmp_path: Path) -> None:
        assert load_conditions_from_dir(tmp_path) == []

    def test_loads_demo_shaped_yaml_with_end_run_set(self, tmp_path: Path) -> None:
        """Design-doc style ``{ end_run }`` and bare ``on:`` load correctly.

        PyYAML treats bare ``on`` as boolean ``True`` and ``{ end_run }`` as
        ``{end_run: None}``; schemas coerce both forms.
        """
        (tmp_path / "demo.yaml").write_text(
            """
name: demo
entry: morning
phases:
  - id: morning
    layout:
      type: stepper
    activities:
      - id: complete
        type: instruction
    on:
      - event: phase_completed
        do:
          - { end_run }
""",
            encoding="utf-8",
        )
        conditions = load_conditions_from_dir(tmp_path)
        assert len(conditions) == 1
        assert conditions[0].phases[0].on[0].do[0].end_run is True

    def test_yaml_on_key_on_activity(self, tmp_path: Path) -> None:
        (tmp_path / "demo.yaml").write_text(
            """
name: demo
entry: sleep
phases:
  - id: sleep
    layout:
      type: hub
    activities:
      - id: sleep
        type: sleep
        on:
          - event: end_sleep
            do:
              - end_run: true
""",
            encoding="utf-8",
        )
        conditions = load_conditions_from_dir(tmp_path)
        assert conditions[0].phases[0].activities[0].on[0].event == "end_sleep"


class TestUnit:
    """Tests for Unit schema."""

    def test_extends_plugin_spec(self) -> None:
        unit = Unit(id="clock", type="clock", settings={"rate": 1.0})
        assert isinstance(unit, PluginSpec)
        assert unit.id == "clock"
        assert unit.settings["rate"] == 1.0
