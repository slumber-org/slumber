"""Tests for the 0.1 UI package (theme, activities, backends, builtins)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from slumber.schemas.condition import Activity as ActivityConfig
from slumber.schemas.study import GuiSettings, StepperLayoutDefaults
from slumber.ui.activities.instruction import (
    InstructionActivity,
    InstructionSettings,
    load_instruction_content,
    rewrite_image_paths,
)
from slumber.ui.activities.sleep import SleepActivity, SleepSettings
from slumber.ui.builtins import BUILT_IN_LAYOUTS, BUILT_IN_UI
from slumber.ui.gui import GuiBackend
from slumber.ui.headless import HeadlessBackend
from slumber.ui.layouts import HubLayout, StepperLayout
from slumber.ui.theme import (
    ACCENT,
    ATTENTION,
    BRAND,
    COLORS,
    DEFAULT_FAVICON_PATH,
    DEFAULT_LOGO_PATH,
    FONT_FILES,
    FONTS_DIR,
    LOGO_SIZE,
    NEGATIVE,
    PAGE_BG,
    POSITIVE,
    SECONDARY,
    SURFACE,
    SURFACE_ALT,
    TEXT,
    TYPE_SCALE,
    default_favicon_path,
    default_logo_path,
)
from slumber.ui.widgets import (
    ButtonSettings,
    ConfirmSettings,
    merge_button_defaults,
)


class TestTheme:
    def test_role_tokens_are_hex(self) -> None:
        for value in (
            PAGE_BG,
            SURFACE,
            SURFACE_ALT,
            BRAND,
            ACCENT,
            SECONDARY,
            ATTENTION,
            TEXT,
        ):
            assert value.startswith("#")
            assert len(value) == 7

    def test_surface_alt_differs_from_page_and_card(self) -> None:
        assert SURFACE_ALT not in (PAGE_BG, SURFACE)

    def test_quasar_primary_is_brand(self) -> None:
        assert COLORS["primary"] == BRAND

    def test_quasar_colours_come_from_the_palette(self) -> None:
        palette = {
            PAGE_BG,
            SURFACE,
            BRAND,
            ACCENT,
            SECONDARY,
            ATTENTION,
            TEXT,
            POSITIVE,
            NEGATIVE,
        }
        assert set(COLORS.values()) <= palette

    def test_logo_and_type_scale_keys(self) -> None:
        assert set(LOGO_SIZE) == {"hero", "header", "hub"}
        assert set(TYPE_SCALE) == {"display", "title", "body", "caption"}

    def test_packaged_assets_exist(self) -> None:
        assert DEFAULT_LOGO_PATH.is_file()
        assert DEFAULT_FAVICON_PATH.is_file()
        assert default_logo_path() == DEFAULT_LOGO_PATH
        assert default_favicon_path() == DEFAULT_FAVICON_PATH
        assert FONTS_DIR.is_dir()
        for filename in FONT_FILES.values():
            assert (FONTS_DIR / filename).is_file()
        assert (FONTS_DIR / "OFL.txt").is_file()


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


class TestRewriteImagePaths:
    """Image paths follow the study's path rules (relative to the study root)."""

    @staticmethod
    def _rewrite(markdown: str, root: Path) -> tuple[str, list[Path]]:
        served: list[Path] = []

        def resolve(text: str) -> Path:
            text = text.replace("{assets_dir}", str(root / "assets"))
            path = Path(text)
            return path if path.is_absolute() else root / path

        def serve(path: Path) -> str:
            served.append(path)
            return f"/static/{path.name}"

        return rewrite_image_paths(markdown, resolve, serve), served

    @staticmethod
    def _image(root: Path, name: str = "band.png") -> Path:
        path = root / "assets" / "instructions" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x")
        return path

    def test_relative_path_is_relative_to_the_study_root(self, tmp_path: Path) -> None:
        image = self._image(tmp_path)

        text, served = self._rewrite(
            "Look: ![The band](assets/instructions/band.png)", tmp_path
        )

        assert text == "Look: ![The band](/static/band.png)"
        assert served == [image]

    def test_placeholders_work(self, tmp_path: Path) -> None:
        image = self._image(tmp_path)

        text, served = self._rewrite(
            "![a]({assets_dir}/instructions/band.png)", tmp_path
        )

        assert text == "![a](/static/band.png)"
        assert served == [image]

    def test_absolute_path_to_a_file_is_served(self, tmp_path: Path) -> None:
        image = self._image(tmp_path)

        text, served = self._rewrite(f"![a]({image})", tmp_path)

        assert text == "![a](/static/band.png)"
        assert served == [image]

    def test_title_is_kept(self, tmp_path: Path) -> None:
        self._image(tmp_path)

        text, _ = self._rewrite(
            '![a](assets/instructions/band.png "The band")', tmp_path
        )

        assert text == '![a](/static/band.png "The band")'

    def test_encoded_spaces_in_the_path(self, tmp_path: Path) -> None:
        image = self._image(tmp_path, "my band.png")

        text, served = self._rewrite(
            "![a](assets/instructions/my%20band.png)", tmp_path
        )

        assert text == "![a](/static/my band.png)"
        assert served == [image]

    @pytest.mark.parametrize(
        "target",
        [
            "https://example.org/a.png",
            "http://example.org/a.png",
            "//example.org/a.png",
            "data:image/png;base64,AAAA",
            "#anchor",
        ],
    )
    def test_web_addresses_are_left_alone(self, tmp_path: Path, target: str) -> None:
        markdown = f"![a]({target})"

        text, served = self._rewrite(markdown, tmp_path)

        assert text == markdown
        assert served == []

    @pytest.mark.parametrize("target", ["assets/missing.png", "/static/a.png"])
    def test_a_path_that_is_not_a_file_is_left_as_written(
        self, tmp_path: Path, target: str
    ) -> None:
        markdown = f"![a]({target})"

        text, served = self._rewrite(markdown, tmp_path)

        assert text == markdown
        assert served == []

    def test_image_syntax_in_code_is_left_alone(self, tmp_path: Path) -> None:
        self._image(tmp_path)
        markdown = (
            "Write `![a](assets/instructions/band.png){width=300}` like this:\n\n"
            "```\n![a](assets/instructions/band.png)\n```\n"
        )

        text, served = self._rewrite(markdown, tmp_path)

        assert text == markdown
        assert served == []

    def test_images_around_code_are_still_rewritten(self, tmp_path: Path) -> None:
        self._image(tmp_path)

        text, served = self._rewrite(
            "![a](assets/instructions/band.png) and `code` and "
            "![b](assets/instructions/band.png)",
            tmp_path,
        )

        assert text == "![a](/static/band.png) and `code` and ![b](/static/band.png)"
        assert len(served) == 2

    def test_links_are_not_images(self, tmp_path: Path) -> None:
        self._image(tmp_path)

        text, served = self._rewrite("[a](assets/instructions/band.png)", tmp_path)

        assert text == "[a](assets/instructions/band.png)"
        assert served == []


