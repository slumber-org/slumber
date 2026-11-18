"""Showing an activity through the shared methods of the Layout base."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from slumber.schemas.condition import Activity as ActivityConfig
from slumber.ui.activities.base import Activity
from slumber.ui.backend import MountedActivity
from slumber.ui.layouts import HubLayout, StepperLayout
from slumber.ui.layouts.base import Layout


class _Activity(Activity):
    """Records what the layout does to it, in a log shared with the others."""

    def __init__(self, name: str, log: list[str]) -> None:
        super().__init__()
        self._name = name
        self._log = log
        self.host: Any = None

    def mount(self, activity_host: Any) -> None:
        self.host = activity_host
        self._log.append(f"mount {self._name}")
        activity_host.complete()

    def unmount(self) -> None:
        self._log.append(f"unmount {self._name}")


class _ActivityHost:
    def __init__(
        self, activity_id: str, container: Any, on_complete: Callable[[str], None]
    ) -> None:
        self.activity_id = activity_id
        self.container = container
        self._on_complete = on_complete

    def complete(self) -> None:
        self._on_complete(self.activity_id)


class _LayoutHost:
    def __init__(self, container: Any = None) -> None:
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
        return _ActivityHost(activity_id, container, on_complete)


class _Layout(Layout):
    """The smallest layout: the base does the mounting."""

    def mount(self, host: Any, activities: list[MountedActivity]) -> None:
        pass


def _mounted(name: str, log: list[str]) -> MountedActivity:
    return MountedActivity(
        config=ActivityConfig(id=name, title=name, type="stub"),
        instance=_Activity(name, log),
    )


def test_mount_activity_gives_the_activity_a_host_for_its_container() -> None:
    log: list[str] = []
    completed: list[str] = []
    mounted = _mounted("a", log)
    container = object()

    _Layout().mount_activity(
        _LayoutHost(), mounted, container, on_complete=completed.append
    )

    host = mounted.instance.host
    assert host.activity_id == "a"
    assert host.container is container
    assert log == ["mount a"]
    assert completed == ["a"]


def test_unmount_activity_unmounts_once_and_forgets_it() -> None:
    log: list[str] = []
    layout = _Layout()
    layout.mount_activity(
        _LayoutHost(), _mounted("a", log), object(), on_complete=lambda _: None
    )

    layout.unmount_activity()
    layout.unmount_activity()

    assert log == ["mount a", "unmount a"]


def test_showing_another_activity_unmounts_the_first_before_mounting() -> None:
    log: list[str] = []
    layout = _Layout()
    host = _LayoutHost()

    layout.mount_activity(
        host, _mounted("a", log), object(), on_complete=lambda _: None
    )
    layout.mount_activity(
        host, _mounted("b", log), object(), on_complete=lambda _: None
    )

    assert log == ["mount a", "unmount a", "mount b"]


def test_unmounting_the_layout_unmounts_its_activity() -> None:
    log: list[str] = []
    layout = _Layout()
    layout.mount_activity(
        _LayoutHost(), _mounted("a", log), object(), on_complete=lambda _: None
    )

    layout.unmount()

    assert log == ["mount a", "unmount a"]


def test_unmounting_a_layout_that_shows_nothing_does_nothing() -> None:
    _Layout().unmount()


@pytest.mark.nicegui
def test_hub_shows_its_activity_and_unmounts_it(client: Any) -> None:
    from nicegui import ui

    log: list[str] = []
    layout = HubLayout()

    with ui.element("div") as body:
        layout.mount(_LayoutHost(body), [_mounted("a", log)])
    layout.unmount()

    assert log == ["mount a", "unmount a"]


@pytest.mark.nicegui
def test_hub_does_not_advance_when_its_activity_completes(client: Any) -> None:
    from nicegui import ui

    host = _LayoutHost()
    with ui.element("div") as body:
        host.container = body
        HubLayout().mount(host, [_mounted("a", [])])

    assert host.phase_completed == 0


@pytest.mark.nicegui
def test_stepper_unmounts_a_step_when_the_next_one_is_shown(client: Any) -> None:
    from nicegui import ui

    log: list[str] = []
    layout = StepperLayout()
    host = _LayoutHost()

    with ui.element("div") as body:
        host.container = body
        layout.mount(host, [_mounted("a", log), _mounted("b", log)])
    layout._go_next()
    layout.unmount()

    assert log == ["mount a", "unmount a", "mount b", "unmount b"]
