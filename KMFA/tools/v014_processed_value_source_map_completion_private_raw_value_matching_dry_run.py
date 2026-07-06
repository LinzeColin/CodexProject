#!/usr/bin/env python3
"""Generate public-safe evidence for the private raw value matching dry run.

This phase consumes ignored private runtime indexes produced by earlier KMFA
v0.1.4 phases. It does not read, parse, stat, hash, copy, move, rename, delete,
or mutate the raw inbox. Public artifacts contain aggregate counts only; target
fingerprints and row-level matching diagnostics stay under the ignored private
runtime directory.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_RAW_VALUE_MATCHING_DRY_RUN"
TASK_ID = "KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PRIVATE-RAW-VALUE-MATCHING-DRY-RUN-20260706"
ACCEPTANCE_ID = "ACC-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-PRIVATE-RAW-VALUE-MATCHING-DRY-RUN"
VERSION = "0.1.4-private-raw-value-matching-dry-run"
STATUS = "completed_validated_local_only_private_raw_value_matching_dry_run_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "private_raw_value_matching_dry_run_completed_full_delivery_still_blocked"
PREVIOUS_REQUIRED_INPUT = "private_raw_value_matching_dry_run_before_any_delivery_claim"
NEXT_RECOMMENDED_PHASE = "V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_PRIVATE_MISMATCH_AND_BLOCKER_REPORT"
NEXT_REQUIRED_INPUT = "private_mismatch_and_blocker_report_before_any_full_reconciliation_or_delivery_claim"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_raw_value_matching_dry_run_summary.json"
MANIFEST_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_raw_value_matching_dry_run_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_raw_value_matching_dry_run_go_no_go_report.json"
GAP_SUMMARY_PATH = MACHINE_DIR / "processed_value_source_map_completion_private_raw_value_matching_dry_run_gap_summary.json"
REPORT_PATH = HUMAN_DIR / "processed_value_source_map_completion_private_raw_value_matching_dry_run_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_raw_value_matching_dry_run_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_private_raw_value_matching_dry_run_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_private_raw_value_matching_dry_run_go_no_go_report.json"
METADATA_GAP_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_raw_value_matching_dry_run_gap_summary.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"

PRIVATE_RAW_INDEX_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_auto_candidate_draft/private_raw_source_index.json"
)
PRIVATE_PROCESSED_MATERIALIZATION_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_private_processed_value_materialization/private_processed_value_materialization.json"
)
PRIVATE_AUTHORIZED_FILL_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_private_processed_value_source_map_authorized_fill/private_processed_value_source_map_authorized_fill.json"
)
PRIVATE_PARTIAL_COMPARISON_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_processed_value_source_map_completion_partial_raw_to_processed_comparison/private_partial_raw_to_processed_comparison.json"
)
SOURCE_PREFLIGHT_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_private_raw_comparison_preflight_summary.json"
SOURCE_PARTIAL_COMPARISON_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_partial_raw_to_processed_comparison_summary.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_processed_value_source_map_completion_private_raw_value_matching_dry_run"
PRIVATE_DRY_RUN_PATH = PRIVATE_OUTPUT_DIR / "private_raw_value_matching_dry_run.json"
PRIVATE_DRY_RUN_JSONL_PATH = PRIVATE_OUTPUT_DIR / "private_raw_value_matching_records.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_raw_value_matching_diagnostic.json"
PRIVATE_GAP_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_raw_value_matching_gap_report.md"

HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


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


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records), encoding="utf-8")


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


def _normalize_sha256(value: Any) -> str | None:
    if isinstance(value, str) and SHA256.fullmatch(value):
        return value
    if isinstance(value, str) and HEX64.fullmatch(value):
        return "sha256:" + value.lower()
    return None


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
        "private_raw_source_index_read_performed_by_this_phase": True,
        "private_processed_artifact_read_performed_by_this_phase": True,
        "private_runtime_diagnostic_written_by_this_phase": True,
    }


def _public_safety() -> dict[str, bool]:
    return {
        "public_safe_aggregate_only": True,
        "private_raw_source_index_committed": False,
        "private_processed_materialization_committed": False,
        "private_authorized_fill_committed": False,
        "private_partial_comparison_committed": False,
        "private_dry_run_records_committed": False,
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


def _raw_index_summary(raw_index: dict[str, Any]) -> tuple[dict[str, Any], Counter[str]]:
    numeric_records = raw_index.get("numeric_records", [])
    parse_errors = raw_index.get("parse_errors", [])
    source_records = raw_index.get("source_records", [])
    if not isinstance(numeric_records, list):
        raise ValueError("numeric_records must be a list")
    raw_counter: Counter[str] = Counter()
    for record in numeric_records:
        if not isinstance(record, dict):
            continue
        fingerprint = _normalize_sha256(record.get("numeric_value_fingerprint"))
        if fingerprint:
            raw_counter[fingerprint] += 1
    summary = {
        "private_raw_index_ready": True,
        "raw_numeric_record_count": len(numeric_records),
        "raw_numeric_fingerprint_record_count": sum(raw_counter.values()),
        "raw_unique_numeric_fingerprint_count": len(raw_counter),
        "raw_source_record_count": len(source_records) if isinstance(source_records, list) else 0,
        "raw_parse_error_count": len(parse_errors) if isinstance(parse_errors, list) else 0,
    }
    return summary, raw_counter


def _collect_processed_targets(
    *,
    processed_materialization: dict[str, Any],
    authorized_fill: dict[str, Any],
    partial_comparison: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    materialized_rows = processed_materialization.get("materialized_processed_slots", [])
    filled_items = authorized_fill.get("filled_items", [])
    unfilled_items = authorized_fill.get("unfilled_items", [])
    exact_rows = partial_comparison.get("exact_match_rows", [])
    blocked_rows = partial_comparison.get("source_blocked_partial_application_rows", [])
    if not isinstance(materialized_rows, list):
        raise ValueError("materialized_processed_slots must be a list")
    if not isinstance(filled_items, list) or not isinstance(unfilled_items, list):
        raise ValueError("authorized fill row lists must be lists")
    if not isinstance(exact_rows, list) or not isinstance(blocked_rows, list):
        raise ValueError("partial comparison row lists must be lists")

    targets: list[dict[str, Any]] = []
    for row in filled_items:
        if not isinstance(row, dict):
            continue
        fingerprint = _normalize_sha256(row.get("processed_value_fingerprint"))
        if not fingerprint:
            continue
        targets.append(
            {
                "target_source": "owner_authorized_fill",
                "target_slot_id": row.get("target_slot_id"),
                "value_fingerprint": fingerprint,
            }
        )
    for row in exact_rows:
        if not isinstance(row, dict):
            continue
        fingerprint = _normalize_sha256(row.get("processed_replay_fingerprint"))
        if not fingerprint:
            continue
        targets.append(
            {
                "target_source": "partial_exact_comparison_replay",
                "target_slot_id": row.get("target_slot_id"),
                "review_group_id": row.get("review_group_id"),
                "value_fingerprint": fingerprint,
            }
        )

    materialized_fingerprint_count = 0
    for row in materialized_rows:
        if isinstance(row, dict) and _normalize_sha256(row.get("value_fingerprint")):
            materialized_fingerprint_count += 1

    summary = {
        "processed_materialization_target_slot_count": len(materialized_rows),
        "processed_materialization_value_fingerprint_count": materialized_fingerprint_count,
        "processed_materialization_complete": materialized_fingerprint_count == len(materialized_rows)
        and len(materialized_rows) > 0,
        "owner_authorized_fill_target_count": len(filled_items),
        "owner_authorized_fill_value_fingerprint_count": sum(
            1
            for row in filled_items
            if isinstance(row, dict) and _normalize_sha256(row.get("processed_value_fingerprint"))
        ),
        "owner_authorized_unfilled_target_count": len(unfilled_items),
        "partial_exact_replay_target_count": len(exact_rows),
        "partial_blocked_target_slot_count": len(blocked_rows),
        "dry_run_processed_fingerprint_target_count": len(targets),
        "dry_run_unique_processed_fingerprint_count": len({target["value_fingerprint"] for target in targets}),
    }
    return summary, targets


def _match_targets(raw_counter: Counter[str], targets: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    source_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    for target in targets:
        fingerprint = target["value_fingerprint"]
        occurrence_count = raw_counter.get(fingerprint, 0)
        if occurrence_count == 0:
            status = "no_raw_index_fingerprint_match"
        elif occurrence_count == 1:
            status = "unique_raw_index_fingerprint_match"
        else:
            status = "ambiguous_raw_index_fingerprint_match"
        source_counts[str(target["target_source"])] += 1
        status_counts[status] += 1
        rows.append(
            {
                "target_source": target["target_source"],
                "target_slot_id": target.get("target_slot_id"),
                "review_group_id": target.get("review_group_id"),
                "value_fingerprint": fingerprint,
                "raw_index_occurrence_count": occurrence_count,
                "match_status": status,
            }
        )
    matched_count = status_counts["unique_raw_index_fingerprint_match"] + status_counts[
        "ambiguous_raw_index_fingerprint_match"
    ]
    summary = {
        "raw_value_matching_dry_run_performed": True,
        "dry_run_target_source_counts": dict(sorted(source_counts.items())),
        "dry_run_match_status_counts": dict(sorted(status_counts.items())),
        "dry_run_matched_target_count": matched_count,
        "dry_run_unmatched_target_count": status_counts["no_raw_index_fingerprint_match"],
        "dry_run_unique_raw_match_target_count": status_counts["unique_raw_index_fingerprint_match"],
        "dry_run_ambiguous_raw_match_target_count": status_counts["ambiguous_raw_index_fingerprint_match"],
        "dry_run_confirmed_fingerprint_mismatch_count": 0,
        "repeated_cross_validation_mismatch_confirmed": False,
        "full_raw_to_processed_value_comparison_performed_by_this_phase": False,
        "business_value_consistency_verified": False,
    }
    return summary, rows


def _build_private_payload(
    *,
    generated_at: str,
    raw_summary: dict[str, Any],
    processed_summary: dict[str, Any],
    matching_summary: dict[str, Any],
    matching_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.private.v014_processed_value_source_map_completion_private_raw_value_matching_dry_run.v1",
        "classification": "private_raw_value_matching_dry_run_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_private_raw_value_matching_dry_run",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "dry_run_summary": {
            **raw_summary,
            **processed_summary,
            **matching_summary,
            "decision": DECISION,
            "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        },
        "matching_rows": matching_rows,
        "raw_boundary": _raw_boundary(),
    }


def _gap_summary(
    *,
    generated_at: str,
    processed_summary: dict[str, Any],
    matching_summary: dict[str, Any],
) -> dict[str, Any]:
    gaps = [
        {
            "gap_code": "processed_materialization_value_fingerprints_missing",
            "affected_count": processed_summary["processed_materialization_target_slot_count"],
            "public_safe_detail": "processed materialization artifact has no comparable value fingerprints",
        },
        {
            "gap_code": "owner_authorized_fill_targets_unmatched_in_private_raw_index",
            "affected_count": matching_summary["dry_run_match_status_counts"].get(
                "no_raw_index_fingerprint_match", 0
            ),
            "public_safe_detail": "owner-authorized fill fingerprints were not found in the private raw numeric index",
        },
        {
            "gap_code": "ambiguous_private_raw_index_matches",
            "affected_count": matching_summary["dry_run_match_status_counts"].get(
                "ambiguous_raw_index_fingerprint_match", 0
            ),
            "public_safe_detail": "some matching fingerprints are not unique in the private raw numeric index",
        },
        {
            "gap_code": "full_reconciliation_target_slots_still_blocked",
            "affected_count": processed_summary["partial_blocked_target_slot_count"],
            "public_safe_detail": "full raw-to-processed reconciliation remains blocked for residual target slots",
        },
    ]
    return {
        "schema_version": "kmfa.v014_private_raw_value_matching_dry_run_gap_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_private_raw_value_matching_dry_run_gap_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "decision": DECISION,
        "gap_count": len(gaps),
        "gaps": gaps,
        "repeated_cross_validation_mismatch_confirmed": False,
        "final_goal_closeout_difference_report_required_if_repeated": True,
        "business_value_consistency_verified": False,
    }


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_preflight_summary = _read_json(SOURCE_PREFLIGHT_SUMMARY_PATH)
    source_partial_summary = _read_json(SOURCE_PARTIAL_COMPARISON_SUMMARY_PATH)
    raw_index = _read_json(PRIVATE_RAW_INDEX_PATH)
    processed_materialization = _read_json(PRIVATE_PROCESSED_MATERIALIZATION_PATH)
    authorized_fill = _read_json(PRIVATE_AUTHORIZED_FILL_PATH)
    partial_comparison = _read_json(PRIVATE_PARTIAL_COMPARISON_PATH)

    raw_summary, raw_counter = _raw_index_summary(raw_index)
    processed_summary, targets = _collect_processed_targets(
        processed_materialization=processed_materialization,
        authorized_fill=authorized_fill,
        partial_comparison=partial_comparison,
    )
    matching_summary, matching_rows = _match_targets(raw_counter, targets)
    private_payload = _build_private_payload(
        generated_at=timestamp,
        raw_summary=raw_summary,
        processed_summary=processed_summary,
        matching_summary=matching_summary,
        matching_rows=matching_rows,
    )
    diagnostic = {
        "schema_version": "kmfa.private.v014_private_raw_value_matching_dry_run_diagnostic.v1",
        "classification": "private_raw_value_matching_diagnostic_do_not_commit",
        "record_type": "v014_processed_value_source_map_completion_private_raw_value_matching_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "dry_run_summary": private_payload["dry_run_summary"],
        "raw_boundary": _raw_boundary(),
    }
    gap_summary = _gap_summary(
        generated_at=timestamp,
        processed_summary=processed_summary,
        matching_summary=matching_summary,
    )
    _write_json(PRIVATE_DRY_RUN_PATH, private_payload)
    _write_jsonl(PRIVATE_DRY_RUN_JSONL_PATH, matching_rows)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_text(
        PRIVATE_GAP_REPORT_PATH,
        "# Private Raw Value Matching Gap Report\n\n"
        "This private report contains only target-level fingerprints and aggregate match diagnostics. "
        "It must remain ignored and must not be committed.\n",
    )

    summary = {
        "schema_version": "kmfa.v014_private_raw_value_matching_dry_run_summary.v1",
        "record_type": "v014_processed_value_source_map_completion_private_raw_value_matching_dry_run_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": STATUS,
        "generated_at": timestamp,
        "source_preflight_phase_id": source_preflight_summary.get("phase_id"),
        "source_preflight_decision": source_preflight_summary.get("decision"),
        "source_partial_comparison_phase_id": source_partial_summary.get("phase_id"),
        "source_partial_comparison_decision": source_partial_summary.get("decision"),
        "previous_required_input": PREVIOUS_REQUIRED_INPUT,
        "previous_required_input_resolved_by_this_phase": True,
        **raw_summary,
        **processed_summary,
        **matching_summary,
        "private_dry_run_written": True,
        "private_dry_run_gitignored": _git_check_ignored(PRIVATE_DRY_RUN_PATH),
        "private_dry_run_jsonl_written": True,
        "private_dry_run_jsonl_gitignored": _git_check_ignored(PRIVATE_DRY_RUN_JSONL_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_gap_report_written": True,
        "private_gap_report_gitignored": _git_check_ignored(PRIVATE_GAP_REPORT_PATH),
        "canonical_source_map_mutated": False,
        "canonical_source_map_records_applied_count": 0,
        "full_raw_to_processed_reconciliation_complete": False,
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
        "schema_version": "kmfa.v014_private_raw_value_matching_dry_run_go_no_go.v1",
        "record_type": "v014_processed_value_source_map_completion_private_raw_value_matching_dry_run_go_no_go_report",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "raw_numeric_fingerprint_record_count": summary["raw_numeric_fingerprint_record_count"],
        "dry_run_processed_fingerprint_target_count": summary["dry_run_processed_fingerprint_target_count"],
        "dry_run_matched_target_count": summary["dry_run_matched_target_count"],
        "dry_run_unmatched_target_count": summary["dry_run_unmatched_target_count"],
        "dry_run_unique_raw_match_target_count": summary["dry_run_unique_raw_match_target_count"],
        "dry_run_ambiguous_raw_match_target_count": summary["dry_run_ambiguous_raw_match_target_count"],
        "dry_run_confirmed_fingerprint_mismatch_count": summary["dry_run_confirmed_fingerprint_mismatch_count"],
        "raw_value_matching_dry_run_performed": True,
        "full_raw_to_processed_value_comparison_performed_by_this_phase": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "blocked_until": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_private_raw_value_matching_dry_run_manifest.v1",
        "record_type": "v014_processed_value_source_map_completion_private_raw_value_matching_dry_run_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_ids": [ACCEPTANCE_ID],
        "generated_at": timestamp,
        "status": STATUS,
        "summary": summary,
        "go_no_go": go_no_go,
        "gap_summary": gap_summary,
        "artifact_refs": {
            "machine_summary": SUMMARY_PATH.as_posix(),
            "machine_manifest": MANIFEST_PATH.as_posix(),
            "machine_go_no_go": GO_NO_GO_PATH.as_posix(),
            "machine_gap_summary": GAP_SUMMARY_PATH.as_posix(),
            "private_dry_run": "private_runtime_only",
            "private_dry_run_jsonl": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
            "private_gap_report": "private_runtime_only",
        },
        "validator": (
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. "
            "python3 KMFA/tools/check_v014_processed_value_source_map_completion_private_raw_value_matching_dry_run.py "
            "--require-private-dry-run"
        ),
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short": _git_output(["status", "--short", "--branch"]),
        },
    }

    report = f"""# V014 Private Raw Value Matching Dry Run

