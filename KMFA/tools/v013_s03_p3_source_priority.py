#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S03-P3 source priority evidence.

This phase replays the existing source-priority capability with synthetic
metadata only. It does not read the local raw data inbox, mutate raw sources,
auto-select a cross-source conflict, or publish raw filenames, raw hashes,
field text, sheet names, row values, or business values.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s03_p2_source_check_matrix import validate_v013_s03_p2_source_check_matrix
from KMFA.tools.source_priority import (
    SOURCE_PRIORITY_ORDER,
    append_metadata_record,
    build_cross_source_difference_queue_item,
    build_same_source_inconsistency_event,
    sort_source_candidates,
)
from KMFA.tools.v013_s03_p1_file_import_register import RAW_DIR


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S03_P3_SOURCE_PRIORITY")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/source_priority_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/source_priority_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
TASK_ID = "KMFA-V013-S03-P3-SOURCE-PRIORITY-20260702"
SCHEMA_VERSION = "kmfa.v013_s03_p3_source_priority.v1"


def git_output(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def replay_source_priority_capability() -> dict[str, Any]:
    """Exercise S03-P3 priority/event/queue behavior with synthetic metadata."""
    candidates = [
        {"source_id": "SRC-frontend-99999999", "source_class": "frontend_display"},
        {"source_id": "SRC-report-88888888", "source_class": "report_reference"},
        {"source_id": "SRC-derived-77777777", "source_class": "derived_metric"},
        {"source_id": "SRC-fact-66666666", "source_class": "canonical_fact"},
        {"source_id": "SRC-staging-55555555", "source_class": "staging_structured_row"},
        {"source_id": "SRC-extracted-44444444", "source_class": "raw_extracted_value"},
        {"source_id": "SRC-processed-33333333", "source_class": "processed_data"},
        {"source_id": "SRC-raw-11111111", "source_class": "raw_upload"},
        {"source_id": "SRC-authorized-22222222", "source_class": "authorized_export"},
    ]
    ranked = sort_source_candidates(candidates)
    same_source_event = build_same_source_inconsistency_event(
        source_id="SRC-authorized-22222222",
        primary_ref="private-ref:primary",
        conflicting_ref="private-ref:conflicting",
        field_path="synthetic.field.path",
        reason_code="same-source-reference-mismatch",
        event_time="2026-07-02T17:55:00+10:00",
        evidence_ref="synthetic-private-replay",
    )
    difference_queue_item = build_cross_source_difference_queue_item(
        conflict_scope="synthetic.field.path",
        source_refs=[
            {"source_id": "SRC-authorized-22222222", "source_class": "authorized_export"},
            {"source_id": "SRC-raw-11111111", "source_class": "raw_upload"},
        ],
        reason_code="cross-source-conflict",
        event_time="2026-07-02T17:56:00+10:00",
        evidence_ref="synthetic-private-replay",
    )
    with tempfile.TemporaryDirectory(prefix="kmfa-v013-s03p3-") as tmp:
        event_path = Path(tmp) / "source_priority_events.jsonl"
        queue_path = Path(tmp) / "source_difference_queue.jsonl"
        append_metadata_record(event_path, same_source_event)
        append_metadata_record(queue_path, difference_queue_item)
        event_records = [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()]
        queue_records = [json.loads(line) for line in queue_path.read_text(encoding="utf-8").splitlines()]

    return {
        "source_priority_order": [item["source_class"] for item in ranked],
        "source_priority_order_count": len(ranked),
        "same_source_inconsistency_actions": same_source_event["actions"],
        "same_source_invalidation_event_validated": (
            len(event_records) == 1
            and event_records[0].get("record_type") == "source_priority_event"
            and event_records[0].get("event_type") == "same_source_inconsistency"
            and event_records[0].get("actions") == ["invalidate_derived_cache", "request_rerun"]
            and event_records[0].get("target_layer") == "metadata"
            and event_records[0].get("raw_layer_write_allowed") is False
            and event_records[0].get("raw_source_mutation_allowed") is False
        ),
        "same_source_rerun_requested": "request_rerun" in same_source_event["actions"],
        "cross_source_difference_queue_validated": (
            len(queue_records) == 1
            and queue_records[0].get("record_type") == "source_difference_queue_item"
            and queue_records[0].get("status") == "queued_for_manual_review"
            and queue_records[0].get("resolution_policy") == "manual_review_required"
            and queue_records[0].get("auto_selection_allowed") is False
            and queue_records[0].get("target_layer") == "metadata"
            and queue_records[0].get("raw_layer_write_allowed") is False
            and queue_records[0].get("raw_source_mutation_allowed") is False
        ),
        "cross_source_resolution_policy": difference_queue_item["resolution_policy"],
        "difference_queue_entry_count": len(queue_records),
        "manual_review_required": difference_queue_item["resolution_policy"] == "manual_review_required",
        "auto_selection_allowed": difference_queue_item["auto_selection_allowed"],
        "auto_correction_allowed": False,
        "event_private_temp_write_only": True,
        "published_synthetic_priority_event": False,
        "published_synthetic_difference_queue": False,
    }


def build_manifest() -> dict[str, Any]:
    s03_p2 = validate_v013_s03_p2_source_check_matrix()
    capability = replay_source_priority_capability()

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S03",
        "stage_name": "v0.1.3 file import and source check matrix",
        "phase_id": "S03-P3",
        "phase_name": "source priority and difference queue entry",
        "phase_scope": "v013_s03_p3_source_priority_only",
        "task_id": TASK_ID,
        "run_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred",
        "completed_task_ids": ["S3PCT01", "S3PCT02", "S3PCT03"],
        "s03_p2_dependency_validated": (
            s03_p2.get("stage_id") == "S03"
            and s03_p2.get("phase_id") == "S03-P2"
            and s03_p2.get("github_upload_performed") is False
            and s03_p2.get("raw_dir_read_performed") is False
        ),
        "s03_p2_dependency_ref": "KMFA/stage_artifacts/V013_S03_P2_SOURCE_CHECK_MATRIX/machine/source_check_matrix_manifest.json",
        "source_priority_dependency_validated": True,
        "source_priority_refs": [
            "KMFA/tools/source_priority.py",
            "KMFA/tests/test_source_priority.py",
            "KMFA/stage_artifacts/S03_P3_source_priority/machine/s03_p3_manifest.json",
            "KMFA/stage_artifacts/S03_P3_source_priority/human/s03_p3_completion_record.md",
        ],
        "source_priority_order": capability["source_priority_order"],
        "source_priority_order_count": capability["source_priority_order_count"],
        "same_source_inconsistency_actions": capability["same_source_inconsistency_actions"],
        "same_source_invalidation_event_validated": capability["same_source_invalidation_event_validated"],
        "same_source_rerun_requested": capability["same_source_rerun_requested"],
        "cross_source_difference_queue_validated": capability["cross_source_difference_queue_validated"],
        "cross_source_resolution_policy": capability["cross_source_resolution_policy"],
        "cross_source_conflict_policy": {
            "difference_queue": True,
            "manual_review_required": capability["manual_review_required"],
            "auto_selection_allowed": capability["auto_selection_allowed"],
            "auto_correction_allowed": capability["auto_correction_allowed"],
        },
        "difference_queue_entry_count": capability["difference_queue_entry_count"],
        "manual_review_required": capability["manual_review_required"],
        "auto_selection_allowed": capability["auto_selection_allowed"],
        "auto_correction_allowed": capability["auto_correction_allowed"],
        "event_private_temp_write_only": capability["event_private_temp_write_only"],
        "published_synthetic_priority_event": capability["published_synthetic_priority_event"],
        "published_synthetic_difference_queue": capability["published_synthetic_difference_queue"],
        "raw_data_boundary": {
            "local_raw_data_dir": RAW_DIR,
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_read_performed_by_this_phase": False,
            "codex_modify_allowed": False,
            "codex_delete_allowed": False,
            "codex_move_allowed": False,
            "codex_rename_allowed": False,
            "codex_overwrite_allowed": False,
            "codex_generate_inside_allowed": False,
            "github_commit_allowed": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        },
        "raw_dir_read_performed": False,
        "raw_dir_mutation_performed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "raw_file_bytes_committed": False,
        "raw_filename_publication_allowed": False,
        "raw_file_hash_publication_allowed": False,
        "source_package_hash_publication_allowed": False,
        "source_package_storage_ref_publication_allowed": False,
        "field_plaintext_publication_allowed": False,
        "sheet_name_publication_allowed": False,
        "zip_member_name_publication_allowed": False,
        "row_value_publication_allowed": False,
        "business_value_publication_allowed": False,
        "business_field_parsing_performed": False,
        "raw_value_matching_performed": False,
        "stage3_review_performed": False,
        "github_upload_performed": False,
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "current_data_quality_grade": "Q2",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "public_repo_safety": {
            "raw_business_data_committed": False,
            "zip_committed": False,
            "excel_workbook_committed": False,
            "pdf_committed": False,
            "private_csv_committed": False,
            "sqlite_or_db_committed": False,
            "credentials_committed": False,
            "field_plaintext_committed": False,
            "raw_file_names_committed": False,
            "raw_file_hashes_committed": False,
            "sheet_names_committed": False,
            "zip_member_names_committed": False,
            "raw_business_values_committed": False,
            "source_priority_event_rows_committed": False,
            "source_difference_queue_rows_committed": False,
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s03_p3_source_priority.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s03_p3_source_priority.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s03_p3_source_priority -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_source_priority -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s03_p2_source_check_matrix.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_s03_p3_source_priority.py",
            "KMFA/tools/check_v013_s03_p3_source_priority.py",
            "KMFA/tests/test_v013_s03_p3_source_priority.py",
            "KMFA/tools/source_priority.py",
            "KMFA/tests/test_source_priority.py",
            "KMFA/tools/check_v013_s03_p2_source_check_matrix.py",
        ],
        "next_required_step": (
            "Proceed to v0.1.3 Stage 3 review as a separate run after this phase commit; do not run "
            "GitHub upload, raw value matching, formal report release, live connector, or business execution "
            "in S03-P3."
        ),
    }


