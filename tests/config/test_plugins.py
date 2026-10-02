"""Tests for resolve_plugin_spec, merges, and validate_study_plugins."""

from __future__ import annotations

from pathlib import Path

import pytest

from slumber.config import init_study, load_study
from slumber.config.plugins import (
    PluginGroup,
    merge_frame_settings,
    merge_layout_settings,
    resolve_plugin_spec,
    validate_study_plugins,
)
from slumber.pipeline.units.clock import ClockUnit
from slumber.plugins import reset_registry
from slumber.schemas.condition import Condition
from slumber.schemas.plugin import PluginSpec
from slumber.schemas.study import FrameSettings, Study
from slumber.ui.activities.instruction import InstructionActivity
from slumber.ui.builtins import GuiBackend, HeadlessBackend, StepperLayout


@pytest.fixture(autouse=True)
def _fresh_registry() -> None:
    reset_registry()
    yield
    reset_registry()


def _minimal_condition(**overrides: object) -> dict:
    data: dict = {
        "name": "demo",
        "entry": "setup",
        "phases": [
            {
                "id": "setup",
                "layout": {"type": "stepper", "settings": {"allow_skip": True}},
                "activities": [
                    {
                        "id": "welcome",
                        "type": "instruction",
                        "settings": {"content": "Hello"},
                    }
                ],
                "on": [{"event": "phase_completed", "do": [{"end_run": True}]}],
            }
        ],
        "pipelines": [
            {
                "id": "main",
                "units": [
                    {"id": "clock", "type": "clock", "settings": {"rate": 1.0}},
                    {
                        "id": "store",
                        "type": "jsonl_writer",
                        "settings": {"path": "{run_dir}/clock.jsonl"},
                    },
                ],
                "connections": [["clock/OUTPUT", "store/INPUT"]],
            }
        ],
    }
    data.update(overrides)
    return data


class TestResolvePluginSpec:
    def test_resolves_headless_ui(self) -> None:
        plugin = resolve_plugin_spec(
            PluginSpec(type="headless"),
            PluginGroup.UI,
        )
        assert isinstance(plugin, HeadlessBackend)

    def test_headless_rejects_settings(self) -> None:
        with pytest.raises(Exception, match="extra|forbid|settings"):
            resolve_plugin_spec(
                PluginSpec(type="headless", settings={"port": 1}),
                PluginGroup.UI,
            )

    def test_resolves_gui_settings(self) -> None:
        plugin = resolve_plugin_spec(
            PluginSpec(type="gui", settings={"port": 9090}),
            PluginGroup.UI,
        )
        assert isinstance(plugin, GuiBackend)
        assert plugin.settings is not None
        assert plugin.settings.port == 9090

    def test_resolves_stepper_layout(self) -> None:
        plugin = resolve_plugin_spec(
            PluginSpec(type="stepper", settings={"allow_skip": True}),
            PluginGroup.LAYOUTS,
        )
        assert isinstance(plugin, StepperLayout)
        assert plugin.settings is not None
        assert plugin.settings.allow_skip is True

    def test_resolves_instruction_activity(self) -> None:
        plugin = resolve_plugin_spec(
            PluginSpec(type="instruction", settings={"content": "Hi"}),
            PluginGroup.ACTIVITIES,
        )
        assert isinstance(plugin, InstructionActivity)
        assert plugin.settings is not None
        assert plugin.settings.content == "Hi"

    def test_resolves_clock_unit(self) -> None:
        unit = resolve_plugin_spec(
            PluginSpec(type="clock", settings={"rate": 2.0}),
            PluginGroup.UNITS,
        )
        assert isinstance(unit, ClockUnit)


class TestMerges:
    def test_merge_layout_settings(self) -> None:
        study = Study(
            study_id="s",
            study_name="S",
            ui=PluginSpec(
                type="gui",
                settings={
                    "layouts": {
                        "stepper": {
                            "previous_button": "Back",
                            "allow_skip": False,
                        }
                    }
                },
            ),
        )
        merged = merge_layout_settings(
            study,
            PluginSpec(type="stepper", settings={"allow_skip": True}),
        )
        assert merged["previous_button"] == "Back"
        assert merged["allow_skip"] is True

    def test_merge_frame_settings(self) -> None:
        merged = merge_frame_settings(
            {"header": {"title": "Study", "logo": "a.png"}, "footer": True},
            FrameSettings(header=False),
        )
        assert merged["header"] is False
        assert merged["footer"] is True


class TestValidateStudyPlugins:
    def test_valid_study(self, tmp_path: Path) -> None:
        study_path = init_study(
            tmp_path, "s1", create_env_example=False, create_gitignore=False
        )
        (study_path / "conditions" / "demo.yaml").write_text(
            """
name: demo
entry: setup
phases:
  - id: setup
    layout: {type: stepper}
    activities:
      - id: welcome
        type: instruction
        settings: {content: Hello}
    on:
      - event: phase_completed
        do: [end_run]
pipelines: []
""",
            encoding="utf-8",
        )
        study = load_study(study_path)
        validate_study_plugins(study)

    def test_unknown_entry(self) -> None:
        study = Study(study_id="s", study_name="S")
        study._conditions = [
            Condition.model_validate(_minimal_condition(entry="missing", pipelines=[]))
        ]
        with pytest.raises(ValueError, match="entry"):
            validate_study_plugins(study)

    def test_unknown_activity_type(self) -> None:
        study = Study(study_id="s", study_name="S")
        bad = _minimal_condition(pipelines=[])
        bad["phases"][0]["activities"][0]["type"] = "nope"
        study._conditions = [Condition.model_validate(bad)]
        with pytest.raises(ValueError, match="nope"):
            validate_study_plugins(study)

    def test_unknown_connection_unit(self) -> None:
        study = Study(study_id="s", study_name="S")
        bad = _minimal_condition()
        bad["pipelines"][0]["connections"] = [["ghost/OUTPUT", "store/INPUT"]]
        study._conditions = [Condition.model_validate(bad)]
        with pytest.raises(ValueError, match="ghost"):
            validate_study_plugins(study)

    def test_unknown_start_phase_in_handler(self) -> None:
        study = Study(study_id="s", study_name="S")
        bad = _minimal_condition(pipelines=[])
        bad["phases"][0]["on"] = [
            {"event": "phase_completed", "do": [{"start_phase": "nope"}]}
        ]
        study._conditions = [Condition.model_validate(bad)]
        with pytest.raises(ValueError, match="start_phase"):
            validate_study_plugins(study)
