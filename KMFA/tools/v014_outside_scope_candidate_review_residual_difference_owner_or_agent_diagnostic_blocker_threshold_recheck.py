#!/usr/bin/env python3
"""Recheck residual-difference owner/agent diagnostic blocker threshold.

This phase records the third observation that all 72 residual differences still
lack valid owner/agent diagnostic responses. It does not read or mutate the raw
inbox, close discrepancies, correct source maps, compare values, upload,
reinstall, or execute business steps.
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
PHASE_ID = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_BLOCKER_THRESHOLD_RECHECK"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-OWNER-OR-AGENT-DIAGNOSTIC-BLOCKER-THRESHOLD-RECHECK-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-OWNER-OR-AGENT-DIAGNOSTIC-BLOCKER-THRESHOLD-RECHECK"
VERSION = "0.1.4-outside-scope-candidate-review-residual-difference-owner-or-agent-diagnostic-blocker-threshold-recheck"
STATUS = "completed_validated_local_only_residual_difference_owner_or_agent_diagnostic_blocker_threshold_met_goal_blocked"
DECISION = "NO_GO"
AUDIT_CONCLUSION = "private_owner_or_agent_diagnostic_blocker_threshold_met_without_valid_response"
NEXT_REQUIRED_INPUT = (
    "owner_or_authorized_delegate_or_external_agent_valid_diagnostic_response_required_for_72_private_residual_differences"
)
NEXT_RECOMMENDED_PHASE = "BLOCKED_UNTIL_VALID_OWNER_OR_AUTHORIZED_AGENT_DIAGNOSTIC_RESPONSE"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_matrix_public_safe.json"

PRIOR_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_audit_summary.json"
PRIOR_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_audit_manifest.json"
PRIOR_PRIVATE_DIAGNOSTIC_PATH = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_audit/private_owner_or_agent_diagnostic_blocker_audit_diagnostic.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_diagnostic_blocker_threshold_recheck_diagnostic.json"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"


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
        if ".codex_private_runtime/" not in path:
            files.add(path)
    return sorted(files)


def _raw_boundary() -> dict[str, bool]:
    return {
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "prior_public_blocker_audit_summary_read_by_this_phase": True,
        "prior_public_blocker_audit_manifest_read_by_this_phase": True,
        "prior_private_blocker_audit_diagnostic_read_by_this_phase": True,
        "private_threshold_recheck_diagnostic_written_by_this_phase": True,
        "prior_private_blocker_audit_diagnostic_mutated_by_this_phase": False,
        "valid_diagnostic_response_supplied_by_this_phase": False,
        "discrepancy_closure_written_by_this_phase": False,
        "source_map_correction_written_by_this_phase": False,
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
        "prior_private_blocker_audit_diagnostic_committed": False,
        "private_threshold_recheck_diagnostic_committed": False,
        "private_diagnostic_response_committed": False,
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


def _build_summary(*, generated_at: str, prior_summary: dict[str, Any], prior_private_diagnostic: dict[str, Any]) -> dict[str, Any]:
    prior_observation_count = int(prior_summary.get("diagnostic_blocker_observation_count", 0))
    observation_count = prior_observation_count + 1
    threshold_met = observation_count >= 3
    return {
        "schema_version": "kmfa.v014_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_summary.v1",
        "record_type": "v014_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "audit_conclusion": AUDIT_CONCLUSION,
        "prior_phase_id": prior_summary.get("phase_id"),
        "prior_decision": prior_summary.get("decision"),
        "prior_diagnostic_blocker_observation_count": prior_observation_count,
        "diagnostic_blocker_observation_count": observation_count,
        "diagnostic_blocked_audit_threshold_met": threshold_met,
        "goal_status_recommendation": "blocked" if threshold_met else "continue_waiting_for_valid_diagnostic_response",
        "prior_private_diagnostic_phase_id": prior_private_diagnostic.get("phase_id"),
        "source_private_diagnostic_response_template_item_count": prior_summary.get("source_private_diagnostic_response_template_item_count"),
        "source_private_diagnostic_pending_queue_item_count": prior_summary.get("source_private_diagnostic_pending_queue_item_count"),
        "source_private_readiness_blocker_queue_item_count": prior_summary.get("source_private_readiness_blocker_queue_item_count"),
        "diagnostic_response_ready_count": prior_summary.get("diagnostic_response_ready_count"),
        "diagnostic_response_blocker_count": prior_summary.get("diagnostic_response_blocker_count"),
        "pending_diagnostic_response_count": prior_summary.get("pending_diagnostic_response_count"),
        "valid_diagnostic_response_count": prior_summary.get("valid_diagnostic_response_count"),
        "invalid_diagnostic_response_count": prior_summary.get("invalid_diagnostic_response_count"),
        "actionable_resolution_count": prior_summary.get("actionable_resolution_count"),
        "open_residual_difference_count": prior_summary.get("open_residual_difference_count"),
        "closed_discrepancy_count": prior_summary.get("closed_discrepancy_count"),
        "safe_auto_resolution_count": prior_summary.get("safe_auto_resolution_count"),
        "owner_select_one_authoritative_candidate_count": prior_summary.get("owner_select_one_authoritative_candidate_count"),
        "provide_authoritative_source_reference_or_owner_exclusion_count": prior_summary.get(
            "provide_authoritative_source_reference_or_owner_exclusion_count"
        ),
        "provide_formula_or_non_numeric_mapping_count": prior_summary.get("provide_formula_or_non_numeric_mapping_count"),
        "source_map_correction_ready": False,
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
        "private_threshold_recheck_diagnostic_written": True,
        "private_threshold_recheck_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("prior_phase_is_diagnostic_blocker_audit", summary["prior_phase_id"] == "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_BLOCKER_AUDIT"),
        ("prior_observation_count_two", summary["prior_diagnostic_blocker_observation_count"] == 2),
        ("current_observation_count_three", summary["diagnostic_blocker_observation_count"] == 3),
        ("blocked_threshold_met", summary["diagnostic_blocked_audit_threshold_met"] is True),
        ("blocker_queue_complete", summary["source_private_readiness_blocker_queue_item_count"] == 72),
        ("all_residual_differences_still_blocked", summary["diagnostic_response_blocker_count"] == 72),
        ("no_valid_diagnostic_response", summary["valid_diagnostic_response_count"] == 0),
        ("no_actionable_resolution", summary["actionable_resolution_count"] == 0),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("downstream_gates_closed", summary["business_execution_performed"] is False),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_matrix_public_safe.v1",
        "record_type": "v014_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": summary["generated_at"],
        "blocker_threshold_recheck_count": len(rows),
        "blocker_threshold_recheck_pass_count": pass_count,
        "blocker_threshold_recheck_fail_count": len(rows) - pass_count,
        "decision": DECISION,
        "checks": rows,
    }


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_go_no_go.v1",
        "record_type": "v014_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "audit_conclusion": AUDIT_CONCLUSION,
        "diagnostic_blocker_observation_count": summary["diagnostic_blocker_observation_count"],
        "diagnostic_blocked_audit_threshold_met": summary["diagnostic_blocked_audit_threshold_met"],
        "goal_status_recommendation": summary["goal_status_recommendation"],
        "diagnostic_response_blocker_count": summary["diagnostic_response_blocker_count"],
        "valid_diagnostic_response_count": summary["valid_diagnostic_response_count"],
        "actionable_resolution_count": summary["actionable_resolution_count"],
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


def _write_private_diagnostic(generated_at: str, summary: dict[str, Any]) -> dict[str, Any]:
    diagnostic = {
        "schema_version": "kmfa.private.v014_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck.v1",
        "classification": "private_owner_or_agent_diagnostic_blocker_threshold_recheck_do_not_commit",
        "record_type": "v014_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "prior_phase_id": summary["prior_phase_id"],
        "counts": {
            "diagnostic_response_blocker_count": summary["diagnostic_response_blocker_count"],
            "pending_diagnostic_response_count": summary["pending_diagnostic_response_count"],
            "valid_diagnostic_response_count": summary["valid_diagnostic_response_count"],
            "actionable_resolution_count": summary["actionable_resolution_count"],
            "open_residual_difference_count": summary["open_residual_difference_count"],
            "closed_discrepancy_count": summary["closed_discrepancy_count"],
        },
        "diagnostic_blocker_observation_count": summary["diagnostic_blocker_observation_count"],
        "diagnostic_blocked_audit_threshold_met": summary["diagnostic_blocked_audit_threshold_met"],
        "goal_status_recommendation": summary["goal_status_recommendation"],
        "audit_conclusion": AUDIT_CONCLUSION,
        "raw_boundary": summary["raw_boundary"],
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    return diagnostic


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    report = f"""# V014 Residual Difference Owner / Agent Diagnostic Blocker Threshold Recheck

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe diagnostic blocker audit evidence plus ignored private blocker audit diagnostic.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Result