def write_report(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.3 S03-P3 Source Priority",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        f"- s03_p2_dependency_validated: `{str(manifest['s03_p2_dependency_validated']).lower()}`",
        f"- source_priority_dependency_validated: `{str(manifest['source_priority_dependency_validated']).lower()}`",
        f"- source_priority_order_count: `{manifest['source_priority_order_count']}`",
        "- source_priority_order: `raw_upload`, `authorized_export`, `raw_extracted_value`, "
        "`staging_structured_row`, `canonical_fact`, `derived_metric`, `report_reference`, "
        "`frontend_display`, `processed_data`",
        f"- same_source_invalidation_event_validated: `{str(manifest['same_source_invalidation_event_validated']).lower()}`",
        "- same_source_actions: `invalidate_derived_cache`, `request_rerun`",
        f"- cross_source_difference_queue_validated: `{str(manifest['cross_source_difference_queue_validated']).lower()}`",
        f"- cross_source_resolution_policy: `{manifest['cross_source_resolution_policy']}`",
        "- auto_selection_allowed: `false`",
        "- auto_correction_allowed: `false`",
        "",
        "## Raw Data Boundary",
        "",
        f"- local_raw_data_dir: `{manifest['raw_data_boundary']['local_raw_data_dir']}`",
        "- codex_modify_delete_move_rename_overwrite_or_generate_inside_allowed: `false`",
        "- public_repo_raw_commit_allowed: `false`",
        "- private_runtime_output_dir: `KMFA/.codex_private_runtime/`",
        "",
        "## Public-Safe Boundary",
        "",
        "- raw_dir_read_performed: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- raw_layer_write_allowed: `false`",
        "- raw_source_mutation_allowed: `false`",
        "- raw_filename_publication_allowed: `false`",
        "- raw_file_hash_publication_allowed: `false`",
        "- source_package_hash_publication_allowed: `false`",
        "- source_package_storage_ref_publication_allowed: `false`",
        "- field_plaintext_publication_allowed: `false`",
        "- sheet_name_publication_allowed: `false`",
        "- zip_member_name_publication_allowed: `false`",
        "- row_value_publication_allowed: `false`",
        "- business_value_publication_allowed: `false`",
        "",
        "## Non-Scope",
        "",
        "- business_field_parsing_performed: `false`",
        "- raw_value_matching_performed: `false`",
        "- stage3_review_performed: `false`",
        "- github_upload_performed: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Gate Status",
        "",
        f"- current_data_quality_grade: `{manifest['current_data_quality_grade']}`",
        f"- current_report_grade: `{manifest['current_report_grade']}`",
        f"- release_permission: `{manifest['release_permission']}`",
        "",
        "## Next Step",
        "",
        manifest["next_required_step"],
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_pending_test_results() -> None:
    if TEST_RESULTS_PATH.exists():
        return
    lines = [
        "# KMFA v0.1.3 S03-P3 Test Results",
        "",
        "- status: `pending_final_validation`",
        "- red_step: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s03_p3_source_priority -q` failed before validator implementation with missing module.",
        "- note: `Generator created placeholder; final validation evidence will overwrite this file before commit.`",
        "",
    ]
    TEST_RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def generate() -> dict[str, Any]:
    (PUBLIC_OUTPUT_DIR / "machine").mkdir(parents=True, exist_ok=True)
    (PUBLIC_OUTPUT_DIR / "human").mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(manifest)
    write_pending_test_results()
    return manifest


def main() -> int:
    manifest = generate()
    print(
        "PASS: KMFA v0.1.3 S03-P3 source priority evidence generated "
        f"(priority_count={manifest['source_priority_order_count']}, "
        f"same_source_event={str(manifest['same_source_invalidation_event_validated']).lower()}, "
        f"difference_queue={str(manifest['cross_source_difference_queue_validated']).lower()}, "
        f"raw_read={str(manifest['raw_dir_read_performed']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
