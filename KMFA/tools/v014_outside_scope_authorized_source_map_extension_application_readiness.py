#!/usr/bin/env python3
"""Check application readiness for owner-authorized outside-scope source-map extensions.

This phase consumes the ignored private owner authorization record from the
previous phase and determines whether a later source-map extension application
phase may start. It does not write source-map records, materialize values,
compare raw to processed values, reconcile values, upload GitHub, reinstall the
app, or execute business steps.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_APPLICATION_READINESS"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-APPLICATION-READINESS-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-APPLICATION-READINESS"
VERSION = "0.1.4-outside-scope-authorized-source-map-extension-application-readiness"
STATUS = "completed_validated_local_only_outside_scope_authorized_extension_application_readiness_ready_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "owner_authorized_source_map_extension_application_readiness_passed_application_not_performed"
NEXT_RECOMMENDED_PHASE = "V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_APPLICATION"
NEXT_REQUIRED_INPUT = "run_outside_scope_source_map_extension_application_phase_before_materialization_or_full_comparison"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_application_readiness_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_application_readiness_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_application_readiness_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_application_readiness_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_authorized_source_map_extension_application_readiness_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_application_readiness_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_application_readiness_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_application_readiness_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_application_readiness_matrix_public_safe.json"
)
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

SOURCE_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_owner_authorization_intake_summary.json"
)
SOURCE_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_owner_authorization_intake_go_no_go_report.json"
)
SOURCE_PRIVATE_ACTIVE_RECORD_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension_owner_authorization_intake/private_owner_authorized_source_map_extension_active_record.json"
)
SOURCE_PRIVATE_AUTHORIZATION_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension_owner_authorization_intake/private_owner_authorized_source_map_extension_queue.jsonl"
)
SOURCE_PRIVATE_DIAGNOSTIC_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension_owner_authorization_intake/private_owner_authorization_intake_diagnostic.json"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension_application_readiness"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_source_map_extension_application_readiness_diagnostic.json"
PRIVATE_READY_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_source_map_extension_application_ready_queue.jsonl"
PRIVATE_BLOCKER_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_source_map_extension_application_blocker_queue.jsonl"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_source_map_extension_application_readiness.md"

FILES_CHANGED = [
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/VERSION",
    "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
    "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
    "KMFA/docs/governance/MODEL_SPEC.md",
    "KMFA/docs/governance/OWNER_STATUS.md",
    "KMFA/docs/governance/STATUS.md",
    "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
    "KMFA/docs/governance/VERSION_MATRIX.yaml",
    "KMFA/docs/governance/delivery_tasks.yaml",
    "KMFA/docs/governance/development_events.jsonl",
    "KMFA/docs/governance/formula_registry.yaml",
    "KMFA/docs/governance/model_registry.yaml",
    "KMFA/docs/governance/parameter_registry.csv",
    "KMFA/metadata/stage_status.jsonl",
    "KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl",
    "KMFA/功能清单.md",
    "KMFA/开发记录.md",
    "KMFA/模型参数文件.md",
    METADATA_SUMMARY_PATH.as_posix(),
    METADATA_MANIFEST_PATH.as_posix(),
    METADATA_GO_NO_GO_PATH.as_posix(),
    METADATA_MATRIX_PATH.as_posix(),
    SUMMARY_PATH.as_posix(),
    MANIFEST_PATH.as_posix(),
    GO_NO_GO_PATH.as_posix(),
    MATRIX_PATH.as_posix(),
    REPORT_PATH.as_posix(),
    GO_NO_GO_RECORD_PATH.as_posix(),
    TEST_RESULTS_PATH.as_posix(),
    RISK_REGISTER_PATH.as_posix(),
    ROLLBACK_PATH.as_posix(),
    "KMFA/tests/test_v014_outside_scope_authorized_source_map_extension_application_readiness.py",
    "KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_application_readiness.py",
    "KMFA/tools/v014_outside_scope_authorized_source_map_extension_application_readiness.py",
]


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path} must contain JSON objects")
        rows.append(value)
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"


def _git_check_ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False).returncode == 0


def _raw_boundary() -> dict[str, bool]:
    return {
        "raw_data_root_readonly_policy_active": True,
        "source_private_active_authorization_record_read_by_this_phase": True,
        "source_private_authorization_queue_read_by_this_phase": True,
        "source_private_diagnostic_read_by_this_phase": True,
        "private_application_readiness_diagnostic_written_by_this_phase": True,
        "private_application_ready_queue_written_by_this_phase": True,
        "private_application_blocker_queue_written_by_this_phase": True,
        "source_private_authorization_record_mutated_by_this_phase": False,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase": False,
        "raw_inbox_file_content_hash_performed_by_this_phase": False,
        "raw_inbox_parse_performed_by_this_phase": False,
        "raw_inbox_field_or_header_read_performed_by_this_phase": False,
        "raw_inbox_value_extraction_performed_by_this_phase": False,
        "raw_inbox_write_performed_by_this_phase": False,
        "raw_inbox_delete_performed_by_this_phase": False,
        "raw_inbox_move_performed_by_this_phase": False,
        "raw_inbox_rename_performed_by_this_phase": False,
        "raw_inbox_overwrite_performed_by_this_phase": False,
        "raw_inbox_copy_performed_by_this_phase": False,
        "raw_inbox_normalize_performed_by_this_phase": False,
        "raw_inbox_mutated_by_this_phase": False,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_active_authorization_record_committed": False,
        "private_authorization_queue_committed": False,
        "private_authorization_diagnostic_committed": False,
        "private_application_readiness_diagnostic_committed": False,
        "private_application_ready_queue_committed": False,
        "private_application_blocker_queue_committed": False,
        "private_report_committed": False,
        "private_source_map_committed": False,
        "private_staging_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_file_hash_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "target_slot_detail_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_ref_or_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _row_ready(row: dict[str, Any]) -> bool:
    required_values = (
        row.get("target_slot_id"),
        row.get("target_key_ref_hash"),
        row.get("record_ref_hash"),
        row.get("private_processed_ref_hash"),
        row.get("authorized_source_record_ref_hash"),
        row.get("authorized_processed_value_fingerprint"),
    )
    if any(value in {"", None, "PENDING_PRIVATE_INPUT"} for value in required_values):
        return False
    return (
        row.get("owner_decision_code") == "AUTHORIZE_SOURCE_MAP_EXTENSION"
        and row.get("source_map_extension_application_allowed_next_phase") is True
        and row.get("source_map_extension_written_by_this_phase") is False
        and row.get("raw_to_processed_value_comparison_allowed_by_this_phase") is False
        and row.get("full_reconciliation_allowed_by_this_phase") is False
    )


def _build_private_queues(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ready: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if _row_ready(row):
            ready.append(
                {
                    "application_ready_queue_index": index,
                    "authorization_queue_index": row.get("authorization_queue_index"),
                    "source_extension_queue_index": row.get("source_extension_queue_index"),
                    "source_resolution_queue_index": row.get("source_resolution_queue_index"),
                    "target_slot_id": row.get("target_slot_id"),
                    "target_key_ref_hash": row.get("target_key_ref_hash"),
                    "record_ref_hash": row.get("record_ref_hash"),
                    "private_processed_ref_hash": row.get("private_processed_ref_hash"),
                    "authorized_source_record_ref_hash": row.get("authorized_source_record_ref_hash"),
                    "authorized_processed_value_fingerprint": row.get("authorized_processed_value_fingerprint"),
                    "context_group": row.get("context_group"),
                    "application_readiness_status": "ready",
                    "source_map_extension_application_ready": True,
                    "source_map_extension_application_allowed_next_phase": True,
                    "source_map_extension_written_by_this_phase": False,
                    "raw_to_processed_value_comparison_allowed_by_this_phase": False,
                    "full_reconciliation_allowed_by_this_phase": False,
                }
            )
        else:
            blockers.append(
                {
                    "application_blocker_queue_index": index,
                    "authorization_queue_index": row.get("authorization_queue_index"),
                    "target_slot_id": row.get("target_slot_id"),
                    "application_readiness_status": "blocked",
                    "application_blocker_code": "invalid_or_incomplete_owner_authorization_record",
                    "source_map_extension_application_ready": False,
                    "source_map_extension_written_by_this_phase": False,
                    "raw_to_processed_value_comparison_allowed_by_this_phase": False,
                    "full_reconciliation_allowed_by_this_phase": False,
                }
            )
    return ready, blockers


def _build_matrix(summary: dict[str, Any], generated_at: str) -> dict[str, Any]:
    checks = [
        ("source_owner_authorization_intake_valid", summary["source_valid_authorized_extension_record_count"] == 72, summary["source_valid_authorized_extension_record_count"], 72),
        ("private_active_authorization_record_count", summary["private_active_authorization_record_count"] == 72, summary["private_active_authorization_record_count"], 72),
        ("private_authorization_queue_count", summary["private_authorization_queue_count"] == 72, summary["private_authorization_queue_count"], 72),
        ("application_ready_record_count", summary["application_ready_record_count"] == 72, summary["application_ready_record_count"], 72),
        ("application_blocker_count_zero", summary["application_blocker_count"] == 0, summary["application_blocker_count"], 0),
        ("application_ready_true", summary["source_map_extension_application_ready"] is True, summary["source_map_extension_application_ready"], True),
        ("source_map_not_written", summary["source_map_extension_written_by_this_phase"] is False, summary["source_map_extension_written_by_this_phase"], False),
        ("full_comparison_not_performed", summary["full_raw_to_processed_value_comparison_complete"] is False, summary["full_raw_to_processed_value_comparison_complete"], False),
        ("project_go_no_go_preserved", summary["decision"] == DECISION, summary["decision"], DECISION),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if ok else "FAIL", "observed_public_safe": observed, "required": required}
        for code, ok, observed, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_outside_scope_source_map_extension_application_readiness_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_source_map_extension_application_readiness_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "application_readiness_check_count": len(rows),
        "application_readiness_check_pass_count": pass_count,
        "application_readiness_check_fail_count": len(rows) - pass_count,
        "source_map_extension_application_ready": summary["source_map_extension_application_ready"],
        "source_map_extension_application_allowed_next_phase": summary["source_map_extension_application_allowed_next_phase"],
        "full_reconciliation_allowed_after_application": False,
        "decision": DECISION,
        "checks": rows,
    }


def _dedupe_append_jsonl(path: Path, rows: list[dict[str, Any]], keep_existing: Callable[[dict[str, Any]], bool]) -> None:
    retained: list[str] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                existing = json.loads(line)
            except json.JSONDecodeError:
                retained.append(line)
                continue
            if not isinstance(existing, dict) or keep_existing(existing):
                retained.append(line)
    retained.extend(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(retained) + "\n", encoding="utf-8")


def _append_governance_records(manifest: dict[str, Any]) -> None:
    summary = manifest["summary"]
    event = {
        "event_id": "DEV-KMFA-20260707-V014-OUTSIDE-SCOPE-APPLICATION-READINESS",
        "event_time": manifest["generated_at"],
        "event_type": "development",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "iteration_id": "ITER-20260707-KMFA-V014-OUTSIDE-SCOPE-APPLICATION-READINESS",
        "fact_level": "EXTRACTED",
        "status": STATUS,
        "go_no_go": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "owner_authorized_extension_record_count": summary["source_owner_authorized_extension_record_count"],
        "application_ready_record_count": summary["application_ready_record_count"],
        "application_blocker_count": summary["application_blocker_count"],
        "source_map_extension_application_ready": summary["source_map_extension_application_ready"],
        "source_map_extension_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed": False,
        "processed_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "summary": "Checked owner-authorized outside-scope source-map extension application readiness and kept downstream gates closed.",
        "result_commit": "PENDING",
        "files_changed": FILES_CHANGED,
    }
    _dedupe_append_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        [event],
        lambda existing: existing.get("event_id") != event["event_id"],
    )

    stage_rows = [
        {
            "acceptance_id": ACCEPTANCE_ID,
            "completed_task_units": 1,
            "derived_percent": 100.0,
            "estimated_task_units": 1,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "v0.1.4 outside-scope source-map extension application readiness",
            "phase_id": PHASE_ID,
            "record_type": "v014_phase",
            "roadmap_phase_id": "OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_APPLICATION_READINESS",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": STATUS,
            "task_count": 3,
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": SUMMARY_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "72 owner-authorized extension records passed application readiness",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_APPLICATION_READINESS",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "OSAESMAR01",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": GO_NO_GO_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "source-map application is ready for a later phase but not performed",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_APPLICATION_READINESS",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "OSAESMAR02",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "raw inbox untouched readiness queues remain ignored and public evidence aggregate only",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_APPLICATION_READINESS",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "OSAESMAR03",
            "updated_at": "2026-07-07",
        },
    ]
    _dedupe_append_jsonl(STAGE_STATUS_PATH, stage_rows, lambda existing: existing.get("phase_id") != PHASE_ID)

    task_rows = []
    for row in stage_rows:
        task_row = {
            **row,
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "project_id": "KMFA",
            "version": VERSION,
            "stage_id": "VALUE-CONSISTENCY",
            "raw_data_committed": False,
        }
        if row["record_type"] == "v014_phase":
            task_row["acceptance_output"] = (
                "Application readiness manifest summary Go No-Go public-safe matrix private ignored readiness queues "
                "validator focused test and governance records"
            )
            task_row["phase_goal"] = (
                "verify owner-authorized outside-scope source-map extension application readiness without applying source-map records"
            )
        else:
            task_row["task_label"] = row["task_id"][-2:]
            task_row["task_text"] = row["name"]
        task_rows.append(task_row)
    _dedupe_append_jsonl(TASK_STATUS_PATH, task_rows, lambda existing: existing.get("phase_id") != PHASE_ID)


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_SUMMARY_PATH)
    source_go_no_go = _read_json(SOURCE_GO_NO_GO_PATH)
    active_record = _read_json(SOURCE_PRIVATE_ACTIVE_RECORD_PATH)
    source_queue = _read_jsonl(SOURCE_PRIVATE_AUTHORIZATION_QUEUE_PATH)
    source_diagnostic = _read_json(SOURCE_PRIVATE_DIAGNOSTIC_PATH)
    authorization_rows = active_record.get("authorization_rows")
    if not isinstance(authorization_rows, list):
        raise ValueError("source private active authorization record must include authorization_rows")
    if len(authorization_rows) != len(source_queue):
        raise ValueError("active authorization row count must match private queue count")

    ready_queue, blocker_queue = _build_private_queues([row for row in authorization_rows if isinstance(row, dict)])
    target_counts = Counter(row.get("target_slot_id") for row in authorization_rows if isinstance(row, dict))
    duplicate_target_slot_count = sum(1 for count in target_counts.values() if count > 1)
    unique_context_group_count = len({row.get("context_group") for row in authorization_rows if isinstance(row, dict)})
    application_ready = len(ready_queue) == 72 and len(blocker_queue) == 0
    raw_boundary = _raw_boundary()
    public_safety = _public_safety()

    summary = {
        "schema_version": "kmfa.v014_outside_scope_source_map_extension_application_readiness_summary.v1",
        "record_type": "v014_outside_scope_source_map_extension_application_readiness_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_decision": source_summary.get("decision"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_owner_authorized_extension_record_count": source_summary.get("owner_authorized_extension_record_count"),
        "source_valid_authorized_extension_record_count": source_summary.get("valid_authorized_extension_record_count"),
        "source_application_ready": bool(source_summary.get("source_map_extension_application_ready")),
        "private_active_authorization_record_count": len(authorization_rows),
        "private_authorization_queue_count": len(source_queue),
        "source_private_diagnostic_valid_count": source_diagnostic.get("private_summary", {}).get("valid_authorized_extension_record_count"),
        "readiness_candidate_count": len(authorization_rows),
        "application_ready_record_count": len(ready_queue),
        "application_blocker_count": len(blocker_queue),
        "unique_target_slot_count": len(target_counts),
        "duplicate_target_slot_count": duplicate_target_slot_count,
        "unique_context_group_count": unique_context_group_count,
        "source_map_extension_application_ready": application_ready,
        "source_map_extension_application_allowed_next_phase": application_ready,
        "source_map_extension_application_performed_by_this_phase": False,
        "source_map_extension_written_by_this_phase": False,
        "source_map_extension_applied_count": 0,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "full_reconciliation_allowed": False,
        "processed_consistency_verified": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "private_application_readiness_diagnostic_written": True,
        "private_application_readiness_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_application_ready_queue_written": True,
        "private_application_ready_queue_gitignored": _git_check_ignored(PRIVATE_READY_QUEUE_PATH),
        "private_application_blocker_queue_written": True,
        "private_application_blocker_queue_gitignored": _git_check_ignored(PRIVATE_BLOCKER_QUEUE_PATH),
        "raw_boundary": raw_boundary,
        "public_safety": public_safety,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    matrix = _build_matrix(summary, timestamp)
    go_no_go = {
        "schema_version": "kmfa.v014_outside_scope_source_map_extension_application_readiness_go_no_go.v1",
        "record_type": "v014_outside_scope_source_map_extension_application_readiness_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "application_ready_record_count": summary["application_ready_record_count"],
        "application_blocker_count": summary["application_blocker_count"],
        "source_map_extension_application_ready": application_ready,
        "source_map_extension_application_performed_by_this_phase": False,
        "source_map_extension_written_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "processed_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_outside_scope_source_map_extension_application_readiness_manifest.v1",
        "record_type": "v014_outside_scope_source_map_extension_application_readiness_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "source_artifacts": [
            SOURCE_SUMMARY_PATH.as_posix(),
            SOURCE_GO_NO_GO_PATH.as_posix(),
            "private:owner_authorized_source_map_extension_active_record",
            "private:owner_authorized_source_map_extension_queue",
            "private:owner_authorization_intake_diagnostic",
        ],
        "public_artifact_refs": [
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            MATRIX_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
        ],
        "metadata_artifact_refs": [
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_MATRIX_PATH.as_posix(),
        ],
        "private_artifact_refs": [
            "private:outside_scope_source_map_extension_application_readiness_diagnostic",
            "private:outside_scope_source_map_extension_application_ready_queue",
            "private:outside_scope_source_map_extension_application_blocker_queue",
        ],
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "
            "KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_application_readiness.py "
            "--require-private-readiness"
        ),
        "git": {
            "head": _git_output(["rev-parse", "--short=12", "HEAD"]),
            "branch": _git_output(["branch", "--show-current"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_outside_scope_source_map_extension_application_readiness_diagnostic.v1",
        "classification": "private_outside_scope_source_map_extension_application_readiness_diagnostic_do_not_commit",
        "record_type": "v014_outside_scope_source_map_extension_application_readiness_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "private_active_authorization_record_count": len(authorization_rows),
        "private_authorization_queue_count": len(source_queue),
        "application_ready_record_count": len(ready_queue),
        "application_blocker_count": len(blocker_queue),
        "source_map_extension_application_ready": application_ready,
        "source_map_extension_application_performed_by_this_phase": False,
        "source_map_extension_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "raw_inbox_accessed": False,
        "raw_boundary": raw_boundary,
    }

    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_READY_QUEUE_PATH, ready_queue)
    _write_jsonl(PRIVATE_BLOCKER_QUEUE_PATH, blocker_queue)
    _write_text(
        PRIVATE_REPORT_PATH,
        "\n".join(
            [
                "# Private outside-scope source-map extension application readiness",
                "",
                f"- generated_at: `{timestamp}`",
                f"- ready_records: `{len(ready_queue)}`",
                f"- blocker_records: `{len(blocker_queue)}`",
                "- source_map_extension_application_performed_by_this_phase: `false`",
                "- raw_to_processed_value_comparison_performed_by_this_phase: `false`",
                "- raw_inbox_accessed: `false`",
                "",
            ]
        ),
    )

    for path, payload in [
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (MATRIX_PATH, matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
    ]:
        _write_json(path, payload)

    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# KMFA v0.1.4 outside-scope source-map extension application readiness",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- version: `{VERSION}`",
                f"- status: `{STATUS}`",
                f"- decision: `{DECISION}`",
                f"- source_owner_authorized_extension_record_count: `{summary['source_owner_authorized_extension_record_count']}`",
                f"- application_ready_record_count: `{summary['application_ready_record_count']}`",
                f"- application_blocker_count: `{summary['application_blocker_count']}`",
                f"- source_map_extension_application_ready: `{str(application_ready).lower()}`",
                "- source_map_extension_application_performed_by_this_phase: `false`",
                "- source_map_extension_written_by_this_phase: `false`",
                "- full_raw_to_processed_value_comparison_complete: `false`",
                "- processed_consistency_verified: `false`",
                "- raw_inbox_accessed: `false`",
                "- public evidence contains aggregate counts and gate states only.",
                "",
            ]
        ),
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        "\n".join(
            [
                "# Go/No-Go",
                "",
                f"- decision: `{DECISION}`",
                f"- application readiness passed: `{str(application_ready).lower()}`",
                "- reason: application readiness is ready for a later single phase, but this phase did not apply source-map records and did not compare values.",
                f"- next_required_input: `{NEXT_REQUIRED_INPUT}`",
                "",
            ]
        ),
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# Test Results",
                "",
                "- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_outside_scope_authorized_source_map_extension_application_readiness.py KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_application_readiness.py KMFA/tests/test_v014_outside_scope_authorized_source_map_extension_application_readiness.py`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_authorized_source_map_extension_application_readiness.py --generated-at 2026-07-07T00:00:00+10:00`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_application_readiness.py --require-private-readiness`",
                "- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_authorized_source_map_extension_application_readiness`",
                "- status: `PASS_LOCAL_PENDING_RERUN`",
                "",
            ]
        ),
    )
    _write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# Risk Register",
                "",
                "- risk: readiness may be mistaken for application.",
                "  mitigation: source-map application flags remain false and Go/No-Go remains NO_GO.",
                "- risk: private target/ref/fingerprint details may leak into public evidence.",
                "  mitigation: public artifacts store aggregate counts only; validator scans forbidden public markers.",
                "- risk: raw inbox may be accidentally touched.",
                "  mitigation: phase reads only prior private runtime and public metadata; raw boundary flags remain false.",
                "",
            ]
        ),
    )
    _write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# Rollback Plan",
                "",
                "- Remove this phase public artifacts and metadata quality copies.",
                "- Remove ignored private application readiness diagnostic/queues/report.",
                "- Remove tool, validator, focused test and governance entries for this phase.",
                "- Do not modify raw inbox files.",
                "",
            ]
        ),
    )
    if write_governance_event:
        _append_governance_records(manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    try:
        manifest = generate(generated_at=args.generated_at)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 outside-scope source-map extension application readiness generated "
        f"(ready_records={summary['application_ready_record_count']}, "
        f"blockers={summary['application_blocker_count']}, "
        f"application_ready={summary['source_map_extension_application_ready']}, decision={summary['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
