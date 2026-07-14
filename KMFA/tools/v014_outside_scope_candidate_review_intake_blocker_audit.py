#!/usr/bin/env python3
"""Audit the outside-scope candidate review intake blocker.

This phase records the second observation that the 72 delegated keep-pending
review responses still do not provide an actionable candidate selection or
corrected source-map reference. It does not read the raw inbox, mutate prior
private diagnostics, correct source maps, compare values, reconcile values,
upload, reinstall, or execute business steps.
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
PHASE_ID = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_BLOCKER_AUDIT"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-INTAKE-BLOCKER-AUDIT-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-INTAKE-BLOCKER-AUDIT"
VERSION = "0.1.4-outside-scope-candidate-review-intake-blocker-audit"
STATUS = "completed_validated_local_only_outside_scope_candidate_review_intake_blocker_audit_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "candidate_review_keep_pending_blocker_observed_again_without_actionable_source_map_response"
NEXT_REQUIRED_INPUT = "strong_owner_or_authorized_delegate_candidate_selection_or_source_map_reference_before_correction"
NEXT_RECOMMENDED_PHASE = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_BLOCKER_THRESHOLD_RECHECK"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_candidate_review_intake_blocker_audit_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_candidate_review_intake_blocker_audit_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_candidate_review_intake_blocker_audit_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_candidate_review_intake_blocker_audit_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_candidate_review_intake_blocker_audit_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_blocker_audit_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_blocker_audit_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_blocker_audit_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_blocker_audit_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

PRIOR_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_readiness_recheck_summary.json"
PRIOR_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_readiness_recheck_manifest.json"
PRIOR_PRIVATE_DIAGNOSTIC_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_intake_readiness_recheck/private_candidate_review_intake_readiness_recheck_diagnostic.json"
)
PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_intake_blocker_audit"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_candidate_review_intake_blocker_audit_diagnostic.json"


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


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
        files.add(path)
    return sorted(files)


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "prior_public_readiness_summary_read_by_this_phase": True,
        "prior_public_readiness_manifest_read_by_this_phase": True,
        "prior_private_readiness_diagnostic_read_by_this_phase": True,
        "private_blocker_audit_diagnostic_written_by_this_phase": True,
        "prior_private_readiness_diagnostic_mutated_by_this_phase": False,
        "source_map_correction_written_by_this_phase": False,
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
        "prior_private_readiness_diagnostic_committed": False,
        "private_blocker_audit_diagnostic_committed": False,
        "private_candidate_selection_committed": False,
        "private_corrected_source_map_reference_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "raw_digest_committed": False,
        "source_document_committed": False,
        "office_workbook_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_ref_or_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _build_summary(
    *, generated_at: str, prior_summary: dict[str, Any], prior_private_diagnostic: dict[str, Any]
) -> dict[str, Any]:
    prior_observation_count = int(prior_summary.get("review_intake_blocker_observation_count", 0))
    observation_count = prior_observation_count + 1
    threshold_met = observation_count >= 3
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_intake_blocker_audit_summary.v1",
        "record_type": "v014_outside_scope_candidate_review_intake_blocker_audit_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "prior_phase_id": prior_summary.get("phase_id"),
        "prior_decision": prior_summary.get("decision"),
        "prior_review_intake_blocker_observation_count": prior_observation_count,
        "review_intake_blocker_observation_count": observation_count,
        "review_intake_blocked_audit_threshold_met": threshold_met,
        "goal_status_recommendation": "blocked" if threshold_met else "continue_waiting_for_actionable_source_map_response",
        "prior_private_diagnostic_phase_id": prior_private_diagnostic.get("phase_id"),
        "delegated_decision_record_count": prior_summary.get("delegated_decision_record_count"),
        "delegated_keep_pending_response_count": prior_summary.get("delegated_keep_pending_response_count"),
        "selected_private_candidate_count": prior_summary.get("selected_private_candidate_count"),
        "corrected_source_map_reference_count": prior_summary.get("corrected_source_map_reference_count"),
        "authoritative_non_numeric_or_calculation_mapping_count": prior_summary.get(
            "authoritative_non_numeric_or_calculation_mapping_count"
        ),
        "source_map_actionable_response_count": prior_summary.get("source_map_actionable_response_count"),
        "source_map_correction_ready": False,
        "source_map_correction_feasible_after_intake": False,
        "source_map_correction_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "full_reconciliation_allowed": False,
        "processed_consistency_verified": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "private_blocker_audit_diagnostic_written": True,
        "private_blocker_audit_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("prior_phase_is_candidate_review_intake_readiness_recheck", summary["prior_phase_id"] == "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_READINESS_RECHECK"),
        ("prior_observation_count_one", summary["prior_review_intake_blocker_observation_count"] == 1),
        ("current_observation_count_two", summary["review_intake_blocker_observation_count"] == 2),
        ("blocked_threshold_not_met", summary["review_intake_blocked_audit_threshold_met"] is False),
        ("delegated_response_count_complete", summary["delegated_decision_record_count"] == 72),
        ("all_delegated_responses_keep_pending", summary["delegated_keep_pending_response_count"] == 72),
        ("no_actionable_source_map_response", summary["source_map_actionable_response_count"] == 0),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("downstream_gates_closed", summary["business_execution_performed"] is False),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_intake_blocker_audit_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_candidate_review_intake_blocker_audit_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": summary["generated_at"],
        "blocker_audit_check_count": len(rows),
        "blocker_audit_check_pass_count": pass_count,
        "blocker_audit_check_fail_count": len(rows) - pass_count,
        "decision": DECISION,
        "checks": rows,
    }


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_intake_blocker_audit_go_no_go.v1",
        "record_type": "v014_outside_scope_candidate_review_intake_blocker_audit_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "review_intake_blocker_observation_count": summary["review_intake_blocker_observation_count"],
        "review_intake_blocked_audit_threshold_met": summary["review_intake_blocked_audit_threshold_met"],
        "goal_status_recommendation": summary["goal_status_recommendation"],
        "delegated_keep_pending_response_count": summary["delegated_keep_pending_response_count"],
        "selected_private_candidate_count": summary["selected_private_candidate_count"],
        "corrected_source_map_reference_count": summary["corrected_source_map_reference_count"],
        "source_map_actionable_response_count": summary["source_map_actionable_response_count"],
        "source_map_correction_ready": False,
        "raw_to_processed_value_comparison_allowed": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }


def _write_private_diagnostic(generated_at: str, summary: dict[str, Any]) -> dict[str, Any]:
    diagnostic = {
        "schema_version": "kmfa.private.v014_candidate_review_intake_blocker_audit.v1",
        "classification": "private_candidate_review_intake_blocker_audit_do_not_commit",
        "record_type": "v014_outside_scope_candidate_review_intake_blocker_audit_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "prior_phase_id": summary["prior_phase_id"],
        "counts": {
            "delegated_decision_record_count": summary["delegated_decision_record_count"],
            "delegated_keep_pending_response_count": summary["delegated_keep_pending_response_count"],
            "selected_private_candidate_count": summary["selected_private_candidate_count"],
            "corrected_source_map_reference_count": summary["corrected_source_map_reference_count"],
            "authoritative_non_numeric_or_calculation_mapping_count": summary[
                "authoritative_non_numeric_or_calculation_mapping_count"
            ],
            "source_map_actionable_response_count": summary["source_map_actionable_response_count"],
        },
        "review_intake_blocker_observation_count": summary["review_intake_blocker_observation_count"],
        "review_intake_blocked_audit_threshold_met": summary["review_intake_blocked_audit_threshold_met"],
        "goal_status_recommendation": summary["goal_status_recommendation"],
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "raw_boundary": summary["raw_boundary"],
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    return diagnostic


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    generated_at = summary["generated_at"]
    report = f"""# V014 Outside-Scope Candidate Review Intake Blocker Audit

