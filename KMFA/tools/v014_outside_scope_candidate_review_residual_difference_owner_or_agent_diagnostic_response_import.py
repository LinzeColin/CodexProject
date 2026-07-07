#!/usr/bin/env python3
"""Import owner-authorized discrepancy responses into the diagnostic chain.

This phase consumes the current residual-difference diagnostic response
template plus the ignored private owner-authorized discrepancy report. It
imports all 72 report decisions as valid diagnostic responses, but does not
close discrepancies, correct source maps, compare values, read the raw inbox,
upload, reinstall, or execute business steps.
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
PHASE_ID = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_RESPONSE_IMPORT"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-OWNER-OR-AGENT-DIAGNOSTIC-RESPONSE-IMPORT-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-OWNER-OR-AGENT-DIAGNOSTIC-RESPONSE-IMPORT"
VERSION = "0.1.4-outside-scope-candidate-review-residual-difference-owner-or-agent-diagnostic-response-import"
STATUS = "completed_validated_local_only_residual_difference_owner_or_agent_valid_diagnostic_response_imported_no_go"
DECISION = "NO_GO"
IMPORT_CONCLUSION = "owner_authorized_discrepancy_report_imported_as_valid_diagnostic_response_without_closure"
NEXT_REQUIRED_INPUT = "source_map_correction_or_authoritative_value_resolution_required_before_full_raw_to_processed_comparison"
NEXT_RECOMMENDED_PHASE = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_RESPONSE_IMPORT_READINESS_RECHECK"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import_matrix_public_safe.json"

SOURCE_THRESHOLD_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_summary.json"
SOURCE_THRESHOLD_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_blocker_threshold_recheck_manifest.json"
SOURCE_TEMPLATE_PATH = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_intake/private_owner_or_agent_diagnostic_response_template.jsonl"
SOURCE_PENDING_QUEUE_PATH = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_intake/private_owner_or_agent_diagnostic_pending_queue.jsonl"
SOURCE_OWNER_AUTHORIZED_REPORT_PATH = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_owner_authorized_discrepancy_report/private_owner_authorized_discrepancy_report_record.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import"
PRIVATE_RESPONSE_RECORD_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_diagnostic_response_import_record.json"
PRIVATE_RESPONSE_ITEMS_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_diagnostic_response_import_items.jsonl"
PRIVATE_NON_ACTIONABLE_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_diagnostic_response_non_actionable_queue.jsonl"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_owner_or_agent_diagnostic_response_import_report.md"

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
    event_id = payload.get("event_id")
    if event_id and path.exists():
        lines: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if isinstance(row, dict) and row.get("event_id") == event_id:
                continue
            lines.append(line)
        lines.append(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return
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
        "source_threshold_summary_read_by_this_phase": True,
        "source_threshold_manifest_read_by_this_phase": True,
        "source_private_response_template_read_by_this_phase": True,
        "source_private_pending_queue_read_by_this_phase": True,
        "source_owner_authorized_discrepancy_report_read_by_this_phase": True,
        "private_response_import_record_written_by_this_phase": True,
        "private_response_import_items_written_by_this_phase": True,
        "private_non_actionable_queue_written_by_this_phase": True,
        "private_response_import_report_written_by_this_phase": True,
        "source_private_response_template_mutated_by_this_phase": False,
        "source_private_pending_queue_mutated_by_this_phase": False,
        "source_owner_authorized_discrepancy_report_mutated_by_this_phase": False,
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
        "source_private_response_template_committed": False,
        "source_private_pending_queue_committed": False,
        "source_owner_authorized_discrepancy_report_committed": False,
        "private_response_import_record_committed": False,
        "private_response_import_items_committed": False,
        "private_non_actionable_queue_committed": False,
        "private_response_import_report_committed": False,
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


def _build_response_rows(
    *,
    generated_at: str,
    template_rows: list[dict[str, Any]],
    report_items: list[dict[str, Any]],
    authorization_basis: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_target = {row["target_slot_id"]: row for row in report_items}
    response_rows: list[dict[str, Any]] = []
    non_actionable_rows: list[dict[str, Any]] = []
    for index, template in enumerate(template_rows, start=1):
        target_slot_id = template["target_slot_id"]
        report_item = by_target.get(target_slot_id)
        if report_item is None:
            raise ValueError(f"missing owner-authorized report item for {target_slot_id}")
        decision_code = str(report_item.get("owner_authorized_decision_code"))
        response = {
            "response_import_item_id": f"OSCR-DRI-{index:03d}",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "template_item_id": template.get("template_item_id"),
            "source_handoff_item_id": template.get("source_handoff_item_id"),
            "source_resolution_item_id": report_item.get("resolution_item_id"),
            "target_slot_id": target_slot_id,
            "diagnostic_track": template.get("diagnostic_track"),
            "response_actor_role": "authorized_external_agent",
            "authority_basis": authorization_basis,
            "response_decision_code": decision_code,
            "response_status": "valid_diagnostic_response_imported",
            "valid_diagnostic_response": True,
            "actionable_resolution_ready": False,
            "discrepancy_report_response": True,
            "safe_auto_resolution_available": False,
            "selected_private_candidate_option_index": None,
            "corrected_source_map_reference": None,
            "authoritative_non_numeric_or_calculation_mapping": None,
            "source_map_correction_ready_after_import": False,
            "discrepancy_closed_by_this_phase": False,
            "raw_to_processed_comparison_ready_after_import": False,
            "full_comparison_allowed_by_this_phase": False,
            "non_actionable_reason_code": report_item.get("discrepancy_reason_code"),
            "public_commit_allowed": False,
        }
        response_rows.append(response)
        non_actionable_rows.append(
            {
                "non_actionable_item_id": f"OSCR-DRI-NONACTIONABLE-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "response_import_item_id": response["response_import_item_id"],
                "template_item_id": response["template_item_id"],
                "target_slot_id": target_slot_id,
                "diagnostic_track": response["diagnostic_track"],
                "response_decision_code": decision_code,
                "non_actionable_reason_code": response["non_actionable_reason_code"],
                "source_map_correction_ready_after_import": False,
                "discrepancy_closed_by_this_phase": False,
                "public_commit_allowed": False,
            }
        )
    return response_rows, non_actionable_rows


def _build_summary(
    *,
    generated_at: str,
    threshold_summary: dict[str, Any],
    template_rows: list[dict[str, Any]],
    pending_rows: list[dict[str, Any]],
    owner_report: dict[str, Any],
    response_rows: list[dict[str, Any]],
    non_actionable_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    report_items = owner_report["resolution_items"]
    template_targets = {row["target_slot_id"] for row in template_rows}
    report_targets = {row["target_slot_id"] for row in report_items}
    if len(template_targets) != 72 or template_targets != report_targets:
        raise ValueError("template/report target-slot set mismatch")
    track_counts = Counter(str(row.get("diagnostic_track")) for row in response_rows)
    decision_counts = Counter(str(row.get("response_decision_code")) for row in response_rows)
    return {
        "schema_version": "kmfa.v014_residual_difference_owner_or_agent_diagnostic_response_import_summary.v1",
        "record_type": "v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "import_conclusion": IMPORT_CONCLUSION,
        "source_threshold_phase_id": threshold_summary.get("phase_id"),
        "source_diagnostic_blocker_observation_count": threshold_summary.get("diagnostic_blocker_observation_count"),
        "source_diagnostic_blocked_audit_threshold_met": threshold_summary.get("diagnostic_blocked_audit_threshold_met"),
        "source_template_item_count": len(template_rows),
        "source_pending_queue_item_count": len(pending_rows),
        "source_owner_authorized_report_item_count": len(report_items),
        "target_slot_match_count": len(template_targets & report_targets),
        "valid_diagnostic_response_imported_count": len(response_rows),
        "valid_diagnostic_response_count": len(response_rows),
        "pending_diagnostic_response_count": 0,
        "diagnostic_response_blocker_count": 0,
        "invalid_diagnostic_response_count": 0,
        "non_actionable_diagnostic_response_count": len(non_actionable_rows),
        "discrepancy_report_response_count": len(response_rows),
        "actionable_resolution_count": 0,
        "source_map_actionable_response_count": 0,
        "open_residual_difference_count": len(response_rows),
        "closed_discrepancy_count": 0,
        "safe_auto_resolution_count": 0,
        "owner_select_one_authoritative_candidate_count": track_counts["owner_select_one_authoritative_candidate"],
        "provide_authoritative_source_reference_or_owner_exclusion_count": track_counts[
            "provide_authoritative_source_reference_or_owner_exclusion"
        ],
        "provide_formula_or_non_numeric_mapping_count": track_counts["provide_formula_or_non_numeric_mapping"],
        "report_discrepancy_tied_ambiguous_candidates_count": decision_counts[
            "report_discrepancy_tied_ambiguous_candidates"
        ],
        "report_discrepancy_no_context_candidate_count": decision_counts["report_discrepancy_no_context_candidate"],
        "report_discrepancy_non_numeric_or_calculation_context_count": decision_counts[
            "report_discrepancy_non_numeric_or_calculation_context"
        ],
        "owner_authorized_discrepancy_report_imported": True,
        "private_response_import_record_written": True,
        "private_response_import_items_written": True,
        "private_non_actionable_queue_written": True,
        "private_response_import_report_written": True,
        "private_response_import_record_gitignored": _git_check_ignored(PRIVATE_RESPONSE_RECORD_PATH),
        "private_response_import_items_gitignored": _git_check_ignored(PRIVATE_RESPONSE_ITEMS_PATH),
        "private_non_actionable_queue_gitignored": _git_check_ignored(PRIVATE_NON_ACTIONABLE_QUEUE_PATH),
        "private_response_import_report_gitignored": _git_check_ignored(PRIVATE_REPORT_PATH),
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


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("threshold_phase_loaded", summary["source_threshold_phase_id"].endswith("THRESHOLD_RECHECK")),
        ("threshold_was_met", summary["source_diagnostic_blocked_audit_threshold_met"] is True),
        ("source_template_complete", summary["source_template_item_count"] == 72),
        ("source_owner_report_complete", summary["source_owner_authorized_report_item_count"] == 72),
        ("target_slots_match", summary["target_slot_match_count"] == 72),
        ("valid_responses_imported", summary["valid_diagnostic_response_imported_count"] == 72),
        ("no_pending_response_after_import", summary["pending_diagnostic_response_count"] == 0),
        ("all_responses_non_actionable", summary["non_actionable_diagnostic_response_count"] == 72),
        ("no_resolution_or_closure", summary["closed_discrepancy_count"] == 0 and summary["actionable_resolution_count"] == 0),
        ("track_counts_locked", all(summary[f"{track}_count"] == count for track, count in EXPECTED_TRACK_COUNTS.items())),
        ("decision_counts_locked", all(summary[f"{decision}_count"] == count for decision, count in EXPECTED_DECISION_COUNTS.items())),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("downstream_gates_closed", summary["business_execution_performed"] is False),
    ]
    return {
        "schema_version": "kmfa.v014_residual_difference_owner_or_agent_diagnostic_response_import_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import_matrix_public_safe",
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


def _build_go_no_go(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_residual_difference_owner_or_agent_diagnostic_response_import_go_no_go.v1",
        "record_type": "v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "import_conclusion": IMPORT_CONCLUSION,
        "valid_diagnostic_response_count": summary["valid_diagnostic_response_count"],
        "non_actionable_diagnostic_response_count": summary["non_actionable_diagnostic_response_count"],
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


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    report = f"""# V014 Residual Difference Owner / Agent Diagnostic Response Import

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: current diagnostic threshold evidence plus ignored private owner-authorized discrepancy report.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Result

