"""Audit log configuration schema."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AuditCategoryToggles(BaseModel):
    """Per-category enabled toggles for the audit log.

    Each field corresponds to one :data:`slumber.runtime.audit.AuditCategory`.
    Disabled categories are filtered out at the loguru handler level.
    """

    model_config = ConfigDict(extra="forbid")

    ui: bool = Field(
        default=True,
        description="Record participant UI interactions (button clicks, page-emitted events).",
    )
    action: bool = Field(
        default=True,
        description="Record router-dispatched action invocations.",
    )
    dag: bool = Field(
        default=True,
        description="Record DAG and device lifecycle (started, stopped, errors).",
    )
    study: bool = Field(
        default=True,
        description="Record researcher-defined scientific/domain events.",
    )


class AuditConfig(BaseModel):
    """Audit log configuration.

    Audit records are routed through loguru: any code can call
    :func:`slumber.runtime.audit.record_event` and a configured handler
    writes a structured JSONL record to disk. Four categories are
    recognized — ``ui``, ``action``, ``dag``, ``study`` — and each can be
    independently disabled.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(
        default=True,
        description="Master switch for the audit log handler.",
    )
    path: str = Field(
        default="events.jsonl",
        description=(
            "Audit log file path. Relative paths resolve against the run "
            "directory; absolute paths are used as-is. Placeholders "
            "({study_id}, {condition_id}, {run_id}, {participant_id}, "
            "{session_id}) are expanded from the run context."
        ),
    )
    categories: AuditCategoryToggles = Field(
        default_factory=AuditCategoryToggles,
        description="Per-category enabled toggles.",
    )