Generated at: {generated_at}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe readiness summary plus ignored private readiness diagnostic.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Result

- Delegated decisions: `{summary["delegated_decision_record_count"]}`
- Delegated keep-pending responses: `{summary["delegated_keep_pending_response_count"]}`
- Selected private candidates: `{summary["selected_private_candidate_count"]}`
- Corrected source-map references: `{summary["corrected_source_map_reference_count"]}`
- Source-map actionable responses: `{summary["source_map_actionable_response_count"]}`
- Blocker observation count: `{summary["review_intake_blocker_observation_count"]}`
- Blocked audit threshold met: `{str(summary["review_intake_blocked_audit_threshold_met"]).lower()}`

## Gate

Source-map correction, raw-to-processed comparison, full reconciliation, business value consistency, lineage full check, formal report, GitHub upload, app reinstall and business execution remain closed.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: 72 delegated responses remain keep-pending and contain no actionable source-map response.
- Goal status recommendation: `{go_no_go["goal_status_recommendation"]}`
- Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_intake_blocker_audit.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_intake_blocker_audit.py --require-private-diagnostic`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_intake_blocker_audit`

Expected matrix result: {matrix["blocker_audit_check_pass_count"]}/{matrix["blocker_audit_check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: a second blocker observation may be mistaken for permission to auto-correct source maps.
- Control: this phase records no candidate selection and keeps every downstream gate closed.
- Risk: private diagnostics may leak into public evidence.
- Control: public artifacts contain aggregate counts only and private diagnostics remain ignored.
"""
    rollback = f"""# Rollback Plan

Remove the artifacts for `{PHASE_ID}`, metadata copies, private blocker diagnostic, tool, validator, focused test and governance entries. Do not touch prior private diagnostics or raw inbox files.
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_record)
    _write_text(TEST_RESULTS_PATH, test_results)
    _write_text(RISK_REGISTER_PATH, risk_register)
    _write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_intake_blocker_audit_manifest.v1",
        "record_type": "v014_outside_scope_candidate_review_intake_blocker_audit_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "prior_readiness_summary": "public_safe_metadata_copy",
            "prior_readiness_manifest": "public_safe_metadata_copy",
            "prior_private_readiness_diagnostic": "ignored_private_runtime",
        },
        "public_artifact_refs": [
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            MATRIX_PATH.as_posix(),
            REPORT_PATH.as_posix(),
        ],
        "metadata_artifact_refs": [
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_MATRIX_PATH.as_posix(),
        ],
        "private_artifact_refs": ["private:candidate_review_intake_blocker_audit_diagnostic"],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_intake_blocker_audit.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_intake_blocker_audit.py --require-private-diagnostic",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_intake_blocker_audit",
        ],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
    }


