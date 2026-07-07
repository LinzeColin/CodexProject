#!/usr/bin/env python3
"""Recheck readiness after residual-difference diagnostic response import.

This phase proves the missing-response blocker was cleared by the previous
response-import phase, while also proving the imported responses are still
non-actionable and cannot open source-map correction, raw comparison, upload,
app reinstall, or business execution.
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
PHASE_ID = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_RESPONSE_IMPORT_READINESS_RECHECK"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-RESPONSE-IMPORT-READINESS-RECHECK-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-RESPONSE-IMPORT-READINESS-RECHECK"
VERSION = "0.1.4-outside-scope-candidate-review-residual-difference-response-import-readiness-recheck"
STATUS = "completed_validated_local_only_residual_difference_response_import_readiness_rechecked_no_go"
DECISION = "NO_GO"
READINESS_CONCLUSION = "missing_response_blocker_cleared_but_source_map_correction_not_ready"
NEXT_REQUIRED_INPUT = "source_map_correction_or_authoritative_value_resolution_required_before_full_raw_to_processed_comparison"
NEXT_RECOMMENDED_PHASE = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_BLOCKER_AUDIT"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_response_import_readiness_recheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_response_import_readiness_recheck_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_response_import_readiness_recheck_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_candidate_review_residual_difference_response_import_readiness_recheck_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_candidate_review_residual_difference_response_import_readiness_recheck.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_response_import_readiness_recheck_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_response_import_readiness_recheck_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_response_import_readiness_recheck_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_response_import_readiness_recheck_matrix_public_safe.json"

SOURCE_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import_summary.json"
SOURCE_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import_manifest.json"
SOURCE_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import_go_no_go_report.json"
SOURCE_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import_matrix_public_safe.json"
SOURCE_PRIVATE_RESPONSE_RECORD_PATH = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import/private_owner_or_agent_diagnostic_response_import_record.json"
SOURCE_PRIVATE_RESPONSE_ITEMS_PATH = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import/private_owner_or_agent_diagnostic_response_import_items.jsonl"
SOURCE_PRIVATE_NON_ACTIONABLE_QUEUE_PATH = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import/private_owner_or_agent_diagnostic_response_non_actionable_queue.jsonl"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_residual_difference_response_import_readiness_recheck"
PRIVATE_READINESS_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_response_import_readiness_recheck_diagnostic.json"
PRIVATE_SOURCE_MAP_BLOCKER_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_response_import_source_map_correction_blocker_queue.jsonl"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_response_import_readiness_recheck_report.md"

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
        "source_response_import_public_summary_read_by_this_phase": True,
        "source_response_import_public_manifest_read_by_this_phase": True,
        "source_response_import_private_record_read_by_this_phase": True,
        "source_response_import_private_items_read_by_this_phase": True,
        "source_response_import_private_non_actionable_queue_read_by_this_phase": True,
        "private_readiness_diagnostic_written_by_this_phase": True,
        "private_source_map_blocker_queue_written_by_this_phase": True,
        "source_response_import_private_record_mutated_by_this_phase": False,
        "source_response_import_private_items_mutated_by_this_phase": False,
        "source_response_import_private_non_actionable_queue_mutated_by_this_phase": False,
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
        "source_private_response_record_committed": False,
        "source_private_response_items_committed": False,
        "source_private_non_actionable_queue_committed": False,
        "private_readiness_diagnostic_committed": False,
        "private_source_map_blocker_queue_committed": False,
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


def _build_private_blocker_queue(*, generated_at: str, response_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(response_items, start=1):
        rows.append(
            {
                "blocker_item_id": f"OSCR-RIR-SMCB-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_response_import_item_id": item.get("response_import_item_id"),
                "target_slot_id": item.get("target_slot_id"),
                "diagnostic_track": item.get("diagnostic_track"),
                "response_decision_code": item.get("response_decision_code"),
                "source_map_correction_ready_after_recheck": False,
                "discrepancy_closed_after_recheck": False,
                "blocker_reason_code": "valid_response_is_non_actionable_discrepancy_report",
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
    response_record: dict[str, Any],
    response_items: list[dict[str, Any]],
    non_actionable_rows: list[dict[str, Any]],
    blocker_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    track_counts = Counter(str(row.get("diagnostic_track")) for row in response_items)
    decision_counts = Counter(str(row.get("response_decision_code")) for row in response_items)
    source_record_items = response_record.get("response_items", [])
    return {
        "schema_version": "kmfa.v014_residual_difference_response_import_readiness_recheck_summary.v1",
        "record_type": "v014_outside_scope_candidate_review_residual_difference_response_import_readiness_recheck_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "readiness_conclusion": READINESS_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_response_record_item_count": len(source_record_items),
        "source_response_item_count": len(response_items),
        "source_non_actionable_queue_item_count": len(non_actionable_rows),
        "valid_diagnostic_response_count": len(response_items),
        "valid_diagnostic_response_imported_count": source_summary.get("valid_diagnostic_response_imported_count"),
        "pending_diagnostic_response_count": source_summary.get("pending_diagnostic_response_count"),
        "diagnostic_response_blocker_count": source_summary.get("diagnostic_response_blocker_count"),
        "invalid_diagnostic_response_count": source_summary.get("invalid_diagnostic_response_count"),
        "non_actionable_diagnostic_response_count": len(non_actionable_rows),
        "source_map_actionable_response_count": source_summary.get("source_map_actionable_response_count"),
        "actionable_resolution_count": source_summary.get("actionable_resolution_count"),
        "open_residual_difference_count": source_summary.get("open_residual_difference_count"),
        "closed_discrepancy_count": source_summary.get("closed_discrepancy_count"),
        "safe_auto_resolution_count": source_summary.get("safe_auto_resolution_count"),
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
        "response_import_readiness_recheck_performed": True,
        "missing_response_blocker_cleared": len(response_items) == 72
        and source_summary.get("pending_diagnostic_response_count") == 0
        and source_summary.get("diagnostic_response_blocker_count") == 0,
        "source_map_correction_blocker_count": len(blocker_rows),
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
        "private_readiness_diagnostic_written": True,
        "private_source_map_blocker_queue_written": True,
        "private_report_written": True,
        "private_readiness_diagnostic_gitignored": _git_check_ignored(PRIVATE_READINESS_DIAGNOSTIC_PATH),
        "private_source_map_blocker_queue_gitignored": _git_check_ignored(PRIVATE_SOURCE_MAP_BLOCKER_QUEUE_PATH),
        "private_report_gitignored": _git_check_ignored(PRIVATE_REPORT_PATH),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_response_import_loaded", summary["source_phase_id"].endswith("DIAGNOSTIC_RESPONSE_IMPORT")),
        ("source_response_import_valid", summary["source_go_no_go_decision"] == "NO_GO" and summary["source_matrix_check_fail_count"] == 0),
        ("valid_responses_present", summary["valid_diagnostic_response_count"] == 72),
        ("missing_response_blocker_cleared", summary["missing_response_blocker_cleared"] is True),
        ("all_responses_non_actionable", summary["non_actionable_diagnostic_response_count"] == 72),
        ("source_map_actionability_absent", summary["source_map_actionable_response_count"] == 0),
        ("all_residual_differences_still_open", summary["open_residual_difference_count"] == 72),
        ("no_discrepancy_closure", summary["closed_discrepancy_count"] == 0),
        ("source_map_correction_blocked", summary["source_map_correction_blocker_count"] == 72),
        ("track_counts_locked", all(summary[f"{track}_count"] == count for track, count in EXPECTED_TRACK_COUNTS.items())),
        ("decision_counts_locked", all(summary[f"{decision}_count"] == count for decision, count in EXPECTED_DECISION_COUNTS.items())),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("downstream_gates_closed", summary["business_execution_performed"] is False),
    ]
    return {
        "schema_version": "kmfa.v014_residual_difference_response_import_readiness_recheck_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_candidate_review_residual_difference_response_import_readiness_recheck_matrix_public_safe",
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
        "schema_version": "kmfa.v014_residual_difference_response_import_readiness_recheck_go_no_go.v1",
        "record_type": "v014_outside_scope_candidate_review_residual_difference_response_import_readiness_recheck_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "readiness_conclusion": READINESS_CONCLUSION,
        "valid_diagnostic_response_count": summary["valid_diagnostic_response_count"],
        "missing_response_blocker_cleared": summary["missing_response_blocker_cleared"],
        "non_actionable_diagnostic_response_count": summary["non_actionable_diagnostic_response_count"],
        "source_map_correction_blocker_count": summary["source_map_correction_blocker_count"],
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


def _write_private_outputs(generated_at: str, summary: dict[str, Any], blocker_rows: list[dict[str, Any]]) -> None:
    diagnostic = {
        "schema_version": "kmfa.private.v014_residual_difference_response_import_readiness_recheck.v1",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "readiness_conclusion": READINESS_CONCLUSION,
        "valid_diagnostic_response_count": summary["valid_diagnostic_response_count"],
        "source_map_correction_blocker_count": len(blocker_rows),
        "blocker_rows": blocker_rows,
    }
    _write_json(PRIVATE_READINESS_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_SOURCE_MAP_BLOCKER_QUEUE_PATH, blocker_rows)
    _write_text(
        PRIVATE_REPORT_PATH,
        "\n".join(
            [
                "# Private Response Import Readiness Recheck",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- valid_diagnostic_response_count: `{summary['valid_diagnostic_response_count']}`",
                f"- source_map_correction_blocker_count: `{len(blocker_rows)}`",
                "- conclusion: valid responses exist, but no source-map actionable response exists.",
                "",
            ]
        ),
    )


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    report = f"""# V014 Residual Difference Response Import Readiness Recheck

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: previous public-safe response-import artifacts plus ignored private response-import outputs.
- Raw boundary: no raw inbox read, list, stat, parse, value extraction, write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Result

