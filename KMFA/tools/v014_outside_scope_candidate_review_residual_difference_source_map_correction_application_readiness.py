#!/usr/bin/env python3
"""Check private application readiness for residual-difference source-map correction.

This phase consumes the ignored private authorization outputs from the previous
phase and determines whether a later private correction/application phase may
start. It does not apply source-map corrections, write authoritative values,
close discrepancies, compare raw and processed values, upload, reinstall, or
execute business steps.
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
PHASE_ID = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_APPLICATION_READINESS"
TASK_ID = (
    "KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-"
    "SOURCE-MAP-CORRECTION-APPLICATION-READINESS-20260707"
)
ACCEPTANCE_ID = (
    "ACC-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-"
    "SOURCE-MAP-CORRECTION-APPLICATION-READINESS"
)
VERSION = "0.1.4-outside-scope-candidate-review-residual-difference-source-map-correction-application-readiness"
STATUS = "completed_validated_local_only_residual_difference_source_map_correction_application_readiness_ready_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "private_resolution_application_readiness_passed_application_not_performed"
NEXT_RECOMMENDED_PHASE = (
    "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_APPLICATION"
)
NEXT_REQUIRED_INPUT = (
    "run_private_source_map_correction_or_authoritative_value_resolution_application_"
    "before_full_raw_to_processed_comparison"
)

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness_manifest.json"
GO_NO_GO_PATH = (
    MACHINE_DIR / "outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness_go_no_go_report.json"
)
MATRIX_PATH = (
    MACHINE_DIR / "outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness_matrix_public_safe.json"
)
REPORT_PATH = HUMAN_DIR / "outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness_matrix_public_safe.json"
)

SOURCE_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_authorization_intake_summary.json"
)
SOURCE_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_authorization_intake_manifest.json"
)
SOURCE_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_authorization_intake_go_no_go_report.json"
)
SOURCE_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_authorization_intake_matrix_public_safe.json"
)
SOURCE_PRIVATE_ACTIVE_RECORD_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_source_map_correction_authorization_intake/private_source_map_correction_authorization_active_record.json"
)
SOURCE_PRIVATE_AUTHORIZATION_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_source_map_correction_authorization_intake/private_source_map_correction_authorization_queue.jsonl"
)
SOURCE_PRIVATE_DIAGNOSTIC_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_source_map_correction_authorization_intake/private_source_map_correction_authorization_intake_diagnostic.json"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness"
)
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_source_map_correction_application_readiness_diagnostic.json"
PRIVATE_READY_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_source_map_correction_application_ready_queue.jsonl"
PRIVATE_BLOCKER_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_source_map_correction_application_blocker_queue.jsonl"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_source_map_correction_application_readiness.md"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

EXPECTED_TRACK_COUNTS = {
    "owner_select_one_authoritative_candidate": 24,
    "provide_authoritative_source_reference_or_owner_exclusion": 40,
    "provide_formula_or_non_numeric_mapping": 8,
}


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


def _changed_kmfa_files() -> list[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "status", "--porcelain=v1", "--untracked-files=all", "--", "KMFA"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        return []
    files: set[str] = set()
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if ".codex_private_runtime/" not in path:
            files.add(path)
    return sorted(files)


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_public_authorization_summary_read_by_this_phase": True,
        "source_public_authorization_manifest_read_by_this_phase": True,
        "source_public_authorization_go_no_go_read_by_this_phase": True,
        "source_public_authorization_matrix_read_by_this_phase": True,
        "source_private_authorization_active_record_read_by_this_phase": True,
        "source_private_authorization_queue_read_by_this_phase": True,
        "source_private_authorization_diagnostic_read_by_this_phase": True,
        "private_application_readiness_diagnostic_written_by_this_phase": True,
        "private_application_ready_queue_written_by_this_phase": True,
        "private_application_blocker_queue_written_by_this_phase": True,
        "source_private_authorization_queue_mutated_by_this_phase": False,
        "source_map_correction_written_by_this_phase": False,
        "authoritative_value_resolution_written_by_this_phase": False,
        "discrepancy_closure_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "raw_inbox_read_performed_by_this_phase": False,
        "raw_inbox_list_performed_by_this_phase": False,
        "raw_inbox_stat_performed_by_this_phase": False,
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
        "private_authorization_active_record_committed": False,
        "private_authorization_queue_committed": False,
        "private_authorization_diagnostic_committed": False,
        "private_application_readiness_diagnostic_committed": False,
        "private_application_ready_queue_committed": False,
        "private_application_blocker_queue_committed": False,
        "private_report_committed": False,
        "private_source_map_committed": False,
        "private_authoritative_value_resolution_committed": False,
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
        row.get("authorization_item_id"),
        row.get("source_final_threshold_item_id"),
        row.get("diagnostic_track"),
        row.get("response_decision_code"),
    )
    return (
        all(value not in {"", None, "PENDING_PRIVATE_INPUT"} for value in required_values)
        and row.get("owner_authorization_decision_code") == "AUTHORIZE_CODEX_PREPARE_PRIVATE_RESOLUTION"
        and row.get("private_resolution_preparation_allowed_next_phase") is True
        and row.get("source_map_correction_application_allowed_by_this_phase") is False
        and row.get("authoritative_value_resolution_application_allowed_by_this_phase") is False
        and row.get("source_map_correction_written_by_this_phase") is False
        and row.get("raw_to_processed_value_comparison_allowed_by_this_phase") is False
        and row.get("full_reconciliation_allowed_by_this_phase") is False
        and row.get("public_commit_allowed") is False
    )


def _build_private_queues(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ready: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if _row_ready(row):
            ready.append(
                {
                    "application_ready_queue_index": index,
                    "authorization_item_id": row.get("authorization_item_id"),
                    "source_final_threshold_item_id": row.get("source_final_threshold_item_id"),
                    "target_slot_id": row.get("target_slot_id"),
                    "diagnostic_track": row.get("diagnostic_track"),
                    "response_decision_code": row.get("response_decision_code"),
                    "application_readiness_status": "ready",
                    "source_map_correction_application_ready": True,
                    "authoritative_value_resolution_application_ready": True,
                    "private_resolution_application_allowed_next_phase": True,
                    "source_map_correction_written_by_this_phase": False,
                    "authoritative_value_resolution_written_by_this_phase": False,
                    "discrepancy_closure_written_by_this_phase": False,
                    "raw_to_processed_value_comparison_allowed_by_this_phase": False,
                    "full_reconciliation_allowed_by_this_phase": False,
                }
            )
        else:
            blockers.append(
                {
                    "application_blocker_queue_index": index,
                    "authorization_item_id": row.get("authorization_item_id"),
                    "target_slot_id": row.get("target_slot_id"),
                    "diagnostic_track": row.get("diagnostic_track"),
                    "application_readiness_status": "blocked",
                    "application_blocker_code": "invalid_or_incomplete_private_resolution_authorization_record",
                    "source_map_correction_application_ready": False,
                    "authoritative_value_resolution_application_ready": False,
                    "private_resolution_application_allowed_next_phase": False,
                    "source_map_correction_written_by_this_phase": False,
                    "authoritative_value_resolution_written_by_this_phase": False,
                    "raw_to_processed_value_comparison_allowed_by_this_phase": False,
                    "full_reconciliation_allowed_by_this_phase": False,
                }
            )
    return ready, blockers


def _build_matrix(summary: dict[str, Any], generated_at: str) -> dict[str, Any]:
    checks = [
        ("source_authorization_intake_valid", summary["source_authorization_item_count"] == 72, summary["source_authorization_item_count"], 72),
        ("private_active_record_count", summary["private_active_authorization_record_count"] == 72, summary["private_active_authorization_record_count"], 72),
        ("private_authorization_queue_count", summary["private_authorization_queue_count"] == 72, summary["private_authorization_queue_count"], 72),
        ("track_counts_match_expected", summary["diagnostic_track_counts"] == EXPECTED_TRACK_COUNTS, summary["diagnostic_track_counts"], EXPECTED_TRACK_COUNTS),
        ("application_ready_record_count", summary["application_ready_record_count"] == 72, summary["application_ready_record_count"], 72),
        ("application_blocker_count_zero", summary["application_blocker_count"] == 0, summary["application_blocker_count"], 0),
        ("private_resolution_application_ready_true", summary["private_resolution_application_ready"] is True, summary["private_resolution_application_ready"], True),
        ("source_map_correction_not_written", summary["source_map_correction_written_by_this_phase"] is False, summary["source_map_correction_written_by_this_phase"], False),
        ("full_comparison_not_performed", summary["full_raw_to_processed_value_comparison_complete"] is False, summary["full_raw_to_processed_value_comparison_complete"], False),
        ("project_go_no_go_preserved", summary["decision"] == DECISION, summary["decision"], DECISION),
    ]
    rows = [
        {"check_code": code, "status": "PASS" if ok else "FAIL", "observed_public_safe": observed, "required": required}
        for code, ok, observed, required in checks
    ]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_residual_difference_source_map_correction_application_readiness_matrix_public_safe.v1",
        "record_type": "v014_residual_difference_source_map_correction_application_readiness_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "check_count": len(rows),
        "check_pass_count": pass_count,
        "check_fail_count": len(rows) - pass_count,
        "private_resolution_application_ready": summary["private_resolution_application_ready"],
        "source_map_correction_application_allowed_next_phase": summary["source_map_correction_application_allowed_next_phase"],
        "authoritative_value_resolution_application_allowed_next_phase": summary[
            "authoritative_value_resolution_application_allowed_next_phase"
        ],
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
        "event_id": "DEV-KMFA-20260707-V014-RESIDUAL-DIFFERENCE-SOURCE-MAP-CORRECTION-APPLICATION-READINESS",
        "event_time": manifest["generated_at"],
        "event_type": "development",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "iteration_id": "ITER-20260707-KMFA-V014-RESIDUAL-DIFFERENCE-SOURCE-MAP-CORRECTION-APPLICATION-READINESS",
        "fact_level": "EXTRACTED",
        "status": STATUS,
        "go_no_go": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "authorization_item_count": summary["source_authorization_item_count"],
        "application_ready_record_count": summary["application_ready_record_count"],
        "application_blocker_count": summary["application_blocker_count"],
        "private_resolution_application_ready": summary["private_resolution_application_ready"],
        "source_map_correction_written_by_this_phase": False,
        "authoritative_value_resolution_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "summary": "Checked private residual-difference source-map correction application readiness and kept downstream gates closed.",
        "result_commit": "PENDING",
        "files_changed": _changed_kmfa_files(),
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
            "name": "v0.1.4 residual difference source-map correction application readiness",
            "phase_id": PHASE_ID,
            "record_type": "v014_phase",
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_APPLICATION_READINESS",
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
            "name": "72 private resolution authorization rows passed application readiness",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_APPLICATION_READINESS",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "RDSMCAR01",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": GO_NO_GO_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "private correction application is ready for a later phase but not performed",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_APPLICATION_READINESS",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "RDSMCAR02",
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
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_APPLICATION_READINESS",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "RDSMCAR03",
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
                "verify residual difference private correction application readiness without applying corrections"
            )
        else:
            task_row["task_label"] = row["task_id"][-2:]
            task_row["task_text"] = row["name"]
        task_rows.append(task_row)
    _dedupe_append_jsonl(TASK_STATUS_PATH, task_rows, lambda existing: existing.get("phase_id") != PHASE_ID)


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_MATRIX_PATH)
    active_record = _read_json(SOURCE_PRIVATE_ACTIVE_RECORD_PATH)
    source_queue = _read_jsonl(SOURCE_PRIVATE_AUTHORIZATION_QUEUE_PATH)
    source_diagnostic = _read_json(SOURCE_PRIVATE_DIAGNOSTIC_PATH)

    if len(source_queue) != 72:
        raise ValueError("source private authorization queue must contain 72 rows")
    if active_record.get("authorization_item_count") != len(source_queue):
        raise ValueError("active authorization count must match private queue length")
    track_counts = dict(Counter(row.get("diagnostic_track") for row in source_queue))
    response_decision_counts = dict(Counter(row.get("response_decision_code") for row in source_queue))
    ready_queue, blocker_queue = _build_private_queues(source_queue)
    target_counts = Counter(row.get("target_slot_id") for row in source_queue)
    duplicate_target_slot_count = sum(1 for count in target_counts.values() if count > 1)
    application_ready = len(ready_queue) == 72 and not blocker_queue and track_counts == EXPECTED_TRACK_COUNTS
    raw_boundary = _raw_boundary()
    public_safety = _public_safety()

    summary = {
        "schema_version": "kmfa.v014_residual_difference_source_map_correction_application_readiness_summary.v1",
        "record_type": "v014_residual_difference_source_map_correction_application_readiness_summary",
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
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_decision": source_summary.get("decision"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_owner_authorization_intaken": source_summary.get("owner_authorization_intaken"),
        "source_authorization_item_count": source_summary.get("authorization_item_count"),
        "source_private_resolution_preparation_allowed_next_phase": source_summary.get(
            "private_resolution_preparation_allowed_next_phase"
        ),
        "private_active_authorization_record_count": active_record.get("authorization_item_count"),
        "private_authorization_queue_count": len(source_queue),
        "source_private_diagnostic_phase_id": source_diagnostic.get("phase_id"),
        "source_private_diagnostic_authorization_item_count": source_diagnostic.get("authorization_item_count"),
        "readiness_candidate_count": len(source_queue),
        "application_ready_record_count": len(ready_queue),
        "application_blocker_count": len(blocker_queue),
        "unique_target_slot_count": len(target_counts),
        "duplicate_target_slot_count": duplicate_target_slot_count,
        "diagnostic_track_counts": track_counts,
        "response_decision_counts_public_safe": response_decision_counts,
        "owner_select_one_authoritative_candidate_count": track_counts.get("owner_select_one_authoritative_candidate", 0),
        "provide_authoritative_source_reference_or_owner_exclusion_count": track_counts.get(
            "provide_authoritative_source_reference_or_owner_exclusion", 0
        ),
        "provide_formula_or_non_numeric_mapping_count": track_counts.get("provide_formula_or_non_numeric_mapping", 0),
        "private_resolution_application_ready": application_ready,
        "source_map_correction_application_ready": application_ready,
        "authoritative_value_resolution_application_ready": application_ready,
        "source_map_correction_application_allowed_next_phase": application_ready,
        "authoritative_value_resolution_application_allowed_next_phase": application_ready,
        "private_resolution_application_performed_by_this_phase": False,
        "source_map_correction_written_by_this_phase": False,
        "source_map_correction_applied_count": 0,
        "authoritative_value_resolution_written_by_this_phase": False,
        "authoritative_value_resolution_applied_count": 0,
        "discrepancy_closure_written_by_this_phase": False,
        "closed_discrepancy_count": 0,
        "open_residual_difference_count": source_summary.get("open_residual_difference_count"),
        "raw_to_processed_value_comparison_ready": False,
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
        "private_application_report_gitignored": _git_check_ignored(PRIVATE_REPORT_PATH),
        "raw_boundary": raw_boundary,
        "public_safety": public_safety,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    matrix = _build_matrix(summary, timestamp)
    go_no_go = {
        "schema_version": "kmfa.v014_residual_difference_source_map_correction_application_readiness_go_no_go.v1",
        "record_type": "v014_residual_difference_source_map_correction_application_readiness_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "application_ready_record_count": summary["application_ready_record_count"],
        "application_blocker_count": summary["application_blocker_count"],
        "private_resolution_application_ready": application_ready,
        "source_map_correction_application_allowed_next_phase": application_ready,
        "authoritative_value_resolution_application_allowed_next_phase": application_ready,
        "private_resolution_application_performed_by_this_phase": False,
        "source_map_correction_written_by_this_phase": False,
        "authoritative_value_resolution_written_by_this_phase": False,
        "discrepancy_closure_written_by_this_phase": False,
        "raw_to_processed_value_comparison_allowed": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_residual_difference_source_map_correction_application_readiness_manifest.v1",
        "record_type": "v014_residual_difference_source_map_correction_application_readiness_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_artifacts": [
            SOURCE_SUMMARY_PATH.as_posix(),
            SOURCE_MANIFEST_PATH.as_posix(),
            SOURCE_GO_NO_GO_PATH.as_posix(),
            SOURCE_MATRIX_PATH.as_posix(),
            "private:source_map_correction_authorization_active_record",
            "private:source_map_correction_authorization_queue",
            "private:source_map_correction_authorization_intake_diagnostic",
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
            "private:source_map_correction_application_readiness_diagnostic",
            "private:source_map_correction_application_ready_queue",
            "private:source_map_correction_application_blocker_queue",
            "private:source_map_correction_application_readiness_report",
        ],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness.py KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness.py KMFA/tests/test_v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness.py --require-private-readiness",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness",
        ],
        "raw_boundary": raw_boundary,
        "public_safety": public_safety,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
    }

    private_diagnostic = {
        "schema_version": "kmfa.private.v014_residual_difference_source_map_correction_application_readiness_diagnostic.v1",
        "record_type": "private_residual_difference_source_map_correction_application_readiness_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "source_phase_id": source_summary.get("phase_id"),
        "authorization_item_count": len(source_queue),
        "application_ready_record_count": len(ready_queue),
        "application_blocker_count": len(blocker_queue),
        "diagnostic_track_counts": track_counts,
        "response_decision_counts": response_decision_counts,
        "private_resolution_application_ready": application_ready,
        "private_resolution_application_performed_by_this_phase": False,
        "source_map_correction_written_by_this_phase": False,
        "authoritative_value_resolution_written_by_this_phase": False,
        "discrepancy_closure_written_by_this_phase": False,
        "raw_inbox_accessed": False,
        "raw_inbox_mutated": False,
    }

    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
    _write_jsonl(PRIVATE_READY_QUEUE_PATH, ready_queue)
    _write_jsonl(PRIVATE_BLOCKER_QUEUE_PATH, blocker_queue)
    _write_text(
        PRIVATE_REPORT_PATH,
        "\n".join(
            [
                "# Private residual difference source-map correction application readiness",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- authorization_item_count: `{len(source_queue)}`",
                f"- application_ready_record_count: `{len(ready_queue)}`",
                f"- application_blocker_count: `{len(blocker_queue)}`",
                f"- private_resolution_application_ready: `{str(application_ready).lower()}`",
                "- source-map correction application was not performed.",
                "- authoritative value resolution application was not performed.",
                "- raw inbox access and mutation were not performed.",
            ]
        )
        + "\n",
    )

    summary["private_application_readiness_diagnostic_gitignored"] = _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH)
    summary["private_application_ready_queue_gitignored"] = _git_check_ignored(PRIVATE_READY_QUEUE_PATH)
    summary["private_application_blocker_queue_gitignored"] = _git_check_ignored(PRIVATE_BLOCKER_QUEUE_PATH)
    summary["private_application_report_gitignored"] = _git_check_ignored(PRIVATE_REPORT_PATH)
    matrix = _build_matrix(summary, timestamp)
    manifest["summary"] = summary
    manifest["matrix"] = matrix
    manifest["go_no_go_report"] = go_no_go

    _write_json(SUMMARY_PATH, summary)
    _write_json(MANIFEST_PATH, manifest)
    _write_json(GO_NO_GO_PATH, go_no_go)
    _write_json(MATRIX_PATH, matrix)
    _write_json(METADATA_SUMMARY_PATH, summary)
    _write_json(METADATA_MANIFEST_PATH, manifest)
    _write_json(METADATA_GO_NO_GO_PATH, go_no_go)
    _write_json(METADATA_MATRIX_PATH, matrix)

    _write_text(
        REPORT_PATH,
        "\n".join(
            [
                "# Residual Difference Source-Map Correction Application Readiness",
                "",
                f"- Phase: `{PHASE_ID}`",
                f"- Decision: `{DECISION}`",
                f"- Application ready records: `{summary['application_ready_record_count']}`",
                f"- Application blocker records: `{summary['application_blocker_count']}`",
                f"- Private resolution application ready: `{str(summary['private_resolution_application_ready']).lower()}`",
                "- Source-map correction and authoritative value resolution were not applied in this phase.",
                "- Raw inbox access and mutation were not performed.",
                "- Public evidence is aggregate/status/ref only.",
                f"- Next required input: `{NEXT_REQUIRED_INPUT}`",
            ]
        )
        + "\n",
    )
    _write_text(
        GO_NO_GO_RECORD_PATH,
        "\n".join(
            [
                "# Go / No-Go Record",
                "",
                f"- Decision: `{DECISION}`",
                f"- Diagnostic: `{DIAGNOSTIC_CONCLUSION}`",
                f"- Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`",
                "- GitHub upload performed: `false`",
                "- App reinstall performed: `false`",
                "- Business execution performed: `false`",
            ]
        )
        + "\n",
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# Test Results",
                "",
                "- Generator: pending local run evidence in terminal.",
                "- Validator: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness.py --require-private-readiness`",
                "- Focused test: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness`",
                "- Raw/private/secret scan: required before commit.",
            ]
        )
        + "\n",
    )
    _write_text(
        RISK_REGISTER_PATH,
        "\n".join(
            [
                "# Risk Register",
                "",
                "- Risk: readiness can be mistaken for actual source-map correction.",
                "  - Control: application/write/comparison/reconciliation/upload flags stay false.",
                "- Risk: private target details leak into public artifacts.",
                "  - Control: public artifacts carry aggregate counts and status refs only.",
                "- Risk: raw inbox accidentally becomes a workspace.",
                "  - Control: this phase does not read, list, parse, hash, write or mutate raw inbox files.",
            ]
        )
        + "\n",
    )
    _write_text(
        ROLLBACK_PATH,
        "\n".join(
            [
                "# Rollback Plan",
                "",
                "- Remove this phase public artifacts and metadata copies.",
                "- Remove this phase ignored private readiness outputs.",
                "- Re-run the previous authorization-intake validator.",
                "- Do not modify raw inbox files during rollback.",
            ]
        )
        + "\n",
    )

    if write_governance_event:
        _append_governance_records(manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-at")
    parser.add_argument("--skip-governance-event", action="store_true")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at, write_governance_event=not args.skip_governance_event)
    summary = manifest["summary"]
    print(
        "PASS: generated V014 residual-difference source-map correction application readiness "
        f"decision={summary['decision']} ready_records={summary['application_ready_record_count']} "
        f"blockers={summary['application_blocker_count']} next={summary['next_recommended_phase']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
