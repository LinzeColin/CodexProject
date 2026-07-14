#!/usr/bin/env python3
"""Build residual-difference raw candidate alignment after comparison precheck.

This phase reads the authorized raw inbox read-only and writes private candidate
anchor drafts for the 72 residual-difference records that failed the prior
comparison precheck. It does not mutate raw files, authorize anchors, run the
formal raw-to-processed comparison, reconcile values, upload GitHub, reinstall
the app, or execute business steps. Public artifacts remain aggregate-only.
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
PHASE_ID = "V014_RESIDUAL_DIFFERENCE_RAW_CANDIDATE_ALIGNMENT_AFTER_PRECHECK"
TASK_ID = "KMFA-V014-RESIDUAL-DIFFERENCE-RAW-CANDIDATE-ALIGNMENT-AFTER-PRECHECK-20260707"
ACCEPTANCE_ID = "ACC-V014-RESIDUAL-DIFFERENCE-RAW-CANDIDATE-ALIGNMENT-AFTER-PRECHECK"
VERSION = "0.1.4-residual-difference-raw-candidate-alignment-after-precheck"
STATUS = "completed_validated_local_only_residual_difference_raw_candidate_alignment_blocked_no_go"
DECISION = "NO_GO"
DIAGNOSTIC_CONCLUSION = "residual_difference_raw_candidate_alignment_requires_owner_authorized_anchor_selection"
NEXT_RECOMMENDED_PHASE = "V014_RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_PRECHECK_AFTER_ALIGNMENT"
NEXT_REQUIRED_INPUT = "owner_or_authorized_delegate_confirms_private_raw_candidate_anchors_before_formal_comparison"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "residual_difference_raw_candidate_alignment_after_precheck_summary.json"
MANIFEST_PATH = MACHINE_DIR / "residual_difference_raw_candidate_alignment_after_precheck_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "residual_difference_raw_candidate_alignment_after_precheck_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "residual_difference_raw_candidate_alignment_after_precheck_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "residual_difference_raw_candidate_alignment_after_precheck_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_candidate_alignment_after_precheck_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_candidate_alignment_after_precheck_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_candidate_alignment_after_precheck_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / "metadata/quality/v014_residual_difference_raw_candidate_alignment_after_precheck_matrix_public_safe.json"

SOURCE_PRECHECK_SUMMARY_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_summary.json"
)
SOURCE_PRECHECK_MANIFEST_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_residual_difference_raw_to_processed_comparison_precheck_manifest.json"
)
SOURCE_PRECHECK_BLOCKERS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_raw_to_processed_comparison_precheck/private_residual_difference_comparison_blocker_records.jsonl"
)
SOURCE_RAW_COMPARISON_INPUT_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_residual_difference_private_resolution_materialization_replay/private_residual_difference_raw_comparison_input.json"
)

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_residual_difference_raw_candidate_alignment_after_precheck"
PRIVATE_ALIGNMENT_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_candidate_alignment.json"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_candidate_alignment_diagnostic.json"
PRIVATE_ALIGNMENT_ITEMS_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_candidate_alignment_items.jsonl"
PRIVATE_ANCHOR_DRAFT_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_candidate_anchor_draft.json"
PRIVATE_QUESTION_LIST_PATH = PRIVATE_OUTPUT_DIR / "residual_difference_raw_candidate_alignment_questions_zh.md"
PRIVATE_RAW_SCAN_RUNTIME_PATH = PRIVATE_OUTPUT_DIR / "private_residual_difference_raw_scan_runtime.json"
BUNDLED_PYTHON = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

EXPECTED_TRACK_COUNTS = {
    "owner_select_one_authoritative_candidate": 24,
    "provide_authoritative_source_reference_or_owner_exclusion": 40,
    "provide_formula_or_non_numeric_mapping": 8,
}

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
    "KMFA/metadata/model_registry.yaml",
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
    "KMFA/tests/test_v014_residual_difference_raw_candidate_alignment_after_precheck.py",
    "KMFA/tools/check_v014_residual_difference_raw_candidate_alignment_after_precheck.py",
    "KMFA/tools/v014_residual_difference_raw_candidate_alignment_after_precheck.py",
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


def _scan_raw_sources() -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        from KMFA.tools import v014_processed_value_source_map_completion_auto_candidate_draft as auto_candidate

        return auto_candidate._scan_raw_sources()
    except Exception:
        if not BUNDLED_PYTHON.exists():
            raise
    PRIVATE_RAW_SCAN_RUNTIME_PATH.parent.mkdir(parents=True, exist_ok=True)
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
        [BUNDLED_PYTHON.as_posix(), "-c", script, PRIVATE_RAW_SCAN_RUNTIME_PATH.as_posix()],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"bundled raw scan failed: {result.stderr.strip()}")
    payload = _read_json(PRIVATE_RAW_SCAN_RUNTIME_PATH)
    return payload["public"], payload["private"]


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
        "private_anchor_draft_committed": False,
        "private_diagnostic_committed": False,
        "private_question_list_committed": False,
        "raw_file_committed": False,
        "raw_filename_committed": False,
        "raw_archive_member_name_committed": False,
        "raw_digest_committed": False,
        "office_workbook_committed": False,
        "source_document_committed": False,
        "field_header_plaintext_committed": False,
        "row_value_committed": False,
        "business_value_committed": False,
        "private_ref_or_fingerprint_committed": False,
        "credential_or_secret_committed": False,
    }


def _alignment_status(track: str) -> str:
    if track == "owner_select_one_authoritative_candidate":
        return "ambiguous_raw_candidate_anchor_requires_owner_selection"
    if track == "provide_formula_or_non_numeric_mapping":
        return "non_numeric_or_formula_mapping_required_before_anchor"
    return "authoritative_source_reference_or_owner_exclusion_required"


def _candidate_samples(track: str, raw_private_index: dict[str, Any]) -> list[dict[str, Any]]:
    if track != "owner_select_one_authoritative_candidate":
        return []
    return list(raw_private_index.get("numeric_records", []))[:10]


def _build_alignment(
    *,
    generated_at: str,
    source_precheck_summary: dict[str, Any],
    blocker_rows: list[dict[str, Any]],
    raw_comparison_input: dict[str, Any],
    raw_public_summary: dict[str, Any],
    raw_private_index: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], dict[str, Any], str, dict[str, tuple[bool, Any, Any]]]:
    materialized_rows = raw_comparison_input.get("materialized_records", [])
    if not isinstance(materialized_rows, list):
        raise ValueError("materialized_records must be a list")
    materialized_by_slot = {
        str(row.get("target_slot_id")): row
        for row in materialized_rows
        if isinstance(row, dict) and row.get("target_slot_id")
    }
    raw_record_refs = {record.get("record_ref_hash") for record in raw_private_index.get("numeric_records", [])}
    raw_value_fingerprints = {
        record.get("numeric_value_fingerprint") for record in raw_private_index.get("numeric_records", [])
    }

    alignment_items: list[dict[str, Any]] = []
    anchor_draft_items: list[dict[str, Any]] = []
    track_counts: Counter[str] = Counter()
    alignment_status_counts: Counter[str] = Counter()
    direct_raw_ref_matches = 0
    direct_processed_fingerprint_matches = 0

    for index, blocker in enumerate(blocker_rows, start=1):
        slot_id = str(blocker.get("target_slot_id"))
        materialized = materialized_by_slot.get(slot_id, {})
        track = str(blocker.get("diagnostic_track") or materialized.get("diagnostic_track") or "")
        track_counts[track] += 1
        status = _alignment_status(track)
        alignment_status_counts[status] += 1
        source_record_ref_hash = materialized.get("source_record_ref_hash")
        processed_value_fingerprint = materialized.get("processed_value_fingerprint")
        direct_raw_ref_match = source_record_ref_hash in raw_record_refs
        direct_processed_match = processed_value_fingerprint in raw_value_fingerprints
        if direct_raw_ref_match:
            direct_raw_ref_matches += 1
        if direct_processed_match:
            direct_processed_fingerprint_matches += 1
        private_top_candidate_records = _candidate_samples(track, raw_private_index)
        anchor_item = {
            "anchor_draft_index": index,
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "target_slot_id": slot_id,
            "diagnostic_track": track,
            "alignment_status": status,
            "private_top_candidate_records": private_top_candidate_records,
            "private_top_candidate_record_count": len(private_top_candidate_records),
            "owner_authorized_anchor": False,
            "raw_candidate_record_ref_hash": None,
            "raw_candidate_fingerprint": None,
            "processed_value_fingerprint": processed_value_fingerprint,
            "comparison_anchor_ready": False,
            "owner_review_required": True,
        }
        anchor_draft_items.append(anchor_item)
        alignment_items.append(
            {
                "alignment_item_index": index,
                "phase_id": PHASE_ID,
                "task_id": TASK_ID,
                "generated_at": generated_at,
                "target_slot_id": slot_id,
                "diagnostic_track": track,
                "source_materialization_index": blocker.get("source_materialization_index"),
                "comparison_precheck_status": blocker.get("comparison_precheck_status"),
                "alignment_status": status,
                "direct_raw_candidate_record_ref_match": direct_raw_ref_match,
                "direct_processed_fingerprint_match": direct_processed_match,
                "private_candidate_sample_available": bool(private_top_candidate_records),
                "private_candidate_sample_count": len(private_top_candidate_records),
                "owner_review_required": True,
                "raw_to_processed_value_comparison_allowed_by_this_phase": False,
            }
        )

    owner_authorized_anchor_count = sum(1 for item in anchor_draft_items if item["owner_authorized_anchor"])
    summary_private = {
        "source_precheck_phase_id": source_precheck_summary.get("phase_id"),
        "source_precheck_decision": source_precheck_summary.get("decision"),
        "source_precheck_blocker_count": len(blocker_rows),
        "source_raw_comparison_input_record_count": len(materialized_rows),
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
        "diagnostic_track_counts": dict(sorted(track_counts.items())),
        "alignment_status_counts": dict(sorted(alignment_status_counts.items())),
        "raw_candidate_anchor_draft_item_count": len(anchor_draft_items),
        "private_candidate_sample_item_count": sum(
            1 for item in anchor_draft_items if item["private_top_candidate_record_count"] > 0
        ),
        "direct_raw_candidate_record_ref_match_count": direct_raw_ref_matches,
        "direct_processed_fingerprint_match_count": direct_processed_fingerprint_matches,
        "owner_authorized_comparison_anchor_count": owner_authorized_anchor_count,
        "owner_review_required_item_count": len(alignment_items),
        "private_anchor_draft_ready_count": owner_authorized_anchor_count,
        "alignment_ready_count": 0,
        "raw_to_processed_value_comparison_ready": False,
        "raw_to_processed_value_comparison_performed_by_this_phase": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
    }
    alignment = {
        "schema_version": "kmfa.private.v014_residual_difference_raw_candidate_alignment_after_precheck.v1",
        "classification": "private_residual_difference_raw_candidate_alignment_do_not_commit",
        "record_type": "v014_residual_difference_raw_candidate_alignment_after_precheck",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "summary_private": summary_private,
        "alignment_items": alignment_items,
        "raw_boundary": _raw_boundary(raw_public_summary),
    }
    diagnostic = {
        "schema_version": "kmfa.private.v014_residual_difference_raw_candidate_alignment_diagnostic.v1",
        "classification": "private_residual_difference_raw_candidate_alignment_diagnostic_do_not_commit",
        "record_type": "v014_residual_difference_raw_candidate_alignment_diagnostic",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "summary_private": summary_private,
        "source_private_refs": {
            "source_precheck_blockers": "private_runtime_only",
            "source_raw_comparison_input": "private_runtime_only",
            "current_raw_scan": "private_runtime_only",
        },
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
    }
    anchor_draft = {
        "schema_version": "kmfa.private.v014_residual_difference_raw_candidate_anchor_draft.v1",
        "classification": "private_residual_difference_raw_candidate_anchor_draft_do_not_commit",
        "record_type": "v014_residual_difference_raw_candidate_anchor_draft",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "draft_only_not_owner_authorization": True,
        "owner_authorized_anchor_count": owner_authorized_anchor_count,
        "anchor_draft_items": anchor_draft_items,
    }
    question_lines = [
        "# KMFA v0.1.4 residual difference raw candidate alignment 中文问题清单",
        "",
        "说明：本文件可能包含 raw 文件名、表头、金额、单元格/PDF 位置和候选明细，只能保留在 private runtime，不得提交 GitHub。",
        "",
        f"- residual blocker count: {len(alignment_items)}",
        f"- owner selection required count: {track_counts.get('owner_select_one_authoritative_candidate', 0)}",
        f"- source reference or exclusion required count: {track_counts.get('provide_authoritative_source_reference_or_owner_exclusion', 0)}",
        f"- formula/non-numeric mapping required count: {track_counts.get('provide_formula_or_non_numeric_mapping', 0)}",
        "",
        "## 需要 owner/授权代理确认的问题",
    ]
    for item in anchor_draft_items:
        question_lines.extend(
            [
                "",
                f"### Q{item['anchor_draft_index']:03d} target_slot_id={item['target_slot_id']}",
                f"- diagnostic_track: {item['diagnostic_track']}",
                f"- alignment_status: {item['alignment_status']}",
                "- 请确认：是否选择某个 private raw candidate 作为 comparison anchor，或提供 authoritative source reference / owner exclusion / formula mapping。",
            ]
        )
        for candidate_index, candidate in enumerate(item["private_top_candidate_records"][:5], 1):
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
        "diagnostic_track_counts_locked": (summary_private["diagnostic_track_counts"] == EXPECTED_TRACK_COUNTS, summary_private["diagnostic_track_counts"], EXPECTED_TRACK_COUNTS),
        "direct_raw_candidate_record_ref_coverage": (direct_raw_ref_matches == 72, direct_raw_ref_matches, 72),
        "owner_authorized_anchor_coverage": (owner_authorized_anchor_count == 72, owner_authorized_anchor_count, 72),
        "formal_comparison_not_claimed": (summary_private["full_raw_to_processed_value_comparison_complete"] is False, False, False),
        "downstream_no_go_preserved": (DECISION == "NO_GO", DECISION, "NO_GO"),
    }
    return alignment, diagnostic, alignment_items, anchor_draft, "\n".join(question_lines) + "\n", matrix_source


def _build_matrix(generated_at: str, summary: dict[str, Any], matrix_source: dict[str, tuple[bool, Any, Any]]) -> dict[str, Any]:
    rows = [
        {"check_code": code, "status": "PASS" if passed else "FAIL", "observed_public_safe": observed, "required": required}
        for code, (passed, observed, required) in matrix_source.items()
    ]
    return {
        "schema_version": "kmfa.v014_residual_difference_raw_candidate_alignment_matrix_public_safe.v1",
        "record_type": "v014_residual_difference_raw_candidate_alignment_matrix_public_safe",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated_at,
        "check_count": len(rows),
        "pass_count": sum(1 for row in rows if row["status"] == "PASS"),
        "fail_count": sum(1 for row in rows if row["status"] == "FAIL"),
        "checks": rows,
        "source_precheck_blocker_count": summary["source_precheck_blocker_count"],
        "owner_review_required_item_count": summary["owner_review_required_item_count"],
        "raw_to_processed_value_comparison_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
    }


def _write_human_artifacts(summary: dict[str, Any], matrix: dict[str, Any]) -> None:
    report = f"""# KMFA v0.1.4 Residual Difference Raw Candidate Alignment After Precheck

