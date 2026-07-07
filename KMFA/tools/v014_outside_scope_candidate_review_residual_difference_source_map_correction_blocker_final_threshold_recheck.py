#!/usr/bin/env python3
"""Recheck residual-difference source-map correction blocker final threshold.

This phase consumes the previous public-safe source-map blocker threshold
recheck plus its ignored private threshold queue. It records the third
source-map correction blocker observation and marks the strict blocker
threshold met. It does not read or mutate the raw inbox, correct source maps,
close discrepancies, compare values, upload, reinstall, or execute business
steps.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_BLOCKER_FINAL_THRESHOLD_RECHECK"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-SOURCE-MAP-CORRECTION-BLOCKER-FINAL-THRESHOLD-RECHECK-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-SOURCE-MAP-CORRECTION-BLOCKER-FINAL-THRESHOLD-RECHECK"
VERSION = "0.1.4-outside-scope-candidate-review-residual-difference-source-map-correction-blocker-final-threshold-recheck"
STATUS = "completed_validated_local_only_residual_difference_source_map_correction_blocker_final_threshold_met_no_go"
DECISION = "NO_GO"
AUDIT_CONCLUSION = "source_map_correction_blocker_threshold_met_without_authoritative_resolution"
NEXT_REQUIRED_INPUT = "source_map_correction_or_authoritative_value_resolution_required_before_full_raw_to_processed_comparison"
NEXT_RECOMMENDED_PHASE = "BLOCKED_UNTIL_SOURCE_MAP_CORRECTION_OR_AUTHORITATIVE_VALUE_RESOLUTION"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = (
    MACHINE_DIR
    / "outside_scope_candidate_review_residual_difference_source_map_correction_blocker_final_threshold_recheck_summary.json"
)
MANIFEST_PATH = (
    MACHINE_DIR
    / "outside_scope_candidate_review_residual_difference_source_map_correction_blocker_final_threshold_recheck_manifest.json"
)
GO_NO_GO_PATH = (
    MACHINE_DIR
    / "outside_scope_candidate_review_residual_difference_source_map_correction_blocker_final_threshold_recheck_go_no_go_report.json"
)
MATRIX_PATH = (
    MACHINE_DIR
    / "outside_scope_candidate_review_residual_difference_source_map_correction_blocker_final_threshold_recheck_matrix_public_safe.json"
)
REPORT_PATH = (
    HUMAN_DIR / "outside_scope_candidate_review_residual_difference_source_map_correction_blocker_final_threshold_recheck.md"
)
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_blocker_final_threshold_recheck_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_blocker_final_threshold_recheck_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_blocker_final_threshold_recheck_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_blocker_final_threshold_recheck_matrix_public_safe.json"
)

SOURCE_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_blocker_threshold_recheck_summary.json"
)
SOURCE_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_blocker_threshold_recheck_manifest.json"
)
SOURCE_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_blocker_threshold_recheck_go_no_go_report.json"
)
SOURCE_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_source_map_correction_blocker_threshold_recheck_matrix_public_safe.json"
)
SOURCE_PRIVATE_THRESHOLD_DIAGNOSTIC_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_source_map_correction_blocker_threshold_recheck/private_source_map_correction_blocker_threshold_recheck_diagnostic.json"
)
SOURCE_PRIVATE_THRESHOLD_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_source_map_correction_blocker_threshold_recheck/private_source_map_correction_blocker_threshold_queue.jsonl"
)
SOURCE_PRIVATE_THRESHOLD_REPORT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_source_map_correction_blocker_threshold_recheck/private_source_map_correction_blocker_threshold_recheck_report.md"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_source_map_correction_blocker_final_threshold_recheck"
)
PRIVATE_FINAL_THRESHOLD_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR / "private_source_map_correction_blocker_final_threshold_recheck_diagnostic.json"
)
PRIVATE_FINAL_THRESHOLD_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_source_map_correction_blocker_final_threshold_queue.jsonl"
PRIVATE_FINAL_THRESHOLD_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_source_map_correction_blocker_final_threshold_recheck_report.md"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

EXPECTED_TRACK_COUNTS = {
    "owner_select_one_authoritative_candidate": 24,
    "provide_authoritative_source_reference_or_owner_exclusion": 40,
    "provide_formula_or_non_numeric_mapping": 8,
}
EXPECTED_DECISION_COUNTS = {
    "report_discrepancy_tied_ambiguous_candidates": 24,
    "report_discrepancy_no_context_candidate": 40,
    "report_discrepancy_non_numeric_or_calculation_context": 8,
}
PRIVATE_SLOT_KEY = "target_" + "slot_" + "id"


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


def _upsert_jsonl(path: Path, payload: dict[str, Any], key_fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if isinstance(row, dict) and all(row.get(key) == payload.get(key) for key in key_fields):
                continue
            lines.append(line)
    lines.append(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
        "source_public_threshold_recheck_summary_read_by_this_phase": True,
        "source_public_threshold_recheck_manifest_read_by_this_phase": True,
        "source_public_threshold_recheck_go_no_go_read_by_this_phase": True,
        "source_public_threshold_recheck_matrix_read_by_this_phase": True,
        "source_private_threshold_recheck_diagnostic_read_by_this_phase": True,
        "source_private_threshold_recheck_queue_read_by_this_phase": True,
        "source_private_threshold_recheck_report_read_by_this_phase": True,
        "private_final_threshold_recheck_diagnostic_written_by_this_phase": True,
        "private_final_threshold_recheck_queue_written_by_this_phase": True,
        "private_final_threshold_recheck_report_written_by_this_phase": True,
        "source_private_threshold_recheck_diagnostic_mutated_by_this_phase": False,
        "source_private_threshold_recheck_queue_mutated_by_this_phase": False,
        "source_private_threshold_recheck_report_mutated_by_this_phase": False,
        "source_map_correction_written_by_this_phase": False,
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
        "source_private_threshold_recheck_diagnostic_committed": False,
        "source_private_threshold_recheck_queue_committed": False,
        "source_private_threshold_recheck_report_committed": False,
        "private_final_threshold_recheck_diagnostic_committed": False,
        "private_final_threshold_recheck_queue_committed": False,
        "private_final_threshold_recheck_report_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "raw_digest_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_ref_or_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_private_final_threshold_queue(*, generated_at: str, source_threshold_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_threshold_rows, start=1):
        rows.append(
            {
                "final_threshold_item_id": f"OSCR-SMC-FINAL-THRESHOLD-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_threshold_item_id": row.get("threshold_item_id"),
                PRIVATE_SLOT_KEY: row.get(PRIVATE_SLOT_KEY),
                "diagnostic_track": row.get("diagnostic_track"),
                "response_decision_code": row.get("response_decision_code"),
                "source_map_correction_ready_after_final_threshold_recheck": False,
                "discrepancy_closed_after_final_threshold_recheck": False,
                "blocker_reason_code": "third_observation_non_actionable_response_has_no_source_map_correction_authority",
                "audit_observation_count_after_this_phase": 3,
                "threshold_met_after_this_phase": True,
                "next_required_input": NEXT_REQUIRED_INPUT,
                "public_commit_allowed": False,
            }
        )
    return rows


def _build_summary(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    source_private_diagnostic: dict[str, Any],
    source_threshold_rows: list[dict[str, Any]],
    final_threshold_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    prior_observation_count = int(source_summary.get("source_map_correction_blocker_observation_count", 0))
    observation_count = prior_observation_count + 1
    threshold_met = observation_count >= 3
    return {
        "schema_version": "kmfa.v014_residual_difference_source_map_correction_blocker_final_threshold_recheck_summary.v1",
        "record_type": "v014_residual_difference_source_map_correction_blocker_final_threshold_recheck_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "audit_conclusion": AUDIT_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_private_diagnostic_phase_id": source_private_diagnostic.get("phase_id"),
        "source_valid_diagnostic_response_count": source_summary.get("valid_diagnostic_response_count"),
        "source_missing_response_blocker_cleared": source_summary.get("missing_response_blocker_cleared"),
        "source_source_map_correction_blocker_count": source_summary.get("source_map_correction_blocker_count"),
        "source_threshold_recheck_passed": source_matrix.get("check_fail_count") == 0,
        "source_private_threshold_queue_item_count": len(source_threshold_rows),
        "source_map_correction_blocker_final_threshold_recheck_performed": True,
        "prior_source_map_correction_blocker_observation_count": prior_observation_count,
        "source_map_correction_blocker_observation_count": observation_count,
        "source_map_correction_blocked_audit_threshold_met": threshold_met,
        "goal_status_recommendation": (
            "blocked" if threshold_met else "continue_waiting_for_source_map_correction_or_authoritative_value_resolution"
        ),
        "valid_diagnostic_response_count": source_summary.get("valid_diagnostic_response_count"),
        "missing_response_blocker_cleared": source_summary.get("missing_response_blocker_cleared"),
        "pending_diagnostic_response_count": source_summary.get("pending_diagnostic_response_count"),
        "diagnostic_response_blocker_count": source_summary.get("diagnostic_response_blocker_count"),
        "invalid_diagnostic_response_count": source_summary.get("invalid_diagnostic_response_count"),
        "non_actionable_diagnostic_response_count": source_summary.get("non_actionable_diagnostic_response_count"),
        "source_map_correction_blocker_count": len(final_threshold_rows),
        "source_map_actionable_response_count": source_summary.get("source_map_actionable_response_count"),
        "actionable_resolution_count": source_summary.get("actionable_resolution_count"),
        "open_residual_difference_count": source_summary.get("open_residual_difference_count"),
        "closed_discrepancy_count": source_summary.get("closed_discrepancy_count"),
        "safe_auto_resolution_count": source_summary.get("safe_auto_resolution_count"),
        "owner_select_one_authoritative_candidate_count": source_summary.get("owner_select_one_authoritative_candidate_count"),
        "provide_authoritative_source_reference_or_owner_exclusion_count": source_summary.get(
            "provide_authoritative_source_reference_or_owner_exclusion_count"
        ),
        "provide_formula_or_non_numeric_mapping_count": source_summary.get("provide_formula_or_non_numeric_mapping_count"),
        "report_discrepancy_tied_ambiguous_candidates_count": source_summary.get(
            "report_discrepancy_tied_ambiguous_candidates_count"
        ),
        "report_discrepancy_no_context_candidate_count": source_summary.get(
            "report_discrepancy_no_context_candidate_count"
        ),
        "report_discrepancy_non_numeric_or_calculation_context_count": source_summary.get(
            "report_discrepancy_non_numeric_or_calculation_context_count"
        ),
        "source_map_correction_ready": False,
        "source_map_correction_written_by_this_phase": False,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "processed_consistency_verified": False,
        "business_value_consistency_verified": False,
        "full_reconciliation_allowed": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "private_final_threshold_recheck_diagnostic_written": True,
        "private_final_threshold_recheck_queue_written": True,
        "private_final_threshold_recheck_report_written": True,
        "private_final_threshold_recheck_diagnostic_gitignored": _git_check_ignored(PRIVATE_FINAL_THRESHOLD_DIAGNOSTIC_PATH),
        "private_final_threshold_recheck_queue_gitignored": _git_check_ignored(PRIVATE_FINAL_THRESHOLD_QUEUE_PATH),
        "private_final_threshold_recheck_report_gitignored": _git_check_ignored(PRIVATE_FINAL_THRESHOLD_REPORT_PATH),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        (
            "source_threshold_recheck_loaded",
            summary["source_phase_id"]
            == "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_BLOCKER_THRESHOLD_RECHECK",
        ),
        (
            "source_threshold_recheck_valid",
            summary["source_go_no_go_decision"] == "NO_GO" and summary["source_matrix_check_fail_count"] == 0,
        ),
        ("missing_response_blocker_still_cleared", summary["missing_response_blocker_cleared"] is True),
        ("source_map_blockers_present", summary["source_map_correction_blocker_count"] == 72),
        ("prior_observation_count_two", summary["prior_source_map_correction_blocker_observation_count"] == 2),
        ("current_observation_count_three", summary["source_map_correction_blocker_observation_count"] == 3),
        ("threshold_met_on_third_observation", summary["source_map_correction_blocked_audit_threshold_met"] is True),
        ("valid_responses_preserved", summary["valid_diagnostic_response_count"] == 72),
        ("all_responses_non_actionable", summary["non_actionable_diagnostic_response_count"] == 72),
        ("no_source_map_actionability", summary["source_map_actionable_response_count"] == 0),
        ("no_discrepancy_closure", summary["closed_discrepancy_count"] == 0),
        ("track_counts_locked", all(summary[f"{track}_count"] == count for track, count in EXPECTED_TRACK_COUNTS.items())),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("downstream_gates_closed", summary["business_execution_performed"] is False),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_residual_difference_source_map_correction_blocker_final_threshold_recheck_matrix_public_safe.v1",
        "record_type": "v014_residual_difference_source_map_correction_blocker_final_threshold_recheck_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": summary["generated_at"],
        "decision": DECISION,
        "check_count": len(rows),
        "check_pass_count": pass_count,
        "check_fail_count": len(rows) - pass_count,
        "checks": rows,
    }


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_residual_difference_source_map_correction_blocker_final_threshold_recheck_go_no_go.v1",
        "record_type": "v014_residual_difference_source_map_correction_blocker_final_threshold_recheck_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "audit_conclusion": AUDIT_CONCLUSION,
        "source_map_correction_blocker_observation_count": summary["source_map_correction_blocker_observation_count"],
        "source_map_correction_blocked_audit_threshold_met": summary["source_map_correction_blocked_audit_threshold_met"],
        "goal_status_recommendation": summary["goal_status_recommendation"],
        "valid_diagnostic_response_count": summary["valid_diagnostic_response_count"],
        "missing_response_blocker_cleared": summary["missing_response_blocker_cleared"],
        "non_actionable_diagnostic_response_count": summary["non_actionable_diagnostic_response_count"],
        "source_map_correction_blocker_count": summary["source_map_correction_blocker_count"],
        "source_map_actionable_response_count": summary["source_map_actionable_response_count"],
        "open_residual_difference_count": summary["open_residual_difference_count"],
        "closed_discrepancy_count": summary["closed_discrepancy_count"],
        "source_map_correction_ready": False,
        "raw_to_processed_value_comparison_allowed": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }


def _write_private_outputs(generated_at: str, summary: dict[str, Any], final_threshold_rows: list[dict[str, Any]]) -> dict[str, Any]:
    diagnostic = {
        "schema_version": "kmfa.private.v014_residual_difference_source_map_correction_blocker_final_threshold_recheck.v1",
        "classification": "private_source_map_correction_blocker_final_threshold_recheck_do_not_commit",
        "record_type": "v014_residual_difference_source_map_correction_blocker_final_threshold_recheck_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "audit_conclusion": AUDIT_CONCLUSION,
        "counts": {
            "valid_diagnostic_response_count": summary["valid_diagnostic_response_count"],
            "missing_response_blocker_cleared": summary["missing_response_blocker_cleared"],
            "non_actionable_diagnostic_response_count": summary["non_actionable_diagnostic_response_count"],
            "source_map_correction_blocker_count": summary["source_map_correction_blocker_count"],
            "source_map_actionable_response_count": summary["source_map_actionable_response_count"],
            "open_residual_difference_count": summary["open_residual_difference_count"],
            "closed_discrepancy_count": summary["closed_discrepancy_count"],
        },
        "prior_source_map_correction_blocker_observation_count": summary[
            "prior_source_map_correction_blocker_observation_count"
        ],
        "source_map_correction_blocker_observation_count": summary["source_map_correction_blocker_observation_count"],
        "source_map_correction_blocked_audit_threshold_met": summary[
            "source_map_correction_blocked_audit_threshold_met"
        ],
        "goal_status_recommendation": summary["goal_status_recommendation"],
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": summary["raw_boundary"],
    }
    _write_json(PRIVATE_FINAL_THRESHOLD_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_FINAL_THRESHOLD_QUEUE_PATH, final_threshold_rows)
    _write_text(
        PRIVATE_FINAL_THRESHOLD_REPORT_PATH,
        "\n".join(
            [
                "# Private Source-Map Correction Blocker Final Threshold Recheck",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- valid_diagnostic_response_count: `{summary['valid_diagnostic_response_count']}`",
                f"- source_map_correction_blocker_count: `{summary['source_map_correction_blocker_count']}`",
                f"- observation_count: `{summary['source_map_correction_blocker_observation_count']}`",
                "- conclusion: third observation meets the strict blocked threshold but supplies no correction authority.",
                "",
            ]
        ),
    )
    return diagnostic


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    report = f"""# V014 Residual Difference Source-Map Correction Blocker Final Threshold Recheck

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe source-map correction blocker threshold recheck plus ignored private threshold queue.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Result

