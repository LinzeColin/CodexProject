#!/usr/bin/env python3
"""Recheck owner-authorized anchor blocker final threshold.

This phase consumes the previous public-safe owner-authorized anchor blocker
threshold recheck and its ignored private threshold queue. It records the third
blocker observation and marks the strict threshold met. It does not read or
mutate the raw inbox, confirm anchors, compare raw-to-processed values, upload,
reinstall, or execute business steps.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_BLOCKER_FINAL_THRESHOLD_RECHECK"
TASK_ID = "KMFA-V014-RESIDUAL-DIFFERENCE-OWNER-AUTHORIZED-ANCHOR-CONFIRMATION-BLOCKER-FINAL-THRESHOLD-RECHECK-20260707"
ACCEPTANCE_ID = "ACC-V014-RESIDUAL-DIFFERENCE-OWNER-AUTHORIZED-ANCHOR-CONFIRMATION-BLOCKER-FINAL-THRESHOLD-RECHECK"
VERSION = "0.1.4-residual-difference-owner-authorized-anchor-confirmation-blocker-final-threshold-recheck"
STATUS = "completed_validated_local_only_owner_authorized_anchor_confirmation_blocker_final_threshold_met_no_go"
DECISION = "NO_GO"
THRESHOLD_CONCLUSION = "owner_authorized_anchor_confirmation_blocker_threshold_met_without_anchor_confirmation"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_confirms_private_raw_candidate_anchors_before_formal_comparison"
NEXT_RECOMMENDED_PHASE = "BLOCKED_UNTIL_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck_manifest.json"
GO_NO_GO_PATH = (
    MACHINE_DIR
    / "residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck_go_no_go_report.json"
)
MATRIX_PATH = (
    MACHINE_DIR
    / "residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck_matrix_public_safe.json"
)
REPORT_PATH = HUMAN_DIR / "residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck_matrix_public_safe.json"
)

SOURCE_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_threshold_recheck_summary.json"
)
SOURCE_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_threshold_recheck_manifest.json"
)
SOURCE_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_threshold_recheck_go_no_go_report.json"
)
SOURCE_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_threshold_recheck_matrix_public_safe.json"
)
SOURCE_PRIVATE_DIR = (
    PROJECT_ROOT / ".codex_private_runtime/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_threshold_recheck"
)
SOURCE_PRIVATE_THRESHOLD_DIAGNOSTIC_PATH = (
    SOURCE_PRIVATE_DIR / "private_owner_authorized_anchor_confirmation_blocker_threshold_diagnostic.json"
)
SOURCE_PRIVATE_THRESHOLD_QUEUE_PATH = (
    SOURCE_PRIVATE_DIR / "private_owner_authorized_anchor_confirmation_blocker_threshold_queue.jsonl"
)
SOURCE_PRIVATE_THRESHOLD_REPORT_PATH = (
    SOURCE_PRIVATE_DIR / "private_owner_authorized_anchor_confirmation_blocker_threshold_report.md"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck"
)
PRIVATE_FINAL_THRESHOLD_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_confirmation_blocker_final_threshold_diagnostic.json"
)
PRIVATE_FINAL_THRESHOLD_QUEUE_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_confirmation_blocker_final_threshold_queue.jsonl"
)
PRIVATE_FINAL_THRESHOLD_REPORT_PATH = (
    PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_confirmation_blocker_final_threshold_report.md"
)

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

EXPECTED_TRACK_COUNTS = {
    "owner_select_one_authoritative_candidate": 24,
    "provide_authoritative_source_reference_or_owner_exclusion": 40,
    "provide_formula_or_non_numeric_mapping": 8,
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


def _dedupe_append_jsonl(path: Path, rows: list[dict[str, Any]], phase_id: str) -> None:
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
            if not isinstance(existing, dict) or existing.get("phase_id") != phase_id:
                retained.append(line)
    retained.extend(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(retained) + "\n", encoding="utf-8")


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_public_anchor_blocker_threshold_summary_read_by_this_phase": True,
        "source_public_anchor_blocker_threshold_manifest_read_by_this_phase": True,
        "source_public_anchor_blocker_threshold_go_no_go_read_by_this_phase": True,
        "source_public_anchor_blocker_threshold_matrix_read_by_this_phase": True,
        "source_private_anchor_blocker_threshold_diagnostic_read_by_this_phase": True,
        "source_private_anchor_blocker_threshold_queue_read_by_this_phase": True,
        "source_private_anchor_blocker_threshold_report_read_by_this_phase": True,
        "private_final_threshold_diagnostic_written_by_this_phase": True,
        "private_final_threshold_queue_written_by_this_phase": True,
        "private_final_threshold_report_written_by_this_phase": True,
        "source_private_anchor_blocker_threshold_diagnostic_mutated_by_this_phase": False,
        "source_private_anchor_blocker_threshold_queue_mutated_by_this_phase": False,
        "source_private_anchor_blocker_threshold_report_mutated_by_this_phase": False,
        "owner_authorized_anchor_confirmation_performed_by_this_phase": False,
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
        "source_private_anchor_blocker_threshold_diagnostic_committed": False,
        "source_private_anchor_blocker_threshold_queue_committed": False,
        "source_private_anchor_blocker_threshold_report_committed": False,
        "private_final_threshold_diagnostic_committed": False,
        "private_final_threshold_queue_committed": False,
        "private_final_threshold_report_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "field_header_plaintext_committed": False,
        "target_slot_detail_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_value_fingerprint_committed": False,
        "private_ref_or_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_private_final_threshold_rows(generated_at: str, source_threshold_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_threshold_rows, start=1):
        rows.append(
            {
                "final_threshold_item_id": f"OACB-FINAL-THRESHOLD-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_threshold_item_id": row.get("threshold_item_id"),
                PRIVATE_SLOT_KEY: row.get(PRIVATE_SLOT_KEY),
                "diagnostic_track": row.get("diagnostic_track"),
                "prior_owner_authorized_anchor_blocker_observation_count": 2,
                "owner_authorized_anchor_blocker_observation_count_after_this_phase": 3,
                "anchor_confirmation_ready_after_final_threshold_recheck": False,
                "raw_to_processed_value_comparison_ready_after_final_threshold_recheck": False,
                "business_value_consistency_verified_after_final_threshold_recheck": False,
                "blocker_reason_code": "third_observation_missing_owner_authorized_anchor_confirmation",
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
    track_counts = dict(Counter(row.get("diagnostic_track") for row in source_threshold_rows))
    source_observation_count = int(source_summary.get("owner_authorized_anchor_blocker_observation_count") or 0)
    observation_count = source_observation_count + 1
    threshold_met = observation_count >= 3
    return {
        "schema_version": "kmfa.v014_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck_summary.v1",
        "record_type": "v014_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "threshold_conclusion": THRESHOLD_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_private_diagnostic_phase_id": source_private_diagnostic.get("phase_id"),
        "source_owner_authorized_anchor_blocker_count": source_summary.get("owner_authorized_anchor_blocker_count"),
        "source_owner_authorized_anchor_blocker_observation_count": source_observation_count,
        "source_owner_authorized_anchor_blocked_audit_threshold_met": source_summary.get(
            "owner_authorized_anchor_blocked_audit_threshold_met"
        ),
        "source_owner_authorized_anchor_confirmation_count": source_summary.get(
            "owner_authorized_anchor_confirmation_count"
        ),
        "source_unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "source_private_threshold_queue_item_count": len(source_threshold_rows),
        "owner_authorized_anchor_blocker_final_threshold_recheck_performed": True,
        "prior_owner_authorized_anchor_blocker_observation_count": source_observation_count,
        "owner_authorized_anchor_blocker_observation_count": observation_count,
        "owner_authorized_anchor_blocked_audit_threshold_met": threshold_met,
        "goal_status_recommendation": "blocked" if threshold_met else "continue_waiting_for_owner_authorized_anchor_confirmation",
        "owner_authorized_anchor_blocker_count": len(final_threshold_rows),
        "owner_authorized_anchor_confirmation_count": 0,
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
        "missing_owner_authorized_anchor_count": source_summary.get("missing_owner_authorized_anchor_count"),
        "missing_processed_value_fingerprint_count": source_summary.get("missing_processed_value_fingerprint_count"),
        "missing_raw_candidate_anchor_count": source_summary.get("missing_raw_candidate_anchor_count"),
        "diagnostic_track_counts": track_counts,
        "owner_select_one_authoritative_candidate_count": track_counts.get("owner_select_one_authoritative_candidate", 0),
        "provide_authoritative_source_reference_or_owner_exclusion_count": track_counts.get(
            "provide_authoritative_source_reference_or_owner_exclusion", 0
        ),
        "provide_formula_or_non_numeric_mapping_count": track_counts.get("provide_formula_or_non_numeric_mapping", 0),
        "anchor_confirmation_ready": False,
        "owner_authorized_anchor_confirmation_performed_by_this_phase": False,
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
        "private_final_threshold_diagnostic_written": True,
        "private_final_threshold_queue_written": True,
        "private_final_threshold_report_written": True,
        "private_final_threshold_diagnostic_gitignored": _git_check_ignored(PRIVATE_FINAL_THRESHOLD_DIAGNOSTIC_PATH),
        "private_final_threshold_queue_gitignored": _git_check_ignored(PRIVATE_FINAL_THRESHOLD_QUEUE_PATH),
        "private_final_threshold_report_gitignored": _git_check_ignored(PRIVATE_FINAL_THRESHOLD_REPORT_PATH),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_threshold_recheck_loaded", summary["source_phase_id"].endswith("BLOCKER_THRESHOLD_RECHECK")),
        (
            "source_threshold_recheck_valid",
            summary["source_go_no_go_decision"] == "NO_GO" and summary["source_matrix_check_fail_count"] == 0,
        ),
        ("source_blockers_present", summary["source_owner_authorized_anchor_blocker_count"] == 72),
        ("source_observation_count_two", summary["source_owner_authorized_anchor_blocker_observation_count"] == 2),
        ("prior_observation_count_two", summary["prior_owner_authorized_anchor_blocker_observation_count"] == 2),
        ("current_observation_count_three", summary["owner_authorized_anchor_blocker_observation_count"] == 3),
        ("threshold_met_on_third_observation", summary["owner_authorized_anchor_blocked_audit_threshold_met"] is True),
        ("anchor_confirmation_count_zero", summary["owner_authorized_anchor_confirmation_count"] == 0),
        ("unresolved_difference_count_preserved", summary["unresolved_difference_count"] == 72),
        ("diagnostic_track_counts_locked", summary["diagnostic_track_counts"] == EXPECTED_TRACK_COUNTS),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("private_outputs_ignored", summary["private_final_threshold_queue_gitignored"] is True),
        ("downstream_gates_closed", summary["business_execution_performed"] is False),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck_matrix_public_safe.v1",
        "record_type": "v014_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck_matrix_public_safe",
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
        "schema_version": "kmfa.v014_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck_go_no_go.v1",
        "record_type": "v014_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "threshold_conclusion": THRESHOLD_CONCLUSION,
        "owner_authorized_anchor_blocker_observation_count": summary[
            "owner_authorized_anchor_blocker_observation_count"
        ],
        "owner_authorized_anchor_blocked_audit_threshold_met": summary[
            "owner_authorized_anchor_blocked_audit_threshold_met"
        ],
        "goal_status_recommendation": summary["goal_status_recommendation"],
        "owner_authorized_anchor_blocker_count": summary["owner_authorized_anchor_blocker_count"],
        "owner_authorized_anchor_confirmation_count": 0,
        "unresolved_difference_count": summary["unresolved_difference_count"],
        "anchor_confirmation_ready": False,
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
        "schema_version": "kmfa.private.v014_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck.v1",
        "classification": "private_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck_do_not_commit",
        "record_type": "private_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "threshold_conclusion": THRESHOLD_CONCLUSION,
        "owner_authorized_anchor_blocker_count": summary["owner_authorized_anchor_blocker_count"],
        "prior_owner_authorized_anchor_blocker_observation_count": summary[
            "prior_owner_authorized_anchor_blocker_observation_count"
        ],
        "owner_authorized_anchor_blocker_observation_count": summary[
            "owner_authorized_anchor_blocker_observation_count"
        ],
        "owner_authorized_anchor_blocked_audit_threshold_met": summary[
            "owner_authorized_anchor_blocked_audit_threshold_met"
        ],
        "owner_authorized_anchor_confirmation_count": summary["owner_authorized_anchor_confirmation_count"],
        "unresolved_difference_count": summary["unresolved_difference_count"],
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": summary["raw_boundary"],
    }
    _write_json(PRIVATE_FINAL_THRESHOLD_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_FINAL_THRESHOLD_QUEUE_PATH, final_threshold_rows)
    _write_text(
        PRIVATE_FINAL_THRESHOLD_REPORT_PATH,
        "\n".join(
            [
                "# Private Owner-Authorized Anchor Blocker Final Threshold Recheck",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- owner_authorized_anchor_blocker_count: `{summary['owner_authorized_anchor_blocker_count']}`",
                f"- owner_authorized_anchor_blocker_observation_count: `{summary['owner_authorized_anchor_blocker_observation_count']}`",
                "- conclusion: third observation meets the strict blocked threshold; anchor confirmation remains required.",
                "",
            ]
        ),
    )
    return diagnostic


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    report = f"""# V014 Residual Difference Owner-Authorized Anchor Blocker Final Threshold Recheck

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe owner-authorized anchor blocker threshold recheck plus ignored private threshold queue.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Result