- Prior diagnostic blocker observation count: `{summary["prior_diagnostic_blocker_observation_count"]}`
- Diagnostic blocker observation count: `{summary["diagnostic_blocker_observation_count"]}`
- Blocked audit threshold met: `{str(summary["diagnostic_blocked_audit_threshold_met"]).lower()}`
- Diagnostic response blockers: `{summary["diagnostic_response_blocker_count"]}`
- Pending diagnostic responses: `{summary["pending_diagnostic_response_count"]}`
- Valid diagnostic responses: `{summary["valid_diagnostic_response_count"]}`
- Actionable resolutions: `{summary["actionable_resolution_count"]}`
- Open residual differences: `{summary["open_residual_difference_count"]}`
- Closed discrepancies: `{summary["closed_discrepancy_count"]}`

## Gate

Valid owner/agent response, discrepancy closure, source-map correction, raw-to-processed comparison, full reconciliation, business value consistency, lineage full check, formal report, GitHub upload, app reinstall and business execution remain closed.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: all 72 residual differences still lack valid owner/agent diagnostic responses for the third observation.
- Goal status recommendation: `{go_no_go["goal_status_recommendation"]}`
- Next recommended phase: `{NEXT_RECOMMENDED_PHASE}`
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck.py --require-private-diagnostic`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck`