class TestImageOptions:
    """``{width=... align=...}`` after an image sets its size and alignment."""

    @staticmethod
    def _rewrite(markdown: str, root: Path) -> str:
        def resolve(text: str) -> Path:
            return root / text

        return rewrite_image_paths(
            markdown, resolve, lambda path: f"/static/{path.name}"
        )

    @staticmethod
    def _image(root: Path) -> None:
        (root / "band.png").write_bytes(b"x")

    def test_width_in_pixels(self, tmp_path: Path) -> None:
        self._image(tmp_path)

        text = self._rewrite("![a](band.png){width=300}", tmp_path)

        assert text == '<img src="/static/band.png" alt="a" style="width: 300px">'

    def test_width_as_a_percentage_or_with_a_unit(self, tmp_path: Path) -> None:
        self._image(tmp_path)

        assert 'style="width: 50%"' in self._rewrite(
            "![a](band.png){width=50%}", tmp_path
        )
        assert 'style="width: 120px"' in self._rewrite(
            "![a](band.png){width=120px}", tmp_path
        )

    @pytest.mark.parametrize("align", ["left", "center", "right"])
    def test_alignment(self, tmp_path: Path, align: str) -> None:
        self._image(tmp_path)

        text = self._rewrite(f"![a](band.png){{align={align}}}", tmp_path)

        assert text == (
            f'<img src="/static/band.png" alt="a" class="slumber-image-{align}">'
        )

    def test_options_title_and_separators_together(self, tmp_path: Path) -> None:
        self._image(tmp_path)

        text = self._rewrite(
            '![a](band.png "The band"){width=300, align=center}', tmp_path
        )

        assert text == (
            '<img src="/static/band.png" alt="a" title="The band" '
            'class="slumber-image-center" style="width: 300px">'
        )

    def test_text_is_escaped(self, tmp_path: Path) -> None:
        self._image(tmp_path)

        text = self._rewrite('![a "b" <c>](band.png "x & y"){width=10}', tmp_path)

        assert 'alt="a &quot;b&quot; &lt;c&gt;"' in text
        assert 'title="x &amp; y"' in text

    def test_invalid_options_are_ignored_and_the_braces_removed(
        self, tmp_path: Path
    ) -> None:
        self._image(tmp_path)

        text = self._rewrite(
            "![a](band.png){width=wide align=middle colour=red}", tmp_path
        )

        assert text == '<img src="/static/band.png" alt="a">'

    def test_web_images_take_options_too(self, tmp_path: Path) -> None:
        text = self._rewrite("![a](https://example.org/a.png){width=200}", tmp_path)

        assert (
            text == '<img src="https://example.org/a.png" alt="a" style="width: 200px">'
        )

    def test_a_missing_file_keeps_its_path(self, tmp_path: Path) -> None:
        text = self._rewrite("![a](missing.png){align=right}", tmp_path)

        assert text == '<img src="missing.png" alt="a" class="slumber-image-right">'

    def test_braces_further_away_are_ordinary_text(self, tmp_path: Path) -> None:
        self._image(tmp_path)

        text = self._rewrite("![a](band.png) {width=300}", tmp_path)

        assert text == "![a](/static/band.png) {width=300}"