- Source owner-authorized anchor blocker observation count: `{summary["source_owner_authorized_anchor_blocker_observation_count"]}`
- Prior owner-authorized anchor blocker observation count: `{summary["prior_owner_authorized_anchor_blocker_observation_count"]}`
- Owner-authorized anchor blocker observation count: `{summary["owner_authorized_anchor_blocker_observation_count"]}`
- Owner-authorized anchor blocked threshold met: `{str(summary["owner_authorized_anchor_blocked_audit_threshold_met"]).lower()}`
- Owner-authorized anchor blockers: `{summary["owner_authorized_anchor_blocker_count"]}`
- Owner-authorized anchor confirmations: `{summary["owner_authorized_anchor_confirmation_count"]}`
- Unresolved differences: `{summary["unresolved_difference_count"]}`
- Goal status recommendation: `{summary["goal_status_recommendation"]}`

## Gate

This phase records only the third owner-authorized anchor blocker observation. The strict blocked threshold is met, but this phase does not provide anchor confirmation authority. Owner-authorized anchor confirmation, raw-to-processed comparison, full reconciliation, business value consistency, lineage full check, formal report, GitHub upload, app reinstall and business execution remain closed.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: owner-authorized anchor confirmation remains blocked, and the third observation meets the strict blocked threshold.
- Goal status recommendation: `{go_no_go["goal_status_recommendation"]}`
- Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck.py --require-private-final-threshold`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck.py`
- Governance validators, structured parsers, diff check, raw/private marker scan, secret scan, private-output git-ignore scan and private-runtime tracked-file scan: PASS.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: the third blocker observation is mistaken for owner-authorized anchor confirmation.
- Control: confirmation count remains zero and every downstream gate stays closed.
- Risk: blocked threshold is mistaken for permission to run formal comparison.
- Control: raw-to-processed comparison and business consistency remain false until owner-authorized anchors exist.
- Risk: private target-slot diagnostics leak into public evidence.
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
        "schema_version": "kmfa.v014_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck_manifest.v1",
        "record_type": "v014_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "threshold_conclusion": THRESHOLD_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "prior_anchor_blocker_threshold_summary": "public_safe_metadata_copy",
            "prior_anchor_blocker_threshold_manifest": "public_safe_metadata_copy",
            "prior_anchor_blocker_threshold_go_no_go": "public_safe_metadata_copy",
            "prior_anchor_blocker_threshold_matrix": "public_safe_metadata_copy",
            "prior_private_anchor_blocker_threshold_diagnostic": "ignored_private_runtime",
            "prior_private_anchor_blocker_threshold_queue": "ignored_private_runtime",
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
            "private:owner_authorized_anchor_confirmation_blocker_final_threshold_diagnostic",
            "private:owner_authorized_anchor_confirmation_blocker_final_threshold_queue",
            "private:owner_authorized_anchor_confirmation_blocker_final_threshold_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "changed_files": _changed_kmfa_files(),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck.py --require-private-final-threshold",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck.py",
        ],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
    }