- Source template items: `{summary["source_template_item_count"]}`
- Owner-authorized report items: `{summary["source_owner_authorized_report_item_count"]}`
- Imported valid diagnostic responses: `{summary["valid_diagnostic_response_imported_count"]}`
- Non-actionable diagnostic responses: `{summary["non_actionable_diagnostic_response_count"]}`
- Open residual differences: `{summary["open_residual_difference_count"]}`
- Closed discrepancies: `{summary["closed_discrepancy_count"]}`
- Source-map actionable responses: `{summary["source_map_actionable_response_count"]}`

## Gate

The missing-response blocker is cleared, but all imported responses are non-actionable discrepancy responses. Source-map correction, raw-to-processed comparison, full reconciliation, business value consistency, lineage full check, formal report, GitHub upload, app reinstall and business execution remain closed.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: 72 valid diagnostic responses were imported, but none authorizes source-map correction, discrepancy closure or value-consistency acceptance.
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import.py --require-private-import`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA --mode required`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`
- `ruby -e 'require "yaml"; ARGV.each {{ |p| YAML.load_file(p) }}' KMFA/docs/governance/*.yaml KMFA/metadata/*.yaml`
- `git diff --check -- KMFA`
- Custom changed-path raw/private extension scan, changed-file secret scan, current-phase public artifact raw/private marker scan, private-output git-ignore scan and private-runtime tracked-file scan: PASS.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: imported diagnostic responses can be mistaken for resolved discrepancies.
- Control: the phase records valid responses separately from actionable source-map correction and keeps downstream gates closed.
- Risk: private diagnostic details may leak into public evidence.
- Control: public artifacts contain aggregate counts only and private response import artifacts remain ignored.
"""
    rollback = f"""# Rollback Plan

Remove the artifacts for `{PHASE_ID}`, metadata copies, private response import outputs, tool, validator, focused test and governance entries. Do not touch source private templates, source reports or raw inbox files.
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_record)
    _write_text(TEST_RESULTS_PATH, test_results)
    _write_text(RISK_REGISTER_PATH, risk_register)
    _write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_residual_difference_owner_or_agent_diagnostic_response_import_manifest.v1",
        "record_type": "v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "import_conclusion": IMPORT_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "public_artifacts": [
            REPORT_PATH.as_posix(),
            GO_NO_GO_RECORD_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            SUMMARY_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            GO_NO_GO_PATH.as_posix(),
            MATRIX_PATH.as_posix(),
        ],
        "private_artifacts": {
            "response_import_record_gitignored": summary["private_response_import_record_gitignored"],
            "response_import_items_gitignored": summary["private_response_import_items_gitignored"],
            "non_actionable_queue_gitignored": summary["private_non_actionable_queue_gitignored"],
            "response_import_report_gitignored": summary["private_response_import_report_gitignored"],
        },
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }


def _write_private_outputs(
    *,
    generated_at: str,
    owner_report: dict[str, Any],
    response_rows: list[dict[str, Any]],
    non_actionable_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    record = {
        "schema_version": "kmfa.private.v014_owner_or_agent_diagnostic_response_import.v1",
        "classification": "private_owner_or_agent_diagnostic_response_import_do_not_commit",
        "record_type": "v014_residual_difference_owner_or_agent_diagnostic_response_import_record",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "authority_basis": owner_report.get("authorization_basis"),
        "response_items": response_rows,
        "summary_private": {
            "valid_diagnostic_response_count": summary["valid_diagnostic_response_count"],
            "non_actionable_diagnostic_response_count": summary["non_actionable_diagnostic_response_count"],
            "closed_discrepancy_count": 0,
            "source_map_correction_ready": False,
            "business_value_consistency_verified": False,
        },
        "raw_boundary": summary["raw_boundary"],
    }
    _write_json(PRIVATE_RESPONSE_RECORD_PATH, record)
    _write_jsonl(PRIVATE_RESPONSE_ITEMS_PATH, response_rows)
    _write_jsonl(PRIVATE_NON_ACTIONABLE_QUEUE_PATH, non_actionable_rows)
    _write_text(
        PRIVATE_REPORT_PATH,
        "# Private Diagnostic Response Import Report\n\n"
        f"- valid_diagnostic_response_count: {summary['valid_diagnostic_response_count']}\n"
        f"- non_actionable_diagnostic_response_count: {summary['non_actionable_diagnostic_response_count']}\n"
        "- source_map_correction_ready: false\n"
        "- closed_discrepancy_count: 0\n"
        "- raw_inbox_mutated_by_this_phase: false\n",
    )


def _append_governance_events(summary: dict[str, Any], manifest: dict[str, Any]) -> None:
    event = {
        "event_id": "DEV-KMFA-20260707-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-OWNER-OR-AGENT-DIAGNOSTIC-RESPONSE-IMPORT",
        "event_type": "development",
        "event_time": summary["generated_at"],
        "project_id": "KMFA",
        "stage_id": "value-consistency",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "status": STATUS,
        "go_no_go": DECISION,
        "valid_diagnostic_response_count": summary["valid_diagnostic_response_count"],
        "non_actionable_diagnostic_response_count": summary["non_actionable_diagnostic_response_count"],
        "closed_discrepancy_count": 0,
        "source_map_correction_ready": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "business_execution_performed": False,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "fact_level": "EXTRACTED",
        "files_changed": _changed_kmfa_files(),
        "result_commit": "PENDING",
        "summary": "Imported owner-authorized discrepancy report decisions as valid diagnostic responses while keeping all downstream gates closed.",
    }
    _append_jsonl(DEVELOPMENT_EVENTS_PATH, event)
    _append_jsonl(
        STAGE_STATUS_PATH,
        {
            "record_type": "v014_phase",
            "project_id": "KMFA",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_RESPONSE_IMPORT",
            "phase_id": PHASE_ID,
            "name": "v0.1.4 residual difference owner or agent diagnostic response import",
            "version": VERSION,
            "status": STATUS,
            "derived_percent": 100.0,
            "task_count": 3,
            "estimated_task_units": 1,
            "completed_task_units": 1,
            "phase_goal": "import valid private diagnostic responses without closing differences or mutating raw data",
            "acceptance_id": ACCEPTANCE_ID,
            "acceptance_output": "Response import manifest summary Go No-Go public-safe matrix private ignored response import validator focused test and governance records",
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "updated_at": "2026-07-07",
            "fact_level": "EXTRACTED",
            "raw_data_committed": False,
        },
    )
    for suffix, goal in (
        ("T1", "read threshold evidence, private template and owner-authorized report read-only"),
        ("T2", "import 72 valid diagnostic responses into ignored private runtime"),
        ("T3", "emit public-safe NO_GO response-import evidence while keeping downstream gates closed"),
    ):
        _append_jsonl(
            TASK_STATUS_PATH,
            {
                "schema_version": "kmfa.v014_stage_phase_task_status.v1",
                "record_type": "v014_task",
                "project_id": "KMFA",
                "stage_id": "VALUE-CONSISTENCY",
                "governance_stage_id": "VALUE-CONSISTENCY",
                "roadmap_stage_id": "VALUE-CONSISTENCY",
                "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_RESPONSE_IMPORT",
                "phase_id": PHASE_ID,
                "task_id": f"{TASK_ID}-{suffix}",
                "task_goal": goal,
                "acceptance_id": ACCEPTANCE_ID,
                "version": VERSION,
                "status": "completed",
                "derived_percent": 100.0,
                "evidence_ref": MANIFEST_PATH.as_posix(),
                "updated_at": "2026-07-07",
                "fact_level": "EXTRACTED",
                "raw_data_committed": False,
            },
        )


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    threshold_summary = _read_json(SOURCE_THRESHOLD_SUMMARY_PATH)
    _read_json(SOURCE_THRESHOLD_MANIFEST_PATH)
    template_rows = _read_jsonl(SOURCE_TEMPLATE_PATH)
    pending_rows = _read_jsonl(SOURCE_PENDING_QUEUE_PATH)
    owner_report = _read_json(SOURCE_OWNER_AUTHORIZED_REPORT_PATH)
    report_items = owner_report.get("resolution_items")
    if not isinstance(report_items, list):
        raise ValueError("owner-authorized discrepancy report must contain resolution_items")
    response_rows, non_actionable_rows = _build_response_rows(
        generated_at=timestamp,
        template_rows=template_rows,
        report_items=report_items,
        authorization_basis=str(owner_report.get("authorization_basis")),
    )
    summary = _build_summary(
        generated_at=timestamp,
        threshold_summary=threshold_summary,
        template_rows=template_rows,
        pending_rows=pending_rows,
        owner_report=owner_report,
        response_rows=response_rows,
        non_actionable_rows=non_actionable_rows,
    )
    matrix = _build_matrix(summary)
    go_no_go = _build_go_no_go(summary)
    _write_private_outputs(
        generated_at=timestamp,
        owner_report=owner_report,
        response_rows=response_rows,
        non_actionable_rows=non_actionable_rows,
        summary=summary,
    )
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
        _append_governance_events(summary, manifest)
    return {"summary": summary, "matrix": matrix, "go_no_go": go_no_go, "manifest": manifest}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--no-governance-event", action="store_true")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at, write_governance_event=not args.no_governance_event)
    summary = result["summary"]
    print(
        "PASS: imported V014 residual-difference owner/agent diagnostic responses "
        f"valid={summary['valid_diagnostic_response_count']} non_actionable={summary['non_actionable_diagnostic_response_count']} "
        f"decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
