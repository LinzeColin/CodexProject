#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S04-P3 basic tool report replay evidence.

This phase replays the existing S04-P3 synthetic boundary report. It does not
read or inspect the local raw data inbox.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s04_p1_amount_precision import validate_v013_s04_p1_amount_precision
from KMFA.tools.check_v013_s04_p2_field_standardization import validate_v013_s04_p2_field_standardization
from KMFA.tools.generate_tool_test_report import build_report, render_markdown
from KMFA.tools.v013_s03_p1_file_import_register import RAW_DIR


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S04_P3_BASIC_TOOL_REPORT")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/basic_tool_report_manifest.json"
JSON_REPORT_PATH = PUBLIC_OUTPUT_DIR / "machine/tool_function_test_report.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/basic_tool_report_replay_report.md"
MARKDOWN_REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/tool_function_test_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
TASK_ID = "KMFA-V013-S04-P3-BASIC-TOOL-REPORT-20260702"
SCHEMA_VERSION = "kmfa.v013_s04_p3_basic_tool_report.v1"


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
    s04_p1 = validate_v013_s04_p1_amount_precision()
    s04_p2 = validate_v013_s04_p2_field_standardization()
    replay = replay_basic_tool_report()

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S04",
        "stage_name": "v0.1.3 amount precision field standardization and basic tools",
        "phase_id": "S04-P3",
        "phase_name": "basic tool report replay",
        "phase_scope": "v013_s04_p3_basic_tool_report_replay_only",
        "task_id": TASK_ID,
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
        ),
        "s04_p1_dependency_ref": "KMFA/stage_artifacts/V013_S04_P1_AMOUNT_PRECISION/machine/amount_precision_manifest.json",
        "s04_p2_dependency_validated": (
            s04_p2.get("phase_id") == "S04-P2"
            and s04_p2.get("status") == "completed_validated_local_only_no_go_upload_deferred"
            and s04_p2.get("github_upload_performed") is False
        ),
        "s04_p2_dependency_ref": "KMFA/stage_artifacts/V013_S04_P2_FIELD_STANDARDIZATION/machine/field_standardization_manifest.json",
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
        "json_report_ref": str(JSON_REPORT_PATH),
        "markdown_report_ref": str(MARKDOWN_REPORT_PATH),
        "raw_data_boundary": {
            "local_raw_data_dir": RAW_DIR,
            "local_raw_data_dir_role": "user_finance_raw_business_data_inbox",
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_read_required_by_this_phase": False,
            "codex_read_performed_by_this_phase": False,
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
        "stage4_review_performed": False,
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
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s04_p3_basic_tool_report.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s04_p3_basic_tool_report.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s04_p3_basic_tool_report -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_basic_tool_boundaries -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/generate_tool_test_report.py --format json",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/generate_tool_test_report.py --format markdown",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s04_p1_amount_precision.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s04_p2_field_standardization.py",
        ],
        "evidence_refs": [
            "KMFA/stage_artifacts/V013_S04_P3_BASIC_TOOL_REPORT/human/basic_tool_report_replay_report.md",
            "KMFA/stage_artifacts/V013_S04_P3_BASIC_TOOL_REPORT/human/test_results.md",
            "KMFA/stage_artifacts/V013_S04_P3_BASIC_TOOL_REPORT/human/tool_function_test_report.md",
            "KMFA/stage_artifacts/V013_S04_P3_BASIC_TOOL_REPORT/machine/basic_tool_report_manifest.json",
            "KMFA/stage_artifacts/V013_S04_P3_BASIC_TOOL_REPORT/machine/tool_function_test_report.json",
        ],
        "legacy_s04_p3_refs": [
            "KMFA/tools/generate_tool_test_report.py",
            "KMFA/tests/test_basic_tool_boundaries.py",
            "KMFA/stage_artifacts/S04_P3_basic_tool_tests/human/s04_p3_completion_record.md",
            "KMFA/stage_artifacts/S04_P3_basic_tool_tests/human/test_results.md",
            "KMFA/stage_artifacts/S04_P3_basic_tool_tests/human/tool_function_test_report.md",
            "KMFA/stage_artifacts/S04_P3_basic_tool_tests/machine/s04_p3_manifest.json",
        ],
        "non_scope": [
            "Stage 4 review",
            "GitHub upload",
            "raw data inspection",
            "raw directory mutation",
            "raw filename publication",
            "field or header plaintext from raw sources",
            "sheet or ZIP member name publication",
            "row value publication",
            "business value publication",
            "raw value matching",
            "lineage full check completion",
            "formal report release",
            "live connector",
            "business execution",
        ],
        "next_required_step": "Stage 4 review in a separate run after S04-P3 is complete. Do not perform GitHub upload until Stage 4 review is complete and findings are fixed.",
    }


