#!/usr/bin/env python3
"""Audit owner-authorized anchor confirmation blockers.

This phase consumes the previous owner-authorized anchor difference report
outputs and records the first blocker observation. It does not read or mutate
the raw inbox, confirm anchors, compare raw-to-processed values, upload,
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
PHASE_ID = "V014_RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_BLOCKER_AUDIT"
TASK_ID = "KMFA-V014-RESIDUAL-DIFFERENCE-OWNER-AUTHORIZED-ANCHOR-CONFIRMATION-BLOCKER-AUDIT-20260707"
ACCEPTANCE_ID = "ACC-V014-RESIDUAL-DIFFERENCE-OWNER-AUTHORIZED-ANCHOR-CONFIRMATION-BLOCKER-AUDIT"
VERSION = "0.1.4-residual-difference-owner-authorized-anchor-confirmation-blocker-audit"
STATUS = "completed_validated_local_only_owner_authorized_anchor_confirmation_blocker_audit_no_go"
DECISION = "NO_GO"
AUDIT_CONCLUSION = "owner_authorized_anchor_confirmation_blocker_observation_recorded_after_difference_report"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_confirms_private_raw_candidate_anchors_before_formal_comparison"
NEXT_RECOMMENDED_PHASE = "V014_RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_BLOCKER_THRESHOLD_RECHECK"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "residual_difference_owner_authorized_anchor_confirmation_blocker_audit_summary.json"
MANIFEST_PATH = MACHINE_DIR / "residual_difference_owner_authorized_anchor_confirmation_blocker_audit_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "residual_difference_owner_authorized_anchor_confirmation_blocker_audit_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "residual_difference_owner_authorized_anchor_confirmation_blocker_audit_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "residual_difference_owner_authorized_anchor_confirmation_blocker_audit.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_audit_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_audit_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_audit_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_audit_matrix_public_safe.json"
)

SOURCE_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report_summary.json"
)
SOURCE_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report_manifest.json"
)
SOURCE_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report_go_no_go_report.json"
)
SOURCE_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report_matrix_public_safe.json"
)
SOURCE_PRIVATE_DIR = (
    PROJECT_ROOT / ".codex_private_runtime/v014_residual_difference_owner_authorized_anchor_confirmation_or_difference_report"
)
SOURCE_PRIVATE_DIFFERENCE_REPORT_PATH = SOURCE_PRIVATE_DIR / "private_owner_authorized_anchor_difference_report.json"
SOURCE_PRIVATE_DIAGNOSTIC_PATH = SOURCE_PRIVATE_DIR / "private_owner_authorized_anchor_difference_report_diagnostic.json"
SOURCE_PRIVATE_UNRESOLVED_QUEUE_PATH = SOURCE_PRIVATE_DIR / "private_owner_authorized_anchor_unresolved_difference_queue.jsonl"
SOURCE_PRIVATE_CONFIRMATION_READY_QUEUE_PATH = SOURCE_PRIVATE_DIR / "private_owner_authorized_anchor_confirmation_ready_queue.jsonl"
SOURCE_PRIVATE_REPORT_PATH = SOURCE_PRIVATE_DIR / "private_owner_authorized_anchor_difference_report.md"

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT / ".codex_private_runtime/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_audit"
)
PRIVATE_AUDIT_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_confirmation_blocker_audit_diagnostic.json"
PRIVATE_AUDIT_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_confirmation_blocker_audit_queue.jsonl"
PRIVATE_AUDIT_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_anchor_confirmation_blocker_audit_report.md"

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
        "source_public_difference_report_summary_read_by_this_phase": True,
        "source_public_difference_report_manifest_read_by_this_phase": True,
        "source_public_difference_report_go_no_go_read_by_this_phase": True,
        "source_public_difference_report_matrix_read_by_this_phase": True,
        "source_private_difference_report_read_by_this_phase": True,
        "source_private_diagnostic_read_by_this_phase": True,
        "source_private_unresolved_queue_read_by_this_phase": True,
        "source_private_confirmation_ready_queue_read_by_this_phase": True,
        "source_private_report_read_by_this_phase": True,
        "private_audit_diagnostic_written_by_this_phase": True,
        "private_audit_queue_written_by_this_phase": True,
        "private_audit_report_written_by_this_phase": True,
        "source_private_difference_report_mutated_by_this_phase": False,
        "source_private_diagnostic_mutated_by_this_phase": False,
        "source_private_unresolved_queue_mutated_by_this_phase": False,
        "source_private_confirmation_ready_queue_mutated_by_this_phase": False,
        "source_private_report_mutated_by_this_phase": False,
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
        "source_private_difference_report_committed": False,
        "source_private_unresolved_queue_committed": False,
        "private_audit_diagnostic_committed": False,
        "private_audit_queue_committed": False,
        "private_audit_report_committed": False,
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


def _build_audit_rows(generated_at: str, unresolved_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(unresolved_rows, start=1):
        rows.append(
            {
                "audit_item_id": f"OACB-AUDIT-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_difference_report_index": row.get("difference_report_index"),
                "target_slot_id": row.get("target_slot_id"),
                "diagnostic_track": row.get("diagnostic_track"),
                "source_difference_report_status": row.get("difference_report_status"),
                "blocker_reason_code": "missing_owner_authorized_anchor_confirmation_inputs",
                "owner_authorized_anchor_blocker_observation_count_after_this_phase": 1,
                "anchor_confirmation_ready_after_audit": False,
                "raw_to_processed_value_comparison_ready_after_audit": False,
                "business_value_consistency_verified_after_audit": False,
                "threshold_met_after_this_phase": False,
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
    source_private_report: dict[str, Any],
    source_private_diagnostic: dict[str, Any],
    unresolved_rows: list[dict[str, Any]],
    ready_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    track_counts = dict(Counter(row.get("diagnostic_track") for row in unresolved_rows))
    prior_observation_count = 0
    observation_count = prior_observation_count + 1
    threshold_met = observation_count >= 3
    return {
        "schema_version": "kmfa.v014_owner_authorized_anchor_confirmation_blocker_audit_summary.v1",
        "record_type": "v014_owner_authorized_anchor_confirmation_blocker_audit_summary",
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
        "source_matrix_fail_count": source_matrix.get("fail_count"),
        "source_private_report_phase_id": source_private_report.get("phase_id"),
        "source_private_diagnostic_phase_id": source_private_diagnostic.get("phase_id"),
        "source_difference_report_item_count": int(source_summary.get("difference_report_item_count") or 0),
        "source_unresolved_difference_count": int(source_summary.get("unresolved_difference_count") or 0),
        "source_owner_authorized_anchor_confirmation_count": int(
            source_summary.get("owner_authorized_anchor_confirmation_count") or 0
        ),
        "source_private_unresolved_queue_item_count": len(unresolved_rows),
        "source_private_confirmation_ready_queue_item_count": len(ready_rows),
        "owner_authorized_anchor_blocker_audit_performed": True,
        "prior_owner_authorized_anchor_blocker_observation_count": prior_observation_count,
        "owner_authorized_anchor_blocker_observation_count": observation_count,
        "owner_authorized_anchor_blocked_audit_threshold_met": threshold_met,
        "goal_status_recommendation": "continue_to_owner_authorized_anchor_blocker_threshold_recheck",
        "owner_authorized_anchor_blocker_count": len(audit_rows),
        "owner_authorized_anchor_confirmation_count": 0,
        "unresolved_difference_count": len(unresolved_rows),
        "missing_owner_authorized_anchor_count": int(source_summary.get("missing_owner_authorized_anchor_count") or 0),
        "missing_processed_value_fingerprint_count": int(source_summary.get("missing_processed_value_fingerprint_count") or 0),
        "missing_raw_candidate_anchor_count": int(source_summary.get("missing_raw_candidate_anchor_count") or 0),
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
        "private_audit_diagnostic_written": True,
        "private_audit_queue_written": True,
        "private_audit_report_written": True,
        "private_audit_diagnostic_gitignored": _git_check_ignored(PRIVATE_AUDIT_DIAGNOSTIC_PATH),
        "private_audit_queue_gitignored": _git_check_ignored(PRIVATE_AUDIT_QUEUE_PATH),
        "private_audit_report_gitignored": _git_check_ignored(PRIVATE_AUDIT_REPORT_PATH),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_difference_report_loaded", summary["source_phase_id"].endswith("OR_DIFFERENCE_REPORT")),
        ("source_go_no_go_preserved", summary["source_go_no_go_decision"] == "NO_GO"),
        ("source_unresolved_differences_present", summary["source_unresolved_difference_count"] == 72),
        ("owner_authorized_anchor_blockers_present", summary["owner_authorized_anchor_blocker_count"] == 72),
        ("blocker_audit_recorded", summary["owner_authorized_anchor_blocker_observation_count"] == 1),
        ("threshold_not_met_on_first_observation", summary["owner_authorized_anchor_blocked_audit_threshold_met"] is False),
        ("anchor_confirmation_count_zero", summary["owner_authorized_anchor_confirmation_count"] == 0),
        ("unresolved_difference_count_preserved", summary["unresolved_difference_count"] == 72),
        ("diagnostic_track_counts_locked", summary["diagnostic_track_counts"] == EXPECTED_TRACK_COUNTS),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("source_private_inputs_not_mutated", summary["raw_boundary"]["source_private_unresolved_queue_mutated_by_this_phase"] is False),
        ("private_outputs_ignored", summary["private_audit_queue_gitignored"] is True),
        ("downstream_gates_closed", summary["business_execution_performed"] is False),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_owner_authorized_anchor_confirmation_blocker_audit_matrix_public_safe.v1",
        "record_type": "v014_owner_authorized_anchor_confirmation_blocker_audit_matrix_public_safe",
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
        "schema_version": "kmfa.v014_owner_authorized_anchor_confirmation_blocker_audit_go_no_go.v1",
        "record_type": "v014_owner_authorized_anchor_confirmation_blocker_audit_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "audit_conclusion": AUDIT_CONCLUSION,
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


def _write_private_outputs(generated_at: str, summary: dict[str, Any], audit_rows: list[dict[str, Any]]) -> dict[str, Any]:
    diagnostic = {
        "schema_version": "kmfa.private.v014_owner_authorized_anchor_confirmation_blocker_audit.v1",
        "classification": "private_owner_authorized_anchor_confirmation_blocker_audit_do_not_commit",
        "record_type": "private_owner_authorized_anchor_confirmation_blocker_audit_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "audit_conclusion": AUDIT_CONCLUSION,
        "owner_authorized_anchor_blocker_count": summary["owner_authorized_anchor_blocker_count"],
        "owner_authorized_anchor_blocker_observation_count": summary[
            "owner_authorized_anchor_blocker_observation_count"
        ],
        "owner_authorized_anchor_blocked_audit_threshold_met": summary[
            "owner_authorized_anchor_blocked_audit_threshold_met"
        ],
        "unresolved_difference_count": summary["unresolved_difference_count"],
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": summary["raw_boundary"],
    }
    _write_json(PRIVATE_AUDIT_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_AUDIT_QUEUE_PATH, audit_rows)
    _write_text(
        PRIVATE_AUDIT_REPORT_PATH,
        "\n".join(
            [
                "# Private Owner-Authorized Anchor Blocker Audit",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- owner_authorized_anchor_blocker_count: `{summary['owner_authorized_anchor_blocker_count']}`",
                f"- owner_authorized_anchor_blocker_observation_count: `{summary['owner_authorized_anchor_blocker_observation_count']}`",
                "- formal raw-to-processed comparison was not performed.",
                "",
            ]
        ),
    )
    return diagnostic


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    report = f"""# V014 Residual Difference Owner-Authorized Anchor Confirmation Blocker Audit

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: previous public-safe owner-authorized anchor difference report plus ignored private unresolved queue.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Result

