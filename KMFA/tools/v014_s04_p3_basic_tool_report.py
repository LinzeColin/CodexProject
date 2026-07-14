#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S04-P3 basic tool report evidence.

This phase locks the existing synthetic boundary tests for amount, date, and
period tools under the v0.1.4 governance namespace. It does not read, list,
hash, mutate, or write the local raw data inbox.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s03_stage_review import RAW_INBOX
from KMFA.tools.check_v014_s04_p1_amount_precision import validate_v014_s04_p1_amount_precision
from KMFA.tools.check_v014_s04_p2_field_standardization import validate_v014_s04_p2_field_standardization
from KMFA.tools.generate_tool_test_report import build_report, render_markdown


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S04_P3_BASIC_TOOL_REPORT")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/basic_tool_report_manifest.json"
JSON_REPORT_PATH = PUBLIC_OUTPUT_DIR / "machine/tool_function_test_report.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/basic_tool_report.md"
MARKDOWN_REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/tool_function_test_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
RISK_REGISTER_PATH = PUBLIC_OUTPUT_DIR / "human/risk_register.md"
ROLLBACK_PATH = PUBLIC_OUTPUT_DIR / "human/rollback_plan.md"
TASK_ID = "KMFA-V014-S04-P3-BASIC-TOOL-REPORT-20260704"
SCHEMA_VERSION = "kmfa.v014_s04_p3_basic_tool_report.v1"


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


def replay_basic_tool_report() -> dict[str, Any]:
    report = build_report()
    amount_cases = report["amount_boundary_cases"]
    date_period_cases = report["date_period_boundary_cases"]
    case_summary = report["case_summary"]
    return {
        "tool_report": report,
        "amount_boundary_case_count": len(amount_cases),
        "date_period_boundary_case_count": len(date_period_cases),
        "synthetic_boundary_case_total": case_summary["total"],
        "synthetic_boundary_case_passed": case_summary["passed"],
        "synthetic_boundary_case_failed": case_summary["failed"],
        "coverage": report["coverage"],
        "categories": sorted({case["category"] for case in amount_cases + date_period_cases}),
        "basic_tool_boundary_dependency_validated": (
            report.get("stage") == "S04"
            and report.get("phase") == "S04-P3"
            and report.get("status") == "PASS"
            and report.get("raw_business_data_used") is False
            and case_summary["total"] == case_summary["passed"] == 22
            and case_summary["failed"] == 0
            and len(amount_cases) == 11
            and len(date_period_cases) == 11
        ),
    }


