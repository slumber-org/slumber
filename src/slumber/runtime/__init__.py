"""Runtime: run directory layout, run logging, event dispatch, and orchestration.

``configure_run_logging`` and ``run_study`` are loaded lazily so importing
``slumber.runtime.run`` (e.g. from ``slumber.schemas.study``) does not pull in
modules that depend on ``slumber.schemas.study`` before it finishes loading.
"""

from __future__ import annotations

from slumber.runtime.audit import (
    AuditCategory,
    configure_audit_logging,
    record_event,
    resolve_audit_path,
)
from slumber.runtime.events import (
    SessionState,
    evaluate_guard,
    get_triggered_procedures,
)
from slumber.runtime.logging import configure_run_logging
from slumber.runtime.orchestrator import run_study
from slumber.runtime.run import (
    VALID_RUN_LAYOUT_KEYS,
    RunContext,
    create_run_dir,
    resolve_run_dir,
    run_context_as_dict,
)
from slumber.runtime.sentry import init_sentry

__all__ = [
    "VALID_RUN_LAYOUT_KEYS",
    "AuditCategory",
    "RunContext",
    "SessionState",
    "configure_audit_logging",
    "configure_run_logging",
    "create_run_dir",
    "evaluate_guard",
    "get_triggered_procedures",
    "init_sentry",
    "record_event",
    "resolve_audit_path",
    "resolve_run_dir",
    "run_context_as_dict",
    "run_study",
]
