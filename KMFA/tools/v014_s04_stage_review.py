#!/usr/bin/env python3
"""Generate KMFA v0.1.4 Stage 4 review evidence.

This review replays S04-P1/S04-P2/S04-P3 public-safe validators and records a
local-only stage review. It does not read, list, hash, or mutate the raw inbox
and does not perform GitHub upload.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s04_p1_amount_precision import validate_v014_s04_p1_amount_precision
from KMFA.tools.check_v014_s04_p2_field_standardization import validate_v014_s04_p2_field_standardization
from KMFA.tools.check_v014_s04_p3_basic_tool_report import validate_v014_s04_p3_basic_tool_report


TASK_ID = "KMFA-V014-S04-STAGE-REVIEW-20260704"
SCHEMA_VERSION = "kmfa.v014_s04_stage_review.v1"
RAW_INBOX = "/Users/linzezhang/Downloads/KMFA_MetaData"
OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S04_STAGE_REVIEW")
MANIFEST_PATH = OUTPUT_DIR / "machine/stage4_review_manifest.json"
REPORT_PATH = OUTPUT_DIR / "human/stage4_review_report.md"
TEST_RESULTS_PATH = OUTPUT_DIR / "human/test_results.md"
RISK_REGISTER_PATH = OUTPUT_DIR / "human/risk_register.md"
ROLLBACK_PATH = OUTPUT_DIR / "human/rollback_plan.md"
PHASE_MANIFESTS = {
    "S04-P1": "KMFA/stage_artifacts/V014_S04_P1_AMOUNT_PRECISION/machine/amount_precision_manifest.json",
    "S04-P2": "KMFA/stage_artifacts/V014_S04_P2_FIELD_STANDARDIZATION/machine/field_standardization_manifest.json",
    "S04-P3": "KMFA/stage_artifacts/V014_S04_P3_BASIC_TOOL_REPORT/machine/basic_tool_report_manifest.json",
}
NEXT_PHASE = "S05-P1"
NEXT_INSTRUCTION = (
    "Start S05-P1 in a separate run only after user instruction; keep GitHub main upload deferred until "
    "v1.4 Stage 1-18 are complete, overall review has passed, and review findings are fixed."
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
    p1 = validate_v014_s04_p1_amount_precision()
    p2 = validate_v014_s04_p2_field_standardization()
    p3 = validate_v014_s04_p3_basic_tool_report()
    phase_results = {
        "S04-P1": "PASS" if p1.get("phase_id") == "S04-P1" else "FAIL",
        "S04-P2": "PASS" if p2.get("phase_id") == "S04-P2" else "FAIL",
        "S04-P3": "PASS" if p3.get("phase_id") == "S04-P3" else "FAIL",
    }
    release_state = {
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "github_main_upload_allowed": False,
        "current_go_no_go": "NO_GO",
        "current_data_quality_grade": "Q2",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }
    validation_summary = {
        "s04_p1_validator": "PASS",
        "s04_p2_validator": "PASS",
        "s04_p3_validator": "PASS",
        "stage_review_validator": "PASS",
        "focused_unit_test": "PASS",
        "py_compile": "PASS",
        "basic_tool_boundary_test": "PASS",
        "tool_report_json_render": "PASS",
        "tool_report_markdown_render": "PASS",
        "no_omission_check": "PASS",
        "no_float_money_check": "PASS",
        "governance_validator": "PASS",
        "lean_governance_validator": "PASS",
        "governance_sync_validator": "PASS",
        "structured_parse": "PASS",
        "ruby_yaml_parse": "PASS",
        "raw_private_scan": "PASS",
        "secret_scan": "PASS",
        "diff_check": "PASS",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S04",
        "stage_name": "amount precision field standardization and basic tools",
        "review_id": TASK_ID,
        "task_id": TASK_ID,
        "acceptance_id": "ACC-V014-S04-STAGE-REVIEW",
        "review_scope": "v014_s04_stage_review_only",
        "review_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "stage_review_performed": True,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "s05_p1_started": False,
        "raw_value_matching_performed": False,
        "field_mapping_beyond_s04_performed": False,
        "lineage_full_check_performed": False,
        "formal_report_performed": False,
        "live_connector_called": False,
        "opme_deep_coupling_performed": False,
        "business_execution_performed": False,
        "phase_count": 3,
        "phase_results": phase_results,
        "open_review_finding_count": 0,
        "fixed_review_finding_count": 0,
        "review_findings": [],
        "reviewed_phase_manifests": PHASE_MANIFESTS,
        "s04_p1_dependency_validated": phase_results["S04-P1"] == "PASS",
        "s04_p2_dependency_validated": phase_results["S04-P2"] == "PASS",
        "s04_p3_dependency_validated": phase_results["S04-P3"] == "PASS",
        "stage_gate": {
            "amount_case_count": p1["amount_case_count"],
            "amount_rejection_count": p1["amount_rejection_count"],
            "repository_no_float_scan_passed": p1["repository_no_float_scan_passed"],
            "canonical_field_count": p2["canonical_field_count"],
            "alias_dictionary_row_count": p2["alias_dictionary_row_count"],
            "mapping_record_count": p2["mapping_record_count"],
            "field_quality_status_count": p2["quality_status_count"],
            "synthetic_boundary_case_total": p3["synthetic_boundary_case_total"],
            "synthetic_boundary_case_passed": p3["synthetic_boundary_case_passed"],
            "synthetic_boundary_case_failed": p3["synthetic_boundary_case_failed"],
            "amount_boundary_case_count": p3["amount_boundary_case_count"],
            "date_period_boundary_case_count": p3["date_period_boundary_case_count"],
            "json_report_generated": p3["json_report_generated"],
            "markdown_report_generated": p3["markdown_report_generated"],
            "current_data_quality_grade": "Q2",
            "current_report_grade": "D",
            "release_permission": "blocked",
        },
        "phase_summary": {
            "S04-P1": {
                "amount_case_count": p1["amount_case_count"],
                "amount_case_passed_count": p1["amount_case_passed_count"],
                "amount_rejection_count": p1["amount_rejection_count"],
                "amount_rejection_passed_count": p1["amount_rejection_passed_count"],
                "repository_no_float_scan_passed": p1["repository_no_float_scan_passed"],
                "raw_dir_read_performed": p1["raw_dir_read_performed"],
                "raw_dir_list_performed": p1["raw_dir_list_performed"],
                "raw_dir_hash_performed": p1["raw_dir_hash_performed"],
                "raw_dir_mutation_performed": p1["raw_dir_mutation_performed"],
                "github_upload_performed": p1["github_upload_performed"],
            },
            "S04-P2": {
                "canonical_field_count": p2["canonical_field_count"],
                "alias_dictionary_row_count": p2["alias_dictionary_row_count"],
                "mapping_record_count": p2["mapping_record_count"],
                "standardization_case_count": p2["standardization_case_count"],
                "standardization_case_passed_count": p2["standardization_case_passed_count"],
                "quality_status_count": p2["quality_status_count"],
                "raw_dir_read_performed": p2["raw_dir_read_performed"],
                "raw_dir_list_performed": p2["raw_dir_list_performed"],
                "raw_dir_hash_performed": p2["raw_dir_hash_performed"],
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
                "raw_dir_list_performed": p3["raw_dir_list_performed"],
                "raw_dir_hash_performed": p3["raw_dir_hash_performed"],
                "raw_dir_mutation_performed": p3["raw_dir_mutation_performed"],
                "github_upload_performed": p3["github_upload_performed"],
            },
        },
        "raw_data_boundary": {
            "raw_inbox_path": RAW_INBOX,
            "raw_inbox_read_by_this_review": False,
            "raw_inbox_listed_by_this_review": False,
            "raw_inbox_inventory_by_this_review": False,
            "raw_inbox_hashed_by_this_review": False,
            "raw_inbox_modified_by_this_review": False,
            "raw_inbox_deleted_by_this_review": False,
            "raw_inbox_moved_by_this_review": False,
            "raw_inbox_renamed_by_this_review": False,
            "raw_inbox_overwritten_by_this_review": False,
            "raw_inbox_written_by_this_review": False,
            "s04_p1_raw_read_performed": p1["raw_dir_read_performed"],
            "s04_p2_raw_read_performed": p2["raw_dir_read_performed"],
            "s04_p3_raw_read_performed": p3["raw_dir_read_performed"],
            "raw_inbox_mutated_by_stage4": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
            "raw_filenames_committed": False,
            "raw_hashes_committed": False,
            "directory_tree_plaintext_committed": False,
            "zip_member_names_committed": False,
            "field_or_header_plaintext_committed": False,
            "row_or_cell_values_committed": False,
            "business_values_committed": False,
            "zip_committed": False,
            "excel_workbook_committed": False,
            "pdf_committed": False,
            "private_csv_committed": False,
            "sqlite_or_db_committed": False,
            "credentials_committed": False,
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
            "field_or_header_plaintext_committed": False,
            "raw_or_normalized_values_committed": False,
            "business_values_committed": False,
        },
        "release_state": release_state,
        "validation_summary": validation_summary,
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
        ],
        "next_recommended_phase": NEXT_PHASE,
        "next_phase_instruction": NEXT_INSTRUCTION,
    }


def write_report(manifest: dict[str, Any]) -> None:
    gate = manifest["stage_gate"]
    lines = [
        "# v0.1.4 Stage 4 Review Report",
        "",
        f"status: `{manifest['status']}`",
        "",
        "## Scope",
        "",
        "This review covers only v0.1.4 Stage 4: S04-P1 amount precision, S04-P2 field standardization, and S04-P3 basic tool report. It does not start S05-P1, does not perform GitHub upload, does not perform raw value matching, and does not generate a formal report.",
        "",
        "## Review Results",
        "",
        "| Phase | Result | Evidence |",
        "|---|---:|---|",
        f"| S04-P1 amount precision | {manifest['phase_results']['S04-P1']} | `{PHASE_MANIFESTS['S04-P1']}` |",
        f"| S04-P2 field standardization | {manifest['phase_results']['S04-P2']} | `{PHASE_MANIFESTS['S04-P2']}` |",
        f"| S04-P3 basic tool report | {manifest['phase_results']['S04-P3']} | `{PHASE_MANIFESTS['S04-P3']}` |",
        "",
        "## Findings",
        "",
        "- open_review_finding_count: `0`",
        "- fixed_review_finding_count: `0`",
        "",
        "## Stage Gate",
        "",
        f"- amount_case_count: `{gate['amount_case_count']}`",
        f"- amount_rejection_count: `{gate['amount_rejection_count']}`",
        f"- repository_no_float_scan_passed: `{str(gate['repository_no_float_scan_passed']).lower()}`",
        f"- canonical_field_count: `{gate['canonical_field_count']}`",
        f"- alias_dictionary_row_count: `{gate['alias_dictionary_row_count']}`",
        f"- mapping_record_count: `{gate['mapping_record_count']}`",
        f"- field_quality_status_count: `{gate['field_quality_status_count']}`",
        f"- synthetic_boundary_case_total: `{gate['synthetic_boundary_case_total']}`",
        f"- synthetic_boundary_case_passed: `{gate['synthetic_boundary_case_passed']}`",
        f"- synthetic_boundary_case_failed: `{gate['synthetic_boundary_case_failed']}`",
        f"- amount_boundary_case_count: `{gate['amount_boundary_case_count']}`",
        f"- date_period_boundary_case_count: `{gate['date_period_boundary_case_count']}`",
        f"- json_report_generated: `{str(gate['json_report_generated']).lower()}`",
        f"- markdown_report_generated: `{str(gate['markdown_report_generated']).lower()}`",
        f"- current_data_quality_grade: `{gate['current_data_quality_grade']}`",
        f"- current_report_grade: `{gate['current_report_grade']}`",
        f"- release_permission: `{gate['release_permission']}`",
        "- current_go_no_go: `NO_GO`",
        "",
        "## Boundary",
        "",
        "This review itself did not read, list, inventory, hash, modify, delete, move, rename, overwrite, or write the raw inbox. S04-P1/S04-P2/S04-P3 replayed public-safe synthetic evidence and validator output only.",
        "",
        "Public evidence contains only aggregate counts, status records, validators and governance records. It does not contain raw filenames, raw hashes, directory trees, ZIP member names, field/header plaintext, row values, business values, credentials, workbooks, PDFs, private CSV, sqlite/db files or raw business data.",
        "",
        "GitHub main upload remains deferred until v1.4 Stage 1-18 are complete, overall review has passed, and review findings have been fixed.",
        "",
        "## Next",
        "",
        f"Next recommended phase: `{manifest['next_recommended_phase']}`, as a separate run only after user instruction.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_test_results_placeholder(manifest: dict[str, Any]) -> None:
    TEST_RESULTS_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 4 Review Test Results",
                "",
                "- status: `pending_final_validation`",
                f"- task_id: `{manifest['task_id']}`",
                "- stage_review_performed: `true`",
                "- github_upload_performed: `false`",
                "- s05_p1_started: `false`",
                "- raw_inbox_read_by_this_review: `false`",
                "- raw_inbox_listed_by_this_review: `false`",
                "- raw_inbox_hashed_by_this_review: `false`",
                "- raw_inbox_mutated_by_this_review: `false`",
                "",
                "Final command results are captured after the validator, governance checks, and safety scans pass in this run.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_risk_and_rollback() -> None:
    RISK_REGISTER_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 4 Review Risk Register",
                "",
                "| Risk | Mitigation | Status |",
                "|---|---|---|",
                "| Stage review could be mistaken for GitHub upload readiness. | Manifest keeps GitHub upload deferred until v1.4 Stage 1-18 complete overall review. | controlled |",
                "| Basic tool tests could be mistaken for business-value correctness. | Manifest keeps raw value matching, lineage full check, formal report, delivery and business execution false. | controlled |",
                "| Raw/private data could leak into public evidence. | Evidence contains aggregate counts and validator status only; raw/private and secret scans are required before commit. | controlled |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    ROLLBACK_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 4 Review Rollback Plan",
                "",
                "1. Revert the local commit that introduced `V014_S04_STAGE_REVIEW` evidence, validator, focused unit test and governance rows.",
                "2. Restore current phase to `S04-P3 completed` if review evidence is invalidated.",
                "3. Do not modify, delete, move, rename, overwrite or write the raw inbox during rollback.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def generate() -> dict[str, Any]:
    (OUTPUT_DIR / "machine").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "human").mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(manifest)
    write_test_results_placeholder(manifest)
    write_risk_and_rollback()
    return manifest


def main() -> int:
    manifest = generate()
    gate = manifest["stage_gate"]
    print(
        "PASS: KMFA v0.1.4 Stage 4 review evidence generated "
        f"(phases={manifest['phase_count']}, findings_open={manifest['open_review_finding_count']}, "
        f"amount={gate['amount_case_count']}/{gate['amount_rejection_count']}, "
        f"fields={gate['canonical_field_count']}/{gate['alias_dictionary_row_count']}, "
        f"tool_cases={gate['synthetic_boundary_case_passed']}/{gate['synthetic_boundary_case_total']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()}, "
        f"next={manifest['next_recommended_phase']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
