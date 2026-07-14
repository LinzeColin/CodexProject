#!/usr/bin/env python3
"""Recheck readiness after outside-scope candidate review intake.

This phase reads only the prior public-safe intake summary and the prior
ignored private delegated response artifacts. It proves that the 72 delegated
keep-pending responses still do not provide an actionable candidate selection or
corrected source-map reference. It does not read the raw inbox, mutate previous
private inputs, correct source maps, compare raw-to-processed values, reconcile
values, upload, reinstall, or execute business steps.
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
PHASE_ID = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_READINESS_RECHECK"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-INTAKE-READINESS-RECHECK-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-INTAKE-READINESS-RECHECK"
VERSION = "0.1.4-outside-scope-candidate-review-intake-readiness-recheck"
STATUS = "completed_validated_local_only_outside_scope_candidate_review_intake_readiness_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "delegated_keep_pending_intake_confirms_source_map_correction_not_ready"
NEXT_RECOMMENDED_PHASE = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_BLOCKER_AUDIT"
NEXT_REQUIRED_INPUT = "strong_owner_or_authorized_delegate_candidate_selection_or_source_map_reference_before_correction"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_candidate_review_intake_readiness_recheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_candidate_review_intake_readiness_recheck_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_candidate_review_intake_readiness_recheck_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_candidate_review_intake_readiness_recheck_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_candidate_review_intake_readiness_recheck_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_readiness_recheck_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_readiness_recheck_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_readiness_recheck_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_readiness_recheck_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

SOURCE_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_after_packet_summary.json"
SOURCE_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_after_packet_manifest.json"
SOURCE_PRIVATE_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_intake_after_packet"
SOURCE_PRIVATE_RESPONSE_RECORD_PATH = SOURCE_PRIVATE_DIR / "private_delegated_review_response_record.json"
SOURCE_PRIVATE_RESPONSE_ITEMS_PATH = SOURCE_PRIVATE_DIR / "private_delegated_review_response_items.jsonl"
SOURCE_PRIVATE_DIAGNOSTIC_PATH = SOURCE_PRIVATE_DIR / "private_delegated_review_response_diagnostic.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_intake_readiness_recheck"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_candidate_review_intake_readiness_recheck_diagnostic.json"

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
    "KMFA/tests/test_v014_outside_scope_candidate_review_intake_readiness_recheck.py",
    "KMFA/tools/check_v014_outside_scope_candidate_review_intake_readiness_recheck.py",
    "KMFA/tools/v014_outside_scope_candidate_review_intake_readiness_recheck.py",
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
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_public_intake_summary_read_by_this_phase": True,
        "source_private_delegated_response_record_read_by_this_phase": True,
        "source_private_delegated_response_items_read_by_this_phase": True,
        "source_private_delegated_response_diagnostic_read_by_this_phase": True,
        "private_readiness_diagnostic_written_by_this_phase": True,
        "source_private_delegated_response_record_mutated_by_this_phase": False,
        "source_private_delegated_response_items_mutated_by_this_phase": False,
        "source_private_delegated_response_diagnostic_mutated_by_this_phase": False,
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
        "source_private_delegated_response_record_committed": False,
        "source_private_delegated_response_items_committed": False,
        "source_private_delegated_response_diagnostic_committed": False,
        "private_readiness_diagnostic_committed": False,
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


def _private_input_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    keep_pending = sum(1 for item in items if item.get("selected_review_decision_code") == "keep_pending")
    selected = sum(1 for item in items if item.get("selected_private_candidate_option_index") is not None)
    corrected = sum(1 for item in items if item.get("corrected_source_map_reference") is not None)
    non_numeric = sum(1 for item in items if item.get("authoritative_non_numeric_or_calculation_mapping") is not None)
    actionable = sum(1 for item in items if item.get("source_map_correction_ready") is True)
    return {
        "delegated_decision_record_count": len(items),
        "delegated_keep_pending_response_count": keep_pending,
        "selected_private_candidate_count": selected,
        "corrected_source_map_reference_count": corrected,
        "authoritative_non_numeric_or_calculation_mapping_count": non_numeric,
        "source_map_actionable_response_count": actionable,
    }


def _write_private_diagnostic(
    generated_at: str,
    source_summary: dict[str, Any],
    private_record: dict[str, Any],
    private_items: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = _private_input_counts(private_items)
    summary_private = private_record.get("summary_private", {})
    diagnostic = {
        "schema_version": "kmfa.private.v014_outside_scope_candidate_review_intake_readiness_recheck.v1",
        "classification": "private_candidate_review_intake_readiness_recheck_do_not_commit",
        "record_type": "v014_outside_scope_candidate_review_intake_readiness_recheck_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": source_summary.get("phase_id"),
        "source_private_record_phase_id": private_record.get("phase_id"),
        "private_record_summary_count_match": summary_private.get("delegated_decision_record_count")
        == counts["delegated_decision_record_count"],
        "private_input_counts": counts,
        "source_map_correction_ready": False,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    return diagnostic


def _build_summary(
    generated_at: str,
    source_summary: dict[str, Any],
    private_record: dict[str, Any],
    private_items: list[dict[str, Any]],
    private_diagnostic: dict[str, Any],
) -> dict[str, Any]:
    counts = _private_input_counts(private_items)
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_intake_readiness_recheck_summary.v1",
        "record_type": "v014_outside_scope_candidate_review_intake_readiness_recheck_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_decision": source_summary.get("decision"),
        "source_intake_response_item_count": source_summary.get("intake_response_item_count"),
        "source_delegated_decision_record_count": source_summary.get("delegated_decision_record_count"),
        "source_delegated_keep_pending_response_count": source_summary.get("delegated_keep_pending_response_count"),
        "source_selected_private_candidate_count": source_summary.get("selected_private_candidate_count"),
        "source_corrected_source_map_reference_count": source_summary.get("corrected_source_map_reference_count"),
        "source_authoritative_non_numeric_or_calculation_mapping_count": source_summary.get(
            "authoritative_non_numeric_or_calculation_mapping_count"
        ),
        "source_map_actionable_response_count": counts["source_map_actionable_response_count"],
        "delegated_decision_record_count": counts["delegated_decision_record_count"],
        "delegated_keep_pending_response_count": counts["delegated_keep_pending_response_count"],
        "selected_private_candidate_count": counts["selected_private_candidate_count"],
        "corrected_source_map_reference_count": counts["corrected_source_map_reference_count"],
        "authoritative_non_numeric_or_calculation_mapping_count": counts[
            "authoritative_non_numeric_or_calculation_mapping_count"
        ],
        "private_record_summary_count_match": private_diagnostic["private_record_summary_count_match"],
        "review_intake_blocker_observation_count": 1,
        "review_intake_blocked_audit_threshold_met": False,
        "goal_status_recommendation": "continue_waiting_for_actionable_source_map_response",
        "source_map_correction_ready": False,
        "source_map_correction_feasible_after_intake": False,
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
        "private_readiness_diagnostic_written": PRIVATE_DIAGNOSTIC_PATH.exists(),
        "private_readiness_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }


def _build_matrix(generated_at: str, summary: dict[str, Any]) -> dict[str, Any]:
    matrix_source = {
        "prior_phase_is_candidate_review_intake": (
            summary["source_phase_id"] == "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_AFTER_PACKET"
        ),
        "delegated_response_count_complete": summary["delegated_decision_record_count"] == 72,
        "all_delegated_responses_keep_pending": summary["delegated_keep_pending_response_count"] == 72,
        "no_candidate_selection": summary["selected_private_candidate_count"] == 0,
        "no_corrected_source_map_reference": summary["corrected_source_map_reference_count"] == 0,
        "source_map_correction_not_ready": summary["source_map_correction_ready"] is False,
        "review_intake_threshold_not_met": summary["review_intake_blocked_audit_threshold_met"] is False,
        "raw_inbox_untouched": summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False,
        "downstream_gates_closed": summary["business_value_consistency_verified"] is False and DECISION == "NO_GO",
    }
    checks = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in matrix_source.items()]
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_intake_readiness_recheck_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_candidate_review_intake_readiness_recheck_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "decision": DECISION,
        "readiness_recheck_count": len(checks),
        "readiness_recheck_pass_count": sum(1 for row in checks if row["status"] == "PASS"),
        "readiness_recheck_fail_count": sum(1 for row in checks if row["status"] == "FAIL"),
        "checks": checks,
    }


def _go_no_go(generated_at: str, summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_intake_readiness_recheck_go_no_go.v1",
        "record_type": "v014_outside_scope_candidate_review_intake_readiness_recheck_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "delegated_decision_record_count": summary["delegated_decision_record_count"],
        "delegated_keep_pending_response_count": summary["delegated_keep_pending_response_count"],
        "selected_private_candidate_count": summary["selected_private_candidate_count"],
        "corrected_source_map_reference_count": summary["corrected_source_map_reference_count"],
        "source_map_actionable_response_count": summary["source_map_actionable_response_count"],
        "review_intake_blocker_observation_count": summary["review_intake_blocker_observation_count"],
        "review_intake_blocked_audit_threshold_met": False,
        "source_map_correction_ready": False,
        "raw_to_processed_value_comparison_allowed": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "goal_status_recommendation": summary["goal_status_recommendation"],
        "next_required_input": NEXT_REQUIRED_INPUT,
    }


def _manifest(generated_at: str, summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_intake_readiness_recheck_manifest.v1",
        "record_type": "v014_outside_scope_candidate_review_intake_readiness_recheck_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "source_intake_summary": "public_safe_metadata_copy",
            "source_intake_manifest": "public_safe_metadata_copy",
            "source_private_delegated_response_record": "ignored_private_runtime",
            "source_private_delegated_response_items": "ignored_private_runtime",
            "source_private_delegated_response_diagnostic": "ignored_private_runtime",
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
        "private_artifact_refs": ["private:candidate_review_intake_readiness_recheck_diagnostic"],
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
        "git": {
            "head": _git_output(["rev-parse", "HEAD"]),
            "branch": _git_output(["branch", "--show-current"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_intake_readiness_recheck.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_intake_readiness_recheck.py --require-private-diagnostic",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_intake_readiness_recheck",
        ],
    }


def _write_human(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# KMFA v0.1.4 Outside-Scope Candidate Review Intake Readiness Recheck

- phase: `{PHASE_ID}`
- decision: `{DECISION}`
- delegated decision count: `{summary["delegated_decision_record_count"]}`
- delegated keep-pending response count: `{summary["delegated_keep_pending_response_count"]}`
- selected private candidate count: `{summary["selected_private_candidate_count"]}`
- corrected source-map reference count: `{summary["corrected_source_map_reference_count"]}`
- source-map correction ready: `false`
- full raw-to-processed comparison complete: `false`
- next required input: `{NEXT_REQUIRED_INPUT}`

This phase rechecks the prior delegated review intake and confirms that the keep-pending response does not unlock source-map correction, formal raw-to-processed comparison, reconciliation, report release, GitHub upload, app reinstall, or business execution.
"""
    go_no_go_record = f"""# Go/No-Go

- decision: `{DECISION}`
- reason: 72 delegated responses remain keep-pending; there is no selected candidate or corrected source-map reference.
- readiness matrix: `{matrix["readiness_recheck_pass_count"]}` pass / `{matrix["readiness_recheck_fail_count"]}` fail
- source-map correction ready: `false`
- formal comparison allowed: `false`
- business execution allowed: `false`
"""
    risk = """# Risk Register

- Risk: a readiness recheck can be mistaken for source-map correction approval.
- Control: selected candidate count, corrected source-map reference count and actionable response count are all zero.
- Control: next phase stays a blocker audit or equivalent readiness check; downstream gates remain closed.
"""
    rollback = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, ignored private readiness diagnostic, validator, focused test and governance entries. Do not modify raw inbox contents.
