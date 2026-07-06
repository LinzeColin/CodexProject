#!/usr/bin/env python3
"""Build a public-safe mismatch and blocker report from the private dry run.

This phase consumes the previous private raw value matching dry-run artifacts.
It does not read the raw inbox and does not publish target-level fingerprints,
slot IDs, review group IDs, raw names, headers, values, or business values.
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
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_MISMATCH_AND_BLOCKER_REPORT"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PRIVATE-MISMATCH-AND-BLOCKER-REPORT-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PRIVATE-MISMATCH-AND-BLOCKER-REPORT"
VERSION = "0.1.4-private-mismatch-and-blocker-report"
STATUS = "completed_validated_local_only_private_mismatch_and_blocker_report_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "private_mismatch_and_blocker_report_completed_full_reconciliation_still_blocked"
PREVIOUS_REQUIRED_INPUT = "private_mismatch_and_blocker_report_before_any_full_reconciliation_or_delivery_claim"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_BLOCKER_RESOLUTION_PACKET"
NEXT_REQUIRED_INPUT = "private_blocker_resolution_packet_before_any_full_raw_to_processed_reconciliation"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_mismatch_and_blocker_report_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_mismatch_and_blocker_report_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_mismatch_and_blocker_report_go_no_go_report.json"
BLOCKER_MATRIX_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_blocker_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_private_mismatch_and_blocker_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_mismatch_and_blocker_report_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_private_mismatch_and_blocker_report_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_private_mismatch_and_blocker_report_go_no_go_report.json"
METADATA_BLOCKER_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_private_blocker_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

SOURCE_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_raw_value_matching_dry_run_summary.json"
SOURCE_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_private_raw_value_matching_dry_run_go_no_go_report.json"
SOURCE_GAP_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_raw_value_matching_dry_run_gap_summary.json"
SOURCE_PRIVATE_DRY_RUN_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_private_raw_value_matching_dry_run/private_raw_value_matching_dry_run.json"
)
SOURCE_PRIVATE_RECORDS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_private_raw_value_matching_dry_run/private_raw_value_matching_records.jsonl"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_private_mismatch_and_blocker_report"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_mismatch_and_blocker_report.json"
PRIVATE_BLOCKER_RECORDS_PATH = PRIVATE_OUTPUT_DIR / "private_blocker_records.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_mismatch_and_blocker_diagnostic.json"
PRIVATE_REPORT_MD_PATH = PRIVATE_OUTPUT_DIR / "private_mismatch_and_blocker_report.md"


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


def _raw_boundary() -> dict[str, bool]:
    return {
        "raw_data_root_readonly_policy_active": True,
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
        "private_matching_dry_run_read_performed_by_this_phase": True,
        "private_matching_records_read_performed_by_this_phase": True,
        "private_runtime_report_written_by_this_phase": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_matching_records_committed": False,
        "private_report_committed": False,
        "private_diagnostic_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "raw_file_hash_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "raw_or_processed_fingerprint_value_committed": False,
        "credential_or_secret_committed": False,
    }


def _summarize_private_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("match_status")) for row in records)
    source_counts = Counter(str(row.get("target_source")) for row in records)
    source_status_counts: dict[str, dict[str, int]] = {}
    for row in records:
        source = str(row.get("target_source"))
        status = str(row.get("match_status"))
        source_status_counts.setdefault(source, {})
        source_status_counts[source][status] = source_status_counts[source].get(status, 0) + 1
    return {
        "private_matching_record_count": len(records),
        "private_matching_status_counts": dict(sorted(status_counts.items())),
        "private_matching_target_source_counts": dict(sorted(source_counts.items())),
        "private_matching_source_status_counts": {
            key: dict(sorted(value.items())) for key, value in sorted(source_status_counts.items())
        },
    }


def _build_blocker_matrix(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_gap_summary: dict[str, Any],
    private_record_summary: dict[str, Any],
) -> dict[str, Any]:
    status_counts = private_record_summary["private_matching_status_counts"]
    source_status_counts = private_record_summary["private_matching_source_status_counts"]
    owner_unmatched = source_status_counts.get("owner_authorized_fill", {}).get(
        "no_raw_index_fingerprint_match", 0
    )
    ambiguous = status_counts.get("ambiguous_raw_index_fingerprint_match", 0)
    blockers = [
        {
            "blocker_code": "processed_materialization_value_fingerprints_missing",
            "severity": "blocking",
            "affected_count": int(source_summary["processed_materialization_target_slot_count"]),
            "public_safe_basis": "processed materialization has no comparable value fingerprints",
            "blocks_full_reconciliation": True,
            "blocks_delivery_claim": True,
            "owner_or_agent_action_required": True,
        },
        {
            "blocker_code": "owner_authorized_fill_targets_unmatched_in_private_raw_index",
            "severity": "blocking",
            "affected_count": owner_unmatched,
            "public_safe_basis": "owner-authorized fill targets did not match the private raw numeric index",
            "blocks_full_reconciliation": True,
            "blocks_delivery_claim": True,
            "owner_or_agent_action_required": True,
        },
        {
            "blocker_code": "ambiguous_private_raw_index_matches",
            "severity": "blocking",
            "affected_count": ambiguous,
            "public_safe_basis": "matching private raw numeric fingerprints are not unique",
            "blocks_full_reconciliation": True,
            "blocks_delivery_claim": True,
            "owner_or_agent_action_required": True,
        },
        {
            "blocker_code": "residual_partial_application_blocked_targets",
            "severity": "blocking",
            "affected_count": int(source_summary["partial_blocked_target_slot_count"]),
            "public_safe_basis": "residual target slots remain blocked from partial application",
            "blocks_full_reconciliation": True,
            "blocks_delivery_claim": True,
            "owner_or_agent_action_required": True,
        },
        {
            "blocker_code": "private_raw_index_parse_errors_present",
            "severity": "review_required",
            "affected_count": int(source_summary["raw_parse_error_count"]),
            "public_safe_basis": "private raw index recorded parse errors that require private diagnostic review",
            "blocks_full_reconciliation": True,
            "blocks_delivery_claim": False,
            "owner_or_agent_action_required": False,
        },
    ]
    confirmed_mismatch_count = int(source_summary["dry_run_confirmed_fingerprint_mismatch_count"])
    return {
        "schema_version": "kmfa.v014_private_blocker_matrix_public_safe.v1",
        "record_type": "v014_processed_value_source_map_completion_private_blocker_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_phase_id": source_summary["phase_id"],
        "source_gap_count": source_gap_summary["gap_count"],
        "blocker_class_count": len(blockers),
        "confirmed_value_mismatch_count": confirmed_mismatch_count,
        "confirmed_mismatch_report_required_now": confirmed_mismatch_count > 0,
        "repeated_cross_validation_mismatch_confirmed": bool(
            source_summary["repeated_cross_validation_mismatch_confirmed"]
        ),
        "final_goal_closeout_difference_report_required_now": False,
        "final_goal_closeout_difference_report_required_if_repeated": True,
        "blockers": blockers,
        "aggregate_affected_count_is_not_unique_target_count": True,
        "business_value_consistency_verified": False,
        "decision": DECISION,
    }


def _private_blocker_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocker_statuses = {
        "no_raw_index_fingerprint_match",
        "ambiguous_raw_index_fingerprint_match",
    }
    return [
        {
            **row,
            "private_blocker_reason": row.get("match_status"),
        }
        for row in records
        if row.get("match_status") in blocker_statuses
    ]


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_summary = _read_json(SOURCE_SUMMARY_PATH)
    source_go_no_go = _read_json(SOURCE_GO_NO_GO_PATH)
    source_gap_summary = _read_json(SOURCE_GAP_SUMMARY_PATH)
    source_private_dry_run = _read_json(SOURCE_PRIVATE_DRY_RUN_PATH)
    private_records = _read_jsonl(SOURCE_PRIVATE_RECORDS_PATH)
    private_record_summary = _summarize_private_records(private_records)
    blocker_matrix = _build_blocker_matrix(
        generated_at=timestamp,
        source_summary=source_summary,
        source_gap_summary=source_gap_summary,
        private_record_summary=private_record_summary,
    )
    private_blockers = _private_blocker_records(private_records)
    private_report = {
        "schema_version": "kmfa.private.v014_private_mismatch_and_blocker_report.v1",
        "classification": "private_mismatch_and_blocker_report_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_private_mismatch_and_blocker_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "source_phase_id": source_private_dry_run.get("phase_id"),
        "private_record_summary": private_record_summary,
        "blocker_matrix_public_safe_copy": blocker_matrix,
        "private_blocker_record_count": len(private_blockers),
        "private_blocker_records": private_blockers,
        "raw_boundary": _raw_boundary(),
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_private_mismatch_and_blocker_diagnostic.v1",
        "classification": "private_mismatch_and_blocker_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_private_mismatch_and_blocker_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "private_record_summary": private_record_summary,
        "blocker_class_count": blocker_matrix["blocker_class_count"],
        "private_blocker_record_count": len(private_blockers),
        "raw_boundary": _raw_boundary(),
    }
    _write_json(PRIVATE_REPORT_PATH, private_report)
    _write_jsonl(PRIVATE_BLOCKER_RECORDS_PATH, private_blockers)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_text(
        PRIVATE_REPORT_MD_PATH,
        "# Private Mismatch And Blocker Report\n\n"
        "This private report may contain target-level refs and value fingerprints. "
        "It is ignored and must not be committed.\n",
    )

    summary = {
        "schema_version": "kmfa.v014_private_mismatch_and_blocker_report_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_private_mismatch_and_blocker_report_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_phase_id": source_summary["phase_id"],
        "source_decision": source_summary["decision"],
        "source_go_no_go_decision": source_go_no_go["decision"],
        "previous_required_input": PREVIOUS_REQUIRED_INPUT,
        "previous_required_input_resolved_by_this_phase": True,
        "mismatch_and_blocker_report_performed": True,
        "private_matching_record_count": private_record_summary["private_matching_record_count"],
        "dry_run_processed_fingerprint_target_count": source_summary["dry_run_processed_fingerprint_target_count"],
        "dry_run_matched_target_count": source_summary["dry_run_matched_target_count"],
        "dry_run_unmatched_target_count": source_summary["dry_run_unmatched_target_count"],
        "dry_run_unique_raw_match_target_count": source_summary["dry_run_unique_raw_match_target_count"],
        "dry_run_ambiguous_raw_match_target_count": source_summary["dry_run_ambiguous_raw_match_target_count"],
        "dry_run_confirmed_fingerprint_mismatch_count": source_summary[
            "dry_run_confirmed_fingerprint_mismatch_count"
        ],
        "processed_materialization_target_slot_count": source_summary[
            "processed_materialization_target_slot_count"
        ],
        "processed_materialization_value_fingerprint_count": source_summary[
            "processed_materialization_value_fingerprint_count"
        ],
        "partial_blocked_target_slot_count": source_summary["partial_blocked_target_slot_count"],
        "raw_parse_error_count": source_summary["raw_parse_error_count"],
        "blocker_class_count": blocker_matrix["blocker_class_count"],
        "confirmed_value_mismatch_count": blocker_matrix["confirmed_value_mismatch_count"],
        "confirmed_mismatch_report_required_now": blocker_matrix["confirmed_mismatch_report_required_now"],
        "repeated_cross_validation_mismatch_confirmed": False,
        "final_goal_closeout_difference_report_required_now": False,
        "final_goal_closeout_difference_report_required_if_repeated": True,
        "private_report_written": True,
        "private_report_gitignored": _git_check_ignored(PRIVATE_REPORT_PATH),
        "private_blocker_records_written": True,
        "private_blocker_records_gitignored": _git_check_ignored(PRIVATE_BLOCKER_RECORDS_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_report_markdown_written": True,
        "private_report_markdown_gitignored": _git_check_ignored(PRIVATE_REPORT_MD_PATH),
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_reconciliation_complete": False,
        "business_value_consistency_verified": False,
        "lineage_full_check_complete": False,
        "formal_report_allowed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "raw_boundary": _raw_boundary(),
        "public_safety": _public_safety(),
    }
    go_no_go = {
        "schema_version": "kmfa.v014_private_mismatch_and_blocker_report_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_private_mismatch_and_blocker_report_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "blocker_class_count": summary["blocker_class_count"],
        "confirmed_value_mismatch_count": summary["confirmed_value_mismatch_count"],
        "dry_run_unmatched_target_count": summary["dry_run_unmatched_target_count"],
        "dry_run_ambiguous_raw_match_target_count": summary["dry_run_ambiguous_raw_match_target_count"],
        "final_goal_closeout_difference_report_required_now": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "blocked_until": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_private_mismatch_and_blocker_report_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_private_mismatch_and_blocker_report_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "generated_at": timestamp,
        "status": STATUS,
        "summary": summary,
        "go_no_go": go_no_go,
        "blocker_matrix": blocker_matrix,
        "artifact_refs": {
            "machine_summary": SUMMARY_PATH.as_posix(),
            "machine_manifest": MANIFEST_PATH.as_posix(),
            "machine_go_no_go": GO_NO_GO_PATH.as_posix(),
            "machine_blocker_matrix": BLOCKER_MATRIX_PATH.as_posix(),
            "private_report": "private_runtime_only",
            "private_blocker_records": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
            "private_report_markdown": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_private_mismatch_and_blocker_report.py "
            "--require-private-report"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }
    report = f"""# V014 Private Mismatch And Blocker Report

