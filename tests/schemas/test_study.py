"""Tests for Study, RunLayout, PluginSpec UI, GuiSettings, and LoggingConfig."""

import pytest
from pydantic import ValidationError

from slumber.schemas import (
    GuiSettings,
    LoggingConfig,
    PluginSpec,
    RunLayout,
    StepperLayoutDefaults,
    Study,
)


class TestPluginSpec:
    """Tests for PluginSpec schema."""

    def test_valid_minimal(self) -> None:
        spec = PluginSpec(type="headless")
        assert spec.type == "headless"
        assert spec.settings == {}

    def test_valid_with_settings(self) -> None:
        spec = PluginSpec(type="gui", settings={"port": 8080})
        assert spec.type == "gui"
        assert spec.settings["port"] == 8080

    def test_type_required(self) -> None:
        with pytest.raises(ValidationError):
            PluginSpec(type="")


class TestGuiSettings:
    """Tests for GuiSettings schema."""

    def test_valid_defaults(self) -> None:
        settings = GuiSettings()
        assert settings.port is None
        assert settings.favicon is None
        assert settings.frame is None
        assert settings.layouts is None

    def test_valid_full(self) -> None:
        settings = GuiSettings(
            port=8080,
            favicon="{assets_dir}/favicon.png",
            frame={
                "header": {"logo": "{assets_dir}/logo.png", "title": "{study_name}"},
            },
            layouts={
                "stepper": {
                    "previous_button": "Back",
                    "allow_skip": True,
                }
            },
        )
        assert settings.port == 8080
        assert settings.frame is not None
        assert settings.frame.header is not None
        assert settings.layouts is not None
        assert settings.layouts.stepper is not None
        assert settings.layouts.stepper.allow_skip is True

    def test_stepper_defaults(self) -> None:
        stepper = StepperLayoutDefaults()
        assert stepper.show_activity_list is True
        assert stepper.show_progress_bar is True
        assert stepper.show_step_count is True
        assert stepper.show_step_name is False
        assert stepper.number_steps is False
        assert stepper.allow_skip is False

    def test_stepper_rejects_unknown_setting(self) -> None:
        with pytest.raises(ValidationError):
            StepperLayoutDefaults(show_progress=True)  # type: ignore[call-arg]

    def test_frame_header_false(self) -> None:
        settings = GuiSettings(frame={"header": False, "footer": False})
        assert settings.frame is not None
        assert settings.frame.header is False
        assert settings.frame.footer is False

    def test_show_phase_title_unset_by_default(self) -> None:
        settings = GuiSettings(frame={"header": {"title": "Study"}})
        assert settings.frame is not None
        assert settings.frame.header.show_phase_title is None
        dumped = settings.frame.model_dump(exclude_none=True)
        assert "show_phase_title" not in dumped["header"]

    def test_show_phase_title_true(self) -> None:
        settings = GuiSettings(frame={"header": {"show_phase_title": True}})
        assert settings.frame is not None
        assert settings.frame.header.show_phase_title is True


class TestRunLayout:
    """Tests for RunLayout schema."""

    def test_valid_defaults(self) -> None:
        layout = RunLayout()
        assert layout.directory == "runs"
        assert layout.layout == "run-{run_id}"

    def test_valid_custom(self) -> None:
        layout = RunLayout(
            directory="output",
            layout="sub-{participant_id}/run-{run_id}",
        )
        assert layout.directory == "output"
        assert layout.layout == "sub-{participant_id}/run-{run_id}"

    def test_invalid_placeholder_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            RunLayout(layout="sub-{participant_id}/run-{unknown_placeholder}")
        assert "unknown" in str(exc_info.value).lower() or "placeholder" in str(
            exc_info.value
        )

    def test_allowed_placeholders_accepted(self) -> None:
        layout = RunLayout(
            layout=(
                "s-{study_id}/p-{participant_id}/c-{condition_id}/"
                "ses-{session_id}/r-{run_id}"
            )
        )
        assert "study_id" in layout.layout


class TestLoggingConfig:
    """Tests for LoggingConfig schema."""

    def test_valid_defaults(self) -> None:
        cfg = LoggingConfig()
        assert cfg.level == "INFO"
        assert cfg.handlers == []

    def test_valid_with_handlers(self) -> None:
        cfg = LoggingConfig(
            level="DEBUG",
            handlers=[
                {"sink": "stderr", "level": "INFO"},
                {"sink": "runs/run_{run_id}.log", "rotation": "10 MB"},
            ],
        )
        assert cfg.level == "DEBUG"
        assert len(cfg.handlers) == 2


class TestStudy:
    """Tests for Study manifest schema."""

    def test_valid_minimal(self) -> None:
        study = Study(
            study_id="test-study",
            study_name="Test Study",
            ui=PluginSpec(type="headless"),
        )
        assert study.study_id == "test-study"
        assert study.study_name == "Test Study"
        assert study.conditions_dir == "conditions"
        assert study.ui.type == "headless"
        assert study.runs.directory == "runs"
        assert study.logging.level == "INFO"
        assert not hasattr(study, "audit") or "audit" not in study.model_fields

    def test_valid_full(self) -> None:
        study = Study(
            study_id="ld-2025",
            study_name="Lucid Dreaming Pilot",
            conditions_dir="conditions",
            ui=PluginSpec(type="gui", settings={"port": 8080}),
        )
        assert study.conditions_dir == "conditions"
        assert study.ui.settings["port"] == 8080

    def test_study_id_required(self) -> None:
        with pytest.raises(ValidationError):
            Study(
                study_id="",
                study_name="A Study",
                ui=PluginSpec(type="headless"),
            )

    def test_study_id_rejects_path_components(self) -> None:
        """study_id must not contain '/', '\\', or '..' so it cannot escape base_dir."""
        for invalid_id in ("a/b", "..", "a/../b", "a\\b", "study..id"):
            with pytest.raises(ValidationError) as exc_info:
                Study(study_id=invalid_id, study_name="Study")
            assert (
                "path" in str(exc_info.value).lower()
                or "forbidden" in str(exc_info.value).lower()
            )

    def test_study_id_accepts_safe_values(self) -> None:
        """study_id accepts alphanumeric, hyphen, underscore (no path components)."""
        study = Study(study_id="my-study_2025", study_name="Study")
        assert study.study_id == "my-study_2025"

    def test_study_name_required(self) -> None:
        with pytest.raises(ValidationError):
            Study(
                study_id="x",
                study_name="",
                ui=PluginSpec(type="headless"),
            )

    def test_ui_has_default(self) -> None:
        """Study accepts minimal args; ui defaults to headless."""
        study = Study(study_id="x", study_name="Y")
        assert study.ui.type == "headless"

    def test_rejects_legacy_name_field(self) -> None:
        with pytest.raises(ValidationError):
            Study(study_id="x", name="Legacy Name")  # type: ignore[call-arg]

    def test_rejects_audit_field(self) -> None:
        with pytest.raises(ValidationError):
            Study(
                study_id="x",
                study_name="Y",
                audit={"enabled": False},  # type: ignore[call-arg]
            )