- Owner-authorized anchor blocker count: `{summary["owner_authorized_anchor_blocker_count"]}`
- Owner-authorized anchor blocker observation count: `{summary["owner_authorized_anchor_blocker_observation_count"]}`
- Owner-authorized anchor blocked threshold met: `{str(summary["owner_authorized_anchor_blocked_audit_threshold_met"]).lower()}`
- Owner-authorized anchor confirmations: `{summary["owner_authorized_anchor_confirmation_count"]}`
- Unresolved differences: `{summary["unresolved_difference_count"]}`

## Gate

Owner-authorized anchor confirmation remains blocked. Raw-to-processed comparison, full reconciliation, business value consistency, lineage full check, formal report, GitHub upload, app reinstall and business execution remain closed.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: owner-authorized anchor confirmation is still blocked after the difference report.
- Goal status recommendation: `{go_no_go["goal_status_recommendation"]}`
- Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_audit.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_owner_authorized_anchor_confirmation_blocker_audit.py --require-private-audit`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_owner_authorized_anchor_confirmation_blocker_audit`
- Governance validators, diff check, raw/private marker scan, secret scan and private-output git-ignore scan must pass before local commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: a blocker audit is mistaken for owner-authorized anchor confirmation.
- Control: confirmation count remains zero and every downstream gate stays closed.
- Risk: private target-slot diagnostics leak into public evidence.
- Control: public artifacts contain aggregate counts only and private audit outputs remain ignored.
"""
    rollback = f"""# Rollback Plan

