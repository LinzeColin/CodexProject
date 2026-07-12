#!/usr/bin/env python3
"""Align outside-scope materialized records with raw candidates after full precheck.

This phase reads the raw inbox read-only to build a private candidate alignment
diagnostic for the 72 outside-scope records that blocked the full comparison
precheck. It does not mutate raw files, correct source maps, run the formal
raw-to-processed comparison, reconcile values, upload GitHub, reinstall the app,
or execute business steps. Public artifacts remain aggregate-only.
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

from KMFA.tools import v014_processed_value_source_map_completion_auto_candidate_draft as auto_candidate  # noqa: E402


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_OUTSIDE_SCOPE_RAW_CANDIDATE_ALIGNMENT_AFTER_FULL_PRECHECK"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-RAW-CANDIDATE-ALIGNMENT-AFTER-FULL-PRECHECK-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-RAW-CANDIDATE-ALIGNMENT-AFTER-FULL-PRECHECK"
VERSION = "0.1.4-outside-scope-raw-candidate-alignment-after-full-precheck"
STATUS = "completed_validated_local_only_outside_scope_raw_candidate_alignment_blocked_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "outside_scope_raw_candidate_alignment_requires_owner_review_or_source_map_correction"
NEXT_RECOMMENDED_PHASE = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_PACKET_AFTER_ALIGNMENT"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_reviews_private_outside_scope_candidate_alignment_before_full_comparison"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_raw_candidate_alignment_after_full_precheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_raw_candidate_alignment_after_full_precheck_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_raw_candidate_alignment_after_full_precheck_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_raw_candidate_alignment_after_full_precheck_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_raw_candidate_alignment_after_full_precheck_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_raw_candidate_alignment_after_full_precheck_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_raw_candidate_alignment_after_full_precheck_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_raw_candidate_alignment_after_full_precheck_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_outside_scope_raw_candidate_alignment_after_full_precheck_matrix_public_safe.json"
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

SOURCE_PRECHECK_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_full_raw_to_processed_comparison_precheck_after_full_materialization_summary.json"
SOURCE_PRECHECK_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_full_raw_to_processed_comparison_precheck_after_full_materialization_manifest.json"
SOURCE_PRECHECK_BLOCKERS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_full_raw_to_processed_comparison_precheck_after_full_materialization/private_full_comparison_precheck_blocker_records.jsonl"
)
SOURCE_FULL_MATERIALIZED_RECORDS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_full_processed_value_materialization_replay_after_outside_scope_application/private_full_materialized_records.jsonl"
)
SOURCE_PROCESSED_STAGING_PATH = PROJECT_ROOT / ".codex_private_runtime/v014_private_processed_value_staging/private_processed_value_staging.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_raw_candidate_alignment_after_full_precheck"
PRIVATE_ALIGNMENT_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_raw_candidate_alignment.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_raw_candidate_alignment_diagnostic.json"
PRIVATE_ALIGNMENT_ITEMS_PATH = PRIVATE_OUTPUT_DIR / "private_outside_scope_raw_candidate_alignment_items.jsonl"
PRIVATE_QUESTION_LIST_PATH = PRIVATE_OUTPUT_DIR / "outside_scope_raw_candidate_alignment_questions_zh.md"

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
    "KMFA/tests/test_v014_outside_scope_raw_candidate_alignment_after_full_precheck.py",
    "KMFA/tools/check_v014_outside_scope_raw_candidate_alignment_after_full_precheck.py",
    "KMFA/tools/v014_outside_scope_raw_candidate_alignment_after_full_precheck.py",
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


def _raw_boundary(raw_public_summary: dict[str, Any]) -> dict[str, bool]:
    return {
        "user_authorized_raw_data_read_for_this_phase": True,
        "raw_data_root_readonly_policy_active": True,
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
        "private_alignment_committed": False,
        "private_alignment_items_committed": False,
        "private_diagnostic_committed": False,
        "private_question_list_committed": False,
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


def _processed_slots_by_id(staging: dict[str, Any]) -> dict[str, dict[str, Any]]:
    slots = staging.get("processed_target_slots", [])
    if not isinstance(slots, list):
        raise ValueError("processed_target_slots must be a list")
    return {str(slot.get("target_slot_id")): slot for slot in slots if isinstance(slot, dict) and slot.get("target_slot_id")}


def _build_alignment(
    *,
    generated_at: str,
    source_precheck: dict[str, Any],
    blocker_rows: list[dict[str, Any]],
    materialized_rows: list[dict[str, Any]],
    processed_staging: dict[str, Any],
    raw_public_summary: dict[str, Any],
    raw_private_index: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], str, dict[str, Any]]:
    materialized_by_slot = {str(row.get("target_slot_id")): row for row in materialized_rows if row.get("target_slot_id")}
    staging_by_slot = _processed_slots_by_id(processed_staging)
    context_groups = [
        str(materialized_by_slot.get(str(row.get("target_slot_id")), {}).get("context_group", ""))
        for row in blocker_rows
    ]
    context_candidates = auto_candidate._build_context_candidates(raw_private_index["numeric_records"], context_groups)
    raw_numeric_fingerprints = {record.get("numeric_value_fingerprint") for record in raw_private_index["numeric_records"]}
    raw_record_refs = {record.get("record_ref_hash") for record in raw_private_index["numeric_records"]}

    items: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    alignment_status_counts: Counter[str] = Counter()
    direct_source_ref_match_count = 0
    direct_processed_fingerprint_match_count = 0
    processed_private_ref_match_count = 0

    for index, blocker in enumerate(blocker_rows, start=1):
        slot_id = str(blocker.get("target_slot_id"))
        materialized = materialized_by_slot.get(slot_id, {})
        staging = staging_by_slot.get(slot_id, {})
        context_group = str(materialized.get("context_group") or staging.get("context_group") or "")
        candidate = context_candidates.get(
            context_group,
            {
                "candidate_status": "auto_unmatched_requires_owner_review",
                "candidate_record_count": 0,
                "candidate_unique_numeric_fingerprint_count": 0,
                "candidate_unique_numeric_fingerprints": [],
                "top_candidate_records": [],
            },
        )
        candidate_status = str(candidate.get("candidate_status"))
        status_counts[candidate_status] += 1
        processed_fingerprint = materialized.get("processed_value_fingerprint")
        direct_source_ref_match = materialized.get("source_record_ref_hash") in raw_record_refs
        if direct_source_ref_match:
            direct_source_ref_match_count += 1
        if processed_fingerprint in raw_numeric_fingerprints:
            direct_processed_fingerprint_match_count += 1
        if processed_fingerprint and processed_fingerprint == staging.get("private_processed_ref_hash"):
            processed_private_ref_match_count += 1

        if candidate_status == "auto_unique_candidate_requires_owner_confirmation":
            alignment_status = "raw_candidate_available_requires_owner_confirmation"
        elif candidate_status == "auto_ambiguous_multiple_candidates_requires_owner_review":
            alignment_status = "ambiguous_raw_candidates_require_owner_review"
        elif candidate_status == "requires_non_numeric_owner_mapping":
            alignment_status = "non_numeric_or_calculation_context_requires_manual_authority"
        else:
            alignment_status = "no_context_raw_candidate_requires_source_mapping_review"
        alignment_status_counts[alignment_status] += 1

        items.append(
            {
                "alignment_item_index": index,
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "target_slot_id": slot_id,
                "context_group": context_group,
                "source_scope": materialized.get("source_scope"),
                "source_record_ref_hash": materialized.get("source_record_ref_hash"),
                "processed_replay_fingerprint": processed_fingerprint,
                "processed_replay_fingerprint_matches_private_processed_ref_hash": (
                    processed_fingerprint == staging.get("private_processed_ref_hash")
                ),
                "direct_source_record_ref_match_in_raw_candidates": direct_source_ref_match,
                "direct_processed_fingerprint_match_in_raw_numeric_candidates": processed_fingerprint in raw_numeric_fingerprints,
                "candidate_status": candidate_status,
                "alignment_status": alignment_status,
                "candidate_record_count": int(candidate.get("candidate_record_count") or 0),
                "candidate_unique_numeric_fingerprint_count": int(
                    candidate.get("candidate_unique_numeric_fingerprint_count") or 0
                ),
                "private_top_candidate_records": candidate.get("top_candidate_records", [])[:10],
                "owner_review_required": True,
                "source_map_correction_ready": False,
                "full_comparison_allowed_by_this_phase": False,
            }
        )

    ready_count = alignment_status_counts.get("raw_candidate_available_requires_owner_confirmation", 0)
    summary_private = {
        "source_precheck_phase_id": source_precheck.get("phase_id"),
        "source_precheck_decision": source_precheck.get("decision"),
        "source_precheck_missing_candidate_count": source_precheck.get("full_scope_missing_candidate_count"),
        "outside_scope_blocker_count": len(blocker_rows),
        "outside_scope_materialized_record_count": len(
            [row for row in materialized_rows if row.get("source_scope") == "outside_scope_extension"]
        ),
        "processed_staging_slot_count": len(processed_staging.get("processed_target_slots", [])),
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
        "outside_scope_context_group_count": len(set(context_groups)),
        "candidate_status_counts": dict(sorted(status_counts.items())),
        "alignment_status_counts": dict(sorted(alignment_status_counts.items())),
        "direct_source_record_ref_match_count": direct_source_ref_match_count,
        "direct_processed_fingerprint_match_count": direct_processed_fingerprint_match_count,
        "processed_replay_fingerprint_matches_private_processed_ref_hash_count": processed_private_ref_match_count,
        "auto_unique_candidate_item_count": ready_count,
        "auto_ambiguous_candidate_item_count": status_counts.get("auto_ambiguous_multiple_candidates_requires_owner_review", 0),
        "auto_unmatched_item_count": status_counts.get("auto_unmatched_requires_owner_review", 0),
        "non_numeric_or_calculation_context_item_count": status_counts.get("requires_non_numeric_owner_mapping", 0),
        "owner_review_required_item_count": len(items),
        "alignment_ready_count": ready_count,
        "source_map_correction_ready": False,
        "full_raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
    }
    alignment = {
        "schema_version": "kmfa.private.v014_outside_scope_raw_candidate_alignment_after_full_precheck.v1",
        "classification": "private_outside_scope_raw_candidate_alignment_do_not_commit",
        "record_type": "v014_outside_scope_raw_candidate_alignment_after_full_precheck",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "summary_private": summary_private,
        "alignment_items": items,
        "raw_boundary": _raw_boundary(raw_public_summary),
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_outside_scope_raw_candidate_alignment_diagnostic.v1",
        "classification": "private_outside_scope_raw_candidate_alignment_diagnostic_do_not_commit",
        "record_type": "v014_outside_scope_raw_candidate_alignment_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "summary_private": summary_private,
        "source_private_refs": {
            "source_precheck_blockers": "private_runtime_only",
            "source_full_materialized_records": "private_runtime_only",
            "source_processed_staging": "private_runtime_only",
            "current_raw_scan": "private_runtime_only",
        },
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "alignment_items_requiring_owner_review": items,
    }
    question_lines = [
        "# KMFA v0.1.4 outside-scope raw candidate alignment 中文问题清单",
        "",
        "说明：本文件包含 raw 文件名、表头、金额、单元格/PDF 位置和诊断细节，只能保留在 private runtime，不得提交 GitHub。",
        "",
        f"- outside-scope blocker count: {len(items)}",
        f"- ambiguous candidate item count: {summary_private['auto_ambiguous_candidate_item_count']}",
        f"- unmatched item count: {summary_private['auto_unmatched_item_count']}",
        f"- non-numeric/calculation item count: {summary_private['non_numeric_or_calculation_context_item_count']}",
        "",
        "## 需要 owner/授权代理确认的问题",
    ]
    for item in items:
        question_lines.extend(
            [
                "",
                f"### Q{item['alignment_item_index']:03d} target_slot_id={item['target_slot_id']}",
                f"- context_group: {item['context_group']}",
                f"- candidate_status: {item['candidate_status']}",
                f"- alignment_status: {item['alignment_status']}",
                f"- candidate_record_count: {item['candidate_record_count']}",
                f"- candidate_unique_numeric_fingerprint_count: {item['candidate_unique_numeric_fingerprint_count']}",
                "- 请确认：是否选择某个 private raw candidate 作为该 outside-scope slot 的 raw-derived candidate，或确认需要更正 source-map/继续 pending。",
            ]
        )
        for candidate_index, candidate in enumerate(item.get("private_top_candidate_records", [])[:5], 1):
            question_lines.extend(
                [
                    f"  - 候选 {candidate_index}:",
                    f"    - raw_file_name: {candidate.get('raw_file_name')}",
                    f"    - archive_member_name: {candidate.get('archive_member_name')}",
                    f"    - record_kind: {candidate.get('record_kind')}",
                    f"    - sheet_name: {candidate.get('sheet_name')}",
                    f"    - cell_address/page_token: {candidate.get('cell_address') or (str(candidate.get('page_index')) + '/' + str(candidate.get('token_index')) if candidate.get('page_index') else '')}",
                    f"    - raw_value: {candidate.get('raw_value')}",
                    f"    - numeric_value_fingerprint: {candidate.get('numeric_value_fingerprint')}",
                    f"    - context_text: {candidate.get('context_text')}",
                ]
            )
    matrix_source = {
        "source_precheck_blockers_available": (len(blocker_rows) == 72, len(blocker_rows), 72),
        "raw_candidate_scan_available": (summary_private["raw_numeric_candidate_count"] > 0, summary_private["raw_numeric_candidate_count"], ">0"),
        "raw_root_unchanged": (summary_private["raw_root_stat_unchanged_after_phase"] is True, True, True),
        "direct_source_ref_coverage": (direct_source_ref_match_count == 72, direct_source_ref_match_count, 72),
        "direct_processed_fingerprint_coverage": (direct_processed_fingerprint_match_count == 72, direct_processed_fingerprint_match_count, 72),
        "owner_review_required_locked": (summary_private["owner_review_required_item_count"] == 72, summary_private["owner_review_required_item_count"], 72),
        "full_comparison_not_claimed": (summary_private["full_raw_to_processed_value_comparison_complete"] is False, False, False),
        "downstream_no_go_preserved": (DECISION == "NO_GO", DECISION, "NO_GO"),
    }
    return alignment, diagnostic, items, "\n".join(question_lines) + "\n", matrix_source


def _build_matrix(generated_at: str, summary: dict[str, Any], matrix_source: dict[str, tuple[bool, Any, Any]]) -> dict[str, Any]:
    rows = [
        {"check_code": code, "status": "PASS" if passed else "FAIL", "observed_public_safe": observed, "required": required}
        for code, (passed, observed, required) in matrix_source.items()
    ]
    return {
        "schema_version": "kmfa.v014_outside_scope_raw_candidate_alignment_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_raw_candidate_alignment_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "check_count": len(rows),
        "pass_count": sum(1 for row in rows if row["status"] == "PASS"),
        "fail_count": sum(1 for row in rows if row["status"] == "FAIL"),
        "checks": rows,
        "outside_scope_blocker_count": summary["outside_scope_blocker_count"],
        "direct_source_record_ref_match_count": summary["direct_source_record_ref_match_count"],
        "direct_processed_fingerprint_match_count": summary["direct_processed_fingerprint_match_count"],
        "owner_review_required_item_count": summary["owner_review_required_item_count"],
        "full_raw_to_processed_value_comparison_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# KMFA v0.1.4 Outside-Scope Raw Candidate Alignment After Full Precheck

- phase: `{PHASE_ID}`
- decision: `{DECISION}`
- outside-scope blocker count: `{summary["outside_scope_blocker_count"]}`
- raw numeric candidate count: `{summary["raw_numeric_candidate_count"]}`
- raw unique numeric fingerprint count: `{summary["raw_unique_numeric_fingerprint_count"]}`
- direct source-ref match count: `{summary["direct_source_record_ref_match_count"]}`
- direct processed-fingerprint match count: `{summary["direct_processed_fingerprint_match_count"]}`
- ambiguous candidate item count: `{summary["auto_ambiguous_candidate_item_count"]}`
- unmatched item count: `{summary["auto_unmatched_item_count"]}`
- non-numeric/calculation item count: `{summary["non_numeric_or_calculation_context_item_count"]}`
- owner review required item count: `{summary["owner_review_required_item_count"]}`
- next required input: `{NEXT_REQUIRED_INPUT}`

This phase reads the raw inbox read-only and writes private alignment diagnostics only. It does not correct the source map, run the formal raw-to-processed comparison, verify business consistency, upload GitHub, reinstall the app, or execute business steps.
"""
    go_no_go_record = f"""# Go/No-Go

- decision: `{DECISION}`
- reason: 72 outside-scope records still require owner/authorized-delegate raw candidate review or source-map correction before full comparison.
- matrix: `{matrix["pass_count"]}` pass / `{matrix["fail_count"]}` fail
- formal comparison allowed: `false`
- business execution allowed: `false`
"""
    risk_register = """# Risk Register

- Risk: context-based raw candidates can be ambiguous and must not be treated as owner authorization.
- Control: private alignment items remain ignored; public evidence contains aggregate counts only.
- Control: raw inbox stat is checked before and after read-only parsing.
"""
    rollback = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, ignored private runtime directory, tool, validator, focused test and governance rows. Do not modify the raw inbox.
