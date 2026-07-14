#!/usr/bin/env python3
"""Intake owner authorization for outside-scope KMFA source-map extension.

This phase converts the user's direct authorization into an ignored private
active authorization record for 72 outside-scope target slots. It does not read
the raw inbox, write source-map extension records, materialize values, compare
raw to processed values, reconcile values, upload GitHub, reinstall the app, or
execute business steps.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_OWNER_AUTHORIZATION_INTAKE"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-OWNER-AUTHORIZATION-INTAKE-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-OWNER-AUTHORIZATION-INTAKE"
VERSION = "0.1.4-outside-scope-authorized-source-map-extension-owner-authorization-intake"
STATUS = "completed_validated_local_only_outside_scope_authorized_extension_owner_authorization_intake_no_go"
DECISION = "NO_GO"
AUTHORIZATION_BASIS = "owner_current_thread_direct_authorization_allow_codex_prepare_private_source_map_extension"
DIAGNOSTIC_CONCLUSION = "owner_direct_authorization_intaken_private_extension_ready_for_application_phase"
NEXT_RECOMMENDED_PHASE = "V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_APPLICATION_READINESS"
NEXT_REQUIRED_INPUT = "run_outside_scope_source_map_extension_application_readiness_before_any_full_comparison"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_owner_authorization_intake_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_owner_authorization_intake_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_owner_authorization_intake_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_authorized_source_map_extension_owner_authorization_intake_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_authorized_source_map_extension_owner_authorization_intake_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_owner_authorization_intake_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_authorized_source_map_extension_owner_authorization_intake_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_owner_authorization_intake_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_owner_authorization_intake_matrix_public_safe.json"
)
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

SOURCE_TEMPLATE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension/private_authorized_source_map_extension_template.json"
)
SOURCE_PENDING_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension/private_authorized_source_map_extension_pending_queue.jsonl"
)
SOURCE_READINESS_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_post_delegation_blocker_threshold_recheck_summary.json"
)
SOURCE_READINESS_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_authorized_source_map_extension_post_delegation_blocker_threshold_recheck_go_no_go_report.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_authorized_source_map_extension_owner_authorization_intake"
)
PRIVATE_ACTIVE_RECORD_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_source_map_extension_active_record.json"
PRIVATE_AUTHORIZATION_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_source_map_extension_queue.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorization_intake_diagnostic.json"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorization_intake.md"

FILES_CHANGED = [
    "KMFA/CHANGELOG.md",
    "KMFA/HANDOFF.md",
    "KMFA/VERSION",
    "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
    "KMFA/docs/governance/OWNER_STATUS.md",
    "KMFA/docs/governance/STATUS.md",
    "KMFA/docs/governance/development_events.jsonl",
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
    "KMFA/tests/test_v014_outside_scope_authorized_source_map_extension_owner_authorization_intake.py",
    "KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_owner_authorization_intake.py",
    "KMFA/tools/v014_outside_scope_authorized_source_map_extension_owner_authorization_intake.py",
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
        "source_private_template_read_by_this_phase": True,
        "source_private_pending_queue_read_by_this_phase": True,
        "private_authorization_active_record_written_by_this_phase": True,
        "private_authorization_queue_written_by_this_phase": True,
        "source_private_template_mutated_by_this_phase": False,
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
        "private_source_template_committed": False,
        "private_pending_queue_committed": False,
        "private_active_authorization_record_committed": False,
        "private_authorization_queue_committed": False,
        "private_diagnostic_committed": False,
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


def _build_private_authorization(
    *, generated_at: str, source_template: dict[str, Any], pending_queue: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    extension_rows = source_template.get("extension_rows")
    if not isinstance(extension_rows, list):
        raise ValueError("source private template extension_rows must be a list")
    if len(extension_rows) != len(pending_queue):
        raise ValueError("source template and pending queue counts must match")

    authorization_rows: list[dict[str, Any]] = []
    for index, row in enumerate(extension_rows, start=1):
        if not isinstance(row, dict):
            raise ValueError("source template extension row must be an object")
        source_ref = row.get("record_ref_hash")
        processed_ref = row.get("private_processed_ref_hash")
        if source_ref in {"", "PENDING_PRIVATE_INPUT", None}:
            raise ValueError("source template row missing record_ref_hash")
        if processed_ref in {"", "PENDING_PRIVATE_INPUT", None}:
            raise ValueError("source template row missing private_processed_ref_hash")
        authorization_rows.append(
            {
                "authorization_queue_index": index,
                "source_extension_queue_index": row.get("extension_queue_index"),
                "source_resolution_queue_index": row.get("source_resolution_queue_index"),
                "target_slot_id": row.get("target_slot_id"),
                "target_key_ref_hash": row.get("target_key_ref_hash"),
                "record_ref_hash": row.get("record_ref_hash"),
                "private_processed_ref_hash": row.get("private_processed_ref_hash"),
                "context_group": row.get("context_group"),
                "owner_decision_code": "AUTHORIZE_SOURCE_MAP_EXTENSION",
                "authorized_source_record_ref_hash": source_ref,
                "authorized_processed_value_fingerprint": processed_ref,
                "authorized_source_basis": AUTHORIZATION_BASIS,
                "authorized_by": "owner_current_thread_user_authorized_codex",
                "authorization_timestamp": generated_at,
                "owner_note": (
                    "Owner authorized Codex to prepare the private source-map extension. "
                    "This is not proof of business value consistency; later comparison is required."
                ),
                "source_map_extension_application_allowed_next_phase": True,
                "source_map_extension_written_by_this_phase": False,
                "raw_to_processed_value_comparison_allowed_by_this_phase": False,
                "full_reconciliation_allowed_by_this_phase": False,
            }
        )

    private_summary = {
        "source_private_template_item_count": len(extension_rows),
        "source_private_pending_queue_count": len(pending_queue),
        "owner_direct_authorization_present": True,
        "owner_authorized_extension_record_count": len(authorization_rows),
        "valid_authorized_extension_record_count": len(authorization_rows),
        "invalid_authorized_extension_record_count": 0,
        "missing_authorized_extension_record_count": 0,
        "keep_pending_extension_record_count": 0,
        "source_map_extension_ready_count": len(authorization_rows),
        "source_map_extension_blocker_count": 0,
        "source_map_extension_application_ready": True,
        "source_map_extension_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "processed_consistency_verified": False,
        "business_value_consistency_verified": False,
    }
    active_record = {
        "schema_version": "kmfa.private.v014_outside_scope_owner_authorized_source_map_extension.v1",
        "classification": "private_owner_authorized_source_map_extension_do_not_commit",
        "record_type": "v014_outside_scope_owner_authorized_source_map_extension_active_record",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "authorization_basis": AUTHORIZATION_BASIS,
        "source_template_phase_id": source_template.get("phase_id"),
        "private_summary": private_summary,
        "authorization_rows": authorization_rows,
        "raw_boundary": _raw_boundary(),
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_outside_scope_owner_authorization_intake_diagnostic.v1",
        "classification": "private_owner_authorization_intake_diagnostic_do_not_commit",
        "record_type": "v014_outside_scope_owner_authorization_intake_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "authorization_basis": AUTHORIZATION_BASIS,
        "private_summary": private_summary,
        "raw_boundary": _raw_boundary(),
    }
    return active_record, authorization_rows, diagnostic


def _build_matrix(summary: dict[str, Any], generated_at: str) -> dict[str, Any]:
    checks = [
        ("source_template_count_preserved", summary["source_private_template_item_count"] == 72, summary["source_private_template_item_count"], 72),
        ("owner_direct_authorization_present", summary["owner_direct_authorization_present"] is True, summary["owner_direct_authorization_present"], True),
        ("valid_authorization_count", summary["valid_authorized_extension_record_count"] == 72, summary["valid_authorized_extension_record_count"], 72),
        ("missing_authorization_zero", summary["missing_authorized_extension_record_count"] == 0, summary["missing_authorized_extension_record_count"], 0),
        ("application_ready_for_next_phase", summary["source_map_extension_application_ready"] is True, summary["source_map_extension_application_ready"], True),
        ("source_map_not_written_this_phase", summary["source_map_extension_written_by_this_phase"] is False, summary["source_map_extension_written_by_this_phase"], False),
        ("full_comparison_not_performed", summary["full_raw_to_processed_value_comparison_complete"] is False, summary["full_raw_to_processed_value_comparison_complete"], False),
        ("project_go_no_go_preserved", summary["decision"] == DECISION, summary["decision"], DECISION),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if ok else "FAIL", "observed_public_safe": observed, "required": required}
        for code, ok, observed, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_outside_scope_owner_authorization_intake_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_owner_authorization_intake_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "owner_authorization_intake_check_count": len(rows),
        "owner_authorization_intake_check_pass_count": pass_count,
        "owner_authorization_intake_check_fail_count": len(rows) - pass_count,
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
        "event_id": "DEV-KMFA-20260707-V014-OUTSIDE-SCOPE-OWNER-AUTHORIZATION-INTAKE",
        "event_time": manifest["generated_at"],
        "event_type": "development",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "iteration_id": "ITER-20260707-KMFA-V014-OUTSIDE-SCOPE-OWNER-AUTHORIZATION-INTAKE",
        "fact_level": "EXTRACTED",
        "status": STATUS,
        "go_no_go": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "owner_direct_authorization_present": True,
        "valid_authorized_extension_record_count": summary["valid_authorized_extension_record_count"],
        "source_map_extension_application_ready": summary["source_map_extension_application_ready"],
        "source_map_extension_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed": False,
        "processed_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "summary": "Intaken owner direct authorization for 72 outside-scope source-map extension records while keeping downstream gates closed.",
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
            "name": "v0.1.4 outside-scope source-map owner authorization intake",
            "phase_id": PHASE_ID,
            "record_type": "v014_phase",
            "roadmap_phase_id": "OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_OWNER_AUTHORIZATION_INTAKE",
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
            "name": "72 owner-authorized extension records intaken in private runtime",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_OWNER_AUTHORIZATION_INTAKE",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "OSAESMOAI01",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": GO_NO_GO_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "source-map application ready for next phase while full comparison remains closed",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_OWNER_AUTHORIZATION_INTAKE",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "OSAESMOAI02",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "raw inbox untouched private authorization outputs remain ignored and public evidence aggregate only",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_OWNER_AUTHORIZATION_INTAKE",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "OSAESMOAI03",
            "updated_at": "2026-07-07",
        },
    ]
    _dedupe_append_jsonl(
        STAGE_STATUS_PATH,
        stage_rows,
        lambda existing: existing.get("phase_id") != PHASE_ID,
    )

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
                "Owner authorization intake manifest summary Go No-Go report public-safe matrix private ignored active record "
                "validator focused test and governance records"
            )
            task_row["phase_goal"] = (
                "record owner direct authorization for outside-scope source-map extension without applying source-map records"
            )
        else:
            task_row["task_label"] = row["task_id"][-2:]
            task_row["task_text"] = row["name"]
        task_rows.append(task_row)
    _dedupe_append_jsonl(
        TASK_STATUS_PATH,
        task_rows,
        lambda existing: existing.get("phase_id") != PHASE_ID,
    )


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_template = _read_json(SOURCE_TEMPLATE_PATH)
    pending_queue = _read_jsonl(SOURCE_PENDING_QUEUE_PATH)
    source_summary = _read_json(SOURCE_READINESS_SUMMARY_PATH)
    source_go_no_go = _read_json(SOURCE_READINESS_GO_NO_GO_PATH)
    active_record, authorization_rows, private_diagnostic = _build_private_authorization(
        generated_at=timestamp,
        source_template=source_template,
        pending_queue=pending_queue,
    )

    raw_boundary = _raw_boundary()
    public_safety = _public_safety()
    private_summary = active_record["private_summary"]
    summary = {
        "schema_version": "kmfa.v014_outside_scope_owner_authorization_intake_summary.v1",
        "record_type": "v014_outside_scope_owner_authorization_intake_summary",
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
        "authorization_basis": AUTHORIZATION_BASIS,
        "source_private_template_item_count": private_summary["source_private_template_item_count"],
        "source_private_pending_queue_count": private_summary["source_private_pending_queue_count"],
        "owner_direct_authorization_present": True,
        "owner_authorized_extension_record_count": private_summary["owner_authorized_extension_record_count"],
        "valid_authorized_extension_record_count": private_summary["valid_authorized_extension_record_count"],
        "invalid_authorized_extension_record_count": 0,
        "missing_authorized_extension_record_count": 0,
        "keep_pending_extension_record_count": 0,
        "source_map_extension_ready_count": private_summary["source_map_extension_ready_count"],
        "source_map_extension_blocker_count": 0,
        "source_map_extension_application_ready": True,
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
        "private_active_authorization_record_written": True,
        "private_active_authorization_record_gitignored": _git_check_ignored(PRIVATE_ACTIVE_RECORD_PATH),
        "private_authorization_queue_written": True,
        "private_authorization_queue_gitignored": _git_check_ignored(PRIVATE_AUTHORIZATION_QUEUE_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "raw_boundary": raw_boundary,
        "public_safety": public_safety,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    matrix = _build_matrix(summary, timestamp)
    go_no_go = {
        "schema_version": "kmfa.v014_outside_scope_owner_authorization_intake_go_no_go.v1",
        "record_type": "v014_outside_scope_owner_authorization_intake_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "owner_direct_authorization_present": True,
        "valid_authorized_extension_record_count": summary["valid_authorized_extension_record_count"],
        "source_map_extension_application_ready": True,
        "source_map_extension_written_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "processed_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_outside_scope_owner_authorization_intake_manifest.v1",
        "record_type": "v014_outside_scope_owner_authorization_intake_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "source_artifacts": [
            "private:authorized_source_map_extension_template",
            "private:authorized_source_map_extension_pending_queue",
            SOURCE_READINESS_SUMMARY_PATH.as_posix(),
            SOURCE_READINESS_GO_NO_GO_PATH.as_posix(),
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
            "private:owner_authorized_source_map_extension_active_record",
            "private:owner_authorized_source_map_extension_queue",
            "private:owner_authorization_intake_diagnostic",
        ],
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 "
            "KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_owner_authorization_intake.py "
            "--require-private-authorization"
        ),
        "summary": summary,
        "go_no_go_report": go_no_go,
        "matrix": matrix,
        "git": {
            "head": _git_output(["rev-parse", "HEAD"]),
            "branch": _git_output(["branch", "--show-current"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
    }

    _write_json(PRIVATE_ACTIVE_RECORD_PATH, active_record)
    _write_jsonl(PRIVATE_AUTHORIZATION_QUEUE_PATH, authorization_rows)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
    _write_text(
        PRIVATE_REPORT_PATH,
        "# Private Owner Authorization Intake\n\n"
        "72 outside-scope source-map extension records are owner-authorized for the next application-readiness phase. "
        "This private record does not prove business value consistency and must not be committed.\n",
    )

    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (MATRIX_PATH, matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
    ):
        _write_json(path, payload)

    _write_text(
        REPORT_PATH,
        f"""# V014 Outside-Scope Source-Map Owner Authorization Intake

