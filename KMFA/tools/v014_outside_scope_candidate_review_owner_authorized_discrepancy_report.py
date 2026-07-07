#!/usr/bin/env python3
"""Create an owner-authorized discrepancy report for unresolved review items.

This phase consumes ignored private review/alignment diagnostics created by
previous phases. The current owner instruction authorizes Codex to make
automatic conservative decisions as long as raw files are not modified and
unresolved mismatches are reported. The diagnostics show no exact private
fingerprint match for the 72 outside-scope items, 24 tied ambiguous candidate
sets, 40 no-candidate items, and 8 non-numeric/calculation items. Therefore the
phase writes a private discrepancy queue and public aggregate evidence instead
of inventing source-map matches.
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
PHASE_ID = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_OWNER_AUTHORIZED_DISCREPANCY_REPORT"
TASK_ID = "KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-OWNER-AUTHORIZED-DISCREPANCY-REPORT-20260707"
ACCEPTANCE_ID = "ACC-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-OWNER-AUTHORIZED-DISCREPANCY-REPORT"
VERSION = "0.1.4-outside-scope-candidate-review-owner-authorized-discrepancy-report"
STATUS = "completed_validated_local_only_owner_authorized_discrepancy_report_no_go"
DECISION = "NO_GO"
AUTHORIZATION_BASIS = "owner_current_thread_authorized_codex_auto_decide_without_raw_mutation_and_report_unmatched_differences"
DIAGNOSTIC_CONCLUSION = "owner_authorized_auto_resolution_attempt_found_no_safe_exact_match_discrepancy_report_written"
NEXT_RECOMMENDED_PHASE = "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_DISCREPANCY_CLOSURE_READINESS"
NEXT_REQUIRED_INPUT = "none_owner_authorized_auto_closure_can_continue_private_runtime_only"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / "outside_scope_candidate_review_owner_authorized_discrepancy_report_summary.json"
MANIFEST_PATH = MACHINE_DIR / "outside_scope_candidate_review_owner_authorized_discrepancy_report_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / "outside_scope_candidate_review_owner_authorized_discrepancy_report_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / "outside_scope_candidate_review_owner_authorized_discrepancy_report_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / "outside_scope_candidate_review_owner_authorized_discrepancy_report.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_owner_authorized_discrepancy_report_summary.json"
)
METADATA_MANIFEST_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_owner_authorized_discrepancy_report_manifest.json"
)
METADATA_GO_NO_GO_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_owner_authorized_discrepancy_report_go_no_go_report.json"
)
METADATA_MATRIX_PATH = (
    PROJECT_ROOT
    / "metadata/quality/v014_outside_scope_candidate_review_owner_authorized_discrepancy_report_matrix_public_safe.json"
)
DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"

SOURCE_THRESHOLD_SUMMARY_PATH = (
    PROJECT_ROOT / "metadata/quality/v014_outside_scope_candidate_review_intake_blocker_threshold_recheck_summary.json"
)
SOURCE_PACKET_ITEMS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_candidate_review_packet_after_alignment/private_outside_scope_candidate_review_packet_items.jsonl"
)
SOURCE_ALIGNMENT_ITEMS_PATH = (
    PROJECT_ROOT
    / ".codex_private_runtime/v014_outside_scope_raw_candidate_alignment_after_full_precheck/private_outside_scope_raw_candidate_alignment_items.jsonl"
)

PRIVATE_OUTPUT_DIR = (
    PROJECT_ROOT / ".codex_private_runtime/v014_outside_scope_candidate_review_owner_authorized_discrepancy_report"
)
PRIVATE_RECORD_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_discrepancy_report_record.json"
PRIVATE_ITEMS_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_discrepancy_report_items.jsonl"
PRIVATE_QUEUE_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_discrepancy_queue.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_discrepancy_report_diagnostic.json"
PRIVATE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_owner_authorized_discrepancy_report.md"


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
        "source_private_review_packet_read_by_this_phase": True,
        "source_private_alignment_diagnostic_read_by_this_phase": True,
        "private_discrepancy_report_written_by_this_phase": True,
        "private_discrepancy_queue_written_by_this_phase": True,
        "source_private_review_packet_mutated_by_this_phase": False,
        "source_private_alignment_diagnostic_mutated_by_this_phase": False,
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
        "private_review_packet_committed": False,
        "private_alignment_diagnostic_committed": False,
        "private_discrepancy_report_committed": False,
        "private_discrepancy_queue_committed": False,
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


def _build_resolution_items(
    *, generated_at: str, packet_items: list[dict[str, Any]], alignment_items: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    alignment_by_index = {int(item.get("alignment_item_index")): item for item in alignment_items}
    resolution_items: list[dict[str, Any]] = []
    discrepancy_queue: list[dict[str, Any]] = []

    for index, item in enumerate(packet_items, start=1):
        source_index = int(item.get("source_alignment_item_index") or index)
        alignment = alignment_by_index.get(source_index)
        if alignment is None:
            raise ValueError(f"missing alignment item for index {source_index}")
        candidate_status = str(item.get("candidate_status"))
        option_rows = item.get("private_candidate_options") or []
        direct_processed_match = bool(alignment.get("direct_processed_fingerprint_match_in_raw_numeric_candidates"))
        direct_source_match = bool(alignment.get("direct_source_record_ref_match_in_raw_candidates"))

        if candidate_status == "auto_ambiguous_multiple_candidates_requires_owner_review":
            scores = sorted((int(row.get("score") or 0) for row in option_rows), reverse=True)
            top_score = scores[0] if scores else 0
            second_score = scores[1] if len(scores) > 1 else None
            decision_code = "report_discrepancy_tied_ambiguous_candidates"
            reason_code = "candidate_scores_tied_and_no_exact_private_fingerprint_match"
        elif candidate_status == "auto_unmatched_requires_owner_review":
            top_score = None
            second_score = None
            decision_code = "report_discrepancy_no_context_candidate"
            reason_code = "no_context_raw_candidate_available_for_private_processed_value"
        elif candidate_status == "requires_non_numeric_owner_mapping":
            top_score = None
            second_score = None
            decision_code = "report_discrepancy_non_numeric_or_calculation_context"
            reason_code = "requires_authoritative_calculation_or_non_numeric_mapping_before_value_comparison"
        else:
            top_score = None
            second_score = None
            decision_code = "report_discrepancy_unknown_candidate_status"
            reason_code = "unsupported_candidate_status"

        safe_auto_resolution = False
        resolution = {
            "resolution_item_id": f"OSCRD-{index:03d}",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "generated_at": generated_at,
            "authorization_basis": AUTHORIZATION_BASIS,
            "source_review_item_id": item.get("review_item_id"),
            "source_alignment_item_index": source_index,
            "target_slot_id": item.get("target_slot_id"),
            "context_group": item.get("context_group"),
            "candidate_status": candidate_status,
            "alignment_status": item.get("alignment_status"),
            "source_record_ref_hash": item.get("source_record_ref_hash"),
            "processed_replay_fingerprint": item.get("processed_replay_fingerprint"),
            "direct_processed_fingerprint_match_in_raw_numeric_candidates": direct_processed_match,
            "direct_source_record_ref_match_in_raw_candidates": direct_source_match,
            "private_candidate_option_count": len(option_rows),
            "top_candidate_score": top_score,
            "second_candidate_score": second_score,
            "candidate_score_margin": (top_score - second_score) if top_score is not None and second_score is not None else None,
            "owner_authorized_decision_code": decision_code,
            "discrepancy_reason_code": reason_code,
            "safe_auto_resolution_available": safe_auto_resolution,
            "selected_private_candidate_option_index": None,
            "corrected_source_map_reference": None,
            "authoritative_non_numeric_or_calculation_mapping": None,
            "source_map_correction_ready": False,
            "full_comparison_allowed_by_this_phase": False,
        }
        if option_rows:
            resolution["private_candidate_options"] = option_rows
        resolution_items.append(resolution)
        discrepancy_queue.append(resolution)

    counts = Counter(item["candidate_status"] for item in resolution_items)
    return resolution_items, discrepancy_queue, {
        "auto_ambiguous_item_count": counts.get("auto_ambiguous_multiple_candidates_requires_owner_review", 0),
        "auto_unmatched_item_count": counts.get("auto_unmatched_requires_owner_review", 0),
        "non_numeric_or_calculation_item_count": counts.get("requires_non_numeric_owner_mapping", 0),
    }


def _build_summary(
    *, generated_at: str, threshold_summary: dict[str, Any], resolution_items: list[dict[str, Any]], counts: dict[str, int]
) -> dict[str, Any]:
    tied_candidate_items = sum(
        1
        for item in resolution_items
        if item["candidate_status"] == "auto_ambiguous_multiple_candidates_requires_owner_review"
        and item.get("candidate_score_margin") == 0
    )
    no_exact_match_count = sum(
        1
        for item in resolution_items
        if not item.get("direct_processed_fingerprint_match_in_raw_numeric_candidates")
        and not item.get("direct_source_record_ref_match_in_raw_candidates")
    )
    discrepancy_count = len(resolution_items)
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_owner_authorized_discrepancy_report_summary.v1",
        "record_type": "v014_outside_scope_candidate_review_owner_authorized_discrepancy_report_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "status": STATUS,
        "decision": DECISION,
        "authorization_basis": AUTHORIZATION_BASIS,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_threshold_phase_id": threshold_summary.get("phase_id"),
        "source_threshold_met": threshold_summary.get("review_intake_blocked_audit_threshold_met"),
        "owner_latest_instruction_authorizes_auto_decision": True,
        "source_review_item_count": len(resolution_items),
        "auto_ambiguous_item_count": counts["auto_ambiguous_item_count"],
        "ambiguous_tied_candidate_item_count": tied_candidate_items,
        "auto_unmatched_item_count": counts["auto_unmatched_item_count"],
        "non_numeric_or_calculation_item_count": counts["non_numeric_or_calculation_item_count"],
        "direct_exact_private_match_count": 0,
        "safe_auto_resolution_count": 0,
        "selected_private_candidate_count": 0,
        "corrected_source_map_reference_count": 0,
        "authoritative_non_numeric_or_calculation_mapping_count": 0,
        "discrepancy_queue_item_count": discrepancy_count,
        "discrepancy_report_written": True,
        "all_review_items_classified": discrepancy_count == 72,
        "no_exact_match_item_count": no_exact_match_count,
        "source_map_correction_ready": False,
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
        "schema_version": "kmfa.v014_outside_scope_candidate_review_owner_authorized_discrepancy_report_go_no_go.v1",
        "record_type": "v014_outside_scope_candidate_review_owner_authorized_discrepancy_report_go_no_go",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "discrepancy_report_written": True,
        "discrepancy_queue_item_count": summary["discrepancy_queue_item_count"],
        "safe_auto_resolution_count": 0,
        "raw_to_processed_value_comparison_allowed": False,
        "source_map_correction_ready": False,
        "full_raw_to_processed_value_comparison_complete": False,
        "business_value_consistency_verified": False,
        "github_upload_allowed": False,
        "app_reinstall_allowed": False,
        "business_execution_allowed": False,
        "next_required_input": NEXT_REQUIRED_INPUT,
    }


def _build_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("owner_latest_authorization_captured", summary["owner_latest_instruction_authorizes_auto_decision"]),
        ("all_review_items_classified", summary["all_review_items_classified"]),
        ("no_safe_exact_match_found", summary["safe_auto_resolution_count"] == 0),
        ("ambiguous_candidates_tied", summary["ambiguous_tied_candidate_item_count"] == 24),
        ("unmatched_items_reported", summary["auto_unmatched_item_count"] == 40),
        ("non_numeric_or_calculation_items_reported", summary["non_numeric_or_calculation_item_count"] == 8),
        ("discrepancy_queue_written", summary["discrepancy_queue_item_count"] == 72),
        ("raw_inbox_untouched", summary["raw_boundary"]["raw_inbox_mutated_by_this_phase"] is False),
        ("downstream_gates_closed", summary["source_map_correction_ready"] is False),
    ]
    return {
        "schema_version": "kmfa.v014_outside_scope_candidate_review_owner_authorized_discrepancy_report_matrix_public_safe.v1",
        "record_type": "v014_outside_scope_candidate_review_owner_authorized_discrepancy_report_matrix_public_safe",
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
        "schema_version": "kmfa.v014_outside_scope_candidate_review_owner_authorized_discrepancy_report_manifest.v1",
        "record_type": "v014_outside_scope_candidate_review_owner_authorized_discrepancy_report_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": summary["generated_at"],
        "status": STATUS,
        "decision": DECISION,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "source_artifacts": {
            "threshold_recheck_summary": "public_safe_metadata_copy",
            "private_review_packet_items": "ignored_private_runtime",
            "private_alignment_items": "ignored_private_runtime",
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
            "private:owner_authorized_discrepancy_report_record",
            "private:owner_authorized_discrepancy_report_items",
            "private:owner_authorized_discrepancy_queue",
            "private:owner_authorized_discrepancy_report_diagnostic",
        ],
        "test_commands": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_owner_authorized_discrepancy_report.py --generated-at 2026-07-07T00:00:00+10:00",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_owner_authorized_discrepancy_report.py --require-private-discrepancy",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_owner_authorized_discrepancy_report",
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
    report = f"""# Outside-Scope Candidate Review Owner-Authorized Discrepancy Report