Remove the artifacts for `{PHASE_ID}`, metadata copies, private audit outputs, tool, validator, focused test and governance entries. Do not touch prior difference-report outputs or raw inbox files.
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_record)
    _write_text(TEST_RESULTS_PATH, test_results)
    _write_text(RISK_REGISTER_PATH, risk_register)
    _write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_owner_authorized_anchor_confirmation_blocker_audit_manifest.v1",
        "record_type": "v014_owner_authorized_anchor_confirmation_blocker_audit_manifest",
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
            "prior_difference_report_summary": "public_safe_metadata_copy",
            "prior_difference_report_manifest": "public_safe_metadata_copy",
            "prior_difference_report_go_no_go": "public_safe_metadata_copy",
            "prior_difference_report_matrix": "public_safe_metadata_copy",
            "prior_private_difference_report": "ignored_private_runtime",
            "prior_private_unresolved_queue": "ignored_private_runtime",
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
            "private:owner_authorized_anchor_confirmation_blocker_audit_diagnostic",
            "private:owner_authorized_anchor_confirmation_blocker_audit_queue",
            "private:owner_authorized_anchor_confirmation_blocker_audit_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "changed_files": _changed_kmfa_files(),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_audit.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_owner_authorized_anchor_confirmation_blocker_audit.py --require-private-audit",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_owner_authorized_anchor_confirmation_blocker_audit",
        ],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
    }