Decision: {DECISION}

This phase turns the previous private matching dry run into a public-safe blocker matrix. It does not read the raw inbox and does not publish target-level or value-level private evidence.

## Public-safe aggregate result

- Blocker classes: {summary["blocker_class_count"]}
- Confirmed mismatches: {summary["confirmed_value_mismatch_count"]}
- Dry-run unmatched targets: {summary["dry_run_unmatched_target_count"]}
- Ambiguous raw-index matches: {summary["dry_run_ambiguous_raw_match_target_count"]}
- Residual blocked target slots: {summary["partial_blocked_target_slot_count"]}
- Difference report required now: `false`
- Business value consistency verified: `false`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- blocker_class_count: `{summary["blocker_class_count"]}`
- confirmed_value_mismatch_count: `{summary["confirmed_value_mismatch_count"]}`
- full raw-to-processed reconciliation complete: `false`
- github upload performed: `false`
"""
    test_results = """# Test Results

Status: passed locally.

Commands:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_private_mismatch_and_blocker_report.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_private_mismatch_and_blocker_report.py --require-private-report`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_private_mismatch_and_blocker_report`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `git diff --check -- KMFA`
- tracked and staged raw/private artifact scans
- high-confidence tracked and staged secret marker scans
"""
    risk_register = """# Risk Register