def build_manifest(*, json_report_generated: bool, markdown_report_generated: bool) -> dict[str, Any]:
    s04_p1 = validate_v014_s04_p1_amount_precision()
    s04_p2 = validate_v014_s04_p2_field_standardization()
    replay = replay_basic_tool_report()

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S04",
        "stage_name": "v0.1.4 amount precision field standardization and basic tools",
        "phase_id": "S04-P3",
        "phase_name": "basic tool report",
        "phase_scope": "v014_s04_p3_basic_tool_report_only",
        "task_id": TASK_ID,
        "acceptance_id": "ACC-V014-S04-P3-BASIC-TOOL-REPORT",
        "run_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred",
        "completed_task_ids": ["S4PCT01", "S4PCT02", "S4PCT03"],
        "s04_p1_dependency_validated": (
            s04_p1.get("phase_id") == "S04-P1"
            and s04_p1.get("status") == "completed_validated_local_only_no_go_upload_deferred"
            and s04_p1.get("github_upload_performed") is False
            and "S04-P2" in s04_p1.get("next_required_step", "")
        ),
        "s04_p1_dependency_ref": "KMFA/stage_artifacts/V014_S04_P1_AMOUNT_PRECISION/machine/amount_precision_manifest.json",
        "s04_p2_dependency_validated": (
            s04_p2.get("phase_id") == "S04-P2"
            and s04_p2.get("status") == "completed_validated_local_only_no_go_upload_deferred"
            and s04_p2.get("github_upload_performed") is False
            and "S04-P3" in s04_p2.get("next_required_step", "")
        ),
        "s04_p2_dependency_ref": "KMFA/stage_artifacts/V014_S04_P2_FIELD_STANDARDIZATION/machine/field_standardization_manifest.json",
        "basic_tool_boundary_dependency_validated": replay["basic_tool_boundary_dependency_validated"],
        "synthetic_boundary_case_total": replay["synthetic_boundary_case_total"],
        "synthetic_boundary_case_passed": replay["synthetic_boundary_case_passed"],
        "synthetic_boundary_case_failed": replay["synthetic_boundary_case_failed"],
        "amount_boundary_case_count": replay["amount_boundary_case_count"],
        "date_period_boundary_case_count": replay["date_period_boundary_case_count"],
        "coverage": replay["coverage"],
        "categories": replay["categories"],
        "json_report_generated": json_report_generated,
        "markdown_report_generated": markdown_report_generated,
        "json_report_ref": JSON_REPORT_PATH.as_posix(),
        "markdown_report_ref": MARKDOWN_REPORT_PATH.as_posix(),
        "raw_data_boundary": {
            "local_raw_data_dir": RAW_INBOX,
            "local_raw_data_dir_role": "user_finance_raw_business_data_inbox",
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_read_required_by_this_phase": False,
            "codex_read_performed_by_this_phase": False,
            "codex_list_performed_by_this_phase": False,
            "codex_hash_performed_by_this_phase": False,
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
        "raw_dir_read_required": False,
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
        "business_field_parsing_performed": False,
        "raw_value_matching_performed": False,
        "raw_field_mapping_performed": False,
        "stage4_review_performed": False,
        "stage4_upload_gate_performed": False,
        "s05_started": False,
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
        "github_upload_status": "deferred_until_v014_stage1_18_complete_overall_review",
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
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s04_p3_basic_tool_report.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s04_p3_basic_tool_report.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s04_p3_basic_tool_report -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_basic_tool_boundaries -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/generate_tool_test_report.py --format json",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/generate_tool_test_report.py --format markdown",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s04_p1_amount_precision.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s04_p2_field_standardization.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            JSON_REPORT_PATH.as_posix(),
            MARKDOWN_REPORT_PATH.as_posix(),
            "KMFA/tools/v014_s04_p3_basic_tool_report.py",
            "KMFA/tools/check_v014_s04_p3_basic_tool_report.py",
            "KMFA/tests/test_v014_s04_p3_basic_tool_report.py",
            "KMFA/tools/generate_tool_test_report.py",
            "KMFA/tests/test_basic_tool_boundaries.py",
        ],
        "legacy_s04_p3_refs": [
            "KMFA/stage_artifacts/S04_P3_basic_tool_tests/human/s04_p3_completion_record.md",
            "KMFA/stage_artifacts/S04_P3_basic_tool_tests/human/test_results.md",
            "KMFA/stage_artifacts/S04_P3_basic_tool_tests/human/tool_function_test_report.md",
            "KMFA/stage_artifacts/S04_P3_basic_tool_tests/machine/s04_p3_manifest.json",
            "KMFA/stage_artifacts/V013_S04_P3_BASIC_TOOL_REPORT/machine/basic_tool_report_manifest.json",
        ],
        "non_scope": [
            "Stage 4 review",
            "Stage 4 GitHub upload gate",
            "GitHub upload",
            "raw root read list hash mutation",
            "raw data inspection",
            "raw filename publication",
            "raw file hash publication",
            "raw source field or header plaintext publication",
            "sheet or ZIP member name publication",
            "row value publication",
            "business value publication",
            "raw value matching",
            "lineage full check",
            "formal report",
            "live connector",
            "OpMe deep coupling",
            "business execution",
        ],
        "next_required_step": (
            "Proceed to v0.1.4 Stage 4 overall review as a separate run after S04-P3 is complete; "
            "do not perform GitHub upload until v1.4 Stage 1-18 complete overall review and findings are fixed."
        ),
    }


