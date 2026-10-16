"""Mounted StepperLayout checks (require slumber[nicegui])."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

pytest.importorskip("nicegui")

from nicegui import ui
from nicegui.client import Client

from slumber.schemas.condition import Activity as ActivityConfig
from slumber.schemas.study import StepperLayoutDefaults
from slumber.ui.activities.base import Activity
from slumber.ui.backend import MountedActivity
from slumber.ui.layouts import StepperLayout

pytestmark = pytest.mark.nicegui


class _ActivityHost:
    def __init__(self, container: Any, complete: Callable[[], None]) -> None:
        self.container = container
        self.complete = complete

    def emit(self, name: str) -> None:
        raise AssertionError(f"unexpected emit {name}")


class _LayoutHost:
    def __init__(self, container: Any) -> None:
        self.container = container
        self.phase_completed = 0

    def emit_phase_completed(self) -> None:
        self.phase_completed += 1

    def make_activity_host(
        self,
        activity_id: str,
        container: Any,
        *,
        on_complete: Callable[[str], None],
    ) -> _ActivityHost:
        return _ActivityHost(container, lambda: on_complete(activity_id))


class _Step(Activity):
    """Finishes on mount when *finishes* is set, otherwise when told to."""

    def __init__(self, finishes: bool) -> None:
        super().__init__()
        self._finishes = finishes
        self.host: _ActivityHost | None = None

    def mount(self, activity_host: Any) -> None:
        self.host = activity_host
        if self._finishes:
            activity_host.complete()


def _mount(
    client: Client, finishes: list[bool], **settings: Any
) -> tuple[StepperLayout, _LayoutHost, list[_Step]]:
    steps = [_Step(done) for done in finishes]
    mounted = [
        MountedActivity(
            config=ActivityConfig(id=f"step{i}", title=f"Step {i}", type="stub"),
            instance=step,
        )
        for i, step in enumerate(steps)
    ]
    host = _LayoutHost(ui.element("div"))
    layout = StepperLayout(StepperLayoutDefaults(**settings))
    layout.mount(host, mounted)
    return layout, host, steps


def _with_class(client: Client, name: str) -> list[Any]:
    return [e for e in client.elements.values() if name in e.classes]


def _rows(client: Client) -> list[Any]:
    rows = [e for e in _with_class(client, "slumber-step") if e.tag == "button"]
    return sorted(rows, key=lambda row: row.props["aria-label"])


def _button(client: Client, label: str) -> Any:
    for element in client.elements.values():
        if isinstance(element, ui.button) and element.props.get("label") == label:
            return element
    raise AssertionError(f"no button {label!r}")


def test_next_waits_for_the_step_to_finish(client: Client) -> None:
    _, _, steps = _mount(client, [False, False])

    first, second = _rows(client)
    assert first.props["aria-label"] == "Step 0, current"
    assert second.props["aria-label"] == "Step 1, not started, not available"
    assert second.props.get("disabled")
    assert not _button(client, "Next").enabled
    assert not _button(client, "Previous").enabled

    assert steps[0].host is not None
    steps[0].host.complete()

    assert _button(client, "Next").enabled
    assert not _rows(client)[1].props.get("disabled")


def test_moving_on_and_completing_the_phase(client: Client) -> None:
    layout, host, steps = _mount(client, [True, False])
    assert _button(client, "Next").enabled

    layout._go_next()

    assert _button(client, "Previous").enabled
    assert not _button(client, "Next").visible
    complete = _button(client, "Complete")
    assert complete.visible
    assert not complete.enabled
    layout._finish_phase()
    assert host.phase_completed == 0

    assert steps[1].host is not None
    steps[1].host.complete()
    assert complete.enabled
    layout._finish_phase()
    assert host.phase_completed == 1


def test_allow_skip_makes_every_step_available(client: Client) -> None:
    layout, host, _ = _mount(client, [False, False], allow_skip=True)

    assert not _rows(client)[1].props.get("disabled")
    assert _button(client, "Next").enabled

    layout._go_next()
    assert _button(client, "Complete").enabled
    layout._finish_phase()
    assert host.phase_completed == 1


def test_clicking_a_step_that_is_not_available_does_nothing(client: Client) -> None:
    layout, _, _ = _mount(client, [False, False])

    layout._go_to(1)

    assert _rows(client)[0].props["aria-label"] == "Step 0, current"


def test_progress_bar_and_text(client: Client) -> None:
    _mount(client, [True, False, False], show_step_name=True)

    texts = [e.text for e in _with_class(client, "slumber-progress-text")]
    assert texts == ["Step 1 of 3 · Step 0"]
    segments = _with_class(client, "slumber-progress-segment")
    assert len(segments) == 3
    assert "slumber-segment-current" in segments[0].classes


def test_parts_can_be_switched_off(client: Client) -> None:
    _mount(
        client,
        [True, True],
        show_activity_list=False,
        show_progress_bar=False,
    )

    assert not _with_class(client, "slumber-step-list")
    assert not _with_class(client, "slumber-progress")
    assert _with_class(client, "slumber-nav-spacer")


def test_steps_can_be_numbered(client: Client) -> None:
    _mount(client, [True, True], number_steps=True)

    numbers = [e.text for e in _with_class(client, "slumber-step-number")]
    assert sorted(numbers) == ["1.", "2."]