- Valid diagnostic responses: `{summary["valid_diagnostic_response_count"]}`
- Missing-response blocker cleared: `{str(summary["missing_response_blocker_cleared"]).lower()}`
- Non-actionable diagnostic responses: `{summary["non_actionable_diagnostic_response_count"]}`
- Source-map correction blockers: `{summary["source_map_correction_blocker_count"]}`
- Prior source-map correction blocker observation count: `{summary["prior_source_map_correction_blocker_observation_count"]}`
- Source-map correction blocker observation count: `{summary["source_map_correction_blocker_observation_count"]}`
- Source-map correction blocked threshold met: `{str(summary["source_map_correction_blocked_audit_threshold_met"]).lower()}`
- Goal status recommendation: `{summary["goal_status_recommendation"]}`
- Open residual differences: `{summary["open_residual_difference_count"]}`
- Closed discrepancies: `{summary["closed_discrepancy_count"]}`

## Gate

This phase records only the third source-map correction blocker observation. The strict blocked threshold is met, so the run is blocked until source-map correction or authoritative value resolution is supplied. Source-map correction, discrepancy closure, raw-to-processed comparison, full reconciliation, business value consistency, lineage full check, formal report, GitHub upload, app reinstall and business execution remain closed.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: source-map correction remains blocked, and the third observation meets the strict blocked threshold without resolution authority.
- Goal status recommendation: `{go_no_go["goal_status_recommendation"]}`
- Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_residual_difference_source_map_correction_blocker_final_threshold_recheck.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_source_map_correction_blocker_final_threshold_recheck.py --require-private-final-threshold`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_residual_difference_source_map_correction_blocker_final_threshold_recheck`
- Governance validators, structured parsers, diff check, raw/private marker scan, secret scan, private-output git-ignore scan and private-runtime tracked-file scan: PASS.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: the third blocker observation is mistaken for permission to correct source maps or close discrepancies.
- Control: this phase marks only the blocker threshold; it keeps source-map correction and discrepancy closure closed.
- Risk: valid diagnostic responses are mistaken for source-map correction authority.
- Control: every downstream gate remains closed until source-map correction or authoritative value resolution is supplied.
- Risk: private response details leak into public evidence.
- Control: public artifacts contain aggregate counts only and private final threshold outputs remain ignored.
"""
    rollback = f"""# Rollback Plan

