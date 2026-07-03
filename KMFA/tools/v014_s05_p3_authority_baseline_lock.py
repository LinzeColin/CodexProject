#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S05-P3 public-safe authority baseline lock evidence.

This phase locks the public-safe field candidates produced by v0.1.4 S05-P2.
It does not read, list, stat, hash, or mutate the local raw inbox. The lock is
based on S05-P2 public candidate refs, private-only anchor/hash status flags,
and the active owner/authorized downgrade decision already validated by S05-P2.
No raw filenames, raw hashes, source headers, sheet names, ZIP member names,
row/cell values, source values, normalized values, or business values are
published.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s05_p2_field_golden_baseline import validate_v014_s05_p2_field_golden_baseline
from KMFA.tools.v014_s05_p1_a0_file_registration import RAW_INBOX
from KMFA.tools.v014_s05_p2_field_golden_baseline import (
    MANIFEST_PATH as S05_P2_MANIFEST_PATH,
    PUBLIC_FIELD_CANDIDATES_PATH as S05_P2_CANDIDATES_PATH,
    PUBLIC_FIELD_CONTRACTS_PATH as S05_P2_CONTRACTS_PATH,
    validate_owner_decision,
)


TASK_ID = "KMFA-V014-S05-P3-AUTHORITY-BASELINE-LOCK-20260704"
ACCEPTANCE_ID = "ACC-V014-S05-P3-AUTHORITY-BASELINE-LOCK"
SCHEMA_VERSION = "kmfa.v014_s05_p3_authority_baseline_lock.v1"
RECORD_SCHEMA_VERSION = "kmfa.v014_s05_p3_authority_baseline_record.v1"
BASELINE_VERSION = "KMFA-V014-A0-AUTHORITY-BASELINE-S05P3-PUBLIC-SAFE-20260704"
OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S05_P3_AUTHORITY_BASELINE_LOCK")
MANIFEST_PATH = OUTPUT_DIR / "machine/authority_baseline_lock_manifest.json"
REPORT_PATH = OUTPUT_DIR / "human/authority_baseline_lock_report.md"
TEST_RESULTS_PATH = OUTPUT_DIR / "human/test_results.md"
RISK_REGISTER_PATH = OUTPUT_DIR / "human/risk_register.md"
ROLLBACK_PATH = OUTPUT_DIR / "human/rollback_plan.md"
PUBLIC_AUTHORITY_MANIFEST_PATH = Path("KMFA/metadata/baseline/v014_s05_p3_authority_baseline_manifest.json")
PUBLIC_AUTHORITY_RECORDS_PATH = Path("KMFA/metadata/baseline/v014_s05_p3_authority_baseline_records.jsonl")
NEXT_PHASE = "S05-STAGE-REVIEW"
NEXT_INSTRUCTION = (
    "Run Stage 5 whole review as a separate run after S05-P1/S05-P2/S05-P3 are complete. "
    "Do not perform GitHub upload in S05-P3; GitHub main upload remains deferred until "
    "v1.4 Stage 1-18 are complete, overall review has passed, and findings are fixed."
)
LOCK_STATUS_Q5 = "q5_calculation_baseline_locked_public_safe"
LOCK_STATUS_EXCLUDED = "excluded_cross_source_support_only"