def write_report(manifest: dict[str, Any]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# KMFA v0.1.3 S04-P3 Basic Tool Report Replay",
        "",
        "- status: `completed_validated_local_only_no_go_upload_deferred`",
        "- phase_scope: `v013_s04_p3_basic_tool_report_replay_only`",
        f"- synthetic_boundary_case_total: `{manifest['synthetic_boundary_case_total']}`",
        f"- synthetic_boundary_case_passed: `{manifest['synthetic_boundary_case_passed']}`",
        f"- synthetic_boundary_case_failed: `{manifest['synthetic_boundary_case_failed']}`",
        f"- amount_boundary_case_count: `{manifest['amount_boundary_case_count']}`",
        f"- date_period_boundary_case_count: `{manifest['date_period_boundary_case_count']}`",
        f"- json_report_generated: `{str(manifest['json_report_generated']).lower()}`",
        f"- markdown_report_generated: `{str(manifest['markdown_report_generated']).lower()}`",
        "- raw_dir_read_required: `false`",
        "- raw_dir_read_performed: `false`",
        "- raw_dir_mutation_performed: `false`",
        f"- local_raw_data_dir: `{manifest['raw_data_boundary']['local_raw_data_dir']}`",
        "- local_raw_data_dir_role: `user_finance_raw_business_data_inbox`",
        "- codex_modify_delete_move_rename_overwrite_or_write_inside_raw_dir_allowed: `false`",
        "- codex_extra_files_inside_raw_dir_allowed: `false`",
        "- raw_filename_publication_allowed: `false`",
        "- field_plaintext_publication_allowed: `false`",
        "- sheet_name_publication_allowed: `false`",
        "- zip_member_name_publication_allowed: `false`",
        "- row_value_publication_allowed: `false`",
        "- business_value_publication_allowed: `false`",
        "- stage4_review_performed: `false`",
        "- github_upload_performed: `false`",
        "- current_data_quality_grade: `Q2`",
        "- current_report_grade: `D`",
        "- release_permission: `blocked`",
        "",
        "## Boundary Note",
        "",
        "This replay uses only synthetic public-safe boundary values from the existing S04-P3 tool report. It does not read the local raw inbox and does not publish raw filenames, hashes, sheet names, ZIP member names, field/header text, row values or business values.",
        "",
        "`/Users/linzezhang/Downloads/KMFA_MetaData` is the user finance raw business data inbox. Codex must not modify, delete, move, rename, overwrite, or write generated/extra files inside that directory. Private diagnostics or scratch outputs must use `KMFA/.codex_private_runtime/` or another project-controlled gitignored work directory.",
        "",
        "## Next",
        "",
        manifest["next_required_step"],
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_test_results_if_missing() -> None:
    TEST_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if TEST_RESULTS_PATH.exists():
        return
    TEST_RESULTS_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.3 S04-P3 Test Results",
                "",
                "- status: `pending_final_validation`",
                "",
                "Final validation results will be recorded before local commit.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def generate() -> dict[str, Any]:
    PUBLIC_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    MARKDOWN_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    tool_report = build_report()
    JSON_REPORT_PATH.write_text(json.dumps(tool_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MARKDOWN_REPORT_PATH.write_text(render_markdown(tool_report), encoding="utf-8")

    manifest = build_manifest(
        json_report_generated=JSON_REPORT_PATH.exists(),
        markdown_report_generated=MARKDOWN_REPORT_PATH.exists(),
    )
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(manifest)
    write_test_results_if_missing()
    return manifest


def main() -> int:
    manifest = generate()
    print(
        "PASS: KMFA v0.1.3 S04-P3 basic tool report evidence generated "
        f"(cases={manifest['synthetic_boundary_case_passed']}/{manifest['synthetic_boundary_case_total']}, "
        f"raw_read={str(manifest['raw_dir_read_performed']).lower()}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