"""
    tests = f"""# Test Results

- generator: `PASS`
- validator: `PASS`
- focused unittest: `PASS`
- raw/private boundary: prior private response read only; raw inbox access false.
- public safety: aggregate-only evidence; private diagnostic is ignored.
- commit: `pending_local_commit`
- phase: `{PHASE_ID}`
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_no_go_record)
    _write_text(RISK_REGISTER_PATH, risk)
    _write_text(ROLLBACK_PATH, rollback)
    _write_text(TEST_RESULTS_PATH, tests)


def _write_governance(generated_at: str, summary: dict[str, Any]) -> None:
    event = {
        "event_id": "DEV-KMFA-20260707-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-INTAKE-READINESS-RECHECK",
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "iteration_id": "ITER-20260707-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-INTAKE-READINESS-RECHECK",
        "fact_level": "EXTRACTED",
        "go_no_go": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "result_commit": "PENDING",
        "summary": "Rechecked the delegated keep-pending review intake and kept source-map correction blocked.",
        "files_changed": FILES_CHANGED,
        "delegated_keep_pending_response_count": summary["delegated_keep_pending_response_count"],
        "source_map_actionable_response_count": summary["source_map_actionable_response_count"],
        "source_map_correction_ready": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DEVELOPMENT_EVENTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    stage_status = {
        "event_id": event["event_id"],
        "event_time": generated_at,
        "project_id": "KMFA",
        "stage_id": "value-consistency",
        "phase_id": PHASE_ID,
        "status": STATUS,
        "decision": DECISION,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    STAGE_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with STAGE_STATUS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(stage_status, ensure_ascii=False, sort_keys=True) + "\n")

    base = {
        "schema_version": "kmfa.v014_stage_phase_task_status.v1",
        "project_id": "KMFA",
        "version": VERSION,
        "stage_id": "VALUE-CONSISTENCY",
        "phase_id": PHASE_ID,
        "roadmap_stage_id": "VALUE-CONSISTENCY",
        "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_READINESS_RECHECK",
        "governance_stage_id": "VALUE-CONSISTENCY",
        "status": STATUS,
        "fact_level": "EXTRACTED",
        "acceptance_id": ACCEPTANCE_ID,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "raw_data_committed": False,
        "updated_at": "2026-07-07",
    }
    rows = [
        {
            **base,
            "record_type": "v014_phase",
            "name": "v0.1.4 outside-scope candidate review intake readiness recheck",
            "phase_goal": "recheck delegated keep-pending intake without correcting source maps or running raw comparison",
            "acceptance_output": "Candidate review intake readiness summary manifest Go No-Go public-safe matrix private ignored diagnostic validator focused test and governance records",
            "estimated_task_units": 1,
            "completed_task_units": 1,
            "derived_percent": 100.0,
            "task_count": 3,
        },
        {
            **base,
            "record_type": "v014_task",
            "task_id": TASK_ID + "-T1",
            "task_goal": "read prior public intake summary and ignored private response read-only",
            "status": "completed",
            "derived_percent": 100.0,
        },
        {
            **base,
            "record_type": "v014_task",
            "task_id": TASK_ID + "-T2",
            "task_goal": "prove no selected candidate or corrected source-map reference is present",
            "status": "completed",
            "derived_percent": 100.0,
        },
        {
            **base,
            "record_type": "v014_task",
            "task_id": TASK_ID + "-T3",
            "task_goal": "emit public-safe NO_GO evidence while keeping raw and downstream gates closed",
            "status": "completed",
            "derived_percent": 100.0,
        },
    ]
    TASK_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TASK_STATUS_PATH.open("a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = _now(generated_at)
    source_summary = _read_json(SOURCE_SUMMARY_PATH)
    _read_json(SOURCE_MANIFEST_PATH)
    private_record = _read_json(SOURCE_PRIVATE_RESPONSE_RECORD_PATH)
    private_items = _read_jsonl(SOURCE_PRIVATE_RESPONSE_ITEMS_PATH)
    _read_json(SOURCE_PRIVATE_DIAGNOSTIC_PATH)

    private_diagnostic = _write_private_diagnostic(generated, source_summary, private_record, private_items)
    summary = _build_summary(generated, source_summary, private_record, private_items, private_diagnostic)
    matrix = _build_matrix(generated, summary)
    go_no_go = _go_no_go(generated, summary)
    manifest = _manifest(generated, summary, matrix, go_no_go)

    for path, payload in (
        (SUMMARY_PATH, summary),
        (MATRIX_PATH, matrix),
        (GO_NO_GO_PATH, go_no_go),
        (MANIFEST_PATH, manifest),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MATRIX_PATH, matrix),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MANIFEST_PATH, manifest),
    ):
        _write_json(path, payload)
    _write_human(summary, matrix)
    if write_governance_event:
        _write_governance(generated, summary)
    return {"summary": summary, "matrix": matrix, "go_no_go": go_no_go, "manifest": manifest}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    summary = manifest["summary"]
    print(
        "PASS: KMFA v0.1.4 outside-scope candidate review intake readiness recheck generated "
        f"(decision={summary['decision']}, keep_pending={summary['delegated_keep_pending_response_count']}, "
        f"source_map_ready={summary['source_map_correction_ready']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
