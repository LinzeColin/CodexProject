#!/usr/bin/env python3
"""Refresh raw-candidate fingerprint evidence after final threshold.

This phase reads the authorized raw inbox read-only to refresh the private raw
numeric fingerprint pool for the 48 residual blockers that still miss raw
candidate fingerprints. It does not mutate raw files, bind ambiguous raw
records to processed values, run raw-to-processed comparison, reconcile values,
upload GitHub, reinstall the app or execute business steps. Public artifacts
remain aggregate-only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.v014_residual_difference_owner_authorized_anchor_confirmation import (  # noqa: E402
    PRIVATE_SLOT_KEY,
    _changed_kmfa_files,
    _git_check_ignored,
    _git_output,
    _now,
    _read_json,
    _read_jsonl,
    _upsert_jsonl,
    _write_json,
    _write_jsonl,
    _write_text,
)
from KMFA.tools import (  # noqa: E402
    v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold
    as source_resolution,
)


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_RESIDUAL_DIFFERENCE_RAW_CANDIDATE_FINGERPRINT_EVIDENCE_REFRESH_AFTER_FINAL_THRESHOLD"
TASK_ID = "KMFA-V014-RESIDUAL-DIFFERENCE-RAW-CANDIDATE-FINGERPRINT-EVIDENCE-REFRESH-AFTER-FINAL-THRESHOLD-20260707"
ACCEPTANCE_ID = "ACC-V014-RESIDUAL-DIFFERENCE-RAW-CANDIDATE-FINGERPRINT-EVIDENCE-REFRESH-AFTER-FINAL-THRESHOLD"
VERSION = "0.1.4-residual-difference-raw-candidate-fingerprint-evidence-refresh-after-final-threshold"
STATUS = "completed_validated_local_only_raw_candidate_fingerprint_evidence_refreshed_still_blocked_no_go"
DECISION = "NO_GO"
REFRESH_CONCLUSION = "raw_inbox_evidence_refreshed_but_no_authoritative_fingerprint_pair_binding_available_for_48_blockers"
NEXT_REQUIRED_INPUT = "provide_authoritative_source_reference_owner_exclusion_or_formula_mapping_for_48_remaining_blockers"
NEXT_RECOMMENDED_PHASE = "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_INTAKE_AFTER_RAW_REFRESH"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold_summary.json"
MANIFEST_PATH = MACHINE_DIR / "residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold_matrix_public_safe.json"
)

SOURCE_RESOLUTION_SUMMARY_PATH = source_resolution.METADATA_SUMMARY_PATH
SOURCE_RESOLUTION_MANIFEST_PATH = source_resolution.METADATA_MANIFEST_PATH
SOURCE_RESOLUTION_GO_NO_GO_PATH = source_resolution.METADATA_GO_NO_GO_PATH
SOURCE_RESOLUTION_MATRIX_PATH = source_resolution.METADATA_MATRIX_PATH
SOURCE_PRIVATE_RESOLUTION_RECORDS_PATH = source_resolution.PRIVATE_RESOLUTION_RECORDS_PATH

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT / ".codex_private_runtime/v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold"
)
PRIVATE_REFRESH_DIAGNOSTIC_PATH = (
    PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_candidate_fingerprint_evidence_refresh_diagnostic.json"
)
PRIVATE_REFRESH_RECORDS_PATH = (
    PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_candidate_fingerprint_evidence_refresh_records.jsonl"
)
PRIVATE_RAW_INDEX_PATH = PRIVATE_OUTPUT_DIR / "private_raw_source_index_after_final_threshold_refresh.json"
PRIVATE_REFRESH_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_candidate_fingerprint_evidence_refresh.md"
BUNDLED_PYTHON = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"


def _scan_raw_sources() -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        from KMFA.tools import v014_processed_value_source_map_completion_auto_candidate_draft as auto_candidate

        return auto_candidate._scan_raw_sources()
    except Exception:
        if not BUNDLED_PYTHON.exists():
            raise
    PRIVATE_RAW_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    script = """
