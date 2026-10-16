"""NiceGUI-marked smoke checks for GUI helpers (require slumber[nicegui])."""

from __future__ import annotations

import pytest

pytest.importorskip("nicegui")

pytestmark = pytest.mark.nicegui


def test_apply_theme_sets_colors() -> None:
    """apply_theme can be called inside a page context without error."""
    from nicegui import ui

    from slumber.ui.theme import COLORS

    # Direct colours call mirrors apply_theme's Quasar map.
    ui.colors(**COLORS)
    assert COLORS["primary"]


def test_theme_css_defines_button_variants() -> None:
    from slumber.ui.theme import build_theme_css

    css = build_theme_css()
    for variant in ("primary", "secondary", "attention"):
        assert f".slumber-btn-{variant}" in css


def test_theme_defines_the_shared_chrome_sizes() -> None:
    from slumber.ui.theme import LOGO_SIZE, build_theme_css

    css = build_theme_css()
    assert "--slumber-pad" in css
    assert "--slumber-header-h" in css
    assert "--slumber-header-h" in LOGO_SIZE["header"]


def test_widgets_importable() -> None:
    from slumber.ui.widgets import (
        confirm_dialog,
        logo_mark,
        outline_button,
        primary_button,
        surface_card,
    )

    assert callable(logo_mark)
    assert callable(primary_button)
    assert callable(outline_button)
    assert callable(surface_card)
    assert callable(confirm_dialog)


def test_app_frame_importable() -> None:
    from slumber.ui.frame import AppFrame

    frame = AppFrame(study_name="Demo", logo_url=None)
    assert not frame.mounted


def test_component_css_is_added_once_per_page(monkeypatch: pytest.MonkeyPatch) -> None:
    from nicegui import ui
    from nicegui.client import Client
    from nicegui.page import page

    from slumber.ui.theme import add_component_css

    added: list[str] = []
    monkeypatch.setattr(ui, "add_css", added.append)

    with Client(page("/")):
        add_component_css(".a { color: red; }")
        add_component_css(".a { color: red; }")
        add_component_css(".b { color: blue; }")
    with Client(page("/")):
        add_component_css(".a { color: red; }")

    assert added == [".a { color: red; }", ".b { color: blue; }", ".a { color: red; }"]


def test_component_css_can_be_added_after_the_current_element_was_deleted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A phase change deletes the clicked button while its handler is running."""
    import gc

    from nicegui import ui
    from nicegui.client import Client
    from nicegui.page import page

    from slumber.ui.theme import add_component_css

    added: list[str] = []
    monkeypatch.setattr(ui, "add_css", added.append)

    def delete_button_keeping_its_slot() -> object:
        button = ui.button("Complete")
        slot = button.default_slot
        button.delete()
        return slot

    with Client(page("/")) as client:
        slot = delete_button_keeping_its_slot()
        gc.collect()
        with slot:
            with pytest.raises(RuntimeError, match="has been deleted"):
                add_component_css(".a { color: red; }")
            add_component_css(".a { color: red; }", client=client)

    assert added == [".a { color: red; }"]


def _frame_elements(client: object, name: str) -> list:
    return [e for e in client.elements.values() if name in e.classes]  # type: ignore[attr-defined]


def test_app_frame_adds_its_css_and_applies_the_phase(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from nicegui.client import Client
    from nicegui.page import page

    from slumber.ui import frame as frame_module

    added: list[str] = []
    monkeypatch.setattr(frame_module, "add_component_css", added.append)

    with Client(page("/")) as client:
        frame = frame_module.AppFrame(study_name="Demo Study", logo_url=None)
        frame.mount()
        assert added == [frame_module.FRAME_CSS]

        (study,) = _frame_elements(client, "slumber-frame-study")
        (phase,) = _frame_elements(client, "slumber-frame-phase")
        (header,) = _frame_elements(client, "slumber-frame-header")
        (footer,) = _frame_elements(client, "slumber-frame-footer")
        assert study.text == "Demo Study"
        assert phase.text == ""

        frame.apply_frame(
            {"header": {"title": "Night", "show_phase_title": True}},
            phase_title="Setup",
        )
        assert (study.text, phase.text) == ("Night", "Setup")
        assert header.visible and footer.visible

        frame.apply_frame({"header": False, "footer": False})
        assert not header.visible and not footer.visible
        assert study.text == "Demo Study"


def test_gui_adds_the_layout_and_activity_css_when_mounting_a_phase(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from types import SimpleNamespace

    from slumber.ui import gui
    from slumber.ui.activities.base import Activity
    from slumber.ui.layouts import Layout

    added: list[str] = []
    monkeypatch.setattr(gui, "add_component_css", lambda css, **_: added.append(css))

    class _Frame:
        mounted = True
        body = SimpleNamespace(client=object())

        def clear_body(self) -> None:
            pass

    class _Styled(Layout):
        css = ".styled { color: red; }"

        def mount(self, host, activities) -> None:
            pass

    class _Plain(Layout):
        def mount(self, host, activities) -> None:
            pass

    class _StyledActivity(Activity):
        css = ".activity { color: blue; }"

        def mount(self, activity_host) -> None:
            pass

    class _PlainActivity(Activity):
        def mount(self, activity_host) -> None:
            pass

    backend = gui.GuiBackend()
    backend._engine = object()  # type: ignore[assignment]
    backend._frame = _Frame()  # type: ignore[assignment]
    phase = SimpleNamespace(id="p")

    def mounted(activity: Activity) -> SimpleNamespace:
        return SimpleNamespace(instance=activity, config=SimpleNamespace(id="a"))

    backend.mount_phase(
        phase,
        _Styled(),
        [mounted(_StyledActivity()), mounted(_PlainActivity())],  # type: ignore[arg-type]
    )
    backend.mount_phase(phase, _Plain(), [])  # type: ignore[arg-type]

    assert added == [".styled { color: red; }", ".activity { color: blue; }"]


def test_builtin_layouts_declare_their_css() -> None:
    from slumber.ui.layouts import HubLayout, StepperLayout

    assert ".slumber-hub" in HubLayout.css
    assert ".slumber-stepper" in StepperLayout.css


def test_builtin_activities_declare_their_css() -> None:
    from slumber.ui.activities.instruction import InstructionActivity

    assert ".slumber-instruction" in InstructionActivity.css