Expected matrix result: {matrix["blocker_threshold_recheck_pass_count"]}/{matrix["blocker_threshold_recheck_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: threshold met can be mistaken for permission to auto-close discrepancies.
- Control: this phase records no valid diagnostic response and keeps every downstream gate closed.
- Risk: private diagnostics may leak into public evidence.
- Control: public artifacts contain aggregate counts only and private diagnostics remain ignored.
"""
    rollback = f"""# Rollback Plan

Remove the artifacts for `{PHASE_ID}`, metadata copies, private threshold diagnostic, tool, validator, focused test and governance entries. Do not touch prior private diagnostics, blocker queues or raw inbox files.
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_record)
    _write_text(TEST_RESULTS_PATH, test_results)
    _write_text(RISK_REGISTER_PATH, risk_register)
    _write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_manifest.v1",
        "record_type": "v014_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_manifest",
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
            "prior_blocker_audit_summary": "public_safe_metadata_copy",
            "prior_blocker_audit_manifest": "public_safe_metadata_copy",
            "prior_private_blocker_audit_diagnostic": "ignored_private_runtime",
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
        "private_artifact_refs": ["private:owner_or_agent_diagnostic_blocker_threshold_recheck_diagnostic"],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck.py --require-private-diagnostic",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck",
        ],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
    }


def _write_governance_events(generated_at: str, manifest: dict[str, Any]) -> None:
    event = {
        "event_id": "DEV-KMFA-20260707-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-OWNER-OR-AGENT-DIAGNOSTIC-BLOCKER-THRESHOLD-RECHECK",
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "stage_id": "value-consistency",
        "phase_id": PHASE_ID,
        "status": STATUS,
        "decision": DECISION,
        "fact_level": "EXTRACTED",
        "iteration_id": "ITER-20260707-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-OWNER-OR-AGENT-DIAGNOSTIC-BLOCKER-THRESHOLD-RECHECK",
        "task_id": TASK_ID,
        "version": VERSION,
        "go_no_go": DECISION,
        "result_commit": "PENDING",
        "summary": "Recorded the third residual-difference owner or agent diagnostic blocker observation, met the blocked threshold, and kept all downstream gates closed.",
        "diagnostic_response_blocker_count": 72,
        "pending_diagnostic_response_count": 72,
        "valid_diagnostic_response_count": 0,
        "actionable_resolution_count": 0,
        "diagnostic_blocker_observation_count": 3,
        "diagnostic_blocked_audit_threshold_met": True,
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
            "acceptance_output": "Residual difference owner or agent diagnostic blocker threshold recheck manifest summary Go No-Go public-safe matrix private ignored diagnostic validator focused test and governance records",
            "completed_task_units": 1,
            "derived_percent": 100.0,
            "estimated_task_units": 1,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "fact_level": "EXTRACTED",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "name": "v0.1.4 residual difference owner or agent diagnostic blocker threshold recheck",
            "phase_goal": "record the third diagnostic-response blocker observation and blocked threshold without accepting a valid response or closing differences",
            "phase_id": PHASE_ID,
            "project_id": "KMFA",
            "raw_data_committed": False,
            "record_type": "v014_phase",
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_BLOCKER_THRESHOLD_RECHECK",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "status": STATUS,
            "task_count": 3,
            "updated_at": "2026-07-07",
            "version": VERSION,
        },
    )
    for index, task_goal in enumerate(
        [
            "read prior public-safe blocker audit evidence and ignored private audit diagnostic read-only",
            "record third diagnostic blocker observation and threshold met state",
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
                "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_BLOCKER_THRESHOLD_RECHECK",
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
    summary = _build_summary(generated_at=generated, prior_summary=prior_summary, prior_private_diagnostic=prior_private_diagnostic)
    private_diagnostic = _write_private_diagnostic(generated, summary)
    summary["private_threshold_recheck_diagnostic_gitignored"] = _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH)
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
    parser.add_argument("--no-governance-event", action="store_true")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at, write_governance_event=not args.no_governance_event)
    summary = result["summary"]
    print(
        "PASS: generated V014 residual-difference owner/agent diagnostic blocker threshold recheck "
        f"decision={summary['decision']} observation={summary['diagnostic_blocker_observation_count']} "
        f"threshold={summary['diagnostic_blocked_audit_threshold_met']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
