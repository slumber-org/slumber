"""Tests for NiceGUI app state management."""

from __future__ import annotations

from slumber.ext.ui.nicegui.state import AppState
from slumber.schemas.condition import Condition
from slumber.schemas.dag import DAG, Component
from slumber.schemas.procedure import Procedure, Step
from slumber.schemas.study import Study


def _step(task: str = "instruction") -> Step:
    return Step(task_type=task)


def _procedure(
    trigger: str | None = None,
    when: dict | str | None = None,
    n_steps: int = 1,
) -> Procedure:
    return Procedure(
        steps=[_step() for _ in range(n_steps)],
        trigger=trigger,
        when=when,
    )


def _dag() -> DAG:
    return DAG(
        components=[Component(name="MASTER", unit_type="Master")],
        connections=[],
        process_components=[],
    )


def _condition(procedures: dict[str, Procedure] | None = None) -> Condition:
    procs = procedures or {"pre_sleep": _procedure(trigger="session_start")}
    return Condition(name="ctrl", procedures=procs, dag=_dag())


def _study() -> Study:
    return Study(study_id="s1", name="Test Study")


class _FakeContext:
    study_id = "s1"
    participant_id = "sub-001"
    session_id = "ses-01"
    run_id = "r001"
    condition_id = "ctrl"


def _state(procedures: dict[str, Procedure] | None = None) -> AppState:
    return AppState(
        study=_study(),
        condition=_condition(procedures),
        context=_FakeContext(),  # type: ignore[arg-type]
        config={},
        authenticated=True,
        current_page="welcome",
    )


class TestFireEvent:
    def test_triggers_matching_procedures(self) -> None:
        state = _state({"pre": _procedure(trigger="session_start")})
        state.fire_event("session_start")
        assert state.current_page == "procedure"
        assert len(state.active_procedures) == 1
        assert state.active_procedures[0][0] == "pre"

    def test_no_match_stays_on_page(self) -> None:
        state = _state({"pre": _procedure(trigger="session_start")})
        state.current_page = "sleep"
        state.fire_event("wake_up")
        assert state.current_page == "sleep"

    def test_session_end_no_match_goes_to_complete(self) -> None:
        state = _state({"pre": _procedure(trigger="session_start")})
        state.fire_event("session_end")
        assert state.current_page == "complete"

    def test_updates_counters(self) -> None:
        state = _state()
        state.fire_event("wake_up")
        assert state.session_state.awakening_count == 1
        state.fire_event("sleep_start")
        assert state.session_state.sleep_count == 1

    def test_guard_filters_procedures(self) -> None:
        state = _state(
            {
                "first": _procedure(trigger="wake_up", when={"awakening_count": 1}),
                "later": _procedure(
                    trigger="wake_up", when={"awakening_count": {"gt": 1}}
                ),
            }
        )
        state.fire_event("wake_up")
        assert len(state.active_procedures) == 1
        assert state.active_procedures[0][0] == "first"

    def test_resets_step_state(self) -> None:
        state = _state({"pre": _procedure(trigger="session_start", n_steps=3)})
        state.current_step_index = 2
        state.completed_steps = {0, 1}
        state.fire_event("session_start")
        assert state.current_step_index == 0
        assert state.completed_steps == set()


class TestAdvanceToNextProcedure:
    def test_advances_to_next(self) -> None:
        state = _state()
        state.active_procedures = [
            ("a", _procedure()),
            ("b", _procedure()),
        ]
        state.active_procedure_index = 0
        state.advance_to_next_procedure()
        assert state.active_procedure_index == 1
        assert state.current_step_index == 0

    def test_goes_to_sleep_when_done(self) -> None:
        state = _state()
        state.active_procedures = [("a", _procedure())]
        state.active_procedure_index = 0
        state._last_event = "wake_up"
        state.advance_to_next_procedure()
        assert state.current_page == "sleep"

    def test_goes_to_complete_on_session_end(self) -> None:
        state = _state()
        state.active_procedures = [("a", _procedure())]
        state.active_procedure_index = 0
        state._last_event = "session_end"
        state.advance_to_next_procedure()
        assert state.current_page == "complete"


class TestStepNavigation:
    def test_next_step(self) -> None:
        state = _state({"p": _procedure(trigger="session_start", n_steps=3)})
        state.fire_event("session_start")
        assert state.current_step_index == 0
        state.next_step()
        assert state.current_step_index == 1
        assert 0 in state.completed_steps

    def test_prev_step(self) -> None:
        state = _state({"p": _procedure(trigger="session_start", n_steps=3)})
        state.fire_event("session_start")
        state.current_step_index = 2
        state.prev_step()
        assert state.current_step_index == 1

    def test_prev_step_at_zero_stays(self) -> None:
        state = _state({"p": _procedure(trigger="session_start", n_steps=3)})
        state.fire_event("session_start")
        state.prev_step()
        assert state.current_step_index == 0

    def test_complete_current_step(self) -> None:
        state = _state({"p": _procedure(trigger="session_start", n_steps=2)})
        state.fire_event("session_start")
        state.complete_current_step()
        assert 0 in state.completed_steps

    def test_is_last_step(self) -> None:
        state = _state({"p": _procedure(trigger="session_start", n_steps=2)})
        state.fire_event("session_start")
        assert not state.is_last_step
        state.current_step_index = 1
        assert state.is_last_step

    def test_all_steps_completed(self) -> None:
        state = _state({"p": _procedure(trigger="session_start", n_steps=2)})
        state.fire_event("session_start")
        assert not state.all_steps_completed
        state.completed_steps = {0, 1}
        assert state.all_steps_completed

    def test_next_on_last_step_advances_procedure(self) -> None:
        state = _state({"p": _procedure(trigger="session_start", n_steps=1)})
        state.fire_event("session_start")
        state._last_event = "session_start"
        state.next_step()
        assert state.current_page == "sleep"
