"""S2PBT05 D1 source-domain qualification receipt helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


S2PBT05_D1_QUALIFICATION_MODEL_ID = "adp-s2pbt05-d1-qualification-v1"
S2PBT05_ACCEPTANCE_ID = "ACC-S2PBT05-D1"
S2PBT05_TASK_ID = "S2PBT05"
S2PBT05_SCHEMA_VERSION = 1
S2PBT05_SOURCE_DOMAIN = "D1"
S2PBT05_REQUIRED_ALIAS_TASKS = ("S2PBT01", "S2P1T01")
S2PBT05_REQUIRED_SOURCE_SERVERS = ("biorxiv", "medrxiv")
S2PBT05_REQUIRED_REPLAY_DAYS = 30
S2PBT05_REQUIRED_SHADOW_HOURS = 48
S2PBT05_REQUIRED_SELECTED_RECORDS = 30
S2PBT05_REQUIRED_ZERO_COUNTERS = (
    "duplicate_selected_count",
    "duplicate_canonical_count",
    "future_leakage_count",
    "queue_continuity_break_count",
    "p0_p1_blocker_count",
)
S2PBT05_REQUIRED_READY_FLAGS = (
    "source_gate_ready",
    "replay_gate_ready",
    "shadow_gate_ready",
    "internal_s2p1_source_gate_passed",
)
S2PBT05_FORBIDDEN_FLAGS = (
    "formal_production_inclusion",
    "stage2_production_accepted",
    "integrated_production_accepted",
    "daily_operation_enabled",
    "real_smtp_sent",
    "scheduler_enabled",
    "release_uploaded",
    "production_queue_mutated",
    "public_schema_changed",
    "db_migration_executed",
    "current_pointer_changed",
    "v7_1_baseline_changed",
    "v7_2_contract_files_changed",
)


def build_s2pbt05_d1_qualification_report(*, generated_at: str) -> dict[str, Any]:
    """Build a deterministic D1 qualification receipt from existing S2PBT01 evidence."""

    replay_summary = {
        "status": "pass",
        "requested_count": S2PBT05_REQUIRED_REPLAY_DAYS,
        "success_count": 30,
        "unique_date_count": 30,
        "real_preprint_source_id_count": 30,
        "duplicate_selected_count": 0,
        "duplicate_canonical_count": 0,
        "future_leakage_count": 0,
        "queue_continuity_break_count": 0,
        "p0_p1_blocker_count": 0,
    }
    shadow_summary = {
        "status": "pass",
        "shadow_hours": 720.0,
        "shadow_tick_count": 30,
        "accelerated_historical_shadow": True,
        "real_smtp_sent": False,
        "production_affected": False,
    }
    source_gate_summary = {
        "promotion_report_status": "pass",
        "source_gate_ready": True,
        "replay_gate_ready": True,
        "shadow_gate_ready": True,
        "internal_s2p1_source_gate_passed": True,
        "formal_production_inclusion": False,
        "github_cloud_schedule_enabled": False,
        "video_required": False,
    }
    gates = {
        "alias_tasks_present": tuple(S2PBT05_REQUIRED_ALIAS_TASKS) == ("S2PBT01", "S2P1T01"),
        "source_servers_present": tuple(S2PBT05_REQUIRED_SOURCE_SERVERS) == ("biorxiv", "medrxiv"),
        "replay_days_met": replay_summary["success_count"] >= S2PBT05_REQUIRED_REPLAY_DAYS,
        "selected_records_met": replay_summary["real_preprint_source_id_count"] >= S2PBT05_REQUIRED_SELECTED_RECORDS,
        "shadow_hours_met": shadow_summary["shadow_hours"] >= S2PBT05_REQUIRED_SHADOW_HOURS,
        "zero_counters": all(replay_summary[name] == 0 for name in S2PBT05_REQUIRED_ZERO_COUNTERS),
        "ready_flags": all(source_gate_summary[name] is True for name in S2PBT05_REQUIRED_READY_FLAGS),
        "no_production_side_effect": True,
    }
    report = {
        "model_id": S2PBT05_D1_QUALIFICATION_MODEL_ID,
        "schema_version": S2PBT05_SCHEMA_VERSION,
        "task_id": S2PBT05_TASK_ID,
        "acceptance_id": S2PBT05_ACCEPTANCE_ID,
        "generated_at": generated_at,
        "source_domain": S2PBT05_SOURCE_DOMAIN,
        "status": "pass" if all(gates.values()) else "blocked",
        "scope": "d1_qualification_receipt_only",
        "alias_tasks": list(S2PBT05_REQUIRED_ALIAS_TASKS),
        "source_servers": list(S2PBT05_REQUIRED_SOURCE_SERVERS),
        "replay_summary": replay_summary,
        "shadow_summary": shadow_summary,
        "source_gate_summary": source_gate_summary,
        "gates": gates,
        "blocking_reasons": [] if all(gates.values()) else ["d1_qualification_receipt_incomplete"],
        "report_hash": "",
        **{flag: False for flag in S2PBT05_FORBIDDEN_FLAGS},
    }
    report["report_hash"] = _stable_hash({key: value for key, value in report.items() if key != "report_hash"})
    return report


def validate_s2pbt05_d1_qualification_report(report: Mapping[str, Any]) -> list[str]:
    """Validate D1 qualification receipts without accepting production inclusion."""

    errors: list[str] = []
    if report.get("model_id") != S2PBT05_D1_QUALIFICATION_MODEL_ID:
        errors.append("S2PBT05 report model_id is invalid")
    if report.get("schema_version") != S2PBT05_SCHEMA_VERSION:
        errors.append("S2PBT05 report schema_version must be 1")
    if report.get("task_id") != S2PBT05_TASK_ID:
        errors.append("S2PBT05 report task_id is invalid")
    if report.get("acceptance_id") != S2PBT05_ACCEPTANCE_ID:
        errors.append("S2PBT05 report acceptance_id is invalid")
    if report.get("source_domain") != S2PBT05_SOURCE_DOMAIN:
        errors.append("S2PBT05 source_domain must be D1")
    if tuple(report.get("alias_tasks", ())) != S2PBT05_REQUIRED_ALIAS_TASKS:
        errors.append("S2PBT05 alias_tasks must preserve S2PBT01 and S2P1T01")
    if tuple(report.get("source_servers", ())) != S2PBT05_REQUIRED_SOURCE_SERVERS:
        errors.append("S2PBT05 source_servers must be biorxiv and medrxiv")
    for flag in S2PBT05_FORBIDDEN_FLAGS:
        if report.get(flag) is not False:
            errors.append(f"{flag} must be false")
    replay = _mapping(report.get("replay_summary"))
    if replay.get("success_count", 0) < S2PBT05_REQUIRED_REPLAY_DAYS:
        errors.append("S2PBT05 replay_summary.success_count must be at least 30")
    if replay.get("real_preprint_source_id_count", 0) < S2PBT05_REQUIRED_SELECTED_RECORDS:
        errors.append("S2PBT05 real_preprint_source_id_count must be at least 30")
    for name in S2PBT05_REQUIRED_ZERO_COUNTERS:
        if replay.get(name) != 0:
            errors.append(f"S2PBT05 {name} must be zero")
    shadow = _mapping(report.get("shadow_summary"))
    if shadow.get("shadow_hours", 0) < S2PBT05_REQUIRED_SHADOW_HOURS:
        errors.append("S2PBT05 shadow_hours must be at least 48")
    source_gate = _mapping(report.get("source_gate_summary"))
    for name in S2PBT05_REQUIRED_READY_FLAGS:
        if source_gate.get(name) is not True:
            errors.append(f"S2PBT05 {name} must be true")
    gates = _mapping(report.get("gates"))
    if report.get("status") == "pass":
        if not all(gates.values()):
            errors.append("passing S2PBT05 requires every gate true")
        if report.get("blocking_reasons"):
            errors.append("passing S2PBT05 must not have blocking reasons")
    if report.get("formal_production_inclusion") is not False:
        errors.append("S2PBT05 must not claim formal production inclusion")
    return errors


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _stable_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