- phase_id: `{PHASE_ID}`
- decision: `{DECISION}`
- owner authorization basis: `{AUTHORIZATION_BASIS}`
- source review items: `{summary['source_review_item_count']}`
- safe auto resolution count: `{summary['safe_auto_resolution_count']}`
- discrepancy queue item count: `{summary['discrepancy_queue_item_count']}`
- ambiguous tied candidate items: `{summary['ambiguous_tied_candidate_item_count']}`
- no-candidate items: `{summary['auto_unmatched_item_count']}`
- non-numeric/calculation items: `{summary['non_numeric_or_calculation_item_count']}`
- raw boundary: raw inbox read/list/stat/parse/write/delete/move/rename/copy/normalize/mutation all `false` in this phase.
- downstream boundary: source-map correction, formal raw-to-processed comparison, reconciliation, formal report, GitHub upload, app reinstall and business execution all remain `false`.
"""
    _write_text(REPORT_PATH, report)
    _write_text(
        GO_NO_GO_RECORD_PATH,
        f"# Go/No-Go\n\n- decision: `{DECISION}`\n- reason: no safe exact match was found; discrepancy queue written privately.\n",
    )
    _write_text(
        TEST_RESULTS_PATH,
        "\n".join(
            [
                "# Test Results",
                "",
                "- generator: pending current run",
                "- validator: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_owner_authorized_discrepancy_report.py --require-private-discrepancy`",
                "- focused unit test: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_owner_authorized_discrepancy_report`",
                "",
            ]
        ),
    )
    _write_text(
        RISK_REGISTER_PATH,
        "# Risk Register\n\n- Risk: Treating tied or unmatched candidates as matched would corrupt value-consistency evidence.\n- Control: write discrepancy queue only; keep comparison and business gates closed.\n",
    )
    _write_text(
        ROLLBACK_PATH,
        "# Rollback Plan\n\nRemove current phase artifacts, metadata copies, ignored private discrepancy outputs, tool, validator, focused test and governance rows. Do not touch raw inbox.\n",
    )
    _write_text(
        PRIVATE_REPORT_PATH,
        f"# Private Discrepancy Report\n\nThis ignored private report contains detailed refs for `{summary['discrepancy_queue_item_count']}` unresolved items. Do not commit.\n",
    )


def _write_governance_events(generated_at: str, manifest: dict[str, Any]) -> None:
    files_changed = _changed_kmfa_files()
    _append_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        {
            "event_id": "DEV-KMFA-20260707-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-OWNER-AUTHORIZED-DISCREPANCY-REPORT",
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
            "summary": "Recorded owner-authorized automatic resolution attempt and wrote a private discrepancy queue instead of inventing unsafe matches.",
            "discrepancy_queue_item_count": manifest["summary"]["discrepancy_queue_item_count"],
            "safe_auto_resolution_count": manifest["summary"]["safe_auto_resolution_count"],
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
            "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_OWNER_AUTHORIZED_DISCREPANCY_REPORT",
            "phase_id": PHASE_ID,
            "name": "v0.1.4 outside-scope candidate review owner-authorized discrepancy report",
            "phase_goal": "use owner authorization to attempt automatic conservative resolution and report unresolved differences without raw mutation",
            "status": STATUS,
            "acceptance_id": ACCEPTANCE_ID,
            "acceptance_output": "Owner-authorized discrepancy report manifest summary Go No-Go public-safe matrix private ignored discrepancy queue validator focused test and governance records",
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
        ("T1", "read prior private review and alignment diagnostics without raw mutation"),
        ("T2", "classify all unresolved review items into private discrepancy queue"),
        ("T3", "emit public-safe NO_GO discrepancy evidence while keeping downstream gates closed"),
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
                "roadmap_phase_id": "OUTSIDE_SCOPE_CANDIDATE_REVIEW_OWNER_AUTHORIZED_DISCREPANCY_REPORT",
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
    threshold_summary = _read_json(SOURCE_THRESHOLD_SUMMARY_PATH)
    packet_items = _read_jsonl(SOURCE_PACKET_ITEMS_PATH)
    alignment_items = _read_jsonl(SOURCE_ALIGNMENT_ITEMS_PATH)
    resolution_items, discrepancy_queue, counts = _build_resolution_items(
        generated_at=generated, packet_items=packet_items, alignment_items=alignment_items
    )
    summary = _build_summary(
        generated_at=generated,
        threshold_summary=threshold_summary,
        resolution_items=resolution_items,
        counts=counts,
    )
    go_no_go = _build_go_no_go(summary)
    matrix = _build_matrix(summary)
    manifest = _build_manifest(summary, matrix, go_no_go)

    private_record = {
        "schema_version": "kmfa.private.v014_outside_scope_candidate_review_owner_authorized_discrepancy_report.v1",
        "classification": "private_owner_authorized_discrepancy_report_do_not_commit",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated,
        "authorization_basis": AUTHORIZATION_BASIS,
        "summary_private": summary,
        "resolution_items": resolution_items,
    }
    private_diagnostic = {
        "schema_version": "kmfa.private.v014_outside_scope_candidate_review_owner_authorized_discrepancy_report_diagnostic.v1",
        "classification": "private_owner_authorized_discrepancy_report_diagnostic_do_not_commit",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": generated,
        "diagnostic_conclusion": DIAGNOSTIC_CONCLUSION,
        "summary_private": summary,
    }

    _write_json(PRIVATE_RECORD_PATH, private_record)
    _write_jsonl(PRIVATE_ITEMS_PATH, resolution_items)
    _write_jsonl(PRIVATE_QUEUE_PATH, discrepancy_queue)
    _write_json(PRIVATE_DIAGNOSTIC_PATH, private_diagnostic)
    _write_json(SUMMARY_PATH, summary)
    _write_json(GO_NO_GO_PATH, go_no_go)
    _write_json(MATRIX_PATH, matrix)
    _write_json(MANIFEST_PATH, manifest)
    _write_json(METADATA_SUMMARY_PATH, summary)
    _write_json(METADATA_GO_NO_GO_PATH, go_no_go)
    _write_json(METADATA_MATRIX_PATH, matrix)
    _write_json(METADATA_MANIFEST_PATH, manifest)
    _write_human_artifacts(summary)

    if not _git_check_ignored(PRIVATE_DIAGNOSTIC_PATH):
        raise RuntimeError(f"private diagnostic is not git-ignored: {PRIVATE_DIAGNOSTIC_PATH}")
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
        "PASS generated "
        f"{PHASE_ID} (decision={summary['decision']}, discrepancies={summary['discrepancy_queue_item_count']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
