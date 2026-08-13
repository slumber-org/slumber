"""Event dispatch engine: session state, guards, and procedure matching.

Core logic for event-driven procedure flow. UI-agnostic — usable by any
backend (NiceGUI, headless, etc.).
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from slumber.schemas.procedure import Procedure

_COMPARISON_OPS: dict[str, Callable[[Any, Any], bool]] = {
    "gt": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
}


class SessionState:
    """Mutable runtime state tracked during a session.

    Built-in counters (``awakening_count``, ``sleep_count``) are
    auto-updated by :meth:`handle_event`. Arbitrary keys can be set
    and read via :meth:`get` / :meth:`set` for custom guard logic.
    """

    def __init__(self) -> None:
        self._data: dict[str, Any] = {"awakening_count": 0, "sleep_count": 0}

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for *key*, or *default* if not set."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set an arbitrary key in the session state."""
        self._data[key] = value

    @property
    def awakening_count(self) -> int:
        """Number of ``wake_up`` events fired so far."""
        return self._data["awakening_count"]

    @property
    def sleep_count(self) -> int:
        """Number of ``sleep_start`` events fired so far."""
        return self._data["sleep_count"]

    def handle_event(self, event: str) -> None:
        """Update built-in counters based on the fired event."""
        if event == "wake_up":
            self._data["awakening_count"] += 1
        elif event == "sleep_start":
            self._data["sleep_count"] += 1


def resolve_callable(dotted_path: str) -> Callable[..., Any]:
    """Import a callable from a ``'module.path:function_name'`` string.

    Args:
        dotted_path: Colon-separated path, e.g. ``'my_study.guards:is_rem'``.

    Returns:
        The imported callable.

    Raises:
        ValueError: If the path format is invalid or import fails.
    """
    if ":" not in dotted_path:
        raise ValueError(
            f"Invalid callable path {dotted_path!r}: expected 'module:attribute' format."
        )
    module_path, attr_name = dotted_path.rsplit(":", 1)
    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise ValueError(
            f"Cannot import module {module_path!r} from path {dotted_path!r}: {exc}"
        ) from exc
    try:
        obj = getattr(module, attr_name)
    except AttributeError as exc:
        raise ValueError(
            f"Module {module_path!r} has no attribute {attr_name!r}."
        ) from exc
    if not callable(obj):
        raise TypeError(f"{dotted_path!r} resolved to a non-callable object.")
    return obj


def _evaluate_declarative_guard(when: dict[str, Any], state: SessionState) -> bool:
    """Evaluate a declarative guard dict (all keys must match — AND logic).

    Each key is looked up in *state*. The value is either a literal
    (exact match) or a dict with a single comparison operator key
    (``gt``, ``gte``, ``lt``, ``lte``).
    """
    for key, expected in when.items():
        actual = state.get(key)
        if actual is None:
            return False

        if isinstance(expected, dict):
            for op_name, op_value in expected.items():
                op_func = _COMPARISON_OPS.get(op_name)
                if op_func is None:
                    logger.warning(
                        "Unknown comparison operator {!r} in guard.", op_name
                    )
                    return False
                if not op_func(actual, op_value):
                    return False
        elif actual != expected:
            return False

    return True


def evaluate_guard(
    when: dict[str, Any] | str | None,
    state: SessionState,
) -> bool:
    """Evaluate a procedure's ``when`` guard against session state.

    Args:
        when: Guard specification — ``None`` (always True), a dict
            (declarative checks), or a string (Python callable path).
        state: Current session state.

    Returns:
        Whether the guard passes.
    """
    if when is None:
        return True

    if isinstance(when, str):
        guard_fn = resolve_callable(when)
        return bool(guard_fn(state))

    if isinstance(when, dict):
        return _evaluate_declarative_guard(when, state)

    logger.warning(
        "Unsupported guard type {!r}; treating as False.", type(when).__name__
    )
    return False


def get_triggered_procedures(
    event: str,
    procedures: dict[str, Procedure],
    state: SessionState,
) -> list[tuple[str, Procedure]]:
    """Return procedures whose trigger matches *event* and whose guard passes.

    Results are returned in the order procedures appear in the dict
    (YAML definition order).

    Args:
        event: The session event name (e.g. ``"wake_up"``).
        procedures: Mapping of procedure name → Procedure from the condition.
        state: Current session state (guards are evaluated against this).

    Returns:
        List of ``(name, procedure)`` tuples for procedures that should run.
    """
    triggered: list[tuple[str, Procedure]] = []
    for name, procedure in procedures.items():
        if procedure.trigger != event:
            continue
        if evaluate_guard(procedure.when, state):
            triggered.append((name, procedure))
    return triggered
