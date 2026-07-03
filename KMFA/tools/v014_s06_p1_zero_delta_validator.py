#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S06-P1 zero-delta validator evidence.

This phase proves the zero-delta validator contract with public-safe synthetic
fixtures only. It does not read, list, stat, hash, or mutate the local raw
inbox and does not create the S06-P2 difference queue, S06-P3 quality outputs,
Stage 6 review, GitHub upload, formal report, or business action.
"""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s05_stage_review import validate_v014_s05_stage_review
from KMFA.tools.v014_s05_p1_a0_file_registration import RAW_INBOX
from KMFA.tools.zero_delta_validator import validate_fixture_file, write_mismatch_report


TASK_ID = "KMFA-V014-S06-P1-ZERO-DELTA-VALIDATOR-20260704"
ACCEPTANCE_ID = "ACC-V014-S06-P1-ZERO-DELTA-VALIDATOR"
SCHEMA_VERSION = "kmfa.v014_s06_p1_zero_delta_validator.v1"
PHASE_SCOPE = "v014_s06_p1_zero_delta_validator_only"
OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S06_P1_ZERO_DELTA_VALIDATOR")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "zero_delta_validator_manifest.json"
PASS_FIXTURE_PATH = MACHINE_DIR / "zero_delta_pass_fixture.json"
PASS_RESULT_PATH = MACHINE_DIR / "zero_delta_pass_result.json"
MISMATCH_FIXTURE_PATH = MACHINE_DIR / "zero_delta_one_cent_mismatch_fixture.json"
MISMATCH_RESULT_PATH = MACHINE_DIR / "zero_delta_one_cent_mismatch_result.json"
MISMATCH_REPORT_PATH = MACHINE_DIR / "mismatch_report.csv"
REPORT_PATH = HUMAN_DIR / "zero_delta_validator_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"
TASKPACK_FIXTURE_PATH = Path("KMFA/metadata/fixtures/a0_project_cost_fixture.json")
S05_STAGE_REVIEW_MANIFEST_PATH = Path("KMFA/stage_artifacts/V014_S05_STAGE_REVIEW/machine/stage5_review_manifest.json")
NEXT_PHASE = "S06-P2"
NEXT_INSTRUCTION = (
    "Run S06-P2 cross-source difference queue as a separate run only after S06-P1 is committed. "
    "Do not run S06-P3, Stage 6 review, or GitHub upload in S06-P1. GitHub main upload remains "
    "deferred until v1.4 Stage 1-18 are complete, overall review has passed, and findings are fixed."
)
REQUIRED_REPORT_COLUMNS = [
    "record_id",
    "source",
    "field",
    "authoritative_value_cents",
    "system_value_cents",
    "difference_cents",
]


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def taskpack_pass_fixture() -> dict[str, Any]:
    fixture = read_json(TASKPACK_FIXTURE_PATH)
    return {
        "schema_version": "kmfa.v014_s06_p1.zero_delta_fixture.v1",
        "fixture_id": "KMFA-V014-S06P1-PUBLIC-SAFE-PASS-FIXTURE",
        "source_fixture_ref": TASKPACK_FIXTURE_PATH.as_posix(),
        "public_safe_fixture_only": True,
        "raw_business_data_used": False,
        "key_fields": fixture["key_fields"],
        "amount_fields": fixture["amount_fields"],
        "authoritative_records": fixture["authoritative_records"],
        "system_records": fixture["system_records"],
    }


def one_cent_mismatch_fixture() -> dict[str, Any]:
    return {
        "schema_version": "kmfa.v014_s06_p1.zero_delta_fixture.v1",
        "fixture_id": "KMFA-V014-S06P1-ONE-CENT-MISMATCH-FIXTURE",
        "public_safe_fixture_only": True,
        "raw_business_data_used": False,
        "key_fields": ["record_id"],
        "amount_fields": ["contract_amount_cents"],
        "authoritative_records": [
            {
                "record_id": "V014-SYN-ZERO-DELTA-001",
                "source": "A0_Q5_PUBLIC_SAFE_AUTHORITY_BASELINE_SYNTHETIC",
                "contract_amount_cents": 10000,
            }
        ],
        "system_records": [
            {
                "record_id": "V014-SYN-ZERO-DELTA-001",
                "source": "SYSTEM_RECOMPUTE_PUBLIC_SAFE_SYNTHETIC",
                "contract_amount_cents": 9999,
            }
        ],
    }


def mismatch_report_columns() -> list[str]:
    with MISMATCH_REPORT_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle).fieldnames or [])


def write_fixture_results() -> tuple[dict[str, Any], dict[str, Any]]:
    write_json(PASS_FIXTURE_PATH, taskpack_pass_fixture())
    write_json(MISMATCH_FIXTURE_PATH, one_cent_mismatch_fixture())
    pass_result = validate_fixture_file(PASS_FIXTURE_PATH)
    mismatch_result = validate_fixture_file(MISMATCH_FIXTURE_PATH)
    write_json(PASS_RESULT_PATH, pass_result)
    write_json(MISMATCH_RESULT_PATH, mismatch_result)
    write_mismatch_report(mismatch_result["mismatches"], MISMATCH_REPORT_PATH)
    return pass_result, mismatch_result


def build_manifest() -> dict[str, Any]:
    s05 = validate_v014_s05_stage_review()
    s05_gate = s05["stage_gate"]
    pass_result, mismatch_result = write_fixture_results()
    pass_fixture = read_json(PASS_FIXTURE_PATH)
    mismatch = mismatch_result["mismatches"][0]
    comparison_count = len(pass_fixture["authoritative_records"]) * len(pass_fixture["amount_fields"])
    columns = mismatch_report_columns()

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S06",
        "stage_name": "zero-delta validation and difference handling",
        "phase_id": "S06-P1",
        "phase_name": "zero-delta validator",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_zero_delta_validator",
        "completed_task_ids": ["S06P1T01", "S06P1T02", "S06P1T03"],
        "s05_stage_review_dependency_validated": True,
        "s05_stage_review_manifest_ref": S05_STAGE_REVIEW_MANIFEST_PATH.as_posix(),
        "s05_dependency_summary": {
            "status": s05["status"],
            "phase_results": s05["phase_results"],
            "open_review_finding_count": s05["open_review_finding_count"],
            "authority_record_count": s05_gate["authority_record_count"],
            "q5_calculation_baseline_locked_count": s05_gate["q5_calculation_baseline_locked_count"],
            "excluded_cross_source_support_only_count": s05_gate["excluded_cross_source_support_only_count"],
            "q5_full_quality_grade_allowed_count": s05_gate["q5_full_quality_grade_allowed_count"],
            "zero_delta_validated_count_before_s06_p1": s05_gate["zero_delta_validated_count"],
            "github_upload_performed": s05["github_upload_performed"],
            "next_recommended_phase": s05["next_recommended_phase"],
        },
        "source_validator_ref": "KMFA/tools/zero_delta_validator.py",
        "source_unit_test_ref": "KMFA/tests/test_zero_delta_validator.py",
        "taskpack_fixture_ref": TASKPACK_FIXTURE_PATH.as_posix(),
        "pass_fixture_ref": PASS_FIXTURE_PATH.as_posix(),
        "pass_result_ref": PASS_RESULT_PATH.as_posix(),
        "mismatch_fixture_ref": MISMATCH_FIXTURE_PATH.as_posix(),
        "mismatch_result_ref": MISMATCH_RESULT_PATH.as_posix(),
        "mismatch_report_ref": MISMATCH_REPORT_PATH.as_posix(),
        "pass_fixture_record_count": len(pass_fixture["authoritative_records"]),
        "pass_fixture_amount_field_count": len(pass_fixture["amount_fields"]),
        "pass_fixture_field_comparison_count": comparison_count,
        "zero_delta_passed_for_public_safe_fixture": pass_result["zero_delta_passed"],
        "pass_fixture_mismatch_count": pass_result["mismatch_count"],
        "one_cent_mismatch_detected": (
            mismatch_result["zero_delta_passed"] is False
            and mismatch_result["mismatch_count"] == 1
            and mismatch["difference_cents"] == 1
        ),
        "minimum_fail_difference_cents": mismatch_result["minimum_fail_difference_cents"],
        "mismatch_fixture_mismatch_count": mismatch_result["mismatch_count"],
        "mismatch_report_generated": MISMATCH_REPORT_PATH.exists(),
        "mismatch_report_required_columns": REQUIRED_REPORT_COLUMNS,
        "mismatch_report_columns": columns,
        "mismatch_report_contains_required_columns": all(column in columns for column in REQUIRED_REPORT_COLUMNS),
        "integer_cent_comparison_only": True,
        "float_money_allowed": False,
        "zero_delta_validator_available": True,
        "zero_delta_validation_scope": "public_safe_synthetic_fixture_only",
        "actual_business_zero_delta_validated": False,
        "raw_business_data_used": False,
        "difference_queue_created": False,
        "metadata_quality_written": False,
        "s06_p2_started": False,
        "s06_p3_started": False,
        "stage6_review_performed": False,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "raw_value_matching_performed": False,
        "lineage_full_check_performed": False,
        "formal_report_performed": False,
        "live_connector_called": False,
        "opme_deep_coupling_performed": False,
        "business_execution_performed": False,
        "release_state": {
            "current_data_quality_grade": "Q4",
            "current_report_grade": "D",
            "current_go_no_go": "NO_GO",
            "release_permission": "blocked",
            "delivery_allowed": False,
            "formal_report_allowed": False,
            "business_decision_basis_allowed": False,
            "business_execution_allowed": False,
            "github_main_upload_allowed": False,
            "blocking_reason": "s06_p2_difference_queue_s06_p3_quality_output_lineage_and_formal_report_not_completed",
        },
        "raw_data_boundary": {
            "raw_inbox_path": str(RAW_INBOX),
            "raw_inbox_read_required_by_this_phase": False,
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
            "raw_inbox_mutated_by_this_phase": False,
            "private_runtime_written_by_this_phase": False,
            "github_commit_allowed_for_raw": False,
        },
        "public_repo_safety": {
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
            "row_or_cell_values_committed": False,
            "source_or_normalized_values_committed": False,
            "business_values_committed": False,
        },
        "validation_summary": {
            "py_compile": "PENDING_FINAL_VALIDATION",
            "generator": "PASS",
            "s05_stage_review_dependency": "PASS",
            "s06_p1_validator": "PENDING_FINAL_VALIDATION",
            "focused_unit_test": "PENDING_FINAL_VALIDATION",
            "zero_delta_validator_unit": "PENDING_FINAL_VALIDATION",
            "no_omission_check": "PENDING_FINAL_VALIDATION",
            "no_float_money_check": "PENDING_FINAL_VALIDATION",
            "governance_validator": "PENDING_FINAL_VALIDATION",
            "lean_governance_validator": "PENDING_FINAL_VALIDATION",
            "governance_sync_validator": "PENDING_FINAL_VALIDATION",
            "raw_private_scan": "PENDING_FINAL_VALIDATION",
            "secret_scan": "PENDING_FINAL_VALIDATION",
            "diff_check": "PENDING_FINAL_VALIDATION",
        },
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            PASS_RESULT_PATH.as_posix(),
            MISMATCH_RESULT_PATH.as_posix(),
            MISMATCH_REPORT_PATH.as_posix(),
        ],
        "next_recommended_phase": NEXT_PHASE,
        "next_phase_instruction": NEXT_INSTRUCTION,
    }


def write_human_evidence(manifest: dict[str, Any]) -> None:
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S06-P1 Zero-Delta Validator",
                "",
                f"- task_id: `{TASK_ID}`",
                f"- status: `{manifest['status']}`",
                f"- dependency: S05 Stage review PASS, open findings `{manifest['s05_dependency_summary']['open_review_finding_count']}`",
                f"- pass fixture comparisons: `{manifest['pass_fixture_field_comparison_count']}`",
                f"- pass fixture mismatch count: `{manifest['pass_fixture_mismatch_count']}`",
                f"- one-cent mismatch detected: `{manifest['one_cent_mismatch_detected']}`",
                f"- mismatch report generated: `{manifest['mismatch_report_generated']}`",
                f"- current quality/report/release: `{manifest['release_state']['current_data_quality_grade']}` / `{manifest['release_state']['current_report_grade']}` / `{manifest['release_state']['release_permission']}`",
                "",
                "## Boundaries",
                "",
                "- Public-safe synthetic fixture only; no raw business data was used.",
                "- S06-P2 difference queue, S06-P3 metadata quality output, Stage 6 review, GitHub upload, formal report, live connector and business execution were not performed.",
                "- Raw inbox read/list/stat/hash/mutation/write flags remain false for this phase.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    TEST_RESULTS_PATH.write_text(
        "\n".join(
            [
                "# Test Results",
                "",
                "- Generator: PASS",
                "- S05 Stage review dependency: PASS",
                "- S06-P1 validator: pending final validation",
                "- Focused unit test: pending final validation",
                "- Governance and safety scans: pending final validation",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    RISK_REGISTER_PATH.write_text(
        "\n".join(
            [
                "# Risk Register",
                "",
                "| Risk | Control | Status |",
                "|---|---|---|",
                "| Public fixture passes but actual business zero-delta is not complete | Manifest explicitly marks actual business zero-delta as false and keeps D/NO_GO | controlled |",
                "| Difference queue skipped | Scope flags keep S06-P2 false and next phase points to S06-P2 | controlled |",
                "| Raw data exposure | Evidence contains only synthetic public-safe values and no raw inbox access | controlled |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    ROLLBACK_PATH.write_text(
        "\n".join(
            [
                "# Rollback Plan",
                "",
                "- Revert the S06-P1 commit.",
                "- Remove `KMFA/stage_artifacts/V014_S06_P1_ZERO_DELTA_VALIDATOR/` if the phase is abandoned before commit.",
                "- Keep `/Users/linzezhang/Downloads/KMFA_MetaData` untouched.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    manifest = build_manifest()
    write_human_evidence(manifest)
    write_json(MANIFEST_PATH, manifest)
    print(
        "PASS: KMFA v0.1.4 S06-P1 zero-delta validator evidence generated "
        f"(comparisons={manifest['pass_fixture_field_comparison_count']}, "
        f"one_cent_mismatch={str(manifest['one_cent_mismatch_detected']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