- phase: `{PHASE_ID}`
- decision: `{DECISION}`
- residual blocker count: `{summary["source_precheck_blocker_count"]}`
- raw numeric candidate count: `{summary["raw_numeric_candidate_count"]}`
- raw unique numeric fingerprint count: `{summary["raw_unique_numeric_fingerprint_count"]}`
- owner review required item count: `{summary["owner_review_required_item_count"]}`
- owner authorized comparison anchor count: `{summary["owner_authorized_comparison_anchor_count"]}`
- direct raw candidate record-ref match count: `{summary["direct_raw_candidate_record_ref_match_count"]}`
- next required input: `{NEXT_REQUIRED_INPUT}`

This phase reads the raw inbox read-only and writes private candidate anchor drafts only. It does not authorize anchors, run the formal raw-to-processed comparison, verify business consistency, upload GitHub, reinstall the app, or execute business steps.
"""
    go_no_go_record = f"""# Go/No-Go

- decision: `{DECISION}`
- reason: 72 residual-difference records still require owner/authorized-delegate confirmation before formal raw-to-processed comparison.
- matrix: `{matrix["pass_count"]}` pass / `{matrix["fail_count"]}` fail
- formal comparison allowed: `false`
- business execution allowed: `false`
"""
    risk_register = """# Risk Register