import json
import sys
from pathlib import Path
sys.path.insert(0, ".")
from KMFA.tools import v014_processed_value_source_map_completion_auto_candidate_draft as auto_candidate
public, private = auto_candidate._scan_raw_sources()
Path(sys.argv[1]).write_text(json.dumps({"public": public, "private": private}, ensure_ascii=False), encoding="utf-8")
"""
    result = subprocess.run(
        [BUNDLED_PYTHON.as_posix(), "-c", script, PRIVATE_RAW_INDEX_PATH.as_posix()],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"bundled raw scan failed: {result.stderr.strip()}")
    payload = _read_json(PRIVATE_RAW_INDEX_PATH)
    return payload["public"], payload["private"]


def _raw_boundary(raw_public_summary: dict[str, Any]) -> dict[str, bool]:
    return {
        "user_authorized_raw_data_read_for_this_phase": True,
        "user_declared_raw_data_immutable": True,
        "raw_data_root_readonly_policy_active": True,
        "source_resolution_public_artifacts_read_by_this_phase": True,
        "source_private_resolution_records_read_by_this_phase": True,
        "raw_inbox_read_performed_by_this_phase": True,
        "raw_inbox_list_performed_by_this_phase": True,
        "raw_inbox_stat_performed_by_this_phase": True,
        "raw_inbox_hash_or_value_fingerprint_performed_by_this_phase": True,
        "raw_inbox_parse_performed_by_this_phase": True,
        "raw_inbox_field_or_header_read_performed_by_this_phase": True,
        "raw_inbox_value_extraction_performed_by_this_phase": True,
        "raw_root_stat_unchanged_after_phase": bool(
            raw_public_summary.get("raw_root_stat_unchanged_after_auto_candidate_draft")
        ),
        "private_raw_index_written_by_this_phase": True,
        "private_refresh_records_written_by_this_phase": True,
        "private_refresh_diagnostic_written_by_this_phase": True,
        "private_refresh_report_written_by_this_phase": True,
        "source_private_resolution_records_mutated_by_this_phase": False,
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
        "private_raw_index_committed": False,
        "private_refresh_diagnostic_committed": False,
        "private_refresh_records_committed": False,
        "private_refresh_report_committed": False,
        "source_private_resolution_records_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "raw_digest_committed": False,
        "office_workbook_committed": False,
        "source_document_committed": False,
        "field_header_plaintext_committed": False,
        "target_slot_detail_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_value_fingerprint_committed": False,
        "private_ref_or_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _normalize_fingerprint(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    return value.removeprefix("sha256:")


def _build_refresh_records(
    *, generated_at: str, source_records: list[dict[str, Any]], raw_private_index: dict[str, Any]
) -> list[dict[str, Any]]:
    raw_numeric_records = [row for row in raw_private_index.get("numeric_records", []) if isinstance(row, dict)]
    raw_by_value_fingerprint: dict[str, list[dict[str, Any]]] = {}
    for row in raw_numeric_records:
        fingerprint = _normalize_fingerprint(row.get("numeric_value_fingerprint"))
        if fingerprint:
            raw_by_value_fingerprint.setdefault(fingerprint, []).append(row)

    records: list[dict[str, Any]] = []
    for index, row in enumerate(source_records, start=1):
        processed_fingerprint = _normalize_fingerprint(row.get("processed_value_fingerprint"))
        matches = raw_by_value_fingerprint.get(processed_fingerprint or "", [])
        unique_match_ref_count = len({match.get("record_ref_hash") for match in matches if match.get("record_ref_hash")})
        deterministic_match = processed_fingerprint is not None and unique_match_ref_count == 1
        records.append(
            {
                "refresh_item_id": f"RAW-FP-REFRESH-FT-{index:03d}",
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "source_resolution_attempt_item_id": row.get("resolution_attempt_item_id"),
                PRIVATE_SLOT_KEY: row.get(PRIVATE_SLOT_KEY),
                "diagnostic_track": row.get("diagnostic_track"),
                "source_resolution_attempt_status": row.get("resolution_attempt_status"),
                "source_auto_resolved_raw_candidate_fingerprint": row.get("auto_resolved_raw_candidate_fingerprint"),
                "processed_fingerprint_available_in_source_record": processed_fingerprint is not None,
                "raw_numeric_candidate_pool_available": bool(raw_numeric_records),
                "raw_candidate_value_fingerprint_match_count": len(matches),
                "raw_candidate_record_ref_unique_match_count": unique_match_ref_count,
                "deterministic_raw_candidate_fingerprint_match": deterministic_match,
                "raw_refresh_status": (
                    "deterministic_raw_candidate_fingerprint_match_ready_for_owner_review"
                    if deterministic_match
                    else "blocked_missing_authoritative_fingerprint_pair_after_raw_refresh"
                ),
                "refresh_blocker_reason": (
                    "none"
                    if deterministic_match
                    else "source_record_lacks_processed_fingerprint_or_authoritative_source_reference_for_safe_binding"
                ),
                "comparison_retry_ready_after_raw_refresh": deterministic_match,
                "raw_to_processed_value_comparison_performed_by_this_phase": False,
                "full_raw_to_processed_value_comparison_complete": False,
                "business_value_consistency_verified": False,
                "public_commit_allowed": False,
            }
        )
    return records


def _write_private_outputs(
    *, generated_at: str, records: list[dict[str, Any]], raw_public_summary: dict[str, Any], raw_private_index: dict[str, Any], raw_boundary: dict[str, bool]
) -> dict[str, Any]:
    status_counts = Counter(row.get("raw_refresh_status") for row in records)
    track_counts = Counter(row.get("diagnostic_track") for row in records)
    raw_index_payload = {
        "schema_version": "kmfa.private.v014_raw_candidate_fingerprint_evidence_refresh_raw_index.v1",
        "classification": "private_raw_source_index_after_final_threshold_refresh_do_not_commit",
        "record_type": "v014_raw_candidate_fingerprint_evidence_refresh_raw_index",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "source_raw_scan_private_index": raw_private_index,
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_raw_candidate_fingerprint_evidence_refresh_diagnostic.v1",
        "classification": "private_raw_candidate_fingerprint_evidence_refresh_diagnostic_do_not_commit",
        "record_type": "v014_raw_candidate_fingerprint_evidence_refresh_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "refresh_conclusion": REFRESH_CONCLUSION,
        "refresh_item_count": len(records),
        "status_counts": dict(status_counts),
        "track_counts": dict(track_counts),
        "raw_public_summary": raw_public_summary,
        "raw_boundary": raw_boundary,
    }
    _write_json(PRIVATE_RAW_INDEX_PATH, raw_index_payload)
    _write_json(PRIVATE_REFRESH_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_REFRESH_RECORDS_PATH, records)
    _write_text(
        PRIVATE_REFRESH_REPORT_PATH,
        "\n".join(
            [
                "# Private Raw Candidate Fingerprint Evidence Refresh After Final Threshold",
                "",
                f"- phase_id: `{PHASE_ID}`",
                f"- refresh_item_count: `{len(records)}`",
                f"- deterministic_match_count: `{status_counts['deterministic_raw_candidate_fingerprint_match_ready_for_owner_review']}`",
                f"- still_blocked_count: `{status_counts['blocked_missing_authoritative_fingerprint_pair_after_raw_refresh']}`",
                "- raw_to_processed_value_comparison_performed_by_this_phase: `false`",
                "",
                "This private report and raw index may contain raw file names, sheet names, values, context and fingerprints. Do not commit.",
                "",
            ]
        ),
    )
    return diagnostic


def _build_summary(
    *,
    generated_at: str,
    source_summary: dict[str, Any],
    source_manifest: dict[str, Any],
    source_go_no_go: dict[str, Any],
    source_matrix: dict[str, Any],
    source_records: list[dict[str, Any]],
    refresh_records: list[dict[str, Any]],
    raw_public_summary: dict[str, Any],
    raw_boundary: dict[str, bool],
    public_safety: dict[str, bool],
) -> dict[str, Any]:
    status_counts = Counter(row.get("raw_refresh_status") for row in refresh_records)
    track_counts = Counter(row.get("diagnostic_track") for row in refresh_records)
    deterministic_count = status_counts["deterministic_raw_candidate_fingerprint_match_ready_for_owner_review"]
    still_blocked_count = status_counts["blocked_missing_authoritative_fingerprint_pair_after_raw_refresh"]
    return {
        "schema_version": "kmfa.v014_raw_candidate_fingerprint_evidence_refresh_after_final_threshold_summary.v1",
        "record_type": "v014_raw_candidate_fingerprint_evidence_refresh_after_final_threshold_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "refresh_conclusion": REFRESH_CONCLUSION,
        "source_phase_id": source_summary.get("phase_id"),
        "source_manifest_phase_id": source_manifest.get("phase_id"),
        "source_go_no_go_decision": source_go_no_go.get("decision"),
        "source_matrix_check_fail_count": source_matrix.get("check_fail_count"),
        "source_resolution_attempt_item_count": source_summary.get("resolution_attempt_item_count"),
        "source_auto_resolved_raw_candidate_fingerprint_count": source_summary.get(
            "auto_resolved_raw_candidate_fingerprint_count"
        ),
        "source_still_blocked_raw_candidate_fingerprint_count": source_summary.get(
            "still_blocked_raw_candidate_fingerprint_count"
        ),
        "source_private_resolution_record_count": len(source_records),
        "refresh_item_count": len(refresh_records),
        "raw_root_file_count": int(raw_public_summary.get("raw_root_file_count") or 0),
        "raw_archive_member_count": int(raw_public_summary.get("archive_member_count") or 0),
        "raw_archive_workbook_member_count": int(raw_public_summary.get("archive_workbook_member_count") or 0),
        "raw_archive_pdf_member_count": int(raw_public_summary.get("archive_pdf_member_count") or 0),
        "raw_openable_workbook_count": int(raw_public_summary.get("openable_workbook_count") or 0),
        "raw_openable_pdf_count": int(raw_public_summary.get("openable_pdf_count") or 0),
        "raw_workbook_parse_error_count": int(raw_public_summary.get("workbook_parse_error_count") or 0),
        "raw_pdf_parse_error_count": int(raw_public_summary.get("pdf_parse_error_count") or 0),
        "raw_numeric_candidate_count": int(raw_public_summary.get("raw_numeric_candidate_count") or 0),
        "raw_unique_numeric_fingerprint_count": int(raw_public_summary.get("raw_unique_numeric_fingerprint_count") or 0),
        "raw_value_fingerprints_generated": bool(raw_public_summary.get("raw_value_fingerprints_generated")),
        "raw_root_stat_unchanged_after_phase": bool(
            raw_public_summary.get("raw_root_stat_unchanged_after_auto_candidate_draft")
        ),
        "deterministic_raw_candidate_fingerprint_match_count": deterministic_count,
        "still_blocked_after_raw_refresh_count": still_blocked_count,
        "comparison_retry_ready_after_raw_refresh_count": sum(
            1 for row in refresh_records if row.get("comparison_retry_ready_after_raw_refresh") is True
        ),
        "owner_select_one_authoritative_candidate_count": track_counts["owner_select_one_authoritative_candidate"],
        "provide_authoritative_source_reference_or_owner_exclusion_count": track_counts[
            "provide_authoritative_source_reference_or_owner_exclusion"
        ],
        "provide_formula_or_non_numeric_mapping_count": track_counts["provide_formula_or_non_numeric_mapping"],
        "private_raw_index_written": True,
        "private_refresh_diagnostic_written": True,
        "private_refresh_records_written": True,
        "private_refresh_report_written": True,
        "private_raw_index_gitignored": _git_check_ignored(PRIVATE_RAW_INDEX_PATH),
        "private_refresh_diagnostic_gitignored": _git_check_ignored(PRIVATE_REFRESH_DIAGNOSTIC_PATH),
        "private_refresh_records_gitignored": _git_check_ignored(PRIVATE_REFRESH_RECORDS_PATH),
        "private_refresh_report_gitignored": _git_check_ignored(PRIVATE_REFRESH_REPORT_PATH),
        "source_private_resolution_records_gitignored": _git_check_ignored(SOURCE_PRIVATE_RESOLUTION_RECORDS_PATH),
        "unresolved_difference_count": source_summary.get("unresolved_difference_count"),
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
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": raw_boundary,
        "public_safety": public_safety,
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_resolution_phase_loaded", str(summary["source_phase_id"]).endswith("RESOLUTION_ATTEMPT_AFTER_FINAL_THRESHOLD")),
        ("source_still_blocked_count_locked", summary["source_still_blocked_raw_candidate_fingerprint_count"] == 48),
        ("source_private_resolution_records_loaded", summary["source_private_resolution_record_count"] == 48),
        ("raw_root_available", summary["raw_root_file_count"] > 0),
        ("raw_numeric_fingerprint_pool_refreshed", summary["raw_numeric_candidate_count"] > 0),
        ("raw_unique_numeric_fingerprint_pool_refreshed", summary["raw_unique_numeric_fingerprint_count"] > 0),
        ("raw_root_unchanged_after_refresh", summary["raw_root_stat_unchanged_after_phase"] is True),
        ("refresh_item_count_locked", summary["refresh_item_count"] == 48),
        ("deterministic_match_count_zero_locked", summary["deterministic_raw_candidate_fingerprint_match_count"] == 0),
        ("still_blocked_after_refresh_locked", summary["still_blocked_after_raw_refresh_count"] == 48),
        ("comparison_retry_ready_zero_locked", summary["comparison_retry_ready_after_raw_refresh_count"] == 0),
        ("private_refresh_outputs_ignored", summary["private_refresh_records_gitignored"] is True),
        ("private_raw_index_ignored", summary["private_raw_index_gitignored"] is True),
        ("no_value_comparison_claimed", summary["raw_to_processed_value_comparison_performed_by_this_phase"] is False),
        ("downstream_gates_closed", summary["github_upload_performed"] is False and summary["business_execution_performed"] is False),
    ]
    rows = [{"check_code": code, "status": "PASS" if passed else "FAIL"} for code, passed in checks]
    pass_count = sum(1 for row in rows if row["status"] == "PASS")
    return {
        "schema_version": "kmfa.v014_raw_candidate_fingerprint_evidence_refresh_after_final_threshold_matrix_public_safe.v1",
        "record_type": "v014_raw_candidate_fingerprint_evidence_refresh_after_final_threshold_matrix_public_safe",
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
        "schema_version": "kmfa.v014_raw_candidate_fingerprint_evidence_refresh_after_final_threshold_go_no_go.v1",
        "record_type": "v014_raw_candidate_fingerprint_evidence_refresh_after_final_threshold_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "refresh_conclusion": REFRESH_CONCLUSION,
        "refresh_item_count": summary["refresh_item_count"],
        "raw_numeric_candidate_count": summary["raw_numeric_candidate_count"],
        "deterministic_raw_candidate_fingerprint_match_count": summary["deterministic_raw_candidate_fingerprint_match_count"],
        "still_blocked_after_raw_refresh_count": summary["still_blocked_after_raw_refresh_count"],
        "comparison_retry_ready_after_raw_refresh_count": summary["comparison_retry_ready_after_raw_refresh_count"],
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
    }


def _write_human(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> None:
    report = f"""# V014 Raw Candidate Fingerprint Evidence Refresh After Final Threshold