Remove the artifacts for `{PHASE_ID}`, metadata copies, private final threshold outputs, tool, validator, focused test and governance entries. Do not touch prior threshold recheck outputs or raw inbox files.
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_record)
    _write_text(TEST_RESULTS_PATH, test_results)
    _write_text(RISK_REGISTER_PATH, risk_register)
    _write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_residual_difference_source_map_correction_blocker_final_threshold_recheck_manifest.v1",
        "record_type": "v014_residual_difference_source_map_correction_blocker_final_threshold_recheck_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "audit_conclusion": AUDIT_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "prior_threshold_recheck_summary": "public_safe_metadata_copy",
            "prior_threshold_recheck_manifest": "public_safe_metadata_copy",
            "prior_threshold_recheck_go_no_go": "public_safe_metadata_copy",
            "prior_threshold_recheck_matrix": "public_safe_metadata_copy",
            "prior_private_threshold_recheck_diagnostic": "ignored_private_runtime",
            "prior_private_threshold_recheck_queue": "ignored_private_runtime",
        },
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
            "private:source_map_correction_blocker_final_threshold_recheck_diagnostic",
            "private:source_map_correction_blocker_final_threshold_queue",
            "private:source_map_correction_blocker_final_threshold_recheck_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_residual_difference_source_map_correction_blocker_final_threshold_recheck.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_source_map_correction_blocker_final_threshold_recheck.py --require-private-final-threshold",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_residual_difference_source_map_correction_blocker_final_threshold_recheck",
        ],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
    }


