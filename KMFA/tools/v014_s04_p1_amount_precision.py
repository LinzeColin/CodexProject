#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S04-P1 amount precision evidence.

This phase locks the existing amount normalization and no-float behavior with
synthetic public-safe values only. It does not read, list, hash, mutate, or
write the local raw data inbox, and it does not perform S04-P2, S04-P3, Stage
4 review, GitHub upload, raw value matching, field mapping, formal reporting,
live connector calls, or business execution.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from KMFA.tools.amount_tools import AmountNormalizationError, normalize_amount_to_cents
from KMFA.tools.check_no_float_money import scan_paths
from KMFA.tools.check_v014_s03_stage_review import RAW_INBOX, validate_v014_s03_stage_review


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S04_P1_AMOUNT_PRECISION")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/amount_precision_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/amount_precision_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
RISK_REGISTER_PATH = PUBLIC_OUTPUT_DIR / "human/risk_register.md"
ROLLBACK_PATH = PUBLIC_OUTPUT_DIR / "human/rollback_plan.md"
TASK_ID = "KMFA-V014-S04-P1-AMOUNT-PRECISION-20260704"
SCHEMA_VERSION = "kmfa.v014_s04_p1_amount_precision.v1"


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


def build_amount_cases() -> list[dict[str, Any]]:
    return [
        {"case_id": "plain_yuan_thousand_separator", "input": "1,234.56", "unit": None, "expected_cents": 123456},
        {"case_id": "rmb_yuan_text", "input": "人民币1,234.56元", "unit": None, "expected_cents": 123456},
        {"case_id": "negative_yuan", "input": "-1,234.56", "unit": None, "expected_cents": -123456},
        {"case_id": "parentheses_negative_yuan", "input": "(1,234.56)", "unit": None, "expected_cents": -123456},
        {"case_id": "decimal_yuan", "input": Decimal("12.30"), "unit": None, "expected_cents": 1230},
        {"case_id": "integer_zero_yuan", "input": 0, "unit": None, "expected_cents": 0},
        {"case_id": "ten_thousand_yuan_text", "input": "1.2345万元", "unit": None, "expected_cents": 1234500},
        {"case_id": "explicit_ten_thousand_yuan", "input": "1,234.56", "unit": "wan_yuan", "expected_cents": 1234560000},
        {"case_id": "thousand_yuan_text", "input": "0.001千元", "unit": None, "expected_cents": 100},
    ]


def build_rejection_cases() -> list[dict[str, Any]]:
    return [
        {"case_id": "float_value_rejected", "input": json.loads("1.23"), "unit": None},
        {"case_id": "fractional_cent_text_rejected", "input": "1.234元", "unit": None},
        {"case_id": "fractional_cent_decimal_rejected", "input": Decimal("1.001"), "unit": None},
        {"case_id": "blank_text_rejected", "input": "", "unit": None},
        {"case_id": "dash_text_rejected", "input": "-", "unit": None},
        {"case_id": "hash_text_rejected", "input": "#", "unit": None},
        {"case_id": "abnormal_text_rejected", "input": "abc", "unit": None},
        {"case_id": "boolean_value_rejected", "input": True, "unit": None},
        {"case_id": "conflicting_unit_rejected", "input": "1万元", "unit": "yuan"},
    ]