class TestActivityHostPaths:
    def test_hosts_resolve_paths_through_the_engine(self) -> None:
        from types import SimpleNamespace

        from slumber.ui.gui import _GuiActivityHost
        from slumber.ui.headless import _HeadlessActivityHost

        engine = SimpleNamespace(resolve_path=lambda text: Path("/study") / text)
        gui_host = _GuiActivityHost(engine, "a", None, on_complete=lambda _: None)
        headless_host = _HeadlessActivityHost(engine, "a", on_complete=lambda _: None)

        assert gui_host.resolve_path("x.png") == Path("/study/x.png")
        assert headless_host.resolve_path("x.png") == Path("/study/x.png")


class TestSleepSettings:
    def test_default_is_the_wake_and_end_buttons(self) -> None:
        settings = SleepSettings()

        assert settings.title == "Sleep well"
        assert settings.message is None
        assert settings.wake_button == ButtonSettings(
            label="I'm Awake", style="primary", confirm=False
        )
        assert settings.end_button == ButtonSettings(
            label="End Session", style="attention", confirm=True
        )

    def test_the_sleep_button_defaults_to_going_to_sleep(self) -> None:
        assert SleepSettings().sleep_button == ButtonSettings(
            label="Going to Sleep", style="primary", confirm=False
        )

    def test_only_the_end_button_asks_by_default(self) -> None:
        settings = SleepSettings()

        assert settings.sleep_button.confirmation() is None
        assert settings.wake_button.confirmation() is None
        assert settings.end_button.confirmation() is not None

    def test_a_label_does_not_change_whether_a_button_asks(self) -> None:
        settings = SleepSettings(sleep_button="Bedtime", end_button="Stop")

        assert settings.sleep_button.confirm is False
        assert settings.end_button.confirm is True

    def test_a_label_keeps_the_default_look(self) -> None:
        settings = SleepSettings(wake_button="Wake up", end_button="Stop")

        assert (settings.wake_button.label, settings.wake_button.style) == (
            "Wake up",
            "primary",
        )
        assert (settings.end_button.label, settings.end_button.style) == (
            "Stop",
            "attention",
        )

    def test_a_partial_mapping_keeps_the_rest_of_the_default(self) -> None:
        settings = SleepSettings(end_button={"confirm": False})

        assert settings.end_button == ButtonSettings(
            label="End Session", style="attention", confirm=False
        )

    def test_title_may_be_false_but_not_true(self) -> None:
        assert SleepSettings(title=False).title is False
        with pytest.raises(ValidationError):
            SleepSettings(title=True)

    @pytest.mark.parametrize(
        "settings",
        [
            {"wake_button": ""},
            {"wake_button": {"label": ""}},
            {"end_button": {"style": "danger"}},
            {"wake_button": False},
            {"end_button": True},
            {"end_button": 3},
        ],
    )
    def test_invalid_values_are_rejected(self, settings: dict) -> None:
        with pytest.raises(ValidationError):
            SleepSettings(**settings)