def write_report(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.4 S04-P3 Basic Tool Report",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        f"- s04_p1_dependency_validated: `{str(manifest['s04_p1_dependency_validated']).lower()}`",
        f"- s04_p2_dependency_validated: `{str(manifest['s04_p2_dependency_validated']).lower()}`",
        f"- basic_tool_boundary_dependency_validated: `{str(manifest['basic_tool_boundary_dependency_validated']).lower()}`",
        f"- synthetic_boundary_cases: `{manifest['synthetic_boundary_case_passed']}/{manifest['synthetic_boundary_case_total']}`",
        f"- synthetic_boundary_case_failed: `{manifest['synthetic_boundary_case_failed']}`",
        f"- amount_boundary_case_count: `{manifest['amount_boundary_case_count']}`",
        f"- date_period_boundary_case_count: `{manifest['date_period_boundary_case_count']}`",
        f"- json_report_generated: `{str(manifest['json_report_generated']).lower()}`",
        f"- markdown_report_generated: `{str(manifest['markdown_report_generated']).lower()}`",
        "",
        "## Coverage",
        "",
    ]
    lines.extend(f"- {item}" for item in manifest["coverage"])
    lines.extend(
        [
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
            "",
            "## Non-Scope",
            "",
            "- stage4_review_performed: `false`",
            "- stage4_upload_gate_performed: `false`",
            "- s05_started: `false`",
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
            f"- github_upload_status: `{manifest['github_upload_status']}`",
            "",
            "## Next Step",
            "",
            manifest["next_required_step"],
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_pending_test_results() -> None:
    if TEST_RESULTS_PATH.exists():
        return
    lines = [
        "# KMFA v0.1.4 S04-P3 Test Results",
        "",
        "- status: `pending_final_validation`",
        "- red_step: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s04_p3_basic_tool_report -q` failed before validator implementation with missing module.",
        "- note: `Generator created placeholder; final validation evidence will overwrite this file before commit.`",
        "",
    ]
    TEST_RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_risk_and_rollback() -> None:
    RISK_REGISTER_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S04-P3 Risk Register",
                "",
                "| risk_id | risk | control | status |",
                "|---|---|---|---|",
                "| `RISK-V014-S04P3-001` | Synthetic boundary cases validate tool behavior but do not prove raw business source correctness. | Keep S04-P3 scoped to public-safe tool tests; raw value matching and authoritative baseline work remain out of scope. | `controlled` |",
                "| `RISK-V014-S04P3-002` | Tool report could be mistaken for Stage 4 review or upload readiness. | Manifest locks Stage 4 review/upload/S05/GitHub upload as false and points next step to a separate Stage 4 review run. | `controlled` |",
                "| `RISK-V014-S04P3-003` | Amount/date/period edge cases could drift from tool implementation. | Validator recomputes all 22 synthetic cases and requires 22/22 PASS before accepting evidence. | `controlled` |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    ROLLBACK_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S04-P3 Rollback Plan",
                "",
                "- revert_files: `KMFA/tools/v014_s04_p3_basic_tool_report.py`, `KMFA/tools/check_v014_s04_p3_basic_tool_report.py`, `KMFA/tests/test_v014_s04_p3_basic_tool_report.py`, `KMFA/stage_artifacts/V014_S04_P3_BASIC_TOOL_REPORT/`, and S04-P3 governance rows.",
                "- raw_data_action: `none`; `/Users/linzezhang/Downloads/KMFA_MetaData` was not read, listed, hashed, modified, deleted, moved, renamed, overwritten, or written by this phase.",
                "- verification_after_rollback: rerun `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s04_p2_field_standardization.py` and governance validators.",
                "- stop_condition: any raw/private payload, business value, credential, raw filename/hash, raw source header plaintext, or GitHub upload side effect requires immediate rollback and report.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def generate() -> dict[str, Any]:
    (PUBLIC_OUTPUT_DIR / "machine").mkdir(parents=True, exist_ok=True)
    (PUBLIC_OUTPUT_DIR / "human").mkdir(parents=True, exist_ok=True)
    report = build_report()
    JSON_REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    MARKDOWN_REPORT_PATH.write_text(render_markdown(report), encoding="utf-8")
    manifest = build_manifest(
        json_report_generated=JSON_REPORT_PATH.exists(),
        markdown_report_generated=MARKDOWN_REPORT_PATH.exists(),
    )
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(manifest)
    write_risk_and_rollback()
    write_pending_test_results()
    return manifest


def main() -> int:
    manifest = generate()
    print(
        "PASS: KMFA v0.1.4 S04-P3 basic tool report evidence generated "
        f"(cases={manifest['synthetic_boundary_case_passed']}/{manifest['synthetic_boundary_case_total']}, "
        f"amount_cases={manifest['amount_boundary_case_count']}, "
        f"date_period_cases={manifest['date_period_boundary_case_count']}, "
        f"raw_read={str(manifest['raw_dir_read_performed']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