def replay_amount_precision_capability() -> dict[str, Any]:
    amount_results: list[dict[str, Any]] = []
    rejection_results: list[dict[str, Any]] = []

    for case in build_amount_cases():
        actual = normalize_amount_to_cents(case["input"], unit=case["unit"])
        amount_results.append(
            {
                "case_id": case["case_id"],
                "expected_cents": case["expected_cents"],
                "actual_cents": actual,
                "passed": actual == case["expected_cents"],
            }
        )

    for case in build_rejection_cases():
        try:
            normalize_amount_to_cents(case["input"], unit=case["unit"])
        except AmountNormalizationError as exc:
            rejection_results.append(
                {
                    "case_id": case["case_id"],
                    "error_type": type(exc).__name__,
                    "rejected": True,
                }
            )
        else:
            rejection_results.append(
                {
                    "case_id": case["case_id"],
                    "error_type": None,
                    "rejected": False,
                }
            )

    with tempfile.TemporaryDirectory(prefix="kmfa-v014-s04p1-") as tmp:
        fixture = Path(tmp) / "forbidden_money.py"
        fixture.write_text(
            "\n".join(
                [
                    "def forbidden_money(value: float):",
                    "    return float(value) + 1.25",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        fixture_findings = scan_paths([Path(tmp)])

    repository_findings = scan_paths([Path("KMFA")])

    return {
        "amount_case_results": amount_results,
        "amount_case_count": len(amount_results),
        "amount_case_passed_count": sum(1 for item in amount_results if item["passed"]),
        "amount_rejection_results": rejection_results,
        "amount_rejection_count": len(rejection_results),
        "amount_rejection_passed_count": sum(1 for item in rejection_results if item["rejected"]),
        "scan_fixture_forbidden_float_findings": len(fixture_findings),
        "repository_no_float_scan_passed": not repository_findings,
        "repository_no_float_finding_count": len(repository_findings),
        "repository_no_float_findings": [
            {
                "path": finding.path.as_posix(),
                "line": finding.line,
                "column": finding.column,
                "message": finding.message,
            }
            for finding in repository_findings
        ],
    }


def build_manifest() -> dict[str, Any]:
    s03_review = validate_v014_s03_stage_review()
    capability = replay_amount_precision_capability()

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S04",
        "stage_name": "v0.1.4 amount precision field standardization and basic tools",
        "phase_id": "S04-P1",
        "phase_name": "amount precision and no-float lock",
        "phase_scope": "v014_s04_p1_amount_precision_only",
        "task_id": TASK_ID,
        "acceptance_id": "ACC-V014-S04-P1-AMOUNT-PRECISION",
        "run_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred",
        "completed_task_ids": ["S4PAT01", "S4PAT02", "S4PAT03"],
        "s03_stage_review_dependency_validated": (
            s03_review.get("stage_id") == "S03"
            and s03_review.get("stage_review_performed") is True
            and s03_review.get("github_upload_performed") is False
            and s03_review.get("open_review_finding_count") == 0
            and s03_review.get("next_recommended_phase") == "S04-P1"
        ),
        "s03_stage_review_dependency_ref": "KMFA/stage_artifacts/V014_S03_STAGE_REVIEW/machine/stage3_review_manifest.json",
        "amount_tools_dependency_validated": (
            capability["amount_case_count"] == capability["amount_case_passed_count"] == 9
            and capability["amount_rejection_count"] == capability["amount_rejection_passed_count"] == 9
        ),
        "no_float_dependency_validated": (
            capability["scan_fixture_forbidden_float_findings"] == 3
            and capability["repository_no_float_scan_passed"] is True
        ),
        "amount_case_count": capability["amount_case_count"],
        "amount_case_passed_count": capability["amount_case_passed_count"],
        "amount_case_results": capability["amount_case_results"],
        "amount_rejection_count": capability["amount_rejection_count"],
        "amount_rejection_passed_count": capability["amount_rejection_passed_count"],
        "amount_rejection_results": capability["amount_rejection_results"],
        "scan_fixture_forbidden_float_findings": capability["scan_fixture_forbidden_float_findings"],
        "repository_no_float_scan_passed": capability["repository_no_float_scan_passed"],
        "repository_no_float_finding_count": capability["repository_no_float_finding_count"],
        "repository_no_float_findings": capability["repository_no_float_findings"],
        "amount_tool_refs": [
            "KMFA/tools/amount_tools.py",
            "KMFA/tools/check_no_float_money.py",
            "KMFA/tests/test_amount_tools.py",
            "KMFA/stage_artifacts/S04_P1_amount_tools/human/s04_p1_completion_record.md",
            "KMFA/stage_artifacts/S04_P1_amount_tools/human/test_results.md",
        ],
        "raw_data_boundary": {
            "local_raw_data_dir": RAW_INBOX,
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_read_performed_by_this_phase": False,
            "codex_list_performed_by_this_phase": False,
            "codex_hash_performed_by_this_phase": False,
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
        "raw_dir_list_performed": False,
        "raw_dir_hash_performed": False,
        "raw_dir_mutation_performed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "raw_file_bytes_committed": False,
        "raw_filename_publication_allowed": False,
        "raw_file_hash_publication_allowed": False,
        "field_plaintext_publication_allowed": False,
        "sheet_name_publication_allowed": False,
        "zip_member_name_publication_allowed": False,
        "row_value_publication_allowed": False,
        "business_value_publication_allowed": False,
        "business_amount_value_publication_allowed": False,
        "business_field_parsing_performed": False,
        "raw_value_matching_performed": False,
        "field_mapping_performed": False,
        "s04_p2_started": False,
        "s04_p3_started": False,
        "stage4_review_performed": False,
        "github_upload_performed": False,
        "github_main_upload_allowed": False,
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "current_data_quality_grade": "Q2",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "current_go_no_go": "NO_GO",
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
            "business_amount_values_committed": False,
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s04_p1_amount_precision.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s04_p1_amount_precision.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s04_p1_amount_precision -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_amount_tools -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s03_stage_review.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            "KMFA/tools/v014_s04_p1_amount_precision.py",
            "KMFA/tools/check_v014_s04_p1_amount_precision.py",
            "KMFA/tests/test_v014_s04_p1_amount_precision.py",
            "KMFA/tools/amount_tools.py",
            "KMFA/tools/check_no_float_money.py",
            "KMFA/tests/test_amount_tools.py",
            "KMFA/tools/check_v014_s03_stage_review.py",
        ],
        "next_required_step": (
            "Proceed to v0.1.4 S04-P2 field standardization as a separate run; do not perform "
            "S04-P3, Stage 4 review, GitHub upload, raw value matching, field mapping beyond S04-P2 scope, "
            "lineage full check, formal report release, live connector, OpMe deep coupling, or business execution in S04-P1."
        ),
    }


def write_report(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.4 S04-P1 Amount Precision",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        f"- s03_stage_review_dependency_validated: `{str(manifest['s03_stage_review_dependency_validated']).lower()}`",
        f"- amount_tools_dependency_validated: `{str(manifest['amount_tools_dependency_validated']).lower()}`",
        f"- no_float_dependency_validated: `{str(manifest['no_float_dependency_validated']).lower()}`",
        f"- amount_case_count: `{manifest['amount_case_count']}`",
        f"- amount_rejection_count: `{manifest['amount_rejection_count']}`",
        f"- scan_fixture_forbidden_float_findings: `{manifest['scan_fixture_forbidden_float_findings']}`",
        f"- repository_no_float_scan_passed: `{str(manifest['repository_no_float_scan_passed']).lower()}`",
        "",
        "## Amount Boundaries",
        "",
        "- supported: `yuan`, `wan_yuan`, `qian_yuan`, thousands separators, negative signs, parentheses negatives, Decimal inputs, integer zero",
        "- rejected: float values, non-cent amounts, blank/dash/hash/null-like text, abnormal text, booleans, conflicting units",
        "- money_storage_unit: `integer_cents`",
        "",
        "## Raw Data Boundary",
        "",
        f"- local_raw_data_dir: `{manifest['raw_data_boundary']['local_raw_data_dir']}`",
        "- codex_read_list_hash_performed_by_this_phase: `false`",
        "- codex_modify_delete_move_rename_overwrite_or_generate_inside_allowed: `false`",
        "- public_repo_raw_commit_allowed: `false`",
        "- private_runtime_output_dir: `KMFA/.codex_private_runtime/`",
        "",
        "## Public-Safe Boundary",
        "",
        "- raw_file_bytes_committed: `false`",
        "- raw_filename_publication_allowed: `false`",
        "- raw_file_hash_publication_allowed: `false`",
        "- field_plaintext_publication_allowed: `false`",
        "- sheet_name_publication_allowed: `false`",
        "- zip_member_name_publication_allowed: `false`",
        "- row_value_publication_allowed: `false`",
        "- business_value_publication_allowed: `false`",
        "- business_amount_value_publication_allowed: `false`",
        "",
        "## Non-Scope",
        "",
        "- business_field_parsing_performed: `false`",
        "- raw_value_matching_performed: `false`",
        "- field_mapping_performed: `false`",
        "- s04_p2_started: `false`",
        "- s04_p3_started: `false`",
        "- stage4_review_performed: `false`",
        "- github_upload_performed: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Gate Status",
        "",
        f"- current_data_quality_grade: `{manifest['current_data_quality_grade']}`",
        f"- current_report_grade: `{manifest['current_report_grade']}`",
        f"- release_permission: `{manifest['release_permission']}`",
        f"- current_go_no_go: `{manifest['current_go_no_go']}`",
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
        "# KMFA v0.1.4 S04-P1 Test Results",
        "",
        "- status: `pending_final_validation`",
        "- red_step: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s04_p1_amount_precision -q` failed before validator implementation with missing module.",
        "- note: `Generator created placeholder; final validation evidence will overwrite this file before commit.`",
        "",
    ]
    TEST_RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_risk_and_rollback() -> None:
    RISK_REGISTER_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S04-P1 Risk Register",
                "",
                "| risk_id | risk | control | status |",
                "|---|---|---|---|",
                "| `RISK-V014-S04P1-001` | Amount normalization evidence uses synthetic values only and does not prove raw business values. | Keep S04-P1 scoped to tool capability and require later raw-authorized mapping phases before business use. | `controlled` |",
                "| `RISK-V014-S04P1-002` | Any business money float use can create precision drift. | `check_no_float_money.py` scans KMFA Python code and the S04-P1 validator requires a forbidden-fixture finding count of 3 plus repository zero findings. | `controlled` |",
                "| `RISK-V014-S04P1-003` | Blank, dash, hash, or abnormal symbols could be interpreted as zero. | Rejection cases require these inputs to raise `AmountNormalizationError`; no silent zero conversion is allowed. | `controlled` |",
                "| `RISK-V014-S04P1-004` | S04-P1 could be mistaken for Stage 4 review or upload readiness. | Manifest locks S04-P2/S04-P3/Stage 4 review/GitHub upload as false and points next step to S04-P2 only. | `controlled` |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    ROLLBACK_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S04-P1 Rollback Plan",
                "",
                "- revert_files: `KMFA/tools/v014_s04_p1_amount_precision.py`, `KMFA/tools/check_v014_s04_p1_amount_precision.py`, `KMFA/tests/test_v014_s04_p1_amount_precision.py`, `KMFA/stage_artifacts/V014_S04_P1_AMOUNT_PRECISION/`, and S04-P1 governance rows.",
                "- raw_data_action: `none`; `/Users/linzezhang/Downloads/KMFA_MetaData` was not read, listed, hashed, modified, deleted, moved, renamed, overwritten, or written by this phase.",
                "- verification_after_rollback: rerun `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s03_stage_review.py` and governance validators.",
                "- stop_condition: any raw/private payload, business value, credential, or GitHub upload side effect requires immediate rollback and report.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def generate() -> dict[str, Any]:
    (PUBLIC_OUTPUT_DIR / "machine").mkdir(parents=True, exist_ok=True)
    (PUBLIC_OUTPUT_DIR / "human").mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(manifest)
    write_risk_and_rollback()
    write_pending_test_results()
    return manifest


def main() -> int:
    manifest = generate()
    print(
        "PASS: KMFA v0.1.4 S04-P1 amount precision evidence generated "
        f"(amount_cases={manifest['amount_case_count']}, "
        f"rejections={manifest['amount_rejection_count']}, "
        f"no_float={str(manifest['repository_no_float_scan_passed']).lower()}, "
        f"raw_read={str(manifest['raw_dir_read_performed']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
