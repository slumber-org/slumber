"""Tests for the event dispatch engine."""

from __future__ import annotations

import pytest

from slumber.runtime.events import (
    SessionState,
    evaluate_guard,
    get_triggered_procedures,
    resolve_callable,
)
from slumber.schemas.procedure import Procedure, Step


def _make_procedure(
    trigger: str | None = None,
    when: dict | str | None = None,
) -> Procedure:
    return Procedure(
        steps=[Step(task_type="instruction")],
        trigger=trigger,
        when=when,
    )


class TestSessionState:
    """Tests for SessionState."""

    def test_initial_counters(self) -> None:
        state = SessionState()
        assert state.awakening_count == 0
        assert state.sleep_count == 0

    def test_handle_wake_up(self) -> None:
        state = SessionState()
        state.handle_event("wake_up")
        assert state.awakening_count == 1
        state.handle_event("wake_up")
        assert state.awakening_count == 2

    def test_handle_sleep_start(self) -> None:
        state = SessionState()
        state.handle_event("sleep_start")
        assert state.sleep_count == 1

    def test_handle_unknown_event(self) -> None:
        state = SessionState()
        state.handle_event("session_start")
        assert state.awakening_count == 0
        assert state.sleep_count == 0

    def test_get_set_custom_key(self) -> None:
        state = SessionState()
        assert state.get("custom_key") is None
        assert state.get("custom_key", "default") == "default"
        state.set("custom_key", "value")
        assert state.get("custom_key") == "value"

    def test_set_overwrites(self) -> None:
        state = SessionState()
        state.set("key", 1)
        state.set("key", 2)
        assert state.get("key") == 2


class TestEvaluateGuard:
    """Tests for evaluate_guard."""

    def test_none_always_true(self) -> None:
        assert evaluate_guard(None, SessionState()) is True

    def test_exact_match(self) -> None:
        state = SessionState()
        state.handle_event("wake_up")
        assert evaluate_guard({"awakening_count": 1}, state) is True
        assert evaluate_guard({"awakening_count": 2}, state) is False

    def test_gt(self) -> None:
        state = SessionState()
        state.handle_event("wake_up")
        state.handle_event("wake_up")
        assert evaluate_guard({"awakening_count": {"gt": 1}}, state) is True
        assert evaluate_guard({"awakening_count": {"gt": 2}}, state) is False

    def test_gte(self) -> None:
        state = SessionState()
        state.handle_event("wake_up")
        assert evaluate_guard({"awakening_count": {"gte": 1}}, state) is True
        assert evaluate_guard({"awakening_count": {"gte": 2}}, state) is False

    def test_lt(self) -> None:
        state = SessionState()
        assert evaluate_guard({"awakening_count": {"lt": 1}}, state) is True
        state.handle_event("wake_up")
        assert evaluate_guard({"awakening_count": {"lt": 1}}, state) is False

    def test_lte(self) -> None:
        state = SessionState()
        state.handle_event("wake_up")
        assert evaluate_guard({"awakening_count": {"lte": 1}}, state) is True
        assert evaluate_guard({"awakening_count": {"lte": 0}}, state) is False

    def test_multiple_keys_and_logic(self) -> None:
        state = SessionState()
        state.handle_event("wake_up")
        state.handle_event("sleep_start")
        assert evaluate_guard({"awakening_count": 1, "sleep_count": 1}, state) is True
        assert evaluate_guard({"awakening_count": 1, "sleep_count": 2}, state) is False

    def test_missing_key_returns_false(self) -> None:
        state = SessionState()
        assert evaluate_guard({"nonexistent_key": 1}, state) is False

    def test_custom_key(self) -> None:
        state = SessionState()
        state.set("arousal_type", "rem")
        assert evaluate_guard({"arousal_type": "rem"}, state) is True
        assert evaluate_guard({"arousal_type": "nrem"}, state) is False

    def test_callable_guard(self) -> None:
        # bool() is a callable that returns False for a SessionState (truthy object → True)
        assert evaluate_guard("builtins:bool", SessionState()) is True

    def test_unknown_operator(self) -> None:
        state = SessionState()
        state.handle_event("wake_up")
        assert evaluate_guard({"awakening_count": {"bad_op": 1}}, state) is False


class TestResolveCallable:
    """Tests for resolve_callable."""

    def test_valid_path(self) -> None:
        fn = resolve_callable("os.path:exists")
        assert callable(fn)

    def test_missing_colon(self) -> None:
        with pytest.raises(ValueError, match="expected 'module:attribute'"):
            resolve_callable("os.path.exists")

    def test_bad_module(self) -> None:
        with pytest.raises(ValueError, match="Cannot import module"):
            resolve_callable("nonexistent_module_xyz:func")

    def test_bad_attribute(self) -> None:
        with pytest.raises(ValueError, match="has no attribute"):
            resolve_callable("os.path:nonexistent_func_xyz")

    def test_non_callable(self) -> None:
        with pytest.raises(TypeError, match="non-callable"):
            resolve_callable("os.path:sep")


class TestGetTriggeredProcedures:
    """Tests for get_triggered_procedures."""

    def test_simple_match(self) -> None:
        procs = {"pre_sleep": _make_procedure(trigger="session_start")}
        result = get_triggered_procedures("session_start", procs, SessionState())
        assert len(result) == 1
        assert result[0][0] == "pre_sleep"

    def test_no_match(self) -> None:
        procs = {"pre_sleep": _make_procedure(trigger="session_start")}
        result = get_triggered_procedures("wake_up", procs, SessionState())
        assert result == []

    def test_no_trigger_skipped(self) -> None:
        procs = {"proc": _make_procedure(trigger=None)}
        result = get_triggered_procedures("session_start", procs, SessionState())
        assert result == []

    def test_guard_filters(self) -> None:
        state = SessionState()
        state.handle_event("wake_up")
        procs = {
            "first": _make_procedure(trigger="wake_up", when={"awakening_count": 1}),
            "later": _make_procedure(
                trigger="wake_up", when={"awakening_count": {"gt": 1}}
            ),
        }
        result = get_triggered_procedures("wake_up", procs, state)
        assert len(result) == 1
        assert result[0][0] == "first"

    def test_multiple_matches_preserve_order(self) -> None:
        procs = {
            "a": _make_procedure(trigger="wake_up"),
            "b": _make_procedure(trigger="wake_up"),
            "c": _make_procedure(trigger="session_start"),
        }
        state = SessionState()
        result = get_triggered_procedures("wake_up", procs, state)
        assert [name for name, _ in result] == ["a", "b"]

    def test_guard_with_updated_state(self) -> None:
        state = SessionState()
        state.handle_event("wake_up")
        state.handle_event("wake_up")
        procs = {
            "first": _make_procedure(trigger="wake_up", when={"awakening_count": 1}),
            "later": _make_procedure(
                trigger="wake_up", when={"awakening_count": {"gt": 1}}
            ),
        }
        result = get_triggered_procedures("wake_up", procs, state)
        assert len(result) == 1
        assert result[0][0] == "later"

    def test_empty_procedures(self) -> None:
        result = get_triggered_procedures("wake_up", {}, SessionState())
        assert result == []