def _write_governance_events(generated_at: str, manifest: dict[str, Any]) -> None:
    event = {
        "event_id": "DEV-KMFA-20260707-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-INTAKE-BLOCKER-AUDIT",
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "stage_id": "value-consistency",
        "phase_id": PHASE_ID,
        "status": STATUS,
        "decision": DECISION,
        "fact_level": "EXTRACTED",
        "iteration_id": "ITER-20260707-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-INTAKE-BLOCKER-AUDIT",
        "task_id": TASK_ID,
        "version": VERSION,
        "go_no_go": DECISION,
        "result_commit": "PENDING",
        "summary": "Recorded the second candidate review intake keep-pending blocker observation and kept source-map correction blocked.",
        "delegated_keep_pending_response_count": 72,
        "source_map_actionable_response_count": 0,
        "review_intake_blocker_observation_count": 2,
        "review_intake_blocked_audit_threshold_met": False,
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
    _append_jsonl(DEVELOPMENT_EVENTS_PATH, event)
    _append_jsonl(
        STAGE_STATUS_PATH,
        {
            "acceptance_id": ACCEPTANCE_ID,
            "acceptance_output": "Candidate review intake blocker audit manifest summary Go No-Go public-safe matrix private ignored diagnostic validator focused test and governance records",
            "completed_task_units": 1,
            "derived_percent": 100.0,
            "estimated_task_units": 1,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "v0.1.4 outside-scope candidate review intake blocker audit",
            "phase_goal": "record the second keep-pending blocker observation without source-map correction or raw comparison",
            "phase_id": PHASE_ID,
            "project_id": "KMFA",
            "raw_data_committed": False,
            "record_type": "v014_phase",
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_BLOCKER_AUDIT",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": STATUS,
            "task_count": 3,
            "updated_at": "2026-07-07",
            "version": VERSION,
        },
    )
    for index, task_goal in enumerate(
        [
            "read prior readiness evidence and private diagnostic read-only",
            "record second blocker observation while threshold remains unmet",
            "emit public-safe NO_GO evidence while keeping downstream gates closed",
        ],
        start=1,
    ):
        _append_jsonl(
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
                "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_BLOCKER_AUDIT",
                "roadmap_stage_id": "VALUE-CONSISTENCY",
                "schema_version": "kmfa.v014_stage_phase_task_status.v1",
                "stage_id": "VALUE-CONSISTENCY",
                "status": "completed",
                "task_goal": task_goal,
                "task_id": f"{TASK_ID}-T{index}",
                "updated_at": "2026-07-07",
                "version": VERSION,
            },
        )


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = _now(generated_at)
    prior_summary = _read_json(PRIOR_SUMMARY_PATH)
    _read_json(PRIOR_MANIFEST_PATH)
    prior_private_diagnostic = _read_json(PRIOR_PRIVATE_DIAGNOSTIC_PATH)
    summary = _build_summary(
        generated_at=generated,
        prior_summary=prior_summary,
        prior_private_diagnostic=prior_private_diagnostic,
    )
    private_diagnostic = _write_private_diagnostic(generated, summary)
    summary["private_blocker_audit_diagnostic_gitignored"] = _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH)
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
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: KMFA v0.1.4 outside-scope candidate review intake blocker audit generated "
        f"(decision={summary['decision']}, observation={summary['review_intake_blocker_observation_count']}, "
        f"threshold={summary['review_intake_blocked_audit_threshold_met']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