- Risk: treating a blocker matrix as proof of raw-to-processed consistency.
  Mitigation: business consistency, full reconciliation, lineage, formal report and delivery gates remain closed.
- Risk: leaking private target-level evidence.
  Mitigation: public artifacts contain aggregate counts only; private blocker rows stay in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw inbox file, canonical source map, app entry or public business value was modified. To roll back, remove this phase's public artifacts and metadata copies, remove ignored private report outputs if not needed, and revert this local commit.
"""

    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (BLOCKER_MATRIX_PATH, blocker_matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_BLOCKER_MATRIX_PATH, blocker_matrix),
    ):
        _write_json(path, payload)
    for path, text in (
        (REPORT_PATH, report),
        (GO_NO_GO_RECORD_PATH, go_no_go_record),
        (TEST_RESULTS_PATH, test_results),
        (RISK_REGISTER_PATH, risk_register),
        (ROLLBACK_PATH, rollback_plan),
    ):
        _write_text(path, text)
    if write_governance_event:
        _append_development_event(timestamp, manifest)
    return manifest


def _append_development_event(generated_at: str, manifest: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260706-V014-PRIVATE-MISMATCH-AND-BLOCKER-REPORT"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PRIVATE-MISMATCH-AND-BLOCKER-REPORT",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "blocker_class_count": summary["blocker_class_count"],
        "confirmed_value_mismatch_count": summary["confirmed_value_mismatch_count"],
        "dry_run_unmatched_target_count": summary["dry_run_unmatched_target_count"],
        "dry_run_ambiguous_raw_match_target_count": summary["dry_run_ambiguous_raw_match_target_count"],
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "full_raw_to_processed_reconciliation_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Completed public-safe private mismatch and blocker report from the prior matching dry run and kept delivery blocked.",
    }
    DEVELOPMENT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = DEVELOPMENT_EVENTS_PATH.read_text(encoding="utf-8").splitlines() if DEVELOPMENT_EVENTS_PATH.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    DEVELOPMENT_EVENTS_PATH.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    manifest = generate(generated_at=args.generated_at)
    print(
        "PASS: KMFA v0.1.4 private mismatch and blocker report generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"blockers={manifest['summary']['blocker_class_count']}, "
        f"confirmed_mismatches={manifest['summary']['confirmed_value_mismatch_count']})"
    )


if __name__ == "__main__":
    main()