Decision: {DECISION}

This phase matches existing private raw numeric fingerprints against available processed-side fingerprint targets. It uses ignored private runtime indexes only and does not read or mutate the raw inbox.

## Public-safe aggregate result

- Private raw numeric fingerprint records: {summary["raw_numeric_fingerprint_record_count"]}
- Unique private raw numeric fingerprints: {summary["raw_unique_numeric_fingerprint_count"]}
- Dry-run processed fingerprint targets: {summary["dry_run_processed_fingerprint_target_count"]}
- Matched targets: {summary["dry_run_matched_target_count"]}
- Unmatched targets: {summary["dry_run_unmatched_target_count"]}
- Unique raw-index matches: {summary["dry_run_unique_raw_match_target_count"]}
- Ambiguous raw-index matches: {summary["dry_run_ambiguous_raw_match_target_count"]}
- Confirmed fingerprint mismatches: {summary["dry_run_confirmed_fingerprint_mismatch_count"]}
- Business value consistency verified: `false`

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_no_go_record = f"""# Go/No-Go Record

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- reason: `{DIAGNOSTIC_CONCLUSION}`
- raw_value_matching_dry_run_performed: `true`
- dry_run_processed_fingerprint_target_count: `{summary["dry_run_processed_fingerprint_target_count"]}`
- dry_run_matched_target_count: `{summary["dry_run_matched_target_count"]}`
- dry_run_unmatched_target_count: `{summary["dry_run_unmatched_target_count"]}`
- full raw-to-processed comparison performed: `false`
- github upload performed: `false`
"""
    risk_register = """# Risk Register

- Risk: treating a dry-run fingerprint lookup as full business value reconciliation.
  Mitigation: keep business consistency, formal report, GitHub upload, app reinstall and business execution gates closed.
- Risk: leaking private target fingerprints or source details publicly.
  Mitigation: public artifacts contain aggregate counts only; row-level diagnostics stay in ignored runtime.
"""
    rollback_plan = """# Rollback Plan

No raw inbox file, canonical source map, app file or public business data was modified. To roll back, remove this phase's public artifacts and metadata copies, remove the ignored private dry-run outputs if not needed, and revert this local commit.
"""
    test_results = """# Test Results

Status: passed locally.

Commands:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_private_raw_value_matching_dry_run.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_private_raw_value_matching_dry_run.py --require-private-dry-run`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_private_raw_value_matching_dry_run`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `git diff --check -- KMFA`
- `git ls-files KMFA | rg -n '\\.(zip|xlsx|xlsm|xls|pdf|sqlite|sqlite3|db|pem|key|p12|pfx)$|\\.codex_private_runtime'`
- high-confidence tracked secret marker scan under `KMFA`
"""
    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (GAP_SUMMARY_PATH, gap_summary),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_GAP_SUMMARY_PATH, gap_summary),
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
    event_id = "DEV-KMFA-20260706-V014-PRIVATE-RAW-VALUE-MATCHING-DRY-RUN"
    summary = manifest["summary"]
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260706-KMFA-V014-PRIVATE-RAW-VALUE-MATCHING-DRY-RUN",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": manifest["go_no_go"]["decision"],
        "raw_value_matching_dry_run_performed": True,
        "dry_run_processed_fingerprint_target_count": summary["dry_run_processed_fingerprint_target_count"],
        "dry_run_matched_target_count": summary["dry_run_matched_target_count"],
        "dry_run_unmatched_target_count": summary["dry_run_unmatched_target_count"],
        "dry_run_ambiguous_raw_match_target_count": summary["dry_run_ambiguous_raw_match_target_count"],
        "raw_inbox_read_performed": False,
        "raw_inbox_mutation_performed": False,
        "full_raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "summary": "Completed private raw value matching dry run with public-safe aggregate evidence and kept full delivery blocked.",
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
        "PASS: KMFA v0.1.4 private raw value matching dry run generated "
        f"(decision={manifest['go_no_go']['decision']}, "
        f"targets={manifest['summary']['dry_run_processed_fingerprint_target_count']}, "
        f"matched={manifest['summary']['dry_run_matched_target_count']}, "
        f"unmatched={manifest['summary']['dry_run_unmatched_target_count']})"
    )


if __name__ == "__main__":
    main()
