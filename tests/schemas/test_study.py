"""Tests for Study, RunLayout, UI, and RunLoggingConfig schemas."""

import pytest
from pydantic import ValidationError

from slumber.schemas import RunLayout, RunLoggingConfig, Study, UI


class TestUI:
    """Tests for UI schema."""

    def test_valid_minimal(self) -> None:
        ui = UI(backend="headless")
        assert ui.backend == "headless"
        assert ui.settings == {}

    def test_valid_with_config(self) -> None:
        ui = UI(backend="headless", settings={"theme": "dark"})
        assert ui.backend == "headless"
        assert ui.settings["theme"] == "dark"

    def test_backend_required(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            UI(backend="")
        assert "backend" in str(exc_info.value).lower() or "min_length" in str(
            exc_info.value
        )


class TestRunLayout:
    """Tests for RunLayout schema."""

    def test_valid_defaults(self) -> None:
        layout = RunLayout()
        assert layout.base_directory == "runs"
        assert layout.layout == "run-{run_id}"

    def test_valid_custom(self) -> None:
        layout = RunLayout(
            base_directory="output",
            layout="sub-{participant_id}/run-{run_id}",
        )
        assert layout.base_directory == "output"
        assert layout.layout == "sub-{participant_id}/run-{run_id}"

    def test_invalid_placeholder_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            RunLayout(layout="sub-{participant_id}/run-{unknown_placeholder}")
        assert "unknown" in str(exc_info.value).lower() or "placeholder" in str(
            exc_info.value
        )

    def test_allowed_placeholders_accepted(self) -> None:
        layout = RunLayout(
            layout="s-{study_id}/p-{participant_id}/c-{condition_id}/ses-{session_id}/r-{run_id}"
        )
        assert "study_id" in layout.layout


class TestRunLoggingConfig:
    """Tests for RunLoggingConfig schema."""

    def test_valid_defaults(self) -> None:
        cfg = RunLoggingConfig()
        assert cfg.level == "INFO"
        assert cfg.handlers == []

    def test_valid_with_handlers(self) -> None:
        cfg = RunLoggingConfig(
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
            name="Test Study",
            ui=UI(backend="headless"),
        )
        assert study.study_id == "test-study"
        assert study.name == "Test Study"
        assert study.conditions_dir == "conditions"
        assert study.ui.backend == "headless"
        assert study.runs.base_directory == "runs"
        assert study.logging.level == "INFO"

    def test_valid_full(self) -> None:
        study = Study(
            study_id="ld-2025",
            name="Lucid Dreaming Pilot",
            conditions_dir="conditions",
            ui=UI(backend="headless", settings={"theme": "dark"}),
        )
        assert study.conditions_dir == "conditions"
        assert study.ui.settings["theme"] == "dark"

    def test_study_id_required(self) -> None:
        with pytest.raises(ValidationError):
            Study(
                study_id="",
                name="A Study",
                ui=UI(backend="headless"),
            )

    def test_study_id_rejects_path_components(self) -> None:
        """study_id must not contain '/', '\\', or '..' so it cannot escape base_dir."""
        for invalid_id in ("a/b", "..", "a/../b", "a\\b", "study..id"):
            with pytest.raises(ValidationError) as exc_info:
                Study(study_id=invalid_id, name="Study")
            assert (
                "path" in str(exc_info.value).lower()
                or "forbidden" in str(exc_info.value).lower()
            )

    def test_study_id_accepts_safe_values(self) -> None:
        """study_id accepts alphanumeric, hyphen, underscore (no path components)."""
        study = Study(study_id="my-study_2025", name="Study")
        assert study.study_id == "my-study_2025"

    def test_name_required(self) -> None:
        with pytest.raises(ValidationError):
            Study(
                study_id="x",
                name="",
                ui=UI(backend="headless"),
            )

    def test_ui_has_default(self) -> None:
        """Study accepts minimal args; ui defaults to headless."""
        study = Study(study_id="x", name="Y")
        assert study.ui.backend == "headless"
