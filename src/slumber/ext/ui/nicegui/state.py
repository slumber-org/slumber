"""Reactive app state for the NiceGUI participant UI.

All pages read/write :class:`AppState`. Page navigation is driven by
setting :attr:`AppState.current_page`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from loguru import logger

from slumber.ext.ui.nicegui.config import NiceGUIConfig
from slumber.runtime.events import SessionState, get_triggered_procedures

if TYPE_CHECKING:
    from slumber.runtime.run import RunContext
    from slumber.schemas.condition import Condition
    from slumber.schemas.procedure import Procedure
    from slumber.schemas.study import Study


@dataclass
class AppState:
    """Central state for the NiceGUI participant app."""

    study: Study
    condition: Condition
    context: RunContext
    config: dict[str, Any]

    authenticated: bool = False
    current_page: str = "login"

    session_state: SessionState = field(default_factory=SessionState)

    active_procedures: list[tuple[str, Procedure]] = field(default_factory=list)
    active_procedure_index: int = 0
    current_step_index: int = 0
    completed_steps: set[int] = field(default_factory=set)

    is_asleep: bool = False
    _last_event: str | None = field(default=None, repr=False)
    _ui_config: NiceGUIConfig | None = field(default=None, repr=False)

    @property
    def ui_config(self) -> NiceGUIConfig:
        """Parsed NiceGUI UI config with defaults."""
        if self._ui_config is None:
            self._ui_config = NiceGUIConfig.model_validate(self.config)
        return self._ui_config

    @property
    def current_procedure_name(self) -> str:
        """Name of the currently active procedure."""
        return self.active_procedures[self.active_procedure_index][0]

    @property
    def current_procedure(self) -> Procedure:
        """Currently active procedure."""
        return self.active_procedures[self.active_procedure_index][1]

    @property
    def current_procedure_title(self) -> str:
        """Display title of the currently active procedure."""
        proc = self.current_procedure
        if proc.title:
            return proc.title
        return self.current_procedure_name.replace("_", " ").title()

    @property
    def current_step(self) -> Any:
        """Currently active step."""
        return self.current_procedure.steps[self.current_step_index]

    @property
    def is_last_step(self) -> bool:
        """Whether the current step is the last in the procedure."""
        return self.current_step_index >= self.current_procedure.n_steps - 1

    @property
    def all_steps_completed(self) -> bool:
        """Whether all steps in the current procedure are completed."""
        return len(self.completed_steps) >= self.current_procedure.n_steps

    def fire_event(self, event: str) -> None:
        """Fire a session event.

        Updates session state counters, finds matching procedures, and
        navigates to the procedure page if any match. If no procedures
        match and the event is ``session_end``, navigates to completion.

        Args:
            event: Session event name (e.g. ``"session_start"``).
        """
        self._last_event = event
        self.session_state.handle_event(event)

        triggered = get_triggered_procedures(
            event, self.condition.procedures, self.session_state
        )
        logger.info("Event {!r}: {} procedure(s) triggered", event, len(triggered))

        if triggered:
            self.active_procedures = triggered
            self.active_procedure_index = 0
            self._reset_step_state()
            self.current_page = "procedure"
        elif event == "session_end":
            self.current_page = "complete"

    def advance_to_next_procedure(self) -> None:
        """Move to the next triggered procedure, or back to sleep/completion."""
        self.active_procedure_index += 1
        if self.active_procedure_index < len(self.active_procedures):
            self._reset_step_state()
            logger.info(
                "Advancing to procedure {!r}",
                self.active_procedures[self.active_procedure_index][0],
            )
        else:
            if self._last_event == "session_end":
                self.current_page = "complete"
            else:
                self.current_page = "sleep"
            logger.info("All triggered procedures done → {}", self.current_page)

    def complete_current_step(self) -> None:
        """Mark the current step as completed."""
        self.completed_steps.add(self.current_step_index)

    def next_step(self) -> None:
        """Advance to the next step (or complete the procedure)."""
        self.complete_current_step()
        if self.is_last_step:
            self.advance_to_next_procedure()
        else:
            self.current_step_index += 1

    def prev_step(self) -> None:
        """Go back to the previous step (no-op on the first step)."""
        if self.current_step_index > 0:
            self.current_step_index -= 1

    def _reset_step_state(self) -> None:
        """Reset step navigation state for a new procedure."""
        self.current_step_index = 0
        self.completed_steps = set()