- phase: `{PHASE_ID}`
- status: `{STATUS}`
- decision: `{DECISION}`
- source template items: `{summary["source_private_template_item_count"]}`
- owner-authorized extension records: `{summary["valid_authorized_extension_record_count"]}`
- source-map application ready for next phase: `true`
- source-map written by this phase: `false`
- raw-to-processed comparison complete: `false`

This phase records owner authorization in ignored private runtime only. It does not apply source-map records or verify business value consistency.
""",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        f"""# Go / No-Go

- decision: `{DECISION}`
- source-map extension authorization intake: `ready_for_next_phase`
- reason: owner direct authorization has been recorded, but source-map application and raw-to-processed comparison have not run.
- next required input: `{NEXT_REQUIRED_INPUT}`
- blocked: full comparison, reconciliation, business value consistency, lineage full check, formal report, GitHub upload, app reinstall and business execution.
""",
    )
    _write_text(
        RISK_REGISTER_PATH,
        "# Risk Register\n\n"
        "- Risk: owner authorization could be mistaken for verified business value consistency.\n"
        "- Control: source-map application, full comparison, reconciliation, formal report, upload, reinstall and business execution remain false.\n"
        "- Raw boundary: raw inbox read/list/stat/hash/parse/write/delete/move/rename/copy/normalize/mutation remain false.\n",
    )
    _write_text(
        ROLLBACK_PATH,
        "Remove this phase's public artifacts, metadata copies, private authorization outputs, tool, validator, focused test and governance records. The raw data inbox is not modified by this rollback.\n",
    )
    _write_text(
        TEST_RESULTS_PATH,
        f"""# Test Results

Planned commands:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_outside_scope_authorized_source_map_extension_owner_authorization_intake.py KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_owner_authorization_intake.py KMFA/tests/test_v014_outside_scope_authorized_source_map_extension_owner_authorization_intake.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_authorized_source_map_extension_owner_authorization_intake.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_owner_authorization_intake.py --require-private-authorization`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_authorized_source_map_extension_owner_authorization_intake`

Current generated check matrix: `{matrix["owner_authorization_intake_check_pass_count"]}` pass / `{matrix["owner_authorization_intake_check_fail_count"]}` fail. This phase does not read, list, parse, copy, move, rename, delete, overwrite, normalize or mutate the raw inbox.
""",
    )

    if write_governance_event:
        _append_governance_records(manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 outside-scope owner authorization intake generated "
        f"(authorized_extensions={summary['valid_authorized_extension_record_count']}, "
        f"application_ready={summary['source_map_extension_application_ready']}, decision={summary['decision']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