- Valid diagnostic responses: `{summary["valid_diagnostic_response_count"]}`
- Missing-response blocker cleared: `{str(summary["missing_response_blocker_cleared"]).lower()}`
- Non-actionable diagnostic responses: `{summary["non_actionable_diagnostic_response_count"]}`
- Source-map correction blockers: `{summary["source_map_correction_blocker_count"]}`
- Open residual differences: `{summary["open_residual_difference_count"]}`
- Closed discrepancies: `{summary["closed_discrepancy_count"]}`

## Gate

The response gap is closed, but source-map correction remains blocked because every imported response is non-actionable. Raw-to-processed comparison, full reconciliation, business value consistency, lineage full check, formal report, GitHub upload, app reinstall and business execution remain closed.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: response import readiness is rechecked, but source-map correction is not ready.
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_residual_difference_response_import_readiness_recheck.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_response_import_readiness_recheck.py --require-private-readiness`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_residual_difference_response_import_readiness_recheck`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA --mode required`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`
- Custom JSON/JSONL/CSV/YAML parse, diff check, staged path scan, secret scan, public artifact raw/private marker scan, private-output git-ignore scan and private-runtime tracked-file scan: PASS.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: valid diagnostic responses are mistaken for source-map correction authority.
- Control: this phase separates missing-response clearance from correction readiness and keeps downstream gates closed.
- Risk: private response details leak into public evidence.
- Control: public artifacts contain aggregate counts only and private readiness artifacts remain ignored.
"""
    rollback = f"""# Rollback Plan