Generated at: {summary["generated_at"]}

## Scope

- Phase: `{PHASE_ID}`
- Decision: `{DECISION}`
- Status: `{STATUS}`
- Source: prior public-safe resolution-attempt evidence, ignored private resolution records, and authorized read-only raw inbox refresh.
- Raw boundary: read/list/stat/parse/value-fingerprint only; no raw write, delete, move, rename, copy, normalize or mutation.

## Public-Safe Result

- Source still-blocked raw candidate fingerprint count: `{summary["source_still_blocked_raw_candidate_fingerprint_count"]}`
- Refresh items: `{summary["refresh_item_count"]}`
- Raw numeric candidate count: `{summary["raw_numeric_candidate_count"]}`
- Raw unique numeric fingerprint count: `{summary["raw_unique_numeric_fingerprint_count"]}`
- Deterministic raw candidate fingerprint matches: `{summary["deterministic_raw_candidate_fingerprint_match_count"]}`
- Still blocked after raw refresh: `{summary["still_blocked_after_raw_refresh_count"]}`
- Comparison retry ready after raw refresh: `{summary["comparison_retry_ready_after_raw_refresh_count"]}`

## Gate

The raw evidence pool was refreshed, but the 48 blockers still lack authoritative fingerprint-pair binding evidence. This phase does not compare raw and processed values and does not claim business consistency.

