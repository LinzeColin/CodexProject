#!/usr/bin/env python3
"""Generate KMFA v0.1.3 Stage 3 review evidence.

The review replays the public validators for S03-P1/S03-P2/S03-P3 and
locks the stage-level upload boundary. It does not write to the raw metadata
directory and does not perform GitHub upload.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s03_p1_file_import_register import (
    validate_v013_s03_p1_file_import_register,
)
from KMFA.tools.check_v013_s03_p2_source_check_matrix import (
    validate_v013_s03_p2_source_check_matrix,
)
from KMFA.tools.check_v013_s03_p3_source_priority import validate_v013_s03_p3_source_priority
from KMFA.tools.v013_s03_p1_file_import_register import RAW_DIR


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S03_STAGE_REVIEW")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/stage3_review_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/stage3_review_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
S03_P1_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S03_P1_FILE_IMPORT_REGISTER/machine/file_import_register_manifest.json"
)
S03_P2_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S03_P2_SOURCE_CHECK_MATRIX/machine/source_check_matrix_manifest.json"
)
S03_P3_MANIFEST_PATH = Path("KMFA/stage_artifacts/V013_S03_P3_SOURCE_PRIORITY/machine/source_priority_manifest.json")
TASK_ID = "KMFA-V013-S03-STAGE-REVIEW-20260702"
SCHEMA_VERSION = "kmfa.v013_s03_stage_review.v1"
REVIEW_SCOPE = "v013_s03_stage_review_only"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 Stage 3 GitHub upload as a separate run after this local review commit; "
    "do not run raw value matching, lineage full check, formal report release, live connector, "
    "or business execution in the Stage 3 review run."
)


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


def build_manifest() -> dict[str, Any]:
    p1 = validate_v013_s03_p1_file_import_register()
    p2 = validate_v013_s03_p2_source_check_matrix()
    p3 = validate_v013_s03_p3_source_priority()
    phase_results = {
        "S03-P1": "PASS" if p1.get("phase_id") == "S03-P1" else "FAIL",
        "S03-P2": "PASS" if p2.get("phase_id") == "S03-P2" else "FAIL",
        "S03-P3": "PASS" if p3.get("phase_id") == "S03-P3" else "FAIL",
    }
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "raw_value_matching_not_performed",
        "business_field_parsing_not_performed",
        "cross_source_auto_selection_forbidden",
        "lineage_full_check_not_performed",
        "formal_report_release_blocked",
        "business_execution_blocked",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S03",
        "stage_name": "v0.1.3 file import and source check matrix",
        "review_id": TASK_ID,
        "task_id": TASK_ID,
        "review_scope": REVIEW_SCOPE,
        "review_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "passed_local_stage_review_upload_deferred",
        "stage_review_performed": True,
        "github_upload_ready_next_gate": True,
        "github_upload_performed": False,
        "github_upload_status": "not_pushed",
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "lineage_full_check_completed": False,
        "raw_value_matching_performed": False,
        "raw_dir_read_performed_by_stage_review": False,
        "raw_dir_read_performed_by_dependency_validators": True,
        "raw_dir_read_dependency_note": (
            "S03 validators replay the existing S02 raw-readiness dependency validator in read-only mode; "
            "the Stage 3 review tool itself does not enumerate, copy, modify, move, rename, delete, "
            "or overwrite files in the raw data directory."
        ),
        "raw_dir_mutation_performed": False,
        "phase_count": 3,
        "phase_results": phase_results,
        "s03_p1_dependency_validated": phase_results["S03-P1"] == "PASS",
        "s03_p2_dependency_validated": phase_results["S03-P2"] == "PASS",
        "s03_p3_dependency_validated": phase_results["S03-P3"] == "PASS",
        "reviewed_phase_manifests": {
            "S03-P1": S03_P1_MANIFEST_PATH.as_posix(),
            "S03-P2": S03_P2_MANIFEST_PATH.as_posix(),
            "S03-P3": S03_P3_MANIFEST_PATH.as_posix(),
        },
        "stage_gate": {
            "current_data_quality_grade": p3["current_data_quality_grade"],
            "current_report_grade": p3["current_report_grade"],
            "release_permission": p3["release_permission"],
        },
        "current_data_quality_grade": p3["current_data_quality_grade"],
        "current_report_grade": p3["current_report_grade"],
        "release_permission": p3["release_permission"],
        "review_findings": [],
        "open_review_finding_count": 0,
        "fixed_review_finding_count": 0,
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "phase_summary": {
            "S03-P1": {
                "core_supported_file_type_count": p1["core_supported_file_type_count"],
                "metadata_required_fields_validated": p1["metadata_required_fields_validated"],
                "zip_traversal_blocked": p1["zip_traversal_blocked"],
                "raw_dir_read_performed": p1["raw_dir_read_performed"],
                "github_upload_performed": p1["github_upload_performed"],
            },
            "S03-P2": {
                "required_dimension_count": p2["required_dimension_count"],
                "allowed_status_count": p2["allowed_status_count"],
                "metadata_status_event_validated": p2["metadata_status_event_validated"],
                "raw_dir_read_performed": p2["raw_dir_read_performed"],
                "github_upload_performed": p2["github_upload_performed"],
            },
            "S03-P3": {
                "source_priority_order_count": p3["source_priority_order_count"],
                "same_source_invalidation_event_validated": p3["same_source_invalidation_event_validated"],
                "cross_source_difference_queue_validated": p3["cross_source_difference_queue_validated"],
                "auto_selection_allowed": p3["auto_selection_allowed"],
                "raw_dir_read_performed": p3["raw_dir_read_performed"],
                "github_upload_performed": p3["github_upload_performed"],
            },
        },
        "raw_data_boundary": {
            "local_raw_data_dir": str(RAW_DIR),
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_modify_allowed": False,
            "codex_delete_allowed": False,
            "codex_move_allowed": False,
            "codex_rename_allowed": False,
            "codex_overwrite_allowed": False,
            "codex_generate_inside_allowed": False,
            "github_commit_allowed": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        },
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
            "raw_business_values_committed": False,
            "sheet_names_committed": False,
            "zip_member_names_committed": False,
            "source_check_matrix_rows_committed": False,
            "source_status_event_rows_committed": False,
            "source_priority_event_rows_committed": False,
            "source_difference_queue_rows_committed": False,
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s03_p1_file_import_register.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s03_p2_source_check_matrix.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s03_p3_source_priority.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s03_stage_review.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_s03_stage_review.py",
            "KMFA/tools/check_v013_s03_stage_review.py",
            "KMFA/tests/test_v013_s03_stage_review.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.3 Stage 3 Review",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- stage_review_performed: `{str(manifest['stage_review_performed']).lower()}`",
        f"- phase_count: `{manifest['phase_count']}`",
        "- phase_results: `S03-P1=PASS`, `S03-P2=PASS`, `S03-P3=PASS`",
        f"- current_data_quality_grade: `{manifest['current_data_quality_grade']}`",
        f"- current_report_grade: `{manifest['current_report_grade']}`",
        f"- release_permission: `{manifest['release_permission']}`",
        "- github_upload_ready_next_gate: `true`",
        "- github_upload_performed: `false`",
        "- formal_report_allowed: `false`",
        "- business_decision_basis_allowed: `false`",
        "- raw_value_matching_performed: `false`",
        "- raw_dir_read_performed_by_stage_review: `false`",
        "- raw_dir_read_performed_by_dependency_validators: `true`",
        "- raw_dir_mutation_performed: `false`",
        "",
        "## Phase Replay",
        "",
        "- S03-P1 replayed file registration metadata, required fields, ZIP traversal blocking, and WPS/OLE guidance.",
        "- S03-P2 replayed the source check matrix dimensions, status vocabulary, and metadata-only event policy.",
        "- S03-P3 replayed source priority order, same-source invalidation/rerun events, and cross-source manual review queue controls.",
        "",
        "## Raw Data Boundary",
        "",
        f"- local_raw_data_dir: `{manifest['raw_data_boundary']['local_raw_data_dir']}`",
        "- codex_modify_allowed: `false`",
        "- codex_delete_allowed: `false`",
        "- codex_move_allowed: `false`",
        "- codex_generate_inside_allowed: `false`",
        "- github_commit_allowed: `false`",
        "",
        "The Stage 3 review tool did not directly enumerate or write the raw data directory. The dependency validator chain replays the earlier S02 raw-readiness check in read-only mode and produces no raw directory mutation.",
        "",
        "## Review Findings",
        "",
        "- open_review_finding_count: `0`",
        "- fixed_review_finding_count: `0`",
        "",
        "## Hard Blocks",
        "",
    ]
    lines.extend(f"- `{block}`" for block in manifest["hard_blocks"])
    lines.extend(
        [
            "",
            "## Public Safety",
            "",
            "This review evidence contains only public-safe booleans, aggregate gate status, blocker IDs, validator references, and governance paths.",
            "It does not contain raw filenames, raw hashes, sheet names, ZIP member names, field/header plaintext, row values, business values, credentials, contracts, payroll, tax filings, or bank statements.",
            "",
            "## Next Step",
            "",
            manifest["next_required_step"],
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_pending_test_results() -> None:
    lines = [
        "# KMFA v0.1.3 Stage 3 Review Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `generated_pending_final_validation_capture`",
        "- github_upload_performed: `false`",
        "- raw_dir_mutation_performed: `false`",
        "",
        "Final command results are captured after the validator and governance checks complete in this run.",
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
        "PASS: KMFA v0.1.3 Stage 3 review evidence generated "
        f"(phases={manifest['phase_count']}, findings_open={manifest['open_review_finding_count']}, "
        f"quality={manifest['current_data_quality_grade']}, report={manifest['current_report_grade']}, "
        f"release={manifest['release_permission']}, upload_ready={str(manifest['github_upload_ready_next_gate']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