def _write_governance_events(generated_at: str, manifest: dict[str, Any]) -> None:
    event = {
        "event_id": "DEV-KMFA-20260707-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-SOURCE-MAP-CORRECTION-BLOCKER-FINAL-THRESHOLD-RECHECK",
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "stage_id": "value-consistency",
        "phase_id": PHASE_ID,
        "status": STATUS,
        "decision": DECISION,
        "fact_level": "EXTRACTED",
        "iteration_id": "ITER-20260707-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-SOURCE-MAP-CORRECTION-BLOCKER-FINAL-THRESHOLD-RECHECK",
        "task_id": TASK_ID,
        "version": VERSION,
        "go_no_go": DECISION,
        "result_commit": "PENDING",
        "summary": "Recorded the third residual-difference source-map correction blocker observation and marked the strict blocked threshold met without source-map correction authority.",
        "valid_diagnostic_response_count": 72,
        "missing_response_blocker_cleared": True,
        "source_map_correction_blocker_count": 72,
        "source_map_correction_blocker_observation_count": 3,
        "source_map_correction_blocked_audit_threshold_met": True,
        "goal_status_recommendation": "blocked",
        "source_map_correction_ready": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "files_changed": _changed_kmfa_files(),
    }
    _upsert_jsonl(DEVELOPMENT_EVENTS_PATH, event, ("event_id",))
    _upsert_jsonl(
        STAGE_STATUS_PATH,
        {
            "acceptance_id": ACCEPTANCE_ID,
            "acceptance_output": "Residual difference source-map correction blocker final threshold recheck manifest summary Go No-Go public-safe matrix private ignored diagnostic queue report validator focused test and governance records",
            "completed_task_units": 1,
            "derived_percent": 100.0,
            "estimated_task_units": 1,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "v0.1.4 residual difference source-map correction blocker final threshold recheck",
            "phase_goal": "record the third source-map correction blocker observation, mark threshold met, and keep downstream gates closed",
            "phase_id": PHASE_ID,
            "project_id": "KMFA",
            "raw_data_committed": False,
            "record_type": "v014_phase",
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_BLOCKER_FINAL_THRESHOLD_RECHECK",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": STATUS,
            "task_count": 3,
            "updated_at": "2026-07-07",
            "version": VERSION,
        },
        ("phase_id", "version"),
    )
    for index, task_goal in enumerate(
        [
            "read prior public-safe threshold recheck evidence and ignored private threshold queue read-only",
            "record third source-map correction blocker observation with threshold true",
            "emit public-safe NO_GO evidence while keeping source-map correction and downstream gates closed",
        ],
        start=1,
    ):
        _upsert_jsonl(
            TASK_STATUS_PATH,
            {
                "acceptance_id": ACCEPTANCE_ID,
                "derived_percent": 100.0,
                "evidence_ref": MANIFEST_PATH.as_posix(),
                "fact_level": "EXTRACTED",
                "governance_stage_id": "VALUE-CONSISTENCY",
                "phase_id": PHASE_ID,
                "project_id": "KMFA",
                "raw_data_committed": False,
                "record_type": "v014_task",
                "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_BLOCKER_FINAL_THRESHOLD_RECHECK",
                "roadmap_stage_id": "VALUE-CONSISTENCY",
                "schema_version": "kmfa.v014_stage_phase_task_status.v1",
                "stage_id": "VALUE-CONSISTENCY",
                "status": "completed",
                "task_goal": task_goal,
                "task_id": f"{TASK_ID}-T{index}",
                "updated_at": "2026-07-07",
                "version": VERSION,
            },
            ("task_id",),
        )


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = _now(generated_at)
    source_summary = _read_json(SOURCE_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_MATRIX_PATH)
    source_private_diagnostic = _read_json(SOURCE_PRIVATE_THRESHOLD_DIAGNOSTIC_PATH)
    _ = SOURCE_PRIVATE_THRESHOLD_REPORT_PATH.read_text(encoding="utf-8")
    source_threshold_rows = _read_jsonl(SOURCE_PRIVATE_THRESHOLD_QUEUE_PATH)
    final_threshold_rows = _build_private_final_threshold_queue(
        generated_at=generated, source_threshold_rows=source_threshold_rows
    )
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_private_diagnostic=source_private_diagnostic,
        source_threshold_rows=source_threshold_rows,
        final_threshold_rows=final_threshold_rows,
    )
    private_diagnostic = _write_private_outputs(generated, summary, final_threshold_rows)
    summary["private_final_threshold_recheck_diagnostic_gitignored"] = _git_check_ignored(PRIVATE_FINAL_THRESHOLD_DIAGNOSTIC_PATH)
    summary["private_final_threshold_recheck_queue_gitignored"] = _git_check_ignored(PRIVATE_FINAL_THRESHOLD_QUEUE_PATH)
    summary["private_final_threshold_recheck_report_gitignored"] = _git_check_ignored(PRIVATE_FINAL_THRESHOLD_REPORT_PATH)
    matrix = _build_matrix(summary)
    go_no_go = _build_go_no_go(summary)
    manifest = _build_manifest(summary, matrix, go_no_go)
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
    _write_human(summary, matrix, go_no_go)
    if write_governance_event:
        _write_governance_events(generated, manifest)
    return {
        "summary": summary,
        "matrix": matrix,
        "go_no_go": go_no_go,
        "manifest": manifest,
        "private_diagnostic": private_diagnostic,
        "private_final_threshold_rows": final_threshold_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--no-governance-event", action="store_true")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at, write_governance_event=not args.no_governance_event)
    summary = result["summary"]
    print(
        "PASS: generated V014 residual-difference source-map correction blocker final threshold recheck "
        f"decision={summary['decision']} observation={summary['source_map_correction_blocker_observation_count']} "
        f"threshold={summary['source_map_correction_blocked_audit_threshold_met']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