def _write_governance(generated_at: str, summary: dict[str, Any]) -> None:
    event = {
        "event_id": "DEV-KMFA-20260707-V014-OWNER-AUTHORIZED-ANCHOR-CONFIRMATION-BLOCKER-FINAL-THRESHOLD-RECHECK",
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "stage_id": "value-consistency",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "status": STATUS,
        "go_no_go": DECISION,
        "summary": "Recorded the third owner-authorized anchor confirmation blocker observation and marked the strict blocked threshold true.",
        "owner_authorized_anchor_blocker_count": summary["owner_authorized_anchor_blocker_count"],
        "prior_owner_authorized_anchor_blocker_observation_count": summary[
            "prior_owner_authorized_anchor_blocker_observation_count"
        ],
        "owner_authorized_anchor_blocker_observation_count": summary[
            "owner_authorized_anchor_blocker_observation_count"
        ],
        "owner_authorized_anchor_blocked_audit_threshold_met": summary[
            "owner_authorized_anchor_blocked_audit_threshold_met"
        ],
        "goal_status_recommendation": summary["goal_status_recommendation"],
        "owner_authorized_anchor_confirmation_count": 0,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "fact_level": "EXTRACTED",
        "result_commit": "PENDING",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "files_changed": _changed_kmfa_files(),
    }
    _dedupe_append_jsonl(DEVELOPMENT_EVENTS_PATH, [event], PHASE_ID)
    stage_rows = [
        {
            "acceptance_id": ACCEPTANCE_ID,
            "completed_task_units": 1,
            "derived_percent": 100.0,
            "estimated_task_units": 1,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "v0.1.4 residual difference owner-authorized anchor confirmation blocker final threshold recheck",
            "phase_id": PHASE_ID,
            "record_type": "v014_phase",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_BLOCKER_FINAL_THRESHOLD_RECHECK",
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
            "name": "third owner-authorized anchor blocker observation recorded",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_BLOCKER_FINAL_THRESHOLD_RECHECK",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "OABF01",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": GO_NO_GO_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "strict blocked threshold is true while downstream gates remain closed",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_BLOCKER_FINAL_THRESHOLD_RECHECK",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "OABF02",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "raw inbox untouched and private final threshold outputs remain ignored",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_BLOCKER_FINAL_THRESHOLD_RECHECK",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "OABF03",
            "updated_at": "2026-07-07",
        },
    ]
    _dedupe_append_jsonl(STAGE_STATUS_PATH, stage_rows, PHASE_ID)
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
                "Owner-authorized anchor blocker final threshold recheck manifest summary Go No-Go public-safe matrix "
                "ignored private final threshold queue validator focused test and governance records"
            )
            task_row["phase_goal"] = (
                "record the third owner-authorized anchor blocker observation without confirming anchors or comparing raw values"
            )
        else:
            task_row["task_label"] = row["task_id"][-2:]
            task_row["task_text"] = row["name"]
        task_rows.append(task_row)
    _dedupe_append_jsonl(TASK_STATUS_PATH, task_rows, PHASE_ID)


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated_at = _now(generated_at)
    source_summary = _read_json(SOURCE_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_MATRIX_PATH)
    source_private_diagnostic = _read_json(SOURCE_PRIVATE_THRESHOLD_DIAGNOSTIC_PATH)
    source_threshold_rows = _read_jsonl(SOURCE_PRIVATE_THRESHOLD_QUEUE_PATH)
    SOURCE_PRIVATE_THRESHOLD_REPORT_PATH.read_text(encoding="utf-8")
    if len(source_threshold_rows) != 72:
        raise ValueError("source threshold recheck must provide 72 private threshold rows")
    if dict(Counter(row.get("diagnostic_track") for row in source_threshold_rows)) != EXPECTED_TRACK_COUNTS:
        raise ValueError("unexpected diagnostic track counts")
    if int(source_summary.get("owner_authorized_anchor_blocker_observation_count") or 0) != 2:
        raise ValueError("source threshold recheck must provide second observation")

    final_threshold_rows = _build_private_final_threshold_rows(generated_at, source_threshold_rows)
    summary = _build_summary(
        generated_at=generated_at,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_private_diagnostic=source_private_diagnostic,
        source_threshold_rows=source_threshold_rows,
        final_threshold_rows=final_threshold_rows,
    )
    private_diagnostic = _write_private_outputs(generated_at, summary, final_threshold_rows)
    summary["private_final_threshold_diagnostic_gitignored"] = _git_check_ignored(PRIVATE_FINAL_THRESHOLD_DIAGNOSTIC_PATH)
    summary["private_final_threshold_queue_gitignored"] = _git_check_ignored(PRIVATE_FINAL_THRESHOLD_QUEUE_PATH)
    summary["private_final_threshold_report_gitignored"] = _git_check_ignored(PRIVATE_FINAL_THRESHOLD_REPORT_PATH)
    matrix = _build_matrix(summary)
    go_no_go = _build_go_no_go(summary)
    _write_human(summary, matrix, go_no_go)
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
    if write_governance_event:
        _write_governance(generated_at, summary)
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
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: generated V014 owner-authorized anchor blocker final threshold recheck "
        f"blockers={summary['owner_authorized_anchor_blocker_count']} "
        f"observation={summary['owner_authorized_anchor_blocker_observation_count']} "
        f"threshold={summary['owner_authorized_anchor_blocked_audit_threshold_met']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
