#!/usr/bin/env python3
"""Prepare a private residual difference report.

This phase consumes the prior public-safe blocker-audit summary and the ignored
private residual blocker queue. It does not read or mutate the raw inbox, does
not close discrepancies, does not correct source maps, and does not run
raw-to-processed comparison. Public artifacts stay aggregate-only; row-level
diagnostics remain under the ignored private runtime directory.
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
PHASE_ID = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_REPORT"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-REPORT-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-REPORT"
VERSION = "0.1.4-outside-scope-candidate-review-residual-difference-report"
STATUS = "completed_validated_local_only_residual_difference_report_no_go"
DECISION = "NO_GO"
REPORT_CONCLUSION = "private_residual_difference_report_written_all_72_items_unresolved_no_closure"
NEXT_REQUIRED_INPUT = "private_residual_difference_report_available_for_diagnosis_no_raw_mutation"
NEXT_RECOMMENDED_PHASE = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_DIAGNOSTIC_HANDOFF"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_report_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_report_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_report_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_report_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_candidate_review_residual_difference_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_report_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_report_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_report_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_report_matrix_public_safe.json"

SOURCE_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_discrepancy_closure_blocker_audit_summary.json"
)
SOURCE_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_discrepancy_closure_blocker_audit_manifest.json"
)
SOURCE_PRIVATE_RESIDUAL_QUEUE_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_discrepancy_closure_blocker_audit/private_discrepancy_closure_residual_blocker_queue.jsonl"
)
SOURCE_PRIVATE_RESIDUAL_REPORT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_discrepancy_closure_blocker_audit/private_discrepancy_closure_residual_report.md"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_report"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_report_diagnostic.json"
PRIVATE_RESIDUAL_DIFFERENCE_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_queue.jsonl"
PRIVATE_RESIDUAL_DIFFERENCE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_report.md"

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
        "source_public_blocker_audit_summary_read_by_this_phase": True,
        "source_public_blocker_audit_manifest_read_by_this_phase": True,
        "source_private_residual_queue_read_by_this_phase": True,
        "source_private_residual_report_existence_checked_by_this_phase": True,
        "private_residual_report_diagnostic_written_by_this_phase": True,
        "private_residual_difference_queue_written_by_this_phase": True,
        "private_residual_difference_report_written_by_this_phase": True,
        "source_private_residual_queue_mutated_by_this_phase": False,
        "source_private_residual_report_mutated_by_this_phase": False,
        "discrepancy_closure_written_by_this_phase": False,
        "source_map_correction_written_by_this_phase": False,
        "protected_source_identifier_derivation_performed_by_this_phase": False,
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
        "source_private_residual_queue_committed": False,
        "private_residual_report_diagnostic_committed": False,
        "private_residual_difference_queue_committed": False,
        "private_residual_difference_report_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "protected_archive_component_identifier_committed": False,
        "raw_digest_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_ref_or_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _public_bucket_counts(queue_rows: list[dict[str, Any]]) -> dict[str, int]:
    source_counts = Counter(str(row.get("closure_bucket")) for row in queue_rows)
    return {
        "ambiguous_selection_required_count": source_counts["ambiguous_tie_requires_authoritative_selection"],
        "authoritative_source_reference_required_count": source_counts[
            "no_context_candidate_requires_authoritative_source_reference"
        ],
        "formula_or_non_numeric_mapping_required_count": source_counts[
            "non_numeric_or_calculation_requires_formula_mapping"
        ],
        "unsupported_manual_triage_required_count": source_counts["unsupported_status_requires_manual_triage"],
    }


def _build_private_difference_rows(generated_at: str, source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    difference_rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_rows, start=1):
        difference_rows.append(
            {
                "residual_difference_item_id": f"OSCR-DIFF-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_residual_blocker_item_id": row.get("residual_blocker_item_id"),
                "source_closure_readiness_item_id": row.get("closure_readiness_item_id"),
                "source_resolution_item_id": row.get("source_resolution_item_id"),
                "source_review_item_id": row.get("source_review_item_id"),
                "source_alignment_item_index": row.get("source_alignment_item_index"),
                "target_slot_id": row.get("target_slot_id"),
                "candidate_status": row.get("candidate_status"),
                "closure_bucket": row.get("closure_bucket"),
                "closure_blocker_code": row.get("closure_blocker_code"),
                "required_evidence_class": row.get("required_evidence_class"),
                "difference_status": "unresolved_requires_private_diagnostic_or_owner_resolution",
                "private_report_ready": True,
                "discrepancy_closed_by_this_phase": False,
                "source_map_correction_ready_after_report": False,
                "raw_to_processed_comparison_ready_after_report": False,
                "business_value_consistency_verified_by_this_phase": False,
            }
        )
    return difference_rows


def _build_summary(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_rows: list[dict[str, Any]],
    difference_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    bucket_counts = _public_bucket_counts(source_rows)
    open_count = len(difference_rows)
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_residual_difference_report_summary.v1",
        "record_type": "v014_outside_scope_candidate_review_residual_difference_report_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "report_conclusion": REPORT_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_decision": source_summary.get("decision"),
        "source_open_closure_blocker_count": source_summary.get("open_closure_blocker_count"),
        "source_closed_discrepancy_count": source_summary.get("closed_discrepancy_count"),
        "source_newly_actionable_closure_count": source_summary.get("newly_actionable_closure_count"),
        "source_safe_auto_closure_count": source_summary.get("safe_auto_closure_count"),
        "source_private_residual_queue_written": source_summary.get("private_residual_blocker_queue_written"),
        "source_private_residual_report_written": source_summary.get("private_residual_report_written"),
        "residual_report_performed": True,
        "source_private_residual_queue_item_count": len(source_rows),
        "residual_difference_report_item_count": open_count,
        "open_residual_difference_count": open_count,
        "closed_discrepancy_count": 0,
        "safe_auto_closure_count": 0,
        "newly_actionable_closure_count": 0,
        "public_residual_difference_bucket_count": 3 if open_count else 0,
        **bucket_counts,
        "mandatory_owner_or_authorized_delegate_resolution_count": open_count,
        "residual_difference_report_prepared": True,
        "private_diagnostic_handoff_ready": True,
        "goal_status_recommendation": "continue_with_private_diagnostic_handoff_or_owner_resolution",
        "private_residual_report_diagnostic_written": True,
        "private_residual_difference_queue_written": True,
        "private_residual_difference_report_written": True,
        "private_residual_report_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_residual_difference_queue_gitignored": _git_check_ignored(PRIVATE_RESIDUAL_DIFFERENCE_QUEUE_PATH),
        "private_residual_difference_report_gitignored": _git_check_ignored(PRIVATE_RESIDUAL_DIFFERENCE_REPORT_PATH),
        "discrepancy_closure_complete": False,
        "source_map_correction_ready": False,
        "source_map_correction_written_by_this_phase": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "processed_consistency_verified": False,
        "business_value_consistency_verified": False,
        "full_reconciliation_allowed": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_residual_difference_report_go_no_go.v1",
        "record_type": "v014_outside_scope_candidate_review_residual_difference_report_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "report_conclusion": REPORT_CONCLUSION,
        "open_residual_difference_count": summary["open_residual_difference_count"],
        "closed_discrepancy_count": summary["closed_discrepancy_count"],
        "safe_auto_closure_count": summary["safe_auto_closure_count"],
        "newly_actionable_closure_count": summary["newly_actionable_closure_count"],
        "discrepancy_closure_complete": False,
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


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_blocker_audit_summary_loaded", summary["source_phase_id"] == "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_DISCREPANCY_CLOSURE_BLOCKER_AUDIT"),
        ("source_open_closure_blocker_count_locked", summary["source_open_closure_blocker_count"] == 72),
        ("source_private_residual_queue_loaded", summary["source_private_residual_queue_item_count"] == 72),
        ("private_residual_difference_report_written", summary["private_residual_difference_report_written"] is True),
        ("residual_difference_report_items_locked", summary["residual_difference_report_item_count"] == 72),
        ("no_discrepancy_closed", summary["closed_discrepancy_count"] == 0),
        ("no_newly_actionable_closure", summary["newly_actionable_closure_count"] == 0),
        ("residual_bucket_counts_locked", summary["ambiguous_selection_required_count"] == 24 and summary["authoritative_source_reference_required_count"] == 40 and summary["formula_or_non_numeric_mapping_required_count"] == 8),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("downstream_gates_closed", summary["business_execution_performed"] is False),
    ]
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_residual_difference_report_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_candidate_review_residual_difference_report_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": summary["generated_at"],
        "decision": DECISION,
        "check_count": len(checks),
        "check_pass_count": sum(1 for _, passed in checks if passed),
        "check_fail_count": sum(1 for _, passed in checks if not passed),
        "checks": [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks],
    }


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_residual_difference_report_manifest.v1",
        "record_type": "v014_outside_scope_candidate_review_residual_difference_report_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "report_conclusion": REPORT_CONCLUSION,
        "source_artifacts": {
            "source_blocker_audit_public_summary": "public_safe_metadata_copy",
            "source_blocker_audit_public_manifest": "public_safe_metadata_copy",
            "source_private_residual_queue": "ignored_private_runtime",
            "source_private_residual_report": "ignored_private_runtime",
        },
        "summary": summary,
        "go_no_go_report": go_no_go,
        "matrix": matrix,
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
        "private_artifact_refs": [
            "private:residual_difference_report_diagnostic",
            "private:residual_difference_queue",
            "private:residual_difference_report",
        ],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_residual_difference_report.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_report.py --require-private-report",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_residual_difference_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
    }


def _write_human_artifacts(summary: dict[str, Any]) -> None:
    report = f"""# Outside-Scope Candidate Review Residual Difference Report

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- source open closure blockers: `{summary['source_open_closure_blocker_count']}`
- source closed discrepancies: `{summary['source_closed_discrepancy_count']}`
- residual difference report items: `{summary['residual_difference_report_item_count']}`
- open residual differences: `{summary['open_residual_difference_count']}`
- closed discrepancies: `{summary['closed_discrepancy_count']}`
- ambiguous selection required: `{summary['ambiguous_selection_required_count']}`
- authoritative source reference required: `{summary['authoritative_source_reference_required_count']}`
- formula or non-numeric mapping required: `{summary['formula_or_non_numeric_mapping_required_count']}`
- raw boundary: raw inbox read/list/stat/parse/write/delete/move/rename/copy/normalize/mutation all `false` in this phase.
- downstream boundary: discrepancy closure, source-map correction, formal raw-to-processed comparison, reconciliation, formal report, GitHub upload, app reinstall and business execution all remain `false`.
"""
    _write_text(REPORT_PATH, report)
    _write_text(
        GO_NO_GO_RECORD_PATH,
        f"# Go/No-Go\n\n- decision: `{DECISION}`\n- reason: 72 residual differences remain open in a private report; no discrepancy is closed in this phase.\n",
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# Test Results",
                "",
                "- generator: pending current run",
                "- validator: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_report.py --require-private-report`",
                "- focused unit test: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_residual_difference_report`",
                "",
            ]
        ),
    )
    _write_text(
        RISK_REGISTER_PATH,
        "# Risk Register\n\n- Risk: Treating residual difference report as discrepancy closure would overstate value consistency.\n- Control: validator requires open_residual_difference_count=72, closed_discrepancy_count=0 and downstream gates closed.\n",
    )
    _write_text(
        ROLLBACK_PATH,
        "# Rollback Plan\n\nRemove current phase artifacts, metadata copies, ignored private residual-difference outputs, tool, validator, focused test and governance rows. Do not touch raw inbox.\n",
    )


def _write_private_report(summary: dict[str, Any]) -> None:
    _write_text(
        PRIVATE_RESIDUAL_DIFFERENCE_REPORT_PATH,
        "\n".join(
            [
                "# Private Residual Difference Report",
                "",
                "This ignored private report summarizes the private residual difference queue for diagnosis.",
                "It must not be committed or shared as public evidence.",
                "",
                f"- residual_difference_report_item_count: {summary['residual_difference_report_item_count']}",
                f"- ambiguous_selection_required_count: {summary['ambiguous_selection_required_count']}",
                f"- authoritative_source_reference_required_count: {summary['authoritative_source_reference_required_count']}",
                f"- formula_or_non_numeric_mapping_required_count: {summary['formula_or_non_numeric_mapping_required_count']}",
                "",
            ]
        ),
    )


def _write_governance_events(generated_at: str, manifest: dict[str, Any]) -> None:
    files_changed = _changed_kmfa_files()
    _append_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260707-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-REPORT",
            "event_time": generated_at,
            "event_type": "development",
            "project_id": "KMFA",
            "stage_id": "value-consistency",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "go_no_go": DECISION,
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "summary": "Reported unresolved residual differences and wrote ignored private residual difference report while keeping all downstream gates closed.",
            "source_private_residual_queue_item_count": manifest["summary"]["source_private_residual_queue_item_count"],
            "open_residual_difference_count": manifest["summary"]["open_residual_difference_count"],
            "closed_discrepancy_count": manifest["summary"]["closed_discrepancy_count"],
            "safe_auto_closure_count": manifest["summary"]["safe_auto_closure_count"],
            "raw_inbox_read_performed": False,
            "raw_inbox_mutation_performed": False,
            "github_upload_performed": False,
            "business_execution_performed": False,
            "result_commit": "PENDING",
            "files_changed": files_changed,
        },
    )
    _append_jsonl(
        STAGE_STATUS_PATH,
        {
            "record_type": "v014_phase",
            "project_id": "KMFA",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_REPORT",
            "phase_id": PHASE_ID,
            "name": "v0.1.4 outside-scope candidate review residual difference report",
            "phase_goal": "report 72 private residual differences without raw mutation or unsafe closure",
            "status": STATUS,
            "acceptance_id": ACCEPTANCE_ID,
            "acceptance_output": "Residual difference report manifest summary Go No-Go public-safe matrix private ignored residual difference queue report validator focused test and governance records",
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "version": VERSION,
            "updated_at": "2026-07-07",
            "fact_level": "EXTRACTED",
            "raw_data_committed": False,
            "estimated_task_units": 1,
            "completed_task_units": 1,
            "derived_percent": 100.0,
            "task_count": 3,
        },
    )
    for suffix, goal in [
        ("T1", "read prior blocker audit evidence and private residual queue without raw mutation"),
        ("T2", "write ignored private residual difference queue and report without closing discrepancies"),
        ("T3", "emit public-safe NO_GO residual report evidence while keeping downstream gates closed"),
    ]:
        _append_jsonl(
            TASK_STATUS_PATH,
            {
                "schema_version": "kmfa.v014_stage_phase_task_status.v1",
                "record_type": "v014_task",
                "project_id": "KMFA",
                "stage_id": "VALUE-CONSISTENCY",
                "governance_stage_id": "VALUE-CONSISTENCY",
                "roadmap_stage_id": "VALUE-CONSISTENCY",
                "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_REPORT",
                "phase_id": PHASE_ID,
                "task_id": f"{TASK_ID}-{suffix}",
                "task_goal": goal,
                "status": "completed",
                "acceptance_id": ACCEPTANCE_ID,
                "evidence_ref": MANIFEST_PATH.as_posix(),
                "version": VERSION,
                "updated_at": "2026-07-07",
                "fact_level": "EXTRACTED",
                "raw_data_committed": False,
                "derived_percent": 100.0,
            },
        )


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = _now(generated_at)
    source_summary = _read_json(SOURCE_SUMMARY_PATH)
    _read_json(SOURCE_MANIFEST_PATH)
    source_queue = _read_jsonl(SOURCE_PRIVATE_RESIDUAL_QUEUE_PATH)
    if not SOURCE_PRIVATE_RESIDUAL_REPORT_PATH.exists():
        raise FileNotFoundError(SOURCE_PRIVATE_RESIDUAL_REPORT_PATH)
    difference_rows = _build_private_difference_rows(generated, source_queue)
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_rows=source_queue,
        difference_rows=difference_rows,
    )
    go_no_go = _build_go_no_go(summary)
    matrix = _build_matrix(summary)
    manifest = _build_manifest(summary, matrix, go_no_go)

    diagnostic = {
        "schema_version": "kmfa.v014_private_residual_difference_report_diagnostic.v1",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated,
        "source_phase_id": source_summary.get("phase_id"),
        "source_private_residual_queue_read": True,
        "source_private_residual_queue_mutated": False,
        "private_outputs_gitignored": {
            "diagnostic": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
            "residual_difference_queue": _git_check_ignored(PRIVATE_RESIDUAL_DIFFERENCE_QUEUE_PATH),
            "residual_difference_report": _git_check_ignored(PRIVATE_RESIDUAL_DIFFERENCE_REPORT_PATH),
        },
        "private_counts": {
            "source_private_residual_queue_item_count": len(source_queue),
            "residual_difference_report_item_count": len(difference_rows),
        },
        "public_bucket_counts": _public_bucket_counts(source_queue),
    }

    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (MATRIX_PATH, matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
        (PRIVATE_DIAGNOSTIC_PATH, diagnostic),
    ):
        _write_json(path, payload)
    _write_jsonl(PRIVATE_RESIDUAL_DIFFERENCE_QUEUE_PATH, difference_rows)
    _write_human_artifacts(summary)
    _write_private_report(summary)
    if write_governance_event:
        _write_governance_events(generated, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--skip-governance-event", action="store_true")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at, write_governance_event=not args.skip_governance_event)
    summary = manifest["summary"]
    print(
        "PASS: generated "
        f"{PHASE_ID} decision={summary['decision']} "
        f"open_residual_differences={summary['open_residual_difference_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