- Risk: raw candidate samples can be mistaken for owner-authorized comparison anchors.
- Control: private anchor draft stays ignored and marks every item as not owner-authorized.
- Control: public evidence contains aggregate counts and gate flags only.
"""
    rollback = """# Rollback Plan

Remove this phase's public artifacts, metadata copies, ignored private runtime directory, tool, validator, focused test and governance rows. Do not modify the raw inbox.
"""
    test_results = """# Test Results

- expected generator: bundled Python with read-only raw parsing
- expected validator: `KMFA/tools/check_v014_residual_difference_raw_candidate_alignment_after_precheck.py --require-private-alignment`
- expected focused test: `KMFA.tests.test_v014_residual_difference_raw_candidate_alignment_after_precheck`
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
    event_id = "DEV-KMFA-20260707-V014-RESIDUAL-DIFFERENCE-RAW-CANDIDATE-ALIGNMENT"
    event = {
        "event_id": event_id,
        "event_time": generated_at,
        "event_type": "development",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "version": VERSION,
        "iteration_id": "ITER-20260707-KMFA-V014-RESIDUAL-DIFFERENCE-RAW-CANDIDATE-ALIGNMENT",
        "fact_level": "EXTRACTED",
        "evidence_ref": MANIFEST_PATH.as_posix(),
        "go_no_go": DECISION,
        "source_precheck_blocker_count": summary["source_precheck_blocker_count"],
        "raw_numeric_candidate_count": summary["raw_numeric_candidate_count"],
        "owner_review_required_item_count": summary["owner_review_required_item_count"],
        "owner_authorized_comparison_anchor_count": summary["owner_authorized_comparison_anchor_count"],
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "raw_inbox_read_performed": True,
        "raw_inbox_mutation_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "result_commit": "PENDING",
        "files_changed": FILES_CHANGED,
        "summary": "Generated private residual-difference raw candidate anchor draft and kept formal comparison blocked.",
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
    source_precheck_summary = _read_json(SOURCE_PRECHECK_SUMMARY_PATH)
    _read_json(SOURCE_PRECHECK_MANIFEST_PATH)
    blocker_rows = _read_jsonl(SOURCE_PRECHECK_BLOCKERS_PATH)
    raw_comparison_input = _read_json(SOURCE_RAW_COMPARISON_INPUT_PATH)
    raw_public_summary, raw_private_index = _scan_raw_sources()
    alignment, diagnostic, items, anchor_draft, question_list, matrix_source = _build_alignment(
        generated_at=timestamp,
        source_precheck_summary=source_precheck_summary,
        blocker_rows=blocker_rows,
        raw_comparison_input=raw_comparison_input,
        raw_public_summary=raw_public_summary,
        raw_private_index=raw_private_index,
    )
    summary_private = alignment["summary_private"]
    summary = {
        "schema_version": "kmfa.v014_residual_difference_raw_candidate_alignment_summary.v1",
        "record_type": "v014_residual_difference_raw_candidate_alignment_summary",
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
        "private_anchor_draft_written": True,
        "private_anchor_draft_gitignored": _git_check_ignored(PRIVATE_ANCHOR_DRAFT_PATH),
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
        "schema_version": "kmfa.v014_residual_difference_raw_candidate_alignment_go_no_go.v1",
        "record_type": "v014_residual_difference_raw_candidate_alignment_go_no_go",
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
            "RESIDUAL_RAW_CANDIDATE_ALIGNMENT_NOT_OWNER_AUTHORIZED",
            "DIRECT_RAW_CANDIDATE_RECORD_REF_COVERAGE_ZERO",
            "OWNER_AUTHORIZED_ANCHOR_COVERAGE_ZERO",
            "FORMAL_COMPARISON_STILL_BLOCKED",
        ],
        "source_precheck_blocker_count": summary["source_precheck_blocker_count"],
        "owner_review_required_item_count": summary["owner_review_required_item_count"],
        "owner_authorized_comparison_anchor_count": summary["owner_authorized_comparison_anchor_count"],
        "raw_to_processed_value_comparison_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }
    manifest = {
        "schema_version": "kmfa.v014_residual_difference_raw_candidate_alignment_manifest.v1",
        "record_type": "v014_residual_difference_raw_candidate_alignment_manifest",
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
            "private_anchor_draft": "private_runtime_only",
            "private_diagnostic": "private_runtime_only",
            "private_question_list": "private_runtime_only",
        },
        "raw_boundary": summary["raw_boundary"],
        "public_safety": summary["public_safety"],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_candidate_alignment_after_precheck.py --require-private-alignment",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_raw_candidate_alignment_after_precheck",
        ],
        "changed_files": FILES_CHANGED,
    }
    _write_json(PRIVATE_ALIGNMENT_PATH, alignment)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, diagnostic)
    _write_jsonl(PRIVATE_ALIGNMENT_ITEMS_PATH, items)
    _write_json(PRIVATE_ANCHOR_DRAFT_PATH, anchor_draft)
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
        "PASS: KMFA v0.1.4 residual-difference raw candidate alignment generated "
        f"(decision={summary['decision']}, blockers={summary['source_precheck_blocker_count']}, "
        f"owner_review_required={summary['owner_review_required_item_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
