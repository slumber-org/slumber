"""Tests for the audit log."""

from __future__ import annotations

import json
from pathlib import Path

from loguru import logger

from slumber.runtime.audit import (
    configure_audit_logging,
    record_event,
    resolve_audit_path,
)
from slumber.runtime.run import RunContext
from slumber.schemas.audit import AuditCategoryToggles, AuditConfig
from slumber.schemas.study import Study


def _ctx() -> RunContext:
    return RunContext(
        study_id="s1",
        run_id="r1",
        condition_id="ctrl",
        participant_id="p1",
        session_id="ses1",
    )


def _study(audit: AuditConfig | None = None) -> Study:
    return Study(study_id="s1", name="S1", audit=audit or AuditConfig())


def _read_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


class TestConfigureAuditLogging:
    def test_writes_jsonl_record_with_required_fields(self, tmp_path: Path) -> None:
        handlers = configure_audit_logging(_study(), _ctx(), tmp_path)
        try:
            record_event("ui", "welcome.start", {"foo": 1})
        finally:
            for hid in handlers:
                logger.remove(hid)

        records = _read_records(tmp_path / "events.jsonl")
        assert len(records) == 1
        record = records[0]
        assert set(record) == {"ts", "category", "event", "payload"}
        assert record["category"] == "ui"
        assert record["event"] == "welcome.start"
        assert record["payload"] == {"foo": 1}

    def test_appends_records_across_categories(self, tmp_path: Path) -> None:
        handlers = configure_audit_logging(_study(), _ctx(), tmp_path)
        try:
            record_event("ui", "welcome.start")
            record_event("action", "open_page", {"page": "procedure"})
            record_event("dag", "started", {"name": "acquisition"})
            record_event("study", "sleep_onset", {"epoch": 42})
        finally:
            for hid in handlers:
                logger.remove(hid)

        records = _read_records(tmp_path / "events.jsonl")
        assert [r["category"] for r in records] == ["ui", "action", "dag", "study"]
        assert records[3]["payload"] == {"epoch": 42}

    def test_master_disable_returns_no_handlers(self, tmp_path: Path) -> None:
        handlers = configure_audit_logging(
            _study(AuditConfig(enabled=False)), _ctx(), tmp_path
        )
        assert handlers == []
        record_event("ui", "welcome.start")  # should not write anywhere
        assert not (tmp_path / "events.jsonl").exists()

    def test_per_category_toggle(self, tmp_path: Path) -> None:
        cfg = AuditConfig(
            categories=AuditCategoryToggles(
                ui=True, action=False, dag=True, study=False
            )
        )
        handlers = configure_audit_logging(_study(cfg), _ctx(), tmp_path)
        try:
            record_event("ui", "welcome.start")
            record_event("action", "open_page")
            record_event("dag", "started")
            record_event("study", "sleep_onset")
        finally:
            for hid in handlers:
                logger.remove(hid)

        records = _read_records(tmp_path / "events.jsonl")
        assert [r["category"] for r in records] == ["ui", "dag"]

    def test_handler_removal_stops_writes(self, tmp_path: Path) -> None:
        handlers = configure_audit_logging(_study(), _ctx(), tmp_path)
        record_event("ui", "first")
        for hid in handlers:
            logger.remove(hid)
        record_event("ui", "second")  # post-teardown — must not appear

        records = _read_records(tmp_path / "events.jsonl")
        assert [r["event"] for r in records] == ["first"]

    def test_record_event_without_handler_does_not_raise(self, tmp_path: Path) -> None:
        # No handler configured — record_event still works (no-op for audit file).
        record_event("study", "sleep_onset", {"epoch": 1})
        assert not (tmp_path / "events.jsonl").exists()


class TestResolveAuditPath:
    def test_relative_path_joins_run_dir(self, tmp_path: Path) -> None:
        cfg = AuditConfig(path="events.jsonl")
        path = resolve_audit_path(cfg, _ctx(), tmp_path)
        assert path == tmp_path / "events.jsonl"

    def test_absolute_path_kept(self, tmp_path: Path) -> None:
        elsewhere = tmp_path / "elsewhere" / "audit.jsonl"
        cfg = AuditConfig(path=str(elsewhere))
        path = resolve_audit_path(cfg, _ctx(), tmp_path)
        assert path == elsewhere

    def test_placeholders_expand(self, tmp_path: Path) -> None:
        cfg = AuditConfig(path="audit-{run_id}-{participant_id}.jsonl")
        path = resolve_audit_path(cfg, _ctx(), tmp_path)
        assert path == tmp_path / "audit-r1-p1.jsonl"

    def test_relative_subdir_joins_run_dir(self, tmp_path: Path) -> None:
        cfg = AuditConfig(path="audit/events.jsonl")
        path = resolve_audit_path(cfg, _ctx(), tmp_path)
        assert path == tmp_path / "audit" / "events.jsonl"