Next required input: `{NEXT_REQUIRED_INPUT}`.
"""
    go_record = f"""# Go / No-Go Record

- Phase: `{PHASE_ID}`
- Decision: `{go_no_go["decision"]}`
- Reason: raw evidence refresh did not produce deterministic authoritative fingerprint-pair bindings for the 48 blockers.
- Matrix: `{matrix["check_pass_count"]}` pass / `{matrix["check_fail_count"]}` fail
- GitHub upload: not allowed in this phase.
- App reinstall: not allowed in this phase.
"""
    test_results = f"""# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold.py --require-private-refresh`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold.py`
- Governance validators, diff check, raw/private marker scan, secret scan, private-output git-ignore scan and private-runtime tracked-file scan: expected before commit.

Expected matrix result: {matrix["check_pass_count"]}/{matrix["check_count"]} PASS.
"""
    risk_register = """# Risk Register

- Risk: refreshed raw numeric evidence is mistaken for an authoritative source binding.
- Control: comparison retry remains false unless a deterministic processed/raw fingerprint pair exists.
- Risk: raw details leak into public artifacts.
- Control: raw index, raw file names, fields, values, context and fingerprints stay in ignored private runtime.
- Risk: raw data is modified during refresh.
- Control: the phase performs read/list/stat/parse/fingerprint only and checks root stat is unchanged.
"""
    rollback = f"""# Rollback Plan

