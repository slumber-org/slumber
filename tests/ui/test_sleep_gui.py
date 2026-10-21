"""Mounted SleepActivity and confirm dialog checks (require slumber[nicegui])."""

from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("nicegui")

from nicegui import ui
from nicegui.client import Client

from slumber.ui.activities.sleep import SleepActivity, SleepSettings
from slumber.ui.widgets import dialog as dialog_module

pytestmark = pytest.mark.nicegui


class _Host:
    def __init__(self, container: Any) -> None:
        self.container = container
        self.emitted: list[str] = []

    def complete(self) -> None:
        raise AssertionError("sleep must not complete")

    def emit(self, name: str) -> None:
        self.emitted.append(name)

    def resolve_path(self, path: str) -> Any:
        raise AssertionError("not used")


def _with_class(client: Client, name: str) -> list[Any]:
    return [e for e in client.elements.values() if name in e.classes]


def _button(client: Client, label: str) -> Any:
    for element in client.elements.values():
        if isinstance(element, ui.button) and element.props.get("label") == label:
            return element
    raise AssertionError(f"no button {label!r}")


def _mount(**settings: Any) -> tuple[SleepActivity, _Host]:
    host = _Host(ui.element("div"))
    activity = SleepActivity(SleepSettings(**settings))
    activity.mount(host)
    return activity, host


def test_default_has_the_moon_a_title_and_the_two_buttons(client: Client) -> None:
    _mount()

    assert [e for e in client.elements.values() if isinstance(e, ui.icon)]
    (title,) = _with_class(client, "slumber-sleep-title")
    assert title.text == "Sleep well"
    assert title.props["role"] == "heading"
    assert not _with_class(client, "slumber-sleep-message")
    sleep_button = _button(client, "Going to Sleep")
    end = _button(client, "End Session")
    assert {"slumber-btn-primary", "slumber-btn-lg"} <= set(sleep_button.classes)
    assert "slumber-btn-attention" in end.classes
    assert "slumber-btn-lg" not in end.classes


def test_title_and_message_can_be_set(client: Client) -> None:
    _mount(title="Good night", message="Rest well.\nSee you in the morning.")

    (title,) = _with_class(client, "slumber-sleep-title")
    (message,) = _with_class(client, "slumber-sleep-message")
    assert title.text == "Good night"
    assert message.text == "Rest well.\nSee you in the morning."


@pytest.mark.parametrize("title", [False, ""])
def test_an_empty_or_false_title_leaves_no_heading(
    client: Client, title: object
) -> None:
    _mount(title=title)

    assert not _with_class(client, "slumber-sleep-title")


def test_the_buttons_take_their_label_and_style_from_the_settings(
    client: Client,
) -> None:
    _mount(
        sleep_button="Bedtime",
        end_button={"label": "Stop", "style": "secondary"},
    )

    bedtime = _button(client, "Bedtime")
    stop = _button(client, "Stop")
    assert {"slumber-btn-primary", "slumber-btn-lg"} <= set(bedtime.classes)
    assert "slumber-btn-secondary" in stop.classes


def test_the_buttons_are_one_above_the_other(client: Client) -> None:
    _mount()

    assert _main_labels(client) == ["Going to Sleep", "End Session"]


def _button_labels(element: Any) -> list[str]:
    """Labels of the buttons under *element*, from top to bottom."""
    labels = []
    for child in element.default_slot.children:
        if isinstance(child, ui.button):
            labels.append(child.props["label"])
        else:
            labels += _button_labels(child)
    return labels


def _main_labels(client: Client) -> list[str]:
    (actions,) = _with_class(client, "slumber-sleep-actions")
    return _button_labels(actions)


@pytest.fixture(autouse=True)
def _confirmed(monkeypatch: pytest.MonkeyPatch) -> None:
    async def confirm(**kwargs: Any) -> bool:
        return True

    monkeypatch.setattr(dialog_module, "confirm_dialog", confirm)


def test_the_main_button_toggles_between_sleep_and_wake(
    client: Client, press: Any
) -> None:
    _, host = _mount()
    assert _main_labels(client) == ["Going to Sleep", "End Session"]

    press("Going to Sleep")
    assert _main_labels(client) == ["I'm Awake", "End Session"]

    press("I'm Awake")
    assert _main_labels(client) == ["Going to Sleep", "End Session"]
    assert host.emitted == ["marked_asleep", "marked_awake"]


def test_the_end_button_emits_end_sleep_and_does_not_toggle(
    client: Client, press: Any
) -> None:
    _, host = _mount()

    press("End Session")

    assert host.emitted == ["end_sleep"]
    assert _main_labels(client) == ["Going to Sleep", "End Session"]


def test_the_wake_button_takes_its_label_and_style_from_the_settings(
    client: Client, press: Any
) -> None:
    _mount(wake_button={"label": "Up again", "style": "secondary"})

    press("Going to Sleep")

    assert "slumber-btn-secondary" in _button(client, "Up again").classes


def test_a_button_asks_the_question_set_in_its_settings(
    client: Client, monkeypatch: pytest.MonkeyPatch, press: Any
) -> None:
    asked: list[dict[str, Any]] = []

    async def confirm(**kwargs: Any) -> bool:
        asked.append(kwargs)
        return True

    monkeypatch.setattr(dialog_module, "confirm_dialog", confirm)
    _, host = _mount(sleep_button={"confirm": "Ready to sleep?"})

    press("Going to Sleep")

    assert asked == [
        {
            "title": "Going to Sleep?",
            "message": "Ready to sleep?",
            "confirm_label": "Confirm",
            "cancel_label": "Cancel",
        }
    ]
    assert host.emitted == ["marked_asleep"]


def test_a_cancelled_question_emits_nothing(
    client: Client, monkeypatch: pytest.MonkeyPatch, press: Any
) -> None:
    async def cancel(**kwargs: Any) -> bool:
        return False

    monkeypatch.setattr(dialog_module, "confirm_dialog", cancel)
    _, host = _mount(sleep_button={"confirm": True})

    press("Going to Sleep")
    press("End Session")

    assert host.emitted == []
    assert _main_labels(client) == ["Going to Sleep", "End Session"]


def test_only_the_end_button_asks_by_default(
    client: Client, monkeypatch: pytest.MonkeyPatch, press: Any
) -> None:
    asked: list[str] = []

    async def confirm(**kwargs: Any) -> bool:
        asked.append(kwargs["title"])
        return True

    monkeypatch.setattr(dialog_module, "confirm_dialog", confirm)
    _, host = _mount()

    press("Going to Sleep")
    press("I'm Awake")
    assert asked == []
    assert host.emitted == ["marked_asleep", "marked_awake"]

    press("End Session")
    assert asked == ["End Session?"]
    assert host.emitted == ["marked_asleep", "marked_awake", "end_sleep"]


def test_a_press_after_the_page_was_removed_during_the_question_emits_nothing(
    client: Client, monkeypatch: pytest.MonkeyPatch, press: Any
) -> None:
    holder: list[SleepActivity] = []

    async def confirm_while_leaving(**kwargs: Any) -> bool:
        holder[0].unmount()
        return True

    monkeypatch.setattr(dialog_module, "confirm_dialog", confirm_while_leaving)
    activity, host = _mount(sleep_button={"confirm": True})
    holder.append(activity)

    press("Going to Sleep")

    assert host.emitted == []