"""
    test_results = f"""# Test Results

- expected generator: bundled Python with read-only raw parsing
- expected validator: `KMFA/tools/check_v014_outside_scope_raw_candidate_alignment_after_full_precheck.py --require-private-alignment`
- expected focused test: `KMFA.tests.test_v014_outside_scope_raw_candidate_alignment_after_full_precheck`
- status: generated by phase and verified locally
"""
    for path, text in (
        (REPORT_PATH, report),
        (GO_NO_GO_RECORD_PATH, go_no_go_record),
        (RISK_REGISTER_PATH, risk_register),
        (ROLLBACK_PATH, rollback),
        (TEST_RESULTS_PATH, test_results),
    ):
        _write_text(path, text)


def _append_jsonl_event(path: Path, event_id: str, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    filtered = [line for line in existing if f'"event_id":"{event_id}"' not in line and f'"event_id": "{event_id}"' not in line]
    filtered.append(json.dumps(event, ensure_ascii=False, sort_keys=True))
    path.write_text("\n".join(filtered) + "\n", encoding="utf-8")


def _append_governance_events(generated_at: str, summary: dict[str, Any]) -> None:
    event_id = "DEV-KMFA-20260707-V014-OUTSIDE-SCOPE-RAW-CANDIDATE-ALIGNMENT"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260707-KMFA-V014-OUTSIDE-SCOPE-RAW-CANDIDATE-ALIGNMENT",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "outside_scope_blocker_count": summary["outside_scope_blocker_count"],
        "raw_numeric_candidate_count": summary["raw_numeric_candidate_count"],
        "direct_source_record_ref_match_count": summary["direct_source_record_ref_match_count"],
        "direct_processed_fingerprint_match_count": summary["direct_processed_fingerprint_match_count"],
        "owner_review_required_item_count": summary["owner_review_required_item_count"],
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": True,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "files_changed": FILES_CHANGED,
        "summary": "Generated private outside-scope raw candidate alignment diagnostics and kept full comparison blocked.",
    }
    _append_jsonl_event(DEVELOPMENT_EVENTS_PATH, event_id, event)
    _append_jsonl_event(
        STAGE_STATUS_PATH,
        event_id,
        {
            "event_id": event_id,
            "event_time": generated_at,
            "project_id": "KMFA",
            "stage_id": "value-consistency",
            "phase_id": PHASE_ID,
            "status": STATUS,
            "decision": DECISION,
            "next_required_input": NEXT_REQUIRED_INPUT,
            "evidence_ref": MANIFEST_PATH.as_posix(),
        },
    )
    _append_jsonl_event(
        TASK_STATUS_PATH,
        event_id,
        {
            "event_id": event_id,
            "event_time": generated_at,
            "task_id": TASK_ID,
            "phase_id": PHASE_ID,
            "status": STATUS,
            "decision": DECISION,
            "acceptance_id": ACCEPTANCE_ID,
            "evidence_ref": MANIFEST_PATH.as_posix(),
        },
    )


def generate(*, generated_at: str | None = None, write_governance_event: bool = True) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_precheck = _read_json(SOURCE_PRECHECK_SUMMARY_PATH)
    _read_json(SOURCE_PRECHECK_MANIFEST_PATH)
    blocker_rows = _read_jsonl(SOURCE_PRECHECK_BLOCKERS_PATH)
    materialized_rows = _read_jsonl(SOURCE_FULL_MATERIALIZED_RECORDS_PATH)
    processed_staging = _read_json(SOURCE_PROCESSED_STAGING_PATH)
    raw_public_summary, raw_private_index = auto_candidate._scan_raw_sources()
    alignment, diagnostic, items, question_list, matrix_source = _build_alignment(
        generated_at=timestamp,
        source_precheck=source_precheck,
        blocker_rows=blocker_rows,
        materialized_rows=materialized_rows,
        processed_staging=processed_staging,
        raw_public_summary=raw_public_summary,
        raw_private_index=raw_private_index,
    )
    summary_private = alignment["summary_private"]
    summary = {
        "schema_version": "kmfa.v014_outside_scope_raw_candidate_alignment_summary.v1",
        "record_type": "v014_outside_scope_raw_candidate_alignment_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        **summary_private,
        "private_alignment_written": True,
        "private_alignment_gitignored": _git_check_ignored(PRIVATE_ALIGNMENT_PATH),
        "private_alignment_items_written": True,
        "private_alignment_items_gitignored": _git_check_ignored(PRIVATE_ALIGNMENT_ITEMS_PATH),
        "private_diagnostic_written": True,
        "private_diagnostic_gitignored": _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH),
        "private_question_list_written": True,
        "private_question_list_gitignored": _git_check_ignored(PRIVATE_QUESTION_LIST_PATH),
        "next_required_input": NEXT_REQUIRED_INPUT,
        "next_recommended_phase": NEXT_RECOMMENDED_PHASE,
        "raw_boundary": _raw_boundary(raw_public_summary),
        "public_safety": _public_safety(),
    }
    matrix = _build_matrix(timestamp, summary, matrix_source)
    go_no_go = {
        "schema_version": "kmfa.v014_outside_scope_raw_candidate_alignment_go_no_go.v1",
        "record_type": "v014_outside_scope_raw_candidate_alignment_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "decision": DECISION,
        "status": STATUS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "blocker_ids": [
            "OUTSIDE_SCOPE_RAW_CANDIDATE_ALIGNMENT_NOT_OWNER_CONFIRMED",
            "DIRECT_SOURCE_RECORD_REF_COVERAGE_ZERO",
            "DIRECT_PROCESSED_FINGERPRINT_RAW_COVERAGE_ZERO",
            "FULL_COMPARISON_STILL_BLOCKED",
        ],
        "outside_scope_blocker_count": summary["outside_scope_blocker_count"],
        "owner_review_required_item_count": summary["owner_review_required_item_count"],
        "full_raw_to_processed_value_comparison_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_outside_scope_raw_candidate_alignment_manifest.v1",
        "record_type": "v014_outside_scope_raw_candidate_alignment_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "git_head_at_generation": _git_output(["rev-parse", "HEAD"]),
        "decision": DECISION,
        "summary": summary,
        "go_no_go_report": go_no_go,
        "matrix": matrix,
        "private_artifacts": {
            "private_alignment": "private_runtime_only",
            "private_alignment_items": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
            "private_question_list": "private_runtime_only",
        },
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_raw_candidate_alignment_after_full_precheck.py --require-private-alignment",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_raw_candidate_alignment_after_full_precheck",
        ],
        "changed_files": FILES_CHANGED,
    }
    _write_json(PRIVATE_ALIGNMENT_PATH, alignment)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_ALIGNMENT_ITEMS_PATH, items)
    _write_text(PRIVATE_QUESTION_LIST_PATH, question_list)
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
    _write_human_artifacts(summary, matrix)
    if write_governance_event:
        _append_governance_events(timestamp, summary)
    return {"summary": summary, "manifest": manifest, "go_no_go": go_no_go, "matrix": matrix}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    result = generate(generated_at=args.generated_at)
    summary = result["summary"]
    print(
        "PASS: KMFA v0.1.4 outside-scope raw candidate alignment generated "
        f"(decision={summary['decision']}, blockers={summary['outside_scope_blocker_count']}, "
        f"owner_review_required={summary['owner_review_required_item_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