class TestButtonSettings:
    def test_defaults(self) -> None:
        button = ButtonSettings(label="Go")

        assert (button.style, button.confirm) == ("primary", True)

    def test_a_label_alone_is_enough(self) -> None:
        assert ButtonSettings.model_validate("Go") == ButtonSettings(label="Go")

    def test_confirm_accepts_a_flag_a_text_or_a_mapping(self) -> None:
        assert ButtonSettings(label="a", confirm=False).confirm is False
        assert ButtonSettings(label="a", confirm="Sure?").confirm == "Sure?"
        mapped = ButtonSettings(
            label="a", confirm={"message": "Sure?", "cancel_label": "No"}
        )
        assert isinstance(mapped.confirm, ConfirmSettings)

    @pytest.mark.parametrize(
        "value",
        ["", {"label": ""}, {"label": "a", "style": "danger"}, {"style": "primary"}, 3],
    )
    def test_invalid_values_are_rejected(self, value: object) -> None:
        with pytest.raises(ValidationError):
            ButtonSettings.model_validate(value)


_BUTTON_DEFAULTS = {"label": "Stop", "style": "attention"}


class TestMergeButtonDefaults:
    def test_a_label_keeps_the_other_defaults(self) -> None:
        assert merge_button_defaults("Halt", _BUTTON_DEFAULTS) == {
            "label": "Halt",
            "style": "attention",
        }

    def test_a_mapping_overrides_only_what_it_sets(self) -> None:
        merged = merge_button_defaults({"confirm": False}, _BUTTON_DEFAULTS)

        assert merged == {"label": "Stop", "style": "attention", "confirm": False}

    def test_anything_else_is_left_for_validation(self) -> None:
        assert merge_button_defaults(3, _BUTTON_DEFAULTS) == 3


class TestButtonConfirmation:
    @staticmethod
    def _confirmation(confirm: object) -> ConfirmSettings | None:
        return ButtonSettings(label="Stop", confirm=confirm).confirmation()

    def test_true_gives_a_standard_question(self) -> None:
        confirmation = self._confirmation(True)

        assert confirmation is not None
        assert confirmation.title == "Stop?"
        assert confirmation.message == "Are you sure?"
        assert (confirmation.confirm_label, confirmation.cancel_label) == (
            "Confirm",
            "Cancel",
        )

    def test_false_gives_no_question(self) -> None:
        assert self._confirmation(False) is None

    def test_a_text_is_the_message(self) -> None:
        confirmation = self._confirmation("End the night?")

        assert confirmation is not None
        assert (confirmation.title, confirmation.message) == ("Stop?", "End the night?")

    def test_a_mapping_can_set_everything(self) -> None:
        settings = {
            "title": "Sure?",
            "message": "m",
            "confirm_label": "Yes",
            "cancel_label": "No",
        }

        assert self._confirmation(settings) == ConfirmSettings(**settings)


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