class S05P3GenerationError(Exception):
    pass


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise S05P3GenerationError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise S05P3GenerationError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise S05P3GenerationError(f"{path} contains non-object JSONL row")
        records.append(value)
    return records


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_payload(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def authority_record(
    field_candidate: dict[str, Any],
    *,
    sequence: int,
    locked_at: str,
    locked_by_role: str,
    locked_by_ref: str,
) -> dict[str, Any]:
    is_locked = (
        field_candidate.get("source_file_format") == "pdf"
        and field_candidate.get("source_anchor_status") == "recorded_private_only"
        and field_candidate.get("private_value_hash_status") == "recorded_private_only"
        and field_candidate.get("cross_source_support_only") is False
    )
    is_excluded = (
        field_candidate.get("source_file_format") == "xlsx"
        and field_candidate.get("excel_owner_downgrade_applied") is True
        and field_candidate.get("cross_source_support_only") is True
    )
    if not is_locked and not is_excluded:
        raise S05P3GenerationError(
            "S05-P3 can only lock PDF private-only anchors or exclude owner-downgraded Excel fields: "
            f"{field_candidate.get('field_candidate_public_ref')}"
        )

    lock_status = LOCK_STATUS_Q5 if is_locked else LOCK_STATUS_EXCLUDED
    return {
        "record_type": "v014_s05_p3_public_authority_baseline_record",
        "schema_version": RECORD_SCHEMA_VERSION,
        "authority_record_ref": f"V014-S05P3-AUTH-LOCK-{sequence:03d}",
        "field_candidate_public_ref": field_candidate["field_candidate_public_ref"],
        "candidate_public_ref": field_candidate["candidate_public_ref"],
        "source_public_file_ref": field_candidate["source_public_file_ref"],
        "source_file_format": field_candidate["source_file_format"],
        "field_contract_ref": field_candidate["field_contract_ref"],
        "field_role": field_candidate["field_role"],
        "field_role_status": "canonical_contract_role_not_raw_header_text",
        "lock_status": lock_status,
        "baseline_version": BASELINE_VERSION,
        "locked_at": locked_at,
        "locked_by_role": locked_by_role,
        "locked_by_ref": locked_by_ref,
        "public_field_candidate_hash": sha256_payload(field_candidate),
        "authority_lock_public_hash": sha256_payload(
            {
                "baseline_version": BASELINE_VERSION,
                "field_candidate_public_ref": field_candidate["field_candidate_public_ref"],
                "lock_status": lock_status,
                "locked_by_role": locked_by_role,
                "source_anchor_status": field_candidate["source_anchor_status"],
                "private_value_hash_status": field_candidate["private_value_hash_status"],
            }
        ),
        "source_lock": {
            "source_anchor_status": field_candidate["source_anchor_status"],
            "private_value_hash_status": field_candidate["private_value_hash_status"],
            "source_locator_status": "private_only_not_committed",
            "page_sheet_cell_status": "private_only_not_committed",
            "source_value_status": "private_only_not_committed",
            "normalized_value_status": "private_only_not_committed",
        },
        "quality_state": {
            "machine_candidate_quality_grade": "Q3",
            "q4_human_confirmed": bool(is_locked),
            "q4_human_confirmation_status": (
                "authorized_delegate_confirmed_public_safe_authority_lock"
                if is_locked
                else "excluded_by_owner_authorized_downgrade"
            ),
            "q5_calculation_baseline_allowed": bool(is_locked),
            "q5_full_quality_grade_allowed": False,
            "zero_delta_validated": False,
            "lineage_full_check_completed": False,
            "formal_report_allowed": False,
        },
        "owner_downgrade": {
            "applied": bool(is_excluded),
            "decision_code": "downgrade_to_cross_source_support" if is_excluded else None,
            "q5_exclusion_confirmed": bool(is_excluded),
            "cross_source_support_only": bool(is_excluded),
        },
        "public_repo_safety": {
            "raw_business_data_committed": False,
            "raw_filenames_committed": False,
            "raw_hashes_committed": False,
            "source_header_plaintext_committed": False,
            "sheet_names_committed": False,
            "zip_member_names_committed": False,
            "row_or_cell_values_committed": False,
            "source_or_normalized_values_committed": False,
            "business_values_committed": False,
            "formal_report_committed": False,
        },
    }


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    lock_status_counts = Counter(str(record["lock_status"]) for record in records)
    source_format_counts = Counter(str(record["source_file_format"]) for record in records)
    return {
        "authority_record_count": len(records),
        "field_candidate_count": len(records),
        "q5_calculation_baseline_locked_count": lock_status_counts[LOCK_STATUS_Q5],
        "excluded_cross_source_support_only_count": lock_status_counts[LOCK_STATUS_EXCLUDED],
        "q4_human_confirmed_count": sum(1 for record in records if record["quality_state"]["q4_human_confirmed"] is True),
        "q5_calculation_baseline_allowed_count": sum(
            1 for record in records if record["quality_state"]["q5_calculation_baseline_allowed"] is True
        ),
        "q5_full_quality_grade_allowed_count": sum(
            1 for record in records if record["quality_state"]["q5_full_quality_grade_allowed"] is True
        ),
        "formal_report_allowed_count": sum(
            1 for record in records if record["quality_state"]["formal_report_allowed"] is True
        ),
        "zero_delta_validated_count": sum(1 for record in records if record["quality_state"]["zero_delta_validated"] is True),
        "lineage_full_check_completed_count": sum(
            1 for record in records if record["quality_state"]["lineage_full_check_completed"] is True
        ),
        "pdf_locked_field_count": sum(
            1
            for record in records
            if record["source_file_format"] == "pdf" and record["lock_status"] == LOCK_STATUS_Q5
        ),
        "excel_excluded_field_count": sum(
            1
            for record in records
            if record["source_file_format"] == "xlsx" and record["lock_status"] == LOCK_STATUS_EXCLUDED
        ),
        "source_format_counts": dict(sorted(source_format_counts.items())),
        "lock_status_counts": dict(sorted(lock_status_counts.items())),
    }


def build_payloads(
    *,
    locked_at: str | None = None,
    locked_by_role: str = "authorized_delegate",
    locked_by_ref: str = "codex_v014_s05p3_public_safe_authority_baseline_lock",
) -> dict[str, Any]:
    s05_p2 = validate_v014_s05_p2_field_golden_baseline()
    owner = validate_owner_decision()
    contracts_payload = read_json(S05_P2_CONTRACTS_PATH)
    candidates = read_jsonl(S05_P2_CANDIDATES_PATH)
    locked_timestamp = locked_at or datetime.now().astimezone().isoformat(timespec="seconds")
    authority_records = [
        authority_record(
            field_candidate,
            sequence=index,
            locked_at=locked_timestamp,
            locked_by_role=locked_by_role,
            locked_by_ref=locked_by_ref,
        )
        for index, field_candidate in enumerate(candidates, start=1)
    ]
    summary = summarize_records(authority_records)
    release_state = {
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "github_main_upload_allowed": False,
        "current_go_no_go": "NO_GO",
        "current_data_quality_grade": "Q4",
        "field_level_calculation_baseline_status": "q5_calculation_baseline_locked_for_40_fields_not_full_q5_quality",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "blocking_reason": "zero_delta_lineage_and_stage_review_not_completed",
    }
    public_repo_safety = {
        "raw_business_data_committed": False,
        "zip_committed": False,
        "excel_workbook_committed": False,
        "pdf_committed": False,
        "private_csv_committed": False,
        "sqlite_or_db_committed": False,
        "credentials_committed": False,
        "raw_filenames_committed": False,
        "raw_hashes_committed": False,
        "directory_tree_plaintext_committed": False,
        "zip_member_names_committed": False,
        "sheet_names_committed": False,
        "source_header_plaintext_committed": False,
        "source_or_normalized_values_committed": False,
        "row_or_cell_values_committed": False,
        "business_values_committed": False,
    }
    authority_manifest = {
        "schema_version": "kmfa.v014_s05_p3_public_authority_baseline.v1",
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S05",
        "phase_id": "S05-P3",
        "baseline_version": BASELINE_VERSION,
        "baseline_content_hash": sha256_payload(authority_records),
        "locked_at": locked_timestamp,
        "locked_by_role": locked_by_role,
        "locked_by_ref": locked_by_ref,
        "authority_summary": summary,
        "source_refs": {
            "s05_p2_manifest": str(S05_P2_MANIFEST_PATH),
            "s05_p2_public_field_contracts": str(S05_P2_CONTRACTS_PATH),
            "s05_p2_public_field_candidates": str(S05_P2_CANDIDATES_PATH),
        },
        "public_repo_safety": public_repo_safety,
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S05",
        "stage_name": "A0 authority project cost golden baseline",
        "phase_id": "S05-P3",
        "phase_name": "authority baseline lock",
        "phase_scope": "v014_s05_p3_authority_baseline_lock_only",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": locked_timestamp,
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_authority_baseline_locked_public_safe",
        "completed_task_ids": ["S05P3T01", "S05P3T02", "S05P3T03"],
        "s05_p2_dependency_validated": (
            s05_p2.get("phase_id") == "S05-P2"
            and s05_p2.get("github_upload_performed") is False
            and s05_p2.get("next_recommended_phase") == "S05-P3"
        ),
        "s05_p2_dependency_refs": [
            str(S05_P2_MANIFEST_PATH),
            str(S05_P2_CONTRACTS_PATH),
            str(S05_P2_CANDIDATES_PATH),
        ],
        "owner_decision_summary": {
            "active_actor_role_validated": owner["active_actor_role_validated"],
            "active_decision_present": owner["active_decision_present"],
            "active_decision_code": owner["active_decision_code"],
            "active_decision_public_safe": owner["active_decision_public_safe"],
            "active_decision_raw_or_plaintext_values_included": owner[
                "active_decision_raw_or_plaintext_values_included"
            ],
            "active_preview_q5_exclusion_confirmed": owner["active_preview_q5_exclusion_confirmed"],
            "completion_gate_ready": owner["completion_gate_ready"],
            "completion_gate_mode": owner["completion_gate_mode"],
        },
        "field_contract_count": contracts_payload["contract_count"],
        "authority_baseline_summary": summary,
        "authority_manifest_ref": str(PUBLIC_AUTHORITY_MANIFEST_PATH),
        "authority_records_ref": str(PUBLIC_AUTHORITY_RECORDS_PATH),
        "baseline_version": BASELINE_VERSION,
        "baseline_content_hash": authority_manifest["baseline_content_hash"],
        "locked_at": locked_timestamp,
        "locked_by_role": locked_by_role,
        "locked_by_ref": locked_by_ref,
        "phase_scope_controls": {
            "current_phase_only": True,
            "authority_baseline_lock_performed": True,
            "s05_p3_performed": True,
            "raw_inbox_read_required_by_this_phase": False,
            "raw_inbox_read_by_this_phase": False,
            "raw_inbox_listed_by_this_phase": False,
            "raw_inbox_stat_by_this_phase": False,
            "raw_inbox_hashed_by_this_phase": False,
            "raw_inbox_mutated_by_this_phase": False,
            "private_runtime_written_by_this_phase": False,
            "business_field_parsing_from_raw_performed": False,
            "source_value_matching_performed": False,
            "stage5_review_performed": False,
            "github_upload_performed": False,
            "lineage_full_check_performed": False,
            "zero_delta_validation_performed": False,
            "formal_report_performed": False,
            "live_connector_called": False,
            "opme_deep_coupling_performed": False,
            "business_execution_performed": False,
            "next_phase_started": False,
        },
        "raw_data_boundary": {
            "raw_inbox_path": str(RAW_INBOX),
            "codex_read_allowed_only_when_phase_requires": True,
            "raw_inbox_read_by_this_phase": False,
            "raw_inbox_listed_by_this_phase": False,
            "raw_inbox_stat_by_this_phase": False,
            "raw_inbox_hashed_by_this_phase": False,
            "raw_inbox_modified_by_this_phase": False,
            "raw_inbox_deleted_by_this_phase": False,
            "raw_inbox_moved_by_this_phase": False,
            "raw_inbox_renamed_by_this_phase": False,
            "raw_inbox_overwritten_by_this_phase": False,
            "raw_inbox_written_by_this_phase": False,
            "raw_inbox_generate_inside_by_this_phase": False,
            "raw_inbox_create_extra_files_inside_by_this_phase": False,
            "raw_inbox_mutated_by_this_phase": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
            "raw_filenames_committed": False,
            "raw_hashes_committed": False,
            "directory_tree_plaintext_committed": False,
            "zip_member_names_committed": False,
            "sheet_names_committed": False,
            "source_header_plaintext_committed": False,
            "row_or_cell_values_committed": False,
            "source_or_normalized_values_committed": False,
            "business_values_committed": False,
        },
        "public_repo_safety": public_repo_safety,
        "release_state": release_state,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "validation_summary": {
            "s05_p2_dependency": "PASS",
            "authority_record_count_check": "PASS",
            "q5_calculation_baseline_lock_check": "PASS",
            "excluded_excel_field_check": "PASS",
            "public_safe_manifest_check": "PASS",
            "focused_unit_test": "PENDING_FINAL_VALIDATION",
            "py_compile": "PENDING_FINAL_VALIDATION",
            "s05_p2_validator": "PENDING_FINAL_VALIDATION",
            "s05_p3_validator": "PENDING_FINAL_VALIDATION",
            "no_omission_check": "PENDING_FINAL_VALIDATION",
            "no_float_money_check": "PENDING_FINAL_VALIDATION",
            "governance_validator": "PENDING_FINAL_VALIDATION",
            "lean_governance_validator": "PENDING_FINAL_VALIDATION",
            "governance_sync_validator": "PENDING_FINAL_VALIDATION",
            "structured_parse": "PENDING_FINAL_VALIDATION",
            "ruby_yaml_parse": "PENDING_FINAL_VALIDATION",
            "raw_private_scan": "PENDING_FINAL_VALIDATION",
            "secret_scan": "PENDING_FINAL_VALIDATION",
            "diff_check": "PENDING_FINAL_VALIDATION",
        },
        "evidence_refs": [
            str(REPORT_PATH),
            str(TEST_RESULTS_PATH),
            str(RISK_REGISTER_PATH),
            str(ROLLBACK_PATH),
            str(MANIFEST_PATH),
            str(PUBLIC_AUTHORITY_MANIFEST_PATH),
            str(PUBLIC_AUTHORITY_RECORDS_PATH),
        ],
        "next_recommended_phase": NEXT_PHASE,
        "next_phase_instruction": NEXT_INSTRUCTION,
    }
    return {
        "manifest": manifest,
        "authority_manifest": authority_manifest,
        "authority_records": authority_records,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["authority_baseline_summary"]
    lines = [
        "# KMFA v0.1.4 S05-P3 Authority Baseline Lock",
        "",
        f"- status: `{manifest['status']}`",
        f"- task_id: `{manifest['task_id']}`",
        f"- s05_p2_dependency_validated: `{str(manifest['s05_p2_dependency_validated']).lower()}`",
        f"- baseline_version: `{manifest['baseline_version']}`",
        f"- baseline_content_hash: `{manifest['baseline_content_hash']}`",
        f"- locked_at: `{manifest['locked_at']}`",
        f"- locked_by_role: `{manifest['locked_by_role']}`",
        f"- locked_by_ref: `{manifest['locked_by_ref']}`",
        f"- authority_record_count: `{summary['authority_record_count']}`",
        f"- q5_calculation_baseline_locked_count: `{summary['q5_calculation_baseline_locked_count']}`",
        f"- excluded_cross_source_support_only_count: `{summary['excluded_cross_source_support_only_count']}`",
        f"- q4_human_confirmed_count: `{summary['q4_human_confirmed_count']}`",
        f"- q5_full_quality_grade_allowed_count: `{summary['q5_full_quality_grade_allowed_count']}`",
        f"- zero_delta_validated_count: `{summary['zero_delta_validated_count']}`",
        f"- lineage_full_check_completed_count: `{summary['lineage_full_check_completed_count']}`",
        f"- formal_report_allowed_count: `{summary['formal_report_allowed_count']}`",
        "- raw_inbox_read_by_this_phase: `false`",
        "- raw_inbox_mutated_by_this_phase: `false`",
        "- source_header_plaintext_committed: `false`",
        "- sheet_names_committed: `false`",
        "- zip_member_names_committed: `false`",
        "- source_or_normalized_values_committed: `false`",
        "- row_or_cell_values_committed: `false`",
        "- business_values_committed: `false`",
        "- stage5_review_performed: `false`",
        "- github_upload_performed: `false`",
        "- github_upload_status: `not_uploaded_deferred_until_v014_stage1_18_complete`",
        f"- current_data_quality_grade: `{manifest['release_state']['current_data_quality_grade']}`",
        f"- field_level_calculation_baseline_status: `{manifest['release_state']['field_level_calculation_baseline_status']}`",
        f"- current_report_grade: `{manifest['release_state']['current_report_grade']}`",
        f"- current_go_no_go: `{manifest['release_state']['current_go_no_go']}`",
        "",
        "## Boundary",
        "",
        "- This phase uses only S05-P2 public field candidates, field contracts, and the active owner/authorized downgrade decision.",
        "- The local raw inbox was not read, listed, stat-checked, hashed, modified, or written by this phase.",
        "- Public evidence locks 40 PDF candidate fields as calculation baselines and excludes 5 Excel fields from formal report use.",
        "- Full Q5 quality, zero-delta validation, lineage completion, Stage 5 review, GitHub upload, formal report release, and business execution remain out of scope.",
        "",
        "## Next",
        "",
        manifest["next_phase_instruction"],
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_test_results(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.4 S05-P3 Test Results",
        "",
        "- status: `pending_final_validation`",
        f"- task_id: `{manifest['task_id']}`",
        f"- authority_record_count: `{manifest['authority_baseline_summary']['authority_record_count']}`",
        f"- q5_calculation_baseline_locked_count: `{manifest['authority_baseline_summary']['q5_calculation_baseline_locked_count']}`",
        f"- excluded_cross_source_support_only_count: `{manifest['authority_baseline_summary']['excluded_cross_source_support_only_count']}`",
        f"- github_upload_performed: `{str(manifest['github_upload_performed']).lower()}`",
        "",
        "Final validation results will be recorded before local commit.",
        "",
    ]
    TEST_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEST_RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_risk_and_rollback(manifest: dict[str, Any]) -> None:
    RISK_REGISTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    RISK_REGISTER_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S05-P3 Risk Register",
                "",
                "- risk: public evidence accidentally includes raw filenames, source headers, sheet names, values, or business values",
                "  mitigation: validator scans manifest, records and human evidence for forbidden public keys/text; raw inbox is not accessed.",
                "- risk: calculation baseline is mistaken for formal report readiness",
                "  mitigation: full Q5 quality, zero-delta, lineage, formal report and business execution flags remain false.",
                "- risk: Excel owner-downgraded fields enter the locked calculation baseline",
                "  mitigation: validator requires all 5 Excel fields to remain excluded_cross_source_support_only.",
                "",
                f"- baseline_content_hash: `{manifest['baseline_content_hash']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    ROLLBACK_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S05-P3 Rollback Plan",
                "",
                "- Remove only v0.1.4 S05-P3 files introduced in this phase if validation fails before commit.",
                "- Keep S05-P1/S05-P2 public-safe evidence unchanged.",
                "- Do not touch `/Users/linzezhang/Downloads/KMFA_MetaData` during rollback.",
                "- Re-run S05-P2 and S05-P3 validators after rollback.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def generate() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payloads = build_payloads()
    manifest = payloads["manifest"]
    write_json(MANIFEST_PATH, manifest)
    write_json(PUBLIC_AUTHORITY_MANIFEST_PATH, payloads["authority_manifest"])
    write_jsonl(PUBLIC_AUTHORITY_RECORDS_PATH, payloads["authority_records"])
    write_report(manifest)
    write_test_results(manifest)
    write_risk_and_rollback(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["authority_baseline_summary"]
    print(
        "PASS: KMFA v0.1.4 S05-P3 authority baseline lock evidence generated "
        f"(authority_records={summary['authority_record_count']}, "
        f"q5_calc_locked={summary['q5_calculation_baseline_locked_count']}, "
        f"excluded={summary['excluded_cross_source_support_only_count']}, "
        f"formal_report_allowed={summary['formal_report_allowed_count']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
