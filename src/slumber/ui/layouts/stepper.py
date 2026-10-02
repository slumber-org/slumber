"""Stepper layout: ordered activities with optional list and nav buttons."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

from slumber.schemas.study import StepperLayoutDefaults
from slumber.ui.layouts.base import Layout, LayoutHost
from slumber.ui.theme import BRAND, POSITIVE, SECONDARY, SURFACE, SURFACE_BORDER
from slumber.ui.widgets import outline_button, primary_button

if TYPE_CHECKING:
    from slumber.ui.backend import MountedActivity


class StepperLayout(Layout):
    """Ordered activities: optional list + activity slot; prev/next/complete."""

    settings_model = StepperLayoutDefaults

    def __init__(self, settings: StepperLayoutDefaults | None = None) -> None:
        super().__init__(settings or StepperLayoutDefaults())
        self._host: LayoutHost | None = None
        self._activities: list[MountedActivity] = []
        self._index = 0
        self._completed: set[str] = set()
        self._slot: Any | None = None
        self._prev_button: Any | None = None
        self._next_button: Any | None = None
        self._complete_button: Any | None = None
        self._list_container: Any | None = None
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
        self._index = 0
        self._completed = set()
        self._mounted_instance = None

        if not activities:
            logger.warning("StepperLayout mounted with no activities.")
            host.emit_phase_completed()
            return

        cfg = self._cfg
        with host.container, ui.column().classes("w-full h-full flex flex-col"):
            with ui.row().classes("w-full flex-1 min-h-0 no-wrap"):
                self._slot = ui.column().classes("flex-grow p-6 min-w-0")
                if cfg.show_activity_list:
                    self._list_container = ui.column().classes(
                        f"w-64 p-4 bg-[{SURFACE}] border-l "
                        f"border-[{SURFACE_BORDER}] shrink-0"
                    )
                    self._render_activity_list()

            with ui.row().classes(
                f"w-full items-center justify-center gap-3 px-6 py-3 "
                f"bg-[{SURFACE}] border-t border-[{SURFACE_BORDER}] shrink-0"
            ):
                self._prev_button = outline_button(
                    cfg.previous_button,
                    icon="arrow_back",
                    on_click=self._go_previous,
                    enabled=False,
                )
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
        self._slot = None

    def _render_activity_list(self) -> None:
        from nicegui import ui

        if self._list_container is None:
            return
        self._list_container.clear()
        with self._list_container:
            ui.label("Activities").classes(f"text-overline text-[{SECONDARY}] mb-3")
            for i, mounted in enumerate(self._activities):
                is_current = i == self._index
                is_done = mounted.config.id in self._completed
                icon = (
                    "check_circle"
                    if is_done
                    else ("play_circle" if is_current else "circle")
                )
                icon_color = (
                    POSITIVE if is_done else (BRAND if is_current else SURFACE_BORDER)
                )
                text_cls = "font-bold" if is_current else f"text-[{SECONDARY}]"
                with ui.row().classes("items-center gap-2 py-1"):
                    ui.icon(icon, size="xs").style(f"color: {icon_color}")
                    ui.label(mounted.config.display_title).classes(
                        f"text-body2 {text_cls}"
                    )

    def _show_current(self) -> None:
        assert self._host is not None
        assert self._slot is not None
        self._unmount_current()
        self._slot.clear()

        mounted = self._activities[self._index]
        activity_id = mounted.config.id

        def on_complete(completed_id: str) -> None:
            self._completed.add(completed_id)
            self._update_nav()
            self._render_activity_list()

        host = self._host.make_activity_host(
            activity_id,
            self._slot,
            on_complete=on_complete,
        )
        self._mounted_instance = mounted.instance
        mounted.instance.mount(host)
        self._update_nav()
        self._render_activity_list()

    def _unmount_current(self) -> None:
        if self._mounted_instance is not None:
            self._mounted_instance.unmount()
            self._mounted_instance = None

    def _update_nav(self) -> None:
        if not self._activities:
            return
        cfg = self._cfg
        current = self._activities[self._index]
        current_done = current.config.id in self._completed
        can_advance = current_done or cfg.allow_skip
        is_last = self._index >= len(self._activities) - 1

        if self._prev_button is not None:
            self._prev_button.set_enabled(self._index > 0)

        if self._next_button is not None and self._complete_button is not None:
            if is_last:
                self._next_button.set_visibility(False)
                self._complete_button.set_visibility(True)
                all_done = (
                    all(a.config.id in self._completed for a in self._activities)
                    or cfg.allow_skip
                )
                self._complete_button.set_enabled(all_done and can_advance)
            else:
                self._next_button.set_visibility(True)
                self._complete_button.set_visibility(False)
                self._next_button.set_enabled(can_advance)

    def _go_previous(self) -> None:
        if self._index <= 0:
            return
        self._index -= 1
        self._show_current()

    def _go_next(self) -> None:
        if self._index >= len(self._activities) - 1:
            return
        current = self._activities[self._index]
        if current.config.id not in self._completed and not self._cfg.allow_skip:
            return
        self._index += 1
        self._show_current()

    def _finish_phase(self) -> None:
        if self._host is None:
            return
        cfg = self._cfg
        if not cfg.allow_skip and not all(
            a.config.id in self._completed for a in self._activities
        ):
            return
        self._host.emit_phase_completed()
