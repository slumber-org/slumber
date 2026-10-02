"""Tests for the 0.1 UI package (theme, activities, backends, builtins)."""

from __future__ import annotations

from pathlib import Path

import pytest

from slumber.schemas.condition import Activity as ActivityConfig
from slumber.schemas.study import GuiSettings, StepperLayoutDefaults
from slumber.ui.activities.instruction import (
    InstructionActivity,
    InstructionSettings,
    load_instruction_content,
)
from slumber.ui.activities.sleep import SleepActivity, SleepSettings
from slumber.ui.builtins import BUILT_IN_LAYOUTS, BUILT_IN_UI
from slumber.ui.gui import GuiBackend
from slumber.ui.headless import HeadlessBackend
from slumber.ui.layouts import HubLayout, StepperLayout
from slumber.ui.theme import (
    ATTENTION,
    BRAND,
    COLORS,
    CTA,
    DEFAULT_FAVICON_PATH,
    DEFAULT_LOGO_PATH,
    LOGO_SIZE,
    PAGE_BG,
    SECONDARY,
    SURFACE,
    TEXT,
    TYPE_SCALE,
    default_favicon_path,
    default_logo_path,
)


class TestTheme:
    def test_role_tokens_are_hex(self) -> None:
        for value in (PAGE_BG, SURFACE, BRAND, CTA, SECONDARY, ATTENTION, TEXT):
            assert value.startswith("#")
            assert len(value) == 7

    def test_quasar_primary_is_cta(self) -> None:
        assert COLORS["primary"] == CTA

    def test_logo_and_type_scale_keys(self) -> None:
        assert set(LOGO_SIZE) == {"hero", "header", "hub"}
        assert set(TYPE_SCALE) == {"display", "title", "body", "caption"}

    def test_packaged_assets_exist(self) -> None:
        assert DEFAULT_LOGO_PATH.is_file()
        assert DEFAULT_FAVICON_PATH.is_file()
        assert default_logo_path() == DEFAULT_LOGO_PATH
        assert default_favicon_path() == DEFAULT_FAVICON_PATH


class TestInstructionActivity:
    def test_load_inline_content(self) -> None:
        assert load_instruction_content("Hello") == "Hello"

    def test_load_file_content(self, tmp_path: Path) -> None:
        path = tmp_path / "intro.md"
        path.write_text("# Hi\n", encoding="utf-8")
        assert load_instruction_content(str(path)) == "# Hi\n"

    def test_completes_on_mount_without_container(self) -> None:
        completed: list[str] = []

        class Host:
            container = None

            def complete(self) -> None:
                completed.append("ok")

            def emit(self, name: str) -> None:
                raise AssertionError(f"unexpected emit {name}")

        activity = InstructionActivity(InstructionSettings(content="Hello"))
        activity.mount(Host())
        assert completed == ["ok"]


class TestSleepActivity:
    def test_mount_headless_does_not_emit(self) -> None:
        class Host:
            container = None

            def complete(self) -> None:
                raise AssertionError("sleep must not complete")

            def emit(self, name: str) -> None:
                raise AssertionError(f"unexpected emit {name}")

        SleepActivity(SleepSettings()).mount(Host())


class TestBuiltins:
    def test_ui_map(self) -> None:
        assert BUILT_IN_UI["gui"] is GuiBackend
        assert BUILT_IN_UI["headless"] is HeadlessBackend

    def test_layout_map(self) -> None:
        assert BUILT_IN_LAYOUTS["stepper"] is StepperLayout
        assert BUILT_IN_LAYOUTS["hub"] is HubLayout

    def test_gui_settings_model(self) -> None:
        assert GuiBackend.settings_model is GuiSettings
        backend = GuiBackend(GuiSettings(port=9090))
        assert backend.settings is not None
        assert backend.settings.port == 9090

    def test_stepper_defaults(self) -> None:
        layout = StepperLayout(StepperLayoutDefaults(allow_skip=True))
        assert layout.settings is not None
        assert layout.settings.allow_skip is True


class TestHeadlessBackend:
    def test_settings_forbid_extras(self) -> None:
        from pydantic import ValidationError

        model = HeadlessBackend.settings_model
        assert model is not None
        with pytest.raises(ValidationError):
            model.model_validate({"port": 1})


class TestMountedActivityShape:
    def test_activity_config_display_title(self) -> None:
        config = ActivityConfig(id="welcome", type="instruction", title="Welcome")
        assert config.display_title == "Welcome"
        assert ActivityConfig(id="welcome", type="instruction").display_title == (
            "welcome"
        )