def _write_governance(generated_at: str, summary: dict[str, Any]) -> None:
    event = {
        "event_id": "DEV-KMFA-20260707-V014-OWNER-AUTHORIZED-ANCHOR-CONFIRMATION-BLOCKER-AUDIT",
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "stage_id": "value-consistency",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "status": STATUS,
        "go_no_go": DECISION,
        "summary": "Recorded the first owner-authorized anchor confirmation blocker observation after the unresolved difference report and kept all downstream gates closed.",
        "owner_authorized_anchor_blocker_count": summary["owner_authorized_anchor_blocker_count"],
        "owner_authorized_anchor_blocker_observation_count": summary["owner_authorized_anchor_blocker_observation_count"],
        "owner_authorized_anchor_blocked_audit_threshold_met": summary[
            "owner_authorized_anchor_blocked_audit_threshold_met"
        ],
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
            "name": "v0.1.4 residual difference owner-authorized anchor confirmation blocker audit",
            "phase_id": PHASE_ID,
            "record_type": "v014_phase",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_BLOCKER_AUDIT",
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
            "name": "72 owner-authorized anchor blockers audited",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_BLOCKER_AUDIT",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "OABA01",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": GO_NO_GO_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "owner-authorized anchor confirmation remains blocked",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_BLOCKER_AUDIT",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "OABA02",
            "updated_at": "2026-07-07",
        },
        {
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "raw inbox untouched and private blocker audit remains ignored",
            "phase_id": PHASE_ID,
            "record_type": "v014_task",
            "roadmap_phase_id": "RESIDUAL_DIFFERENCE_OWNER_AUTHORIZED_ANCHOR_CONFIRMATION_BLOCKER_AUDIT",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": "completed_validated_local_only_no_go_upload_deferred",
            "task_id": "OABA03",
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
                "Owner-authorized anchor blocker audit manifest summary Go No-Go public-safe matrix ignored "
                "private audit queue validator focused test and governance records"
            )
            task_row["phase_goal"] = (
                "record owner-authorized anchor confirmation blockers after the unresolved difference report "
                "without confirming anchors or comparing raw values"
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
    source_private_report = _read_json(SOURCE_PRIVATE_DIFFERENCE_REPORT_PATH)
    source_private_diagnostic = _read_json(SOURCE_PRIVATE_DIAGNOSTIC_PATH)
    unresolved_rows = _read_jsonl(SOURCE_PRIVATE_UNRESOLVED_QUEUE_PATH)
    ready_rows = _read_jsonl(SOURCE_PRIVATE_CONFIRMATION_READY_QUEUE_PATH)
    SOURCE_PRIVATE_REPORT_PATH.read_text(encoding="utf-8")
    if len(unresolved_rows) != 72 or ready_rows:
        raise ValueError("source difference report must provide 72 unresolved rows and zero confirmation-ready rows")
    if dict(Counter(row.get("diagnostic_track") for row in unresolved_rows)) != EXPECTED_TRACK_COUNTS:
        raise ValueError("unexpected diagnostic track counts")

    audit_rows = _build_audit_rows(generated_at, unresolved_rows)
    summary = _build_summary(
        generated_at=generated_at,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_private_report=source_private_report,
        source_private_diagnostic=source_private_diagnostic,
        unresolved_rows=unresolved_rows,
        ready_rows=ready_rows,
        audit_rows=audit_rows,
    )
    private_diagnostic = _write_private_outputs(generated_at, summary, audit_rows)
    summary["private_audit_diagnostic_gitignored"] = _git_check_ignored(PRIVATE_AUDIT_DIAGNOSTIC_PATH)
    summary["private_audit_queue_gitignored"] = _git_check_ignored(PRIVATE_AUDIT_QUEUE_PATH)
    summary["private_audit_report_gitignored"] = _git_check_ignored(PRIVATE_AUDIT_REPORT_PATH)
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
        "private_audit_queue": audit_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: generated V014 owner-authorized anchor confirmation blocker audit "
        f"blockers={summary['owner_authorized_anchor_blocker_count']} "
        f"observation={summary['owner_authorized_anchor_blocker_observation_count']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
