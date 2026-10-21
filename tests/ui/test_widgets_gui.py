"""Mounted button and dialog widgets (require slumber[nicegui])."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

pytest.importorskip("nicegui")

from nicegui import ui
from nicegui.client import Client

from slumber.ui.widgets import dialog as dialog_module
from slumber.ui.widgets.buttons import ButtonSettings, action_button, toggle_button
from slumber.ui.widgets.dialog import with_confirmation

pytestmark = pytest.mark.nicegui


def _with_class(client: Client, name: str) -> list[Any]:
    return [e for e in client.elements.values() if name in e.classes]


def _labels(client: Client) -> list[str]:
    return [
        e.props["label"] for e in client.elements.values() if isinstance(e, ui.button)
    ]


def _answer(monkeypatch: pytest.MonkeyPatch, *answers: bool) -> list[dict[str, Any]]:
    """Make the confirm dialog answer in turn; return what it was asked."""
    asked: list[dict[str, Any]] = []
    remaining = list(answers)

    async def confirm(**kwargs: Any) -> bool:
        asked.append(kwargs)
        return remaining.pop(0) if remaining else True

    monkeypatch.setattr(dialog_module, "confirm_dialog", confirm)
    return asked


def test_an_action_button_calls_what_it_was_given_on_every_press(
    client: Client, press: Any
) -> None:
    pressed: list[str] = []
    action_button(ButtonSettings(label="Go"), lambda: pressed.append("x"))

    press("Go")
    press("Go")

    assert pressed == ["x", "x"]


@pytest.mark.parametrize(
    ("style", "classes"),
    [
        ("primary", {"slumber-btn-primary", "slumber-btn-lg"}),
        ("secondary", {"slumber-btn-secondary"}),
        ("attention", {"slumber-btn-attention"}),
    ],
)
def test_the_style_picks_the_button(client: Client, style: str, classes: set) -> None:
    button = action_button(
        ButtonSettings(label="A", style=style), lambda: None, large=True
    )

    assert classes <= set(button.classes)
    assert ("slumber-btn-lg" in button.classes) == (style == "primary")


@pytest.mark.parametrize("confirmed", [True, False])
def test_an_action_with_confirmation_runs_only_after_confirming(
    client: Client, monkeypatch: pytest.MonkeyPatch, press: Any, confirmed: bool
) -> None:
    asked = _answer(monkeypatch, confirmed)
    pressed: list[str] = []
    settings = ButtonSettings(label="Stop")
    action_button(settings, with_confirmation(settings, lambda: pressed.append("x")))

    press("Stop")

    assert pressed == (["x"] if confirmed else [])
    assert asked == [
        {
            "title": "Stop?",
            "message": "Are you sure?",
            "confirm_label": "Confirm",
            "cancel_label": "Cancel",
        }
    ]


def test_an_async_action_is_awaited_after_confirming(
    client: Client, monkeypatch: pytest.MonkeyPatch, press: Any
) -> None:
    _answer(monkeypatch, True)
    pressed: list[str] = []

    async def action() -> None:
        pressed.append("x")

    settings = ButtonSettings(label="Stop")
    action_button(settings, with_confirmation(settings, action))

    press("Stop")

    assert pressed == ["x"]


def test_an_action_that_declines_leaves_a_toggle_button_as_it_is(
    client: Client, monkeypatch: pytest.MonkeyPatch, press: Any
) -> None:
    _answer(monkeypatch, True)

    async def declines() -> bool:
        return False

    on = ButtonSettings(label="On")
    toggle_button(
        on,
        ButtonSettings(label="Off"),
        on_first=with_confirmation(on, declines),
        on_second=lambda: None,
    )

    press("On")

    assert _labels(client) == ["On"]


def test_an_action_without_a_question_is_returned_unchanged() -> None:
    def action() -> None:
        pass

    assert (
        with_confirmation(ButtonSettings(label="Go", confirm=False), action) is action
    )


def test_the_dialog_text_comes_from_the_settings(
    client: Client, monkeypatch: pytest.MonkeyPatch, press: Any
) -> None:
    asked = _answer(monkeypatch)
    settings = ButtonSettings(
        label="Stop",
        confirm={
            "title": "Really stop?",
            "message": "This ends the night.",
            "confirm_label": "Yes, stop",
            "cancel_label": "Keep going",
        },
    )
    action_button(settings, with_confirmation(settings, lambda: None))

    press("Stop")

    assert asked == [
        {
            "title": "Really stop?",
            "message": "This ends the night.",
            "confirm_label": "Yes, stop",
            "cancel_label": "Keep going",
        }
    ]


def _toggle(*, confirm: bool, calls: list[str]) -> None:
    on = ButtonSettings(label="On", confirm=confirm)
    off = ButtonSettings(label="Off", confirm=confirm)
    toggle_button(
        on,
        off,
        on_first=with_confirmation(on, lambda: calls.append("on")),
        on_second=with_confirmation(off, lambda: calls.append("off")),
    )


def test_a_toggle_button_swaps_after_each_press(client: Client, press: Any) -> None:
    calls: list[str] = []
    _toggle(confirm=False, calls=calls)
    assert _labels(client) == ["On"]

    press("On")
    assert _labels(client) == ["Off"]

    press("Off")
    assert _labels(client) == ["On"]
    assert calls == ["on", "off"]


def test_a_cancelled_question_does_not_swap_a_toggle_button(
    client: Client, monkeypatch: pytest.MonkeyPatch, press: Any
) -> None:
    _answer(monkeypatch, False)
    calls: list[str] = []
    _toggle(confirm=True, calls=calls)

    press("On")

    assert _labels(client) == ["On"]
    assert calls == []


def test_a_confirmed_question_swaps_a_toggle_button(
    client: Client, monkeypatch: pytest.MonkeyPatch, press: Any
) -> None:
    _answer(monkeypatch, True)
    calls: list[str] = []
    _toggle(confirm=True, calls=calls)

    press("On")

    assert _labels(client) == ["Off"]
    assert calls == ["on"]


def test_a_toggle_button_leaves_the_page_alone_when_its_press_removed_it(
    client: Client, press: Any
) -> None:
    removed: list[Any] = []
    holder = toggle_button(
        ButtonSettings(label="On"),
        ButtonSettings(label="Off"),
        on_first=lambda: removed[0].delete(),
        on_second=lambda: None,
    )
    removed.append(holder)

    press("On")

    assert holder.is_deleted
    assert "Off" not in _labels(client)


def test_the_dialog_is_centred_borderless_and_focuses_cancel(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    added: list[str] = []
    monkeypatch.setattr(dialog_module, "add_component_css", added.append)

    _, cancel, confirm = dialog_module.build_confirm_dialog(
        title="End sleep?", message="Stop the sleep phase?"
    )

    assert added == [dialog_module.DIALOG_CSS]
    assert cancel.props["data-autofocus"]
    assert "data-autofocus" not in confirm.props
    assert cancel.props["label"] == "Cancel"
    assert confirm.props["label"] == "Confirm"
    (actions,) = _with_class(client, "slumber-dialog-actions")
    assert set(actions.default_slot.children) == {cancel, confirm}
    (title,) = _with_class(client, "slumber-dialog-title")
    assert title.text == "End sleep?"


def test_the_dialog_button_labels_can_be_set(client: Client) -> None:
    _, cancel, confirm = dialog_module.build_confirm_dialog(
        title="t", message="m", confirm_label="Yes", cancel_label="No"
    )

    assert cancel.props["label"] == "No"
    assert confirm.props["label"] == "Yes"


async def _ask(client: Client) -> asyncio.Future[bool]:
    """Start ``confirm_dialog`` the way a click handler does, inside the page."""

    async def handler() -> bool:
        with client:
            return await dialog_module.confirm_dialog(title="t", message="m")

    task = asyncio.ensure_future(handler())
    await asyncio.sleep(0)
    return task


def _dialogs(client: Client) -> list[Any]:
    return [e for e in client.elements.values() if isinstance(e, ui.dialog)]


@pytest.mark.parametrize("answer", [True, False])
def test_confirm_dialog_returns_the_answer_and_removes_itself(
    client: Client, answer: bool
) -> None:
    async def run() -> bool:
        task = await _ask(client)
        (dialog,) = _dialogs(client)
        dialog.submit(answer)
        return await task

    assert asyncio.run(run()) is answer
    assert _dialogs(client) == []


def test_confirm_dialog_copes_with_the_dialog_already_being_gone(
    client: Client,
) -> None:
    """A phase change can remove the whole body while the dialog is open."""

    async def run() -> bool:
        task = await _ask(client)
        (dialog,) = _dialogs(client)
        dialog.delete()
        dialog.submit(True)
        return await task

    assert asyncio.run(run()) is True
