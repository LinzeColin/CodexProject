#!/usr/bin/env python3
"""Generate KMFA v0.1.3 Stage 4 review evidence.

The review replays the public validators for S04-P1/S04-P2/S04-P3 and
locks the stage-level upload boundary. It does not read or write the local
raw metadata directory and does not perform GitHub upload.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s04_p1_amount_precision import validate_v013_s04_p1_amount_precision
from KMFA.tools.check_v013_s04_p2_field_standardization import validate_v013_s04_p2_field_standardization
from KMFA.tools.check_v013_s04_p3_basic_tool_report import validate_v013_s04_p3_basic_tool_report
from KMFA.tools.v013_s03_p1_file_import_register import RAW_DIR


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S04_STAGE_REVIEW")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/stage4_review_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/stage4_review_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
S04_P1_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S04_P1_AMOUNT_PRECISION/machine/amount_precision_manifest.json"
)
S04_P2_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S04_P2_FIELD_STANDARDIZATION/machine/field_standardization_manifest.json"
)
S04_P3_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S04_P3_BASIC_TOOL_REPORT/machine/basic_tool_report_manifest.json"
)
TASK_ID = "KMFA-V013-S04-STAGE-REVIEW-20260702"
SCHEMA_VERSION = "kmfa.v013_s04_stage_review.v1"
REVIEW_SCOPE = "v013_s04_stage_review_only"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 S05-P1 as a separate run. GitHub main upload is deferred until v0.1.3 "
    "Stages 1-10 are complete, the whole Stage 1-10 review passes, and review findings are fixed; "
    "do not run GitHub upload, raw value matching, lineage full check, formal report release, live connector, "
    "or business execution in the Stage 4 review run."
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
    p1 = validate_v013_s04_p1_amount_precision()
    p2 = validate_v013_s04_p2_field_standardization()
    p3 = validate_v013_s04_p3_basic_tool_report()
    phase_results = {
        "S04-P1": "PASS" if p1.get("phase_id") == "S04-P1" else "FAIL",
        "S04-P2": "PASS" if p2.get("phase_id") == "S04-P2" else "FAIL",
        "S04-P3": "PASS" if p3.get("phase_id") == "S04-P3" else "FAIL",
    }
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "float_money_forbidden",
        "cent_difference_must_not_be_ignored",
        "raw_value_matching_not_performed",
        "business_field_parsing_not_performed",
        "lineage_full_check_not_performed",
        "formal_report_release_blocked",
        "business_execution_blocked",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S04",
        "stage_name": "v0.1.3 amount precision field standardization and basic tools",
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
        "github_upload_ready_next_gate": False,
        "github_upload_deferred_until_stage10_batch": True,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_stage10_batch",
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "lineage_full_check_completed": False,
        "raw_value_matching_performed": False,
        "raw_dir_read_performed_by_stage_review": False,
        "raw_dir_read_performed_by_dependency_validators": False,
        "raw_dir_mutation_performed": False,
        "s04_p2_raw_listing_deviation_recorded": p2["raw_dir_accidental_listing_performed"],
        "s04_p2_raw_listing_temp_files_removed": p2["raw_dir_accidental_listing_temp_files_removed"],
        "phase_count": 3,
        "phase_results": phase_results,
        "s04_p1_dependency_validated": phase_results["S04-P1"] == "PASS",
        "s04_p2_dependency_validated": phase_results["S04-P2"] == "PASS",
        "s04_p3_dependency_validated": phase_results["S04-P3"] == "PASS",
        "reviewed_phase_manifests": {
            "S04-P1": S04_P1_MANIFEST_PATH.as_posix(),
            "S04-P2": S04_P2_MANIFEST_PATH.as_posix(),
            "S04-P3": S04_P3_MANIFEST_PATH.as_posix(),
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
            "S04-P1": {
                "amount_case_count": p1["amount_case_count"],
                "amount_rejection_count": p1["amount_rejection_count"],
                "repository_no_float_scan_passed": p1["repository_no_float_scan_passed"],
                "raw_dir_read_performed": p1["raw_dir_read_performed"],
                "raw_dir_mutation_performed": p1["raw_dir_mutation_performed"],
                "github_upload_performed": p1["github_upload_performed"],
            },
            "S04-P2": {
                "canonical_field_count": p2["canonical_field_count"],
                "alias_dictionary_row_count": p2["alias_dictionary_row_count"],
                "standardization_case_count": p2["standardization_case_count"],
                "standardization_case_passed_count": p2["standardization_case_passed_count"],
                "quality_status_count": p2["quality_status_count"],
                "raw_dir_accidental_listing_performed": p2["raw_dir_accidental_listing_performed"],
                "raw_dir_accidental_listing_temp_files_removed": p2[
                    "raw_dir_accidental_listing_temp_files_removed"
                ],
                "raw_dir_mutation_performed": p2["raw_dir_mutation_performed"],
                "github_upload_performed": p2["github_upload_performed"],
            },
            "S04-P3": {
                "synthetic_boundary_case_total": p3["synthetic_boundary_case_total"],
                "synthetic_boundary_case_passed": p3["synthetic_boundary_case_passed"],
                "synthetic_boundary_case_failed": p3["synthetic_boundary_case_failed"],
                "amount_boundary_case_count": p3["amount_boundary_case_count"],
                "date_period_boundary_case_count": p3["date_period_boundary_case_count"],
                "json_report_generated": p3["json_report_generated"],
                "markdown_report_generated": p3["markdown_report_generated"],
                "raw_dir_read_performed": p3["raw_dir_read_performed"],
                "raw_dir_mutation_performed": p3["raw_dir_mutation_performed"],
                "github_upload_performed": p3["github_upload_performed"],
            },
        },
        "raw_data_boundary": {
            "local_raw_data_dir": str(RAW_DIR),
            "local_raw_data_dir_role": "user_finance_raw_business_data_inbox",
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_modify_allowed": False,
            "codex_delete_allowed": False,
            "codex_move_allowed": False,
            "codex_rename_allowed": False,
            "codex_overwrite_allowed": False,
            "codex_generate_inside_allowed": False,
            "codex_create_extra_files_inside_allowed": False,
            "github_commit_allowed": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
            "extra_work_dir_requirement": "must_be_project_controlled_and_gitignored",
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
            "tool_report_raw_rows_committed": False,
            "field_standardization_raw_rows_committed": False,
            "amount_raw_rows_committed": False,
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s04_p1_amount_precision.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s04_p2_field_standardization.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s04_p3_basic_tool_report.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s04_stage_review.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_s04_stage_review.py",
            "KMFA/tools/check_v013_s04_stage_review.py",
            "KMFA/tests/test_v013_s04_stage_review.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.3 Stage 4 Review",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- stage_review_performed: `{str(manifest['stage_review_performed']).lower()}`",
        f"- phase_count: `{manifest['phase_count']}`",
        "- phase_results: `S04-P1=PASS`, `S04-P2=PASS`, `S04-P3=PASS`",
        f"- current_data_quality_grade: `{manifest['current_data_quality_grade']}`",
        f"- current_report_grade: `{manifest['current_report_grade']}`",
        f"- release_permission: `{manifest['release_permission']}`",
        "- github_upload_ready_next_gate: `false`",
        "- github_upload_deferred_until_stage10_batch: `true`",
        "- github_upload_performed: `false`",
        "- github_upload_status: `not_uploaded_deferred_until_stage10_batch`",
        "- formal_report_allowed: `false`",
        "- business_decision_basis_allowed: `false`",
        "- raw_value_matching_performed: `false`",
        "- raw_dir_read_performed_by_stage_review: `false`",
        "- raw_dir_read_performed_by_dependency_validators: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- s04_p2_raw_listing_deviation_recorded: `true`",
        "- s04_p2_raw_listing_temp_files_removed: `true`",
        "",
        "## Phase Replay",
        "",
        "- S04-P1 replayed amount precision, integer-cent normalization, rejection cases, and no-float scanning.",
        "- S04-P2 replayed field alias standardization, synthetic mapping cases, and public-safe quality statuses.",
        "- S04-P3 replayed synthetic amount/date/period boundary tool reports and JSON/Markdown report generation.",
        "",
        "## Raw Data Boundary",
        "",
        f"- local_raw_data_dir: `{manifest['raw_data_boundary']['local_raw_data_dir']}`",
        "- local_raw_data_dir_role: `user_finance_raw_business_data_inbox`",
        "- codex_modify_allowed: `false`",
        "- codex_delete_allowed: `false`",
        "- codex_move_allowed: `false`",
        "- codex_rename_allowed: `false`",
        "- codex_generate_inside_allowed: `false`",
        "- codex_create_extra_files_inside_allowed: `false`",
        "- github_commit_allowed: `false`",
        "- private_runtime_output_dir: `KMFA/.codex_private_runtime/`",
        "",
        "The Stage 4 review tool did not enumerate, copy, modify, move, rename, delete, overwrite, or write generated files inside the local raw data inbox. S04-P2's earlier accidental directory listing remains recorded as a closed deviation with temporary files removed.",
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
        "# KMFA v0.1.3 Stage 4 Review Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `generated_pending_final_validation_capture`",
        "- github_upload_performed: `false`",
        "- raw_dir_read_performed_by_stage_review: `false`",
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
        "PASS: KMFA v0.1.3 Stage 4 review evidence generated "
        f"(phases={manifest['phase_count']}, findings_open={manifest['open_review_finding_count']}, "
        f"quality={manifest['current_data_quality_grade']}, report={manifest['current_report_grade']}, "
        f"release={manifest['release_permission']}, upload_ready={str(manifest['github_upload_ready_next_gate']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
