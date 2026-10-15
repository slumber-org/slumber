"""Stepper layout: ordered activities with optional list and nav buttons."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from loguru import logger

from slumber.schemas.study import StepperLayoutDefaults
from slumber.ui.layouts.base import Layout, LayoutHost
from slumber.ui.widgets import outline_button, primary_button, surface_card

if TYPE_CHECKING:
    from slumber.ui.backend import MountedActivity

STEPPER_CSS = """
:root {
  --slumber-gap: 16px;
  --slumber-card-pad: 24px;
  --slumber-list-w: 288px;
  --slumber-nav-h: 76px;
}
@media (max-width: 1199px) { :root { --slumber-list-w: 248px; } }
@media (max-width: 999px) { :root { --slumber-list-w: 216px; } }
@media (max-width: 799px) { :root { --slumber-card-pad: 20px; } }
@media (max-height: 760px) { :root { --slumber-nav-h: 64px; } }
@media (max-height: 640px) { :root { --slumber-nav-h: 56px; --slumber-gap: 12px; } }

.slumber-stepper { flex: 1; min-height: 0; display: flex; flex-direction: column; }
.slumber-stepper-main {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: var(--slumber-gap);
  padding: var(--slumber-pad);
}
.slumber-stepper-slot, .slumber-step-list {
  scrollbar-width: thin;
  scrollbar-color: var(--slumber-secondary) transparent;
}
.slumber-stepper-slot {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow: auto;
  padding: var(--slumber-card-pad);
  overflow-wrap: anywhere;
}
.slumber-step-list {
  width: var(--slumber-list-w);
  flex-shrink: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px 12px;
  overflow-y: auto;
}
.slumber-step-list-title {
  padding: 0 12px 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--slumber-secondary);
}
.slumber-step {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  height: 44px;
  flex-shrink: 0;
  padding: 0 12px;
  border: 0;
  border-radius: 8px;
  background: none;
  color: var(--slumber-text);
  font: inherit;
  text-align: left;
  cursor: pointer;
}
.slumber-step-text { flex: 1; min-width: 0; display: flex; }
.slumber-step-name { min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.slumber-step-number { flex-shrink: 0; margin-right: 6px; font-weight: 600; color: var(--slumber-secondary); }
.slumber-step-icon { flex-shrink: 0; font-size: 22px; }
.slumber-step-pending .slumber-step-icon { color: color-mix(in srgb, var(--slumber-text) 40%, transparent); }
.slumber-step-current .slumber-step-icon { color: var(--slumber-secondary); }
.slumber-step-done .slumber-step-icon { color: var(--slumber-accent); }
.slumber-step:not(:disabled):not(.slumber-step-current):hover {
  background: color-mix(in srgb, var(--slumber-secondary) 12%, transparent);
}
.slumber-step-current { background: var(--slumber-page-bg); font-weight: 700; cursor: default; }
.slumber-step:disabled { opacity: 0.4; cursor: not-allowed; color: var(--slumber-text); }
.slumber-step:focus-visible { outline: 2px solid var(--slumber-text); outline-offset: 2px; }
.slumber-nav {
  display: flex;
  align-items: center;
  gap: 24px;
  height: var(--slumber-nav-h);
  flex-shrink: 0;
  padding: 0 var(--slumber-pad);
  background: var(--slumber-surface);
}
.slumber-nav-spacer { flex: 1; }
.slumber-progress { flex: 1; min-width: 0; display: flex; flex-direction: column; justify-content: center; gap: 6px; }
.slumber-progress-text {
  text-align: center;
  font-size: 13px;
  color: var(--slumber-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.slumber-progress-segments { display: flex; gap: 6px; }
.slumber-progress-segment { flex: 1; min-width: 4px; height: 6px; border-radius: 3px; background: var(--slumber-page-bg); }
.slumber-segment-done { background: var(--slumber-accent); }
.slumber-segment-current { background: var(--slumber-secondary); }
@media (max-width: 799px) {
  .slumber-stepper-main { flex-direction: column; }
  .slumber-step-list {
    order: -1;
    width: auto;
    flex-direction: row;
    flex-shrink: 0;
    overflow-x: auto;
    overflow-y: hidden;
    padding: 8px;
  }
  .slumber-step-list-title { display: none; }
  .slumber-step-list .slumber-step { width: 190px; }
}
"""

# TODO: add a "skipped" status together with explicit skipping (an activity
# decides, e.g. ``host.skip()``); see the skipping follow-up task.
StepStatus = Literal["pending", "current", "done"]

_STATUS_ICONS: dict[StepStatus, str] = {
    "pending": "radio_button_unchecked",
    "current": "radio_button_checked",
    "done": "check_circle_outline",
}

# Spoken by screen readers after the step title.
_STATUS_LABELS: dict[StepStatus, str] = {
    "pending": "not started",
    "current": "current",
    "done": "done",
}


class StepperProgress:
    """Which steps are finished, and which the participant can reach.

    A step's *status* and its *availability* are separate. Status records what
    happened to the step; availability says whether the participant may go there,
    and is worked out from the statuses.

    The *gate* is the first step that is not done. Steps up to and including the
    gate are available; later steps are not. With no gate, every step is
    available and the phase can be completed. With ``allow_skip`` there is never
    a gate.

    Args:
        count: Number of steps.
        allow_skip: Whether the participant may move past unfinished steps.
    """

    def __init__(self, count: int, *, allow_skip: bool = False) -> None:
        self._count = count
        self._allow_skip = allow_skip
        self._done: set[int] = set()
        self._current = 0

    @property
    def current(self) -> int:
        """Index of the step being shown."""
        return self._current

    @property
    def count(self) -> int:
        """Number of steps."""
        return self._count

    @property
    def is_last(self) -> bool:
        """Whether the current step is the last one."""
        return self._current == self._count - 1

    def status(self, index: int) -> StepStatus:
        """Return the status of step *index*."""
        if index == self._current:
            return "current"
        if index in self._done:
            return "done"
        return "pending"

    def mark_done(self, index: int) -> None:
        """Record that step *index* finished."""
        self._done.add(index)

    def _gate(self) -> int | None:
        if self._allow_skip:
            return None
        for index in range(self._count):
            if index not in self._done:
                return index
        return None

    def is_available(self, index: int) -> bool:
        """Whether the participant may go to step *index*."""
        if index == self._current:
            return True
        gate = self._gate()
        return 0 <= index < self._count and (gate is None or index <= gate)

    def can_complete(self) -> bool:
        """Whether the phase can be completed (no unfinished step blocks it)."""
        return self._gate() is None

    def go_to(self, index: int) -> bool:
        """Move to step *index* if it is available.

        Returns:
            Whether the move happened.
        """
        if index == self._current or not self.is_available(index):
            return False
        self._current = index
        return True


class StepperLayout(Layout):
    """Ordered activities: optional list, progress bar, and prev/next/complete."""

    settings_model = StepperLayoutDefaults
    css = STEPPER_CSS

    def __init__(self, settings: StepperLayoutDefaults | None = None) -> None:
        super().__init__(settings or StepperLayoutDefaults())
        self._host: LayoutHost | None = None
        self._activities: list[MountedActivity] = []
        self._progress: StepperProgress | None = None
        self._slot: Any | None = None
        self._prev_button: Any | None = None
        self._next_button: Any | None = None
        self._complete_button: Any | None = None
        self._list_container: Any | None = None
        self._progress_container: Any | None = None
        self._mounted_instance: Any | None = None

    @property
    def _cfg(self) -> StepperLayoutDefaults:
        assert isinstance(self.settings, StepperLayoutDefaults)
        return self.settings

    def mount(self, host: LayoutHost, activities: list[MountedActivity]) -> None:
        """Build stepper chrome and mount the first activity."""
        from nicegui import ui

        self._host = host
        self._activities = list(activities)
        self._mounted_instance = None

        if not activities:
            logger.warning("StepperLayout mounted with no activities.")
            host.emit_phase_completed()
            return

        cfg = self._cfg
        self._progress = StepperProgress(len(activities), allow_skip=cfg.allow_skip)
        with host.container, ui.element("div").classes("slumber-stepper"):
            with ui.element("div").classes("slumber-stepper-main"):
                with surface_card(classes="slumber-stepper-slot") as slot:
                    self._slot = slot
                if cfg.show_activity_list:
                    with surface_card(classes="slumber-step-list") as step_list:
                        self._list_container = step_list
                    step_list.props["aria-label"] = "Activities"

            with ui.element("div").classes("slumber-nav"):
                self._prev_button = outline_button(
                    cfg.previous_button,
                    icon="arrow_back",
                    on_click=self._go_previous,
                    enabled=False,
                )
                if cfg.show_progress_bar:
                    self._progress_container = ui.element("div").classes(
                        "slumber-progress"
                    )
                else:
                    ui.element("div").classes("slumber-nav-spacer")
                self._next_button = primary_button(
                    cfg.next_button,
                    icon="arrow_forward",
                    on_click=self._go_next,
                    enabled=False,
                )
                self._complete_button = primary_button(
                    cfg.complete_button,
                    icon="check",
                    on_click=self._finish_phase,
                    enabled=False,
                )
                self._complete_button.set_visibility(False)

        self._show_current()

    def unmount(self) -> None:
        """Unmount the active activity plugin."""
        self._unmount_current()
        self._host = None
        self._activities = []
        self._progress = None
        self._slot = None

    def _render_step_list(self) -> None:
        from nicegui import ui

        if self._list_container is None or self._progress is None:
            return
        self._list_container.clear()
        with self._list_container:
            ui.label("Activities").classes("slumber-step-list-title")
            for index, mounted in enumerate(self._activities):
                self._render_step(index, mounted.config.display_title)

    def _render_step(self, index: int, title: str) -> None:
        from nicegui import ui

        assert self._progress is not None
        status = self._progress.status(index)
        available = self._progress.is_available(index)
        label = f"{title}, {_STATUS_LABELS[status]}"
        if not available:
            label += ", not available"

        row = ui.element("button").classes(f"slumber-step slumber-step-{status}")
        row.props["type"] = "button"
        row.props["title"] = title
        row.props["aria-label"] = label
        if status == "current":
            row.props["aria-current"] = "step"
        if not available:
            row.props["disabled"] = True
        row.on("click", lambda index=index: self._go_to(index))
        with row:
            ui.icon(_STATUS_ICONS[status]).classes("slumber-step-icon")
            with ui.element("div").classes("slumber-step-text"):
                if self._cfg.number_steps:
                    ui.label(f"{index + 1}.").classes("slumber-step-number")
                ui.label(title).classes("slumber-step-name")

    def _render_progress(self) -> None:
        from nicegui import ui

        if self._progress_container is None or self._progress is None:
            return
        progress = self._progress
        cfg = self._cfg
        parts = []
        if cfg.show_step_count:
            parts.append(f"Step {progress.current + 1} of {progress.count}")
        if cfg.show_step_name:
            parts.append(self._activities[progress.current].config.display_title)
        text = " · ".join(parts)

        container = self._progress_container
        container.clear()
        container.props["role"] = "progressbar"
        container.props["aria-valuemin"] = 1
        container.props["aria-valuemax"] = progress.count
        container.props["aria-valuenow"] = progress.current + 1
        container.props["aria-valuetext"] = text or f"Step {progress.current + 1}"
        with container:
            if text:
                ui.label(text).classes("slumber-progress-text")
            with ui.element("div").classes("slumber-progress-segments"):
                for index in range(progress.count):
                    status = progress.status(index)
                    segment = "slumber-progress-segment"
                    if status != "pending":
                        segment += f" slumber-segment-{status}"
                    ui.element("i").classes(segment)

    def _show_current(self) -> None:
        assert self._host is not None
        assert self._progress is not None
        assert self._slot is not None
        self._unmount_current()
        self._slot.clear()

        index = self._progress.current
        mounted = self._activities[index]

        def on_complete(completed_id: str) -> None:
            del completed_id
            if self._progress is None:
                return
            self._progress.mark_done(index)
            self._refresh()

        host = self._host.make_activity_host(
            mounted.config.id,
            self._slot,
            on_complete=on_complete,
        )
        self._mounted_instance = mounted.instance
        mounted.instance.mount(host)
        self._refresh()

    def _unmount_current(self) -> None:
        if self._mounted_instance is not None:
            self._mounted_instance.unmount()
            self._mounted_instance = None

    def _refresh(self) -> None:
        """Bring the buttons, step list and progress bar up to date."""
        if self._progress is None:
            return
        progress = self._progress
        if self._prev_button is not None:
            self._prev_button.set_enabled(progress.current > 0)

        if self._next_button is not None and self._complete_button is not None:
            is_last = progress.is_last
            self._next_button.set_visibility(not is_last)
            self._complete_button.set_visibility(is_last)
            if is_last:
                self._complete_button.set_enabled(progress.can_complete())
            else:
                self._next_button.set_enabled(
                    progress.is_available(progress.current + 1)
                )

        self._render_step_list()
        self._render_progress()

    def _go_to(self, index: int) -> None:
        if self._progress is None or not self._progress.go_to(index):
            return
        self._show_current()
        self._scroll_slot_to_top()

    def _scroll_slot_to_top(self) -> None:
        from nicegui import ui

        if self._slot is not None:
            ui.run_javascript(
                f"document.getElementById('c{self._slot.id}').scrollTop = 0"
            )

    def _go_previous(self) -> None:
        if self._progress is not None:
            self._go_to(self._progress.current - 1)

    def _go_next(self) -> None:
        if self._progress is not None:
            self._go_to(self._progress.current + 1)

    def _finish_phase(self) -> None:
        if self._host is None or self._progress is None:
            return
        if self._progress.can_complete():
            self._host.emit_phase_completed()