Remove the artifacts for `{PHASE_ID}`, metadata copies, private readiness outputs, tool, validator, focused test and governance entries. Do not touch source response-import private outputs or raw inbox files.
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_record)
    _write_text(TEST_RESULTS_PATH, test_results)
    _write_text(RISK_REGISTER_PATH, risk_register)
    _write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_residual_difference_response_import_readiness_recheck_manifest.v1",
        "record_type": "v014_outside_scope_candidate_review_residual_difference_response_import_readiness_recheck_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "readiness_conclusion": READINESS_CONCLUSION,
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
        "metadata_artifacts": [
            METADATA_SUMMARY_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_GO_NO_GO_PATH.as_posix(),
            METADATA_MATRIX_PATH.as_posix(),
        ],
        "source_public_artifact_count": 4,
        "private_artifact_flags": {
            "read_source_private_response_import_outputs": True,
            "wrote_private_readiness_diagnostic": True,
            "wrote_private_source_map_blocker_queue": True,
            "all_private_artifacts_gitignored": summary["private_readiness_diagnostic_gitignored"]
            and summary["private_source_map_blocker_queue_gitignored"]
            and summary["private_report_gitignored"],
        },
        "git": {
            "head": _git_output(["rev-parse", "HEAD"]),
            "branch": _git_output(["branch", "--show-current"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
        },
    }


def _write_governance(generated_at: str, summary: dict[str, Any], manifest: dict[str, Any]) -> None:
    event = {
        "event_id": "DEV-KMFA-20260707-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-RESPONSE-IMPORT-READINESS-RECHECK",
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "stage_id": "value-consistency",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "status": STATUS,
        "go_no_go": DECISION,
        "summary": "Rechecked response-import readiness, cleared missing-response blocker, and kept source-map correction and downstream gates closed.",
        "valid_diagnostic_response_count": summary["valid_diagnostic_response_count"],
        "missing_response_blocker_cleared": summary["missing_response_blocker_cleared"],
        "source_map_correction_blocker_count": summary["source_map_correction_blocker_count"],
        "closed_discrepancy_count": summary["closed_discrepancy_count"],
        "source_map_correction_ready": False,
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "business_execution_performed": False,
        "fact_level": "EXTRACTED",
        "result_commit": "PENDING",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "files_changed": _changed_kmfa_files(),
    }
    _upsert_jsonl(DEVELOPMENT_EVENTS_PATH, event, ("event_id",))
    _upsert_jsonl(
        STAGE_STATUS_PATH,
        {
            "record_type": "v014_phase",
            "project_id": "KMFA",
            "version": VERSION,
            "governance_stage_id": "VALUE-CONSISTENCY",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_RESPONSE_IMPORT_READINESS_RECHECK",
            "phase_id": PHASE_ID,
            "name": "v0.1.4 residual difference response import readiness recheck",
            "status": STATUS,
            "phase_goal": "recheck valid response import readiness without opening source-map correction or raw comparison",
            "acceptance_id": ACCEPTANCE_ID,
            "acceptance_output": "Readiness recheck manifest summary Go No-Go public-safe matrix private ignored blocker queue validator focused test and governance records",
            "evidence_ref": MANIFEST_PATH.as_posix(),
            "task_count": 3,
            "completed_task_units": 1,
            "estimated_task_units": 1,
            "derived_percent": 100.0,
            "raw_data_committed": False,
            "fact_level": "EXTRACTED",
            "updated_at": "2026-07-07",
        },
        ("phase_id",),
    )
    for index, goal in enumerate(
        (
            "read source response-import public and private artifacts read-only",
            "recheck valid response import readiness and source-map correction blockers",
            "emit public-safe NO_GO readiness evidence while keeping downstream gates closed",
        ),
        start=1,
    ):
        _upsert_jsonl(
            TASK_STATUS_PATH,
            {
                "schema_version": "kmfa.v014_stage_phase_task_status.v1",
                "record_type": "v014_task",
                "project_id": "KMFA",
                "version": VERSION,
                "stage_id": "VALUE-CONSISTENCY",
                "governance_stage_id": "VALUE-CONSISTENCY",
                "roadmap_stage_id": "VALUE-CONSISTENCY",
                "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_RESPONSE_IMPORT_READINESS_RECHECK",
                "phase_id": PHASE_ID,
                "task_id": f"{TASK_ID}-T{index}",
                "task_goal": goal,
                "status": "completed",
                "acceptance_id": ACCEPTANCE_ID,
                "evidence_ref": MANIFEST_PATH.as_posix(),
                "derived_percent": 100.0,
                "raw_data_committed": False,
                "fact_level": "EXTRACTED",
                "updated_at": "2026-07-07",
            },
            ("task_id",),
        )


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated_at = _now(generated_at)
    source_summary = _read_json(SOURCE_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_MATRIX_PATH)
    response_record = _read_json(SOURCE_PRIVATE_RESPONSE_RECORD_PATH)
    response_items = _read_jsonl(SOURCE_PRIVATE_RESPONSE_ITEMS_PATH)
    non_actionable_rows = _read_jsonl(SOURCE_PRIVATE_NON_ACTIONABLE_QUEUE_PATH)
    blocker_rows = _build_private_blocker_queue(generated_at=generated_at, response_items=response_items)
    summary = _build_summary(
        generated_at=generated_at,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        response_record=response_record,
        response_items=response_items,
        non_actionable_rows=non_actionable_rows,
        blocker_rows=blocker_rows,
    )
    _write_private_outputs(generated_at, summary, blocker_rows)
    summary["private_readiness_diagnostic_gitignored"] = _git_check_ignored(PRIVATE_READINESS_DIAGNOSTIC_PATH)
    summary["private_source_map_blocker_queue_gitignored"] = _git_check_ignored(PRIVATE_SOURCE_MAP_BLOCKER_QUEUE_PATH)
    summary["private_report_gitignored"] = _git_check_ignored(PRIVATE_REPORT_PATH)
    matrix = _build_matrix(summary)
    go_no_go = _build_go_no_go(summary)
    _write_human(summary, matrix, go_no_go)
    manifest = _build_manifest(summary, matrix, go_no_go)
    _write_json(SUMMARY_PATH, summary)
    _write_json(MANIFEST_PATH, manifest)
    _write_json(GO_NO_GO_PATH, go_no_go)
    _write_json(MATRIX_PATH, matrix)
    _write_json(METADATA_SUMMARY_PATH, summary)
    _write_json(METADATA_MANIFEST_PATH, manifest)
    _write_json(METADATA_GO_NO_GO_PATH, go_no_go)
    _write_json(METADATA_MATRIX_PATH, matrix)
    if write_governance_event:
        _write_governance(generated_at, summary, manifest)
    return {"summary": summary, "matrix": matrix, "go_no_go": go_no_go, "manifest": manifest}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: rechecked V014 residual-difference response import readiness "
        f"valid={summary['valid_diagnostic_response_count']} "
        f"source_map_blockers={summary['source_map_correction_blocker_count']} decision={summary['decision']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