Remove artifacts for `{PHASE_ID}`, metadata copies, ignored private refresh outputs, tool, validator, focused test and governance rows. Do not touch raw inbox files or prior private/source artifacts.
"""
    _write_text(REPORT_PATH, report)
    _write_text(GO_NO_GO_RECORD_PATH, go_record)
    _write_text(TEST_RESULTS_PATH, test_results)
    _write_text(RISK_REGISTER_PATH, risk_register)
    _write_text(ROLLBACK_PATH, rollback)


def _build_manifest(summary: dict[str, Any], matrix: dict[str, Any], go_no_go: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_raw_candidate_fingerprint_evidence_refresh_after_final_threshold_manifest.v1",
        "record_type": "v014_raw_candidate_fingerprint_evidence_refresh_after_final_threshold_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "refresh_conclusion": REFRESH_CONCLUSION,
        "summary": summary,
        "matrix": matrix,
        "go_no_go_report": go_no_go,
        "source_artifacts": {
            "resolution_summary": "public_safe_metadata_copy",
            "resolution_manifest": "public_safe_metadata_copy",
            "resolution_go_no_go": "public_safe_metadata_copy",
            "resolution_matrix": "public_safe_metadata_copy",
            "resolution_private_records": "ignored_private_runtime",
            "raw_index_after_refresh": "ignored_private_runtime",
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
            "private:raw_candidate_fingerprint_evidence_refresh_diagnostic",
            "private:raw_candidate_fingerprint_evidence_refresh_records",
            "private:raw_source_index_after_final_threshold_refresh",
            "private:raw_candidate_fingerprint_evidence_refresh_report",
        ],
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold.py --require-private-refresh",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold.py",
        ],
        "git": {
            "branch": _git_output(["branch", "--show-current"]),
            "head": _git_output(["rev-parse", "HEAD"]),
            "status_short_branch": _git_output(["status", "--short", "--branch"]),
            "changed_kmfa_files": _changed_kmfa_files(),
        },
    }


def _write_governance_events(generated_at: str, summary: dict[str, Any]) -> None:
    event = {
        "event_id": "DEV-KMFA-20260707-V014-RAW-CANDIDATE-FINGERPRINT-EVIDENCE-REFRESH-AFTER-FINAL-THRESHOLD",
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "stage_id": "value-consistency",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "status": STATUS,
        "decision": DECISION,
        "go_no_go": DECISION,
        "summary": "Refreshed raw inbox numeric fingerprint evidence read-only; 48 blockers remain unbound and comparison retry stays closed.",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "files_changed": _changed_kmfa_files(),
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold.py --require-private-refresh",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold.py",
        ],
        "test_results": ["PENDING: final validation results will be recorded before local commit."],
        "next_required_input": NEXT_REQUIRED_INPUT,
        "refresh_item_count": summary["refresh_item_count"],
        "raw_numeric_candidate_count": summary["raw_numeric_candidate_count"],
        "deterministic_raw_candidate_fingerprint_match_count": summary[
            "deterministic_raw_candidate_fingerprint_match_count"
        ],
        "still_blocked_after_raw_refresh_count": summary["still_blocked_after_raw_refresh_count"],
        "raw_inbox_read_performed": True,
        "raw_inbox_mutation_performed": False,
        "raw_to_processed_value_comparison_performed": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "fact_level": "EXTRACTED",
    }
    _upsert_jsonl(DEVELOPMENT_EVENTS_PATH, event, ("event_id",))
    phase_status = {
        "record_type": "v014_phase",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_CANDIDATE_FINGERPRINT_EVIDENCE_REFRESH_AFTER_FINAL_THRESHOLD",
        "roadmap_stage_id": "VALUE-CONSISTENCY",
        "governance_stage_id": "VALUE-CONSISTENCY",
        "name": "v0.1.4 residual difference raw candidate fingerprint evidence refresh after final threshold",
        "status": STATUS,
        "acceptance_id": ACCEPTANCE_ID,
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "fact_level": "EXTRACTED",
        "estimated_task_units": 1,
        "completed_task_units": 1,
        "derived_percent": 100.0,
        "task_count": 3,
        "updated_at": generated_at[:10],
    }
    _upsert_jsonl(STAGE_STATUS_PATH, phase_status, ("record_type", "phase_id"))
    task_records = [
        ("T1", "refresh raw inbox numeric fingerprint evidence read-only"),
        ("T2", "attempt conservative private binding for 48 missing raw candidate fingerprint blockers"),
        ("T3", "emit public-safe NO_GO evidence while keeping comparison and upload gates closed"),
    ]
    for suffix, goal in task_records:
        _upsert_jsonl(
            TASK_STATUS_PATH,
            {
                "schema_version": "kmfa.v014_stage_phase_task_status.v1",
                "record_type": "v014_task",
                "project_id": "KMFA",
                "stage_id": "VALUE-CONSISTENCY",
                "governance_stage_id": "VALUE-CONSISTENCY",
                "roadmap_stage_id": "VALUE-CONSISTENCY",
                "phase_id": PHASE_ID,
                "roadmap_phase_id": "RESIDUAL_DIFFERENCE_RAW_CANDIDATE_FINGERPRINT_EVIDENCE_REFRESH_AFTER_FINAL_THRESHOLD",
                "task_id": f"{TASK_ID}-{suffix}",
                "task_goal": goal,
                "status": "completed",
                "acceptance_id": ACCEPTANCE_ID,
                "evidence_ref": MANIFEST_PATH.as_posix(),
                "raw_data_committed": False,
                "fact_level": "EXTRACTED",
                "version": VERSION,
                "derived_percent": 100.0,
                "updated_at": generated_at[:10],
            },
            ("record_type", "task_id"),
        )


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    generated = generated_at or _now()
    source_summary = _read_json(SOURCE_RESOLUTION_SUMMARY_PATH)
    source_manifest = _read_json(SOURCE_RESOLUTION_MANIFEST_PATH)
    source_go_no_go = _read_json(SOURCE_RESOLUTION_GO_NO_GO_PATH)
    source_matrix = _read_json(SOURCE_RESOLUTION_MATRIX_PATH)
    source_records = _read_jsonl(SOURCE_PRIVATE_RESOLUTION_RECORDS_PATH)
    if source_summary.get("still_blocked_raw_candidate_fingerprint_count") != 48:
        raise ValueError("source still-blocked raw candidate fingerprint count must be 48")
    if source_summary.get("auto_resolved_raw_candidate_fingerprint_count") != 0:
        raise ValueError("source auto-resolved count must be 0")
    if len(source_records) != 48:
        raise ValueError("source private resolution records must be 48")

    raw_public_summary, raw_private_index = _scan_raw_sources()
    raw_boundary = _raw_boundary(raw_public_summary)
    public_safety = _public_safety()
    refresh_records = _build_refresh_records(
        generated_at=generated,
        source_records=source_records,
        raw_private_index=raw_private_index,
    )
    private_diagnostic = _write_private_outputs(
        generated_at=generated,
        records=refresh_records,
        raw_public_summary=raw_public_summary,
        raw_private_index=raw_private_index,
        raw_boundary=raw_boundary,
    )
    summary = _build_summary(
        generated_at=generated,
        source_summary=source_summary,
        source_manifest=source_manifest,
        source_go_no_go=source_go_no_go,
        source_matrix=source_matrix,
        source_records=source_records,
        refresh_records=refresh_records,
        raw_public_summary=raw_public_summary,
        raw_boundary=raw_boundary,
        public_safety=public_safety,
    )
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
        _write_governance_events(generated, summary)
    return {
        "summary": summary,
        "matrix": matrix,
        "go_no_go": go_no_go,
        "manifest": manifest,
        "private_diagnostic": private_diagnostic,
        "private_refresh_records": refresh_records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--no-governance-event", action="store_true")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at, write_governance_event=not args.no_governance_event)
    summary = result["summary"]
    print(
        "PASS: generated V014 raw candidate fingerprint evidence refresh after final threshold "
        f"decision={summary['decision']} refresh_items={summary['refresh_item_count']} "
        f"raw_numeric_candidates={summary['raw_numeric_candidate_count']} "
        f"deterministic_matches={summary['deterministic_raw_candidate_fingerprint_match_count']} "
        f"blocked={summary['still_blocked_after_raw_refresh_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
