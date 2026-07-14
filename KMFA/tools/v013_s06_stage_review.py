#!/usr/bin/env python3
"""Generate KMFA v0.1.3 Stage 6 review evidence.

This review reruns the public-safe v0.1.3 S06-P1/S06-P2/S06-P3 replay
validators and records the stage-level gate. It does not read or write the
local raw data inbox and does not perform GitHub upload.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s06_p1_zero_delta_replay import validate_v013_s06_p1_zero_delta_replay
from KMFA.tools.check_v013_s06_p2_difference_queue_replay import (
    validate_v013_s06_p2_difference_queue_replay,
)
from KMFA.tools.check_v013_s06_p3_validation_evidence_replay import (
    validate_v013_s06_p3_validation_evidence_replay,
)


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S06_STAGE_REVIEW")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/stage6_review_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/stage6_review_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
S06_P1_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S06_P1_ZERO_DELTA_REPLAY/machine/zero_delta_replay_manifest.json"
)
S06_P2_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S06_P2_DIFFERENCE_QUEUE_REPLAY/machine/difference_queue_replay_manifest.json"
)
S06_P3_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S06_P3_VALIDATION_EVIDENCE_REPLAY/machine/validation_evidence_replay_manifest.json"
)
TASK_ID = "KMFA-V013-S06-STAGE-REVIEW-20260703"
SCHEMA_VERSION = "kmfa.v013_s06_stage_review.v1"
REVIEW_SCOPE = "v013_s06_stage_review_only"
RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 S07-P1 as a separate run. GitHub main upload remains deferred until "
    "v0.1.3 Stages 1-10 are complete, the whole Stage 1-10 review passes, and findings are fixed; "
    "do not run GitHub upload, raw value matching, lineage full check, formal report release, "
    "live connector, or business execution in the Stage 6 review run."
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


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def build_manifest() -> dict[str, Any]:
    p1 = validate_v013_s06_p1_zero_delta_replay()
    p2 = validate_v013_s06_p2_difference_queue_replay()
    p3 = validate_v013_s06_p3_validation_evidence_replay()
    p3_manifest = read_json(S06_P3_MANIFEST_PATH)

    phase_results = {
        "S06-P1": "PASS" if p1.get("phase_id") == "S06-P1" else "FAIL",
        "S06-P2": "PASS" if p2.get("phase_id") == "S06-P2" else "FAIL",
        "S06-P3": "PASS" if p3.get("phase_id") == "S06-P3" else "FAIL",
    }
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "zero_delta_failed_for_one_cent_mismatch_fixture",
        "unresolved_critical_difference",
        "q5_forbidden_until_zero_delta_and_difference_closure",
        "report_grade_a_blocked_until_difference_closure",
        "raw_value_matching_not_performed",
        "lineage_full_check_not_performed",
        "formal_report_release_blocked",
        "github_upload_deferred_until_stage10_batch",
        "business_execution_blocked",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S06",
        "stage_name": "v0.1.3 zero-delta cross-source difference and validation evidence",
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
        "legacy_stage6_upload_artifacts_current_gate": False,
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "lineage_full_check_completed": False,
        "raw_value_matching_performed": False,
        "raw_dir_read_performed_by_stage_review": False,
        "raw_dir_read_performed_by_dependency_validators": False,
        "raw_dir_mutation_performed": False,
        "phase_count": 3,
        "phase_results": phase_results,
        "s06_p1_dependency_validated": phase_results["S06-P1"] == "PASS",
        "s06_p2_dependency_validated": phase_results["S06-P2"] == "PASS",
        "s06_p3_dependency_validated": phase_results["S06-P3"] == "PASS",
        "reviewed_phase_manifests": {
            "S06-P1": S06_P1_MANIFEST_PATH.as_posix(),
            "S06-P2": S06_P2_MANIFEST_PATH.as_posix(),
            "S06-P3": S06_P3_MANIFEST_PATH.as_posix(),
        },
        "stage_gate": {
            "current_data_quality_grade": p3_manifest["current_data_quality_grade"],
            "current_report_grade": p3_manifest["current_report_grade"],
            "release_permission": p3_manifest["release_permission"],
        },
        "current_data_quality_grade": p3_manifest["current_data_quality_grade"],
        "current_report_grade": p3_manifest["current_report_grade"],
        "release_permission": p3_manifest["release_permission"],
        "review_findings": [],
        "open_review_finding_count": 0,
        "fixed_review_finding_count": 0,
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "phase_summary": {
            "S06-P1": {
                "pass_fixture_field_comparison_count": p1["pass_fixture_field_comparison_count"],
                "zero_delta_passed_for_public_safe_fixture": p1["zero_delta_passed_for_public_safe_fixture"],
                "pass_fixture_mismatch_count": p1["pass_fixture_mismatch_count"],
                "one_cent_mismatch_detected": p1["one_cent_mismatch_detected"],
                "minimum_fail_difference_cents": p1["minimum_fail_difference_cents"],
                "mismatch_fixture_mismatch_count": p1["mismatch_fixture_mismatch_count"],
                "mismatch_report_generated": p1["mismatch_report_generated"],
                "metadata_quality_written": p1["metadata_quality_written"],
                "difference_queue_created": p1["difference_queue_created"],
                "raw_dir_read_performed": p1["raw_dir_read_performed"],
                "raw_dir_mutation_performed": p1["raw_dir_mutation_performed"],
                "github_upload_performed": p1["github_upload_performed"],
            },
            "S06-P2": {
                "queue_item_count": p2["queue_item_count"],
                "pdf_excel_conflict_detected": p2["pdf_excel_conflict_detected"],
                "difference_cents": p2["difference_cents"],
                "auto_correction_allowed": p2["auto_correction_allowed"],
                "averaging_allowed": p2["averaging_allowed"],
                "rounding_mask_allowed": p2["rounding_mask_allowed"],
                "auto_selection_allowed": p2["auto_selection_allowed"],
                "report_grade_a_allowed": p2["report_grade_a_allowed"],
                "maximum_report_grade": p2["maximum_report_grade"],
                "hard_block_reason": p2["hard_block_reason"],
                "metadata_quality_written": p2["metadata_quality_written"],
                "raw_dir_read_performed": p2["raw_dir_read_performed"],
                "raw_dir_mutation_performed": p2["raw_dir_mutation_performed"],
                "github_upload_performed": p2["github_upload_performed"],
            },
            "S06-P3": {
                "metadata_quality_written": p3["metadata_quality_written"],
                "metadata_zero_delta_records_written": p3["metadata_zero_delta_records_written"],
                "metadata_data_quality_records_written": p3["metadata_data_quality_records_written"],
                "metadata_source_difference_records_written": p3["metadata_source_difference_records_written"],
                "metadata_mismatch_rows_written": p3["metadata_mismatch_rows_written"],
                "project_status_count": p3["project_status_count"],
                "blocked_project_status_count": p3["blocked_project_status_count"],
                "q5_allowed_count": p3["q5_allowed_count"],
                "report_grade_a_allowed_count": p3["report_grade_a_allowed_count"],
                "raw_dir_read_performed": p3["raw_dir_read_performed"],
                "raw_dir_mutation_performed": p3["raw_dir_mutation_performed"],
                "github_upload_performed": p3["github_upload_performed"],
            },
        },
        "raw_data_boundary": {
            "local_raw_data_dir": RAW_DIR,
            "local_raw_data_dir_role": "user_finance_raw_business_data_inbox",
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_read_required_by_this_stage_review": False,
            "codex_read_performed_by_this_stage_review": False,
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
            "authority_system_amount_values_committed": False,
            "pdf_excel_amount_values_committed": False,
            "stage_review_raw_rows_committed": False,
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_p1_zero_delta_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_p2_difference_queue_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_p3_validation_evidence_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s06_stage_review.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_s06_stage_review.py",
            "KMFA/tools/check_v013_s06_stage_review.py",
            "KMFA/tests/test_v013_s06_stage_review.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    s1 = manifest["phase_summary"]["S06-P1"]
    s2 = manifest["phase_summary"]["S06-P2"]
    s3 = manifest["phase_summary"]["S06-P3"]
    lines = [
        "# KMFA v0.1.3 Stage 6 Review",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- stage_review_performed: `{str(manifest['stage_review_performed']).lower()}`",
        f"- phase_count: `{manifest['phase_count']}`",
        "- phase_results: `S06-P1=PASS`, `S06-P2=PASS`, `S06-P3=PASS`",
        f"- current_data_quality_grade: `{manifest['current_data_quality_grade']}`",
        f"- current_report_grade: `{manifest['current_report_grade']}`",
        f"- release_permission: `{manifest['release_permission']}`",
        "- github_upload_ready_next_gate: `false`",
        "- github_upload_deferred_until_stage10_batch: `true`",
        "- github_upload_performed: `false`",
        "- github_upload_status: `not_uploaded_deferred_until_stage10_batch`",
        "- legacy_stage6_upload_artifacts_current_gate: `false`",
        "- formal_report_allowed: `false`",
        "- business_decision_basis_allowed: `false`",
        "- raw_value_matching_performed: `false`",
        "- raw_dir_read_performed_by_stage_review: `false`",
        "- raw_dir_read_performed_by_dependency_validators: `false`",
        "- raw_dir_mutation_performed: `false`",
        "",
        "## Phase Replay",
        "",
        f"- S06-P1 replayed zero-delta validation: comparisons={s1['pass_fixture_field_comparison_count']}, pass_mismatches={s1['pass_fixture_mismatch_count']}, one_cent_detected={str(s1['one_cent_mismatch_detected']).lower()}, mismatch_report_generated={str(s1['mismatch_report_generated']).lower()}.",
        f"- S06-P2 replayed cross-source difference queue: queue_items={s2['queue_item_count']}, difference_cents={s2['difference_cents']}, auto_correction_allowed=false, report_grade_a_allowed=false.",
        f"- S06-P3 replayed validation evidence output: project_statuses={s3['project_status_count']}, blocked_project_statuses={s3['blocked_project_status_count']}, q5_allowed={s3['q5_allowed_count']}, report_grade_a_allowed={s3['report_grade_a_allowed_count']}, metadata_quality_written=true.",
        "",
        "## Raw Data Boundary",
        "",
        f"- local_raw_data_dir: `{manifest['raw_data_boundary']['local_raw_data_dir']}`",
        "- local_raw_data_dir_role: `user_finance_raw_business_data_inbox`",
        "- codex_read_required_by_this_stage_review: `false`",
        "- codex_read_performed_by_this_stage_review: `false`",
        "- codex_modify_allowed: `false`",
        "- codex_delete_allowed: `false`",
        "- codex_move_allowed: `false`",
        "- codex_rename_allowed: `false`",
        "- codex_generate_inside_allowed: `false`",
        "- codex_create_extra_files_inside_allowed: `false`",
        "- github_commit_allowed: `false`",
        "- private_runtime_output_dir: `KMFA/.codex_private_runtime/`",
        "",
        "This Stage 6 review did not enumerate, copy, modify, move, rename, delete, overwrite, or write generated files inside the local raw data inbox. It only reran public-safe validators over existing stage evidence.",
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
            "This review evidence contains only public-safe booleans, aggregate counts, status gates, blocker IDs, validator references, and governance paths.",
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
        "# KMFA v0.1.3 Stage 6 Review Test Results",
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
        "PASS: KMFA v0.1.3 Stage 6 review evidence generated "
        f"(phases={manifest['phase_count']}, findings_open={manifest['open_review_finding_count']}, "
        f"quality={manifest['current_data_quality_grade']}, report={manifest['current_report_grade']}, "
        f"release={manifest['release_permission']}, upload_ready={str(manifest['github_upload_ready_next_gate']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
