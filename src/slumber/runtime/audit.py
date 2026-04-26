"""Audit log: structured event records routed through loguru.

The audit log is a configured loguru handler: any code can call
:func:`record_event`, which translates to a tagged loguru call, and the
audit handler — a JSONL sink filtered on the ``audit`` extra — writes a
structured record to disk. Per-category toggles and the file path come
from :class:`slumber.schemas.audit.AuditConfig`.

Categories:
    * ``ui``     — participant UI interactions (button clicks, page-emitted events)
    * ``action`` — router-dispatched action invocations
    * ``dag``    — DAG and device lifecycle (started, stopped, errors)
    * ``study``  — researcher-defined scientific/domain events (open category)
"""

from __future__ import annotations

import json
from datetime import timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from loguru import logger

from slumber.runtime.run import resolve_path_template

if TYPE_CHECKING:
    from slumber.runtime.run import RunContext
    from slumber.schemas.audit import AuditConfig
    from slumber.schemas.study import Study


AuditCategory = Literal["ui", "action", "dag", "study"]

_AUDIT_LEVEL = "INFO"


def record_event(
    category: AuditCategory,
    event: str,
    payload: dict[str, Any] | None = None,
) -> None:
    """Record an audit event.

    Translates to a tagged ``logger.bind(audit=True, ...)`` call. Safe to
    call when no audit handler is configured (the record still flows
    through any normal log handlers as a regular info entry).

    Args:
        category: One of ``"ui"``, ``"action"``, ``"dag"``, ``"study"``.
        event: Short event name (e.g. ``"welcome.start"``, ``"sleep_onset"``).
        payload: Optional JSON-serializable dict of extra fields.
    """
    logger.bind(audit=True, category=category, event=event, payload=payload or {}).log(
        _AUDIT_LEVEL, "{}.{}", category, event
    )


def resolve_audit_path(
    config: "AuditConfig", context: "RunContext", run_dir: Path
) -> Path:
    """Expand placeholders in ``config.path`` and resolve relative to *run_dir*.

    Mirrors the placeholder/relative-path handling in
    :func:`slumber.runtime.logging.configure_run_logging`.

    Args:
        config: Audit configuration.
        context: Run context for placeholder expansion.
        run_dir: Run directory used to resolve relative paths.

    Returns:
        Absolute path to the audit log file.
    """
    return resolve_path_template(config.path, context, base_dir=run_dir)


def configure_audit_logging(
    study: "Study",
    context: "RunContext",
    run_dir: Path,
) -> list[int]:
    """Add a loguru handler that writes audit records as JSONL.

    The handler filters on ``record["extra"]["audit"] is True`` and on
    the per-category toggles in :class:`AuditConfig`. The format function
    emits ``{ts, category, event, payload}`` as a single JSON object per
    line.

    Args:
        study: Study manifest (provides :attr:`Study.audit`).
        context: Run context (used for path placeholder expansion).
        run_dir: Run directory; relative audit paths resolve against it.

    Returns:
        List of loguru handler IDs. Pass each to ``logger.remove()`` on
        run teardown. Empty list when ``audit.enabled`` is False.
    """
    cfg = study.audit
    if not cfg.enabled:
        return []

    enabled_categories = _enabled_categories(cfg)
    audit_path = resolve_audit_path(cfg, context, run_dir)
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    def audit_filter(record: dict) -> bool:
        if not record["extra"].get("audit"):
            return False
        return record["extra"].get("category") in enabled_categories

    handler_id = logger.add(
        str(audit_path),
        filter=audit_filter,
        format=_format_audit_record,
        level=_AUDIT_LEVEL,
    )
    return [handler_id]


def _enabled_categories(cfg: "AuditConfig") -> set[str]:
    cats = cfg.categories
    enabled: set[str] = set()
    if cats.ui:
        enabled.add("ui")
    if cats.action:
        enabled.add("action")
    if cats.dag:
        enabled.add("dag")
    if cats.study:
        enabled.add("study")
    return enabled


def _format_audit_record(record: dict) -> str:
    """Loguru format callable: return one JSON object per audit record.

    Loguru applies ``str.format_map(record)`` to the output of this
    function, so any literal ``{`` or ``}`` in the JSON would be treated
    as placeholders. Escape both to ``{{`` / ``}}``; ``format_map`` then
    collapses them back to literal braces in the final write.
    """
    extras = record["extra"]
    obj = {
        "ts": record["time"].astimezone(timezone.utc).isoformat(),
        "category": extras.get("category"),
        "event": extras.get("event"),
        "payload": extras.get("payload", {}),
    }
    line = json.dumps(obj, default=str).replace("{", "{{").replace("}", "}}")
    return line + "\n"
