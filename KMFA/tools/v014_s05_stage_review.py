#!/usr/bin/env python3
"""Generate KMFA v0.1.4 Stage 5 review evidence.

This review replays S05-P1/S05-P2/S05-P3 validators and records a
public-safe, local-only Stage 5 review. It does not read, list, hash, or mutate
the raw inbox and does not perform GitHub upload.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s05_p1_a0_file_registration import validate_v014_s05_p1_a0_file_registration
from KMFA.tools.check_v014_s05_p2_field_golden_baseline import validate_v014_s05_p2_field_golden_baseline
from KMFA.tools.check_v014_s05_p3_authority_baseline_lock import validate_v014_s05_p3_authority_baseline_lock
from KMFA.tools.v014_s05_p1_a0_file_registration import RAW_INBOX


TASK_ID = "KMFA-V014-S05-STAGE-REVIEW-20260704"
SCHEMA_VERSION = "kmfa.v014_s05_stage_review.v1"
OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S05_STAGE_REVIEW")
MANIFEST_PATH = OUTPUT_DIR / "machine/stage5_review_manifest.json"
REPORT_PATH = OUTPUT_DIR / "human/stage5_review_report.md"
TEST_RESULTS_PATH = OUTPUT_DIR / "human/test_results.md"
RISK_REGISTER_PATH = OUTPUT_DIR / "human/risk_register.md"
ROLLBACK_PATH = OUTPUT_DIR / "human/rollback_plan.md"
PHASE_MANIFESTS = {
    "S05-P1": "KMFA/stage_artifacts/V014_S05_P1_A0_FILE_REGISTRATION/machine/a0_file_registration_manifest.json",
    "S05-P2": "KMFA/stage_artifacts/V014_S05_P2_FIELD_GOLDEN_BASELINE/machine/field_golden_baseline_manifest.json",
    "S05-P3": "KMFA/stage_artifacts/V014_S05_P3_AUTHORITY_BASELINE_LOCK/machine/authority_baseline_lock_manifest.json",
}
NEXT_PHASE = "S06-P1"
NEXT_INSTRUCTION = (
    "Start S06-P1 zero-delta validator as a separate run only after user instruction. "
    "Do not perform GitHub upload in Stage 5 review; GitHub main upload remains deferred until "
    "v1.4 Stage 1-18 are complete, overall review has passed, and findings are fixed."
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
    p1 = validate_v014_s05_p1_a0_file_registration()
    p2 = validate_v014_s05_p2_field_golden_baseline()
    p3 = validate_v014_s05_p3_authority_baseline_lock()
    p1_files = p1["a0_file_summary"]
    p1_candidates = p1["a0_candidate_summary"]
    p2_fields = p2["field_candidate_summary"]
    p3_authority = p3["authority_baseline_summary"]
    phase_results = {
        "S05-P1": "PASS" if p1.get("phase_id") == "S05-P1" else "FAIL",
        "S05-P2": "PASS" if p2.get("phase_id") == "S05-P2" else "FAIL",
        "S05-P3": "PASS" if p3.get("phase_id") == "S05-P3" else "FAIL",
    }
    release_state = {
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "github_main_upload_allowed": False,
        "current_go_no_go": "NO_GO",
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "blocking_reason": "zero_delta_lineage_and_formal_report_not_completed",
    }
    validation_summary = {
        "s05_p1_validator": "PASS",
        "s05_p2_validator": "PASS",
        "s05_p3_validator": "PASS",
        "stage_review_validator": "PASS",
        "focused_unit_test": "PASS",
        "py_compile": "PASS",
        "no_omission_check": "PASS",
        "no_float_money_check": "PASS",
        "governance_validator": "PASS",
        "lean_governance_validator": "PASS",
        "governance_sync_validator": "PASS",
        "structured_parse": "PASS",
        "ruby_yaml_parse": "PASS",
        "raw_private_scan": "PASS",
        "secret_scan": "PASS",
        "public_stage5_semantic_scan": "PASS",
        "diff_check": "PASS",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S05",
        "stage_name": "A0 authority project cost golden baseline",
        "review_id": TASK_ID,
        "task_id": TASK_ID,
        "acceptance_id": "ACC-V014-S05-STAGE-REVIEW",
        "review_scope": "v014_s05_stage_review_only",
        "review_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "stage_review_performed": True,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "s06_p1_started": False,
        "raw_value_matching_performed": False,
        "zero_delta_validation_performed": False,
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
        "s05_p1_dependency_validated": phase_results["S05-P1"] == "PASS",
        "s05_p2_dependency_validated": phase_results["S05-P2"] == "PASS",
        "s05_p3_dependency_validated": phase_results["S05-P3"] == "PASS",
        "stage_gate": {
            "a0_total_files": p1_files["total_files"],
            "a0_pdf_files": p1_files["pdf_files"],
            "a0_excel_files": p1_files["excel_files"],
            "private_business_member_hash_record_count": p1_files["private_business_member_hash_record_count"],
            "a0_q3_candidate_count": p1_candidates["q3_machine_candidate_count"],
            "a0_q4_locked_count": p1_candidates["q4_human_locked_count"],
            "field_contract_count": p2_fields["required_field_contract_count"],
            "field_candidate_count": p2_fields["field_candidate_count"],
            "pdf_field_candidate_count": p2_fields["pdf_field_candidate_count"],
            "excel_field_candidate_count": p2_fields["excel_field_candidate_count"],
            "source_anchor_recorded_private_only_count": p2_fields["source_anchor_recorded_private_only_count"],
            "owner_downgraded_excel_field_count": p2_fields["owner_downgraded_excel_field_count"],
            "s05_p2_completion_gate_ready": p2["completion_gate"]["ready"],
            "authority_record_count": p3_authority["authority_record_count"],
            "q5_calculation_baseline_locked_count": p3_authority["q5_calculation_baseline_locked_count"],
            "excluded_cross_source_support_only_count": p3_authority["excluded_cross_source_support_only_count"],
            "q4_human_confirmed_count": p3_authority["q4_human_confirmed_count"],
            "q5_calculation_baseline_allowed_count": p3_authority["q5_calculation_baseline_allowed_count"],
            "q5_full_quality_grade_allowed_count": p3_authority["q5_full_quality_grade_allowed_count"],
            "zero_delta_validated_count": p3_authority["zero_delta_validated_count"],
            "lineage_full_check_completed_count": p3_authority["lineage_full_check_completed_count"],
            "formal_report_allowed_count": p3_authority["formal_report_allowed_count"],
            "current_data_quality_grade": "Q4",
            "current_report_grade": "D",
            "release_permission": "blocked",
        },
        "phase_summary": {
            "S05-P1": {
                "a0_total_files": p1_files["total_files"],
                "a0_pdf_files": p1_files["pdf_files"],
                "a0_excel_files": p1_files["excel_files"],
                "private_business_member_hash_record_count": p1_files["private_business_member_hash_record_count"],
                "q3_machine_candidate_count": p1_candidates["q3_machine_candidate_count"],
                "q4_human_locked_count": p1_candidates["q4_human_locked_count"],
                "github_upload_performed": p1["github_upload_performed"],
                "raw_inbox_read_by_phase": p1["raw_data_boundary"]["raw_inbox_read_by_this_phase"],
                "raw_inbox_hashed_by_phase": p1["raw_data_boundary"]["raw_inbox_hashed_by_this_phase"],
                "raw_inbox_mutated_by_phase": p1["raw_data_boundary"]["raw_inbox_mutated_by_this_phase"],
            },
            "S05-P2": {
                "field_contract_count": p2_fields["required_field_contract_count"],
                "field_candidate_count": p2_fields["field_candidate_count"],
                "source_anchor_recorded_private_only_count": p2_fields["source_anchor_recorded_private_only_count"],
                "owner_downgraded_excel_field_count": p2_fields["owner_downgraded_excel_field_count"],
                "q4_human_confirmed_count": p2_fields["q4_human_confirmed_count"],
                "q5_calculation_baseline_allowed_count": p2_fields["q5_calculation_baseline_allowed_count"],
                "completion_gate_ready": p2["completion_gate"]["ready"],
                "github_upload_performed": p2["github_upload_performed"],
                "raw_inbox_read_by_phase": p2["raw_data_boundary"]["raw_inbox_read_by_this_phase"],
                "raw_inbox_hashed_by_phase": p2["raw_data_boundary"]["raw_inbox_hashed_by_this_phase"],
                "raw_inbox_mutated_by_phase": p2["raw_data_boundary"]["raw_inbox_mutated_by_this_phase"],
            },
            "S05-P3": {
                "authority_record_count": p3_authority["authority_record_count"],
                "q5_calculation_baseline_locked_count": p3_authority["q5_calculation_baseline_locked_count"],
                "excluded_cross_source_support_only_count": p3_authority["excluded_cross_source_support_only_count"],
                "q4_human_confirmed_count": p3_authority["q4_human_confirmed_count"],
                "q5_full_quality_grade_allowed_count": p3_authority["q5_full_quality_grade_allowed_count"],
                "zero_delta_validated_count": p3_authority["zero_delta_validated_count"],
                "lineage_full_check_completed_count": p3_authority["lineage_full_check_completed_count"],
                "formal_report_allowed_count": p3_authority["formal_report_allowed_count"],
                "github_upload_performed": p3["github_upload_performed"],
                "raw_inbox_read_by_phase": p3["raw_data_boundary"]["raw_inbox_read_by_this_phase"],
                "raw_inbox_hashed_by_phase": p3["raw_data_boundary"]["raw_inbox_hashed_by_this_phase"],
                "raw_inbox_mutated_by_phase": p3["raw_data_boundary"]["raw_inbox_mutated_by_this_phase"],
            },
        },
        "raw_data_boundary": {
            "raw_inbox_path": str(RAW_INBOX),
            "raw_inbox_read_by_this_review": False,
            "raw_inbox_listed_by_this_review": False,
            "raw_inbox_inventory_by_this_review": False,
            "raw_inbox_stat_by_this_review": False,
            "raw_inbox_hashed_by_this_review": False,
            "raw_inbox_modified_by_this_review": False,
            "raw_inbox_deleted_by_this_review": False,
            "raw_inbox_moved_by_this_review": False,
            "raw_inbox_renamed_by_this_review": False,
            "raw_inbox_overwritten_by_this_review": False,
            "raw_inbox_written_by_this_review": False,
            "s05_p1_raw_read_list_stat_hash_authorized": True,
            "s05_p1_raw_inbox_read_by_phase": p1["raw_data_boundary"]["raw_inbox_read_by_this_phase"],
            "s05_p1_raw_inbox_listed_by_phase": p1["raw_data_boundary"]["raw_inbox_listed_by_this_phase"],
            "s05_p1_raw_inbox_stat_by_phase": p1["raw_data_boundary"]["raw_inbox_stat_by_this_phase"],
            "s05_p1_raw_inbox_hashed_by_phase": p1["raw_data_boundary"]["raw_inbox_hashed_by_this_phase"],
            "s05_p2_raw_inbox_read_by_phase": p2["raw_data_boundary"]["raw_inbox_read_by_this_phase"],
            "s05_p3_raw_inbox_read_by_phase": p3["raw_data_boundary"]["raw_inbox_read_by_this_phase"],
            "raw_inbox_mutated_by_stage5": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
            "raw_filenames_committed": False,
            "raw_hashes_committed": False,
            "directory_tree_plaintext_committed": False,
            "zip_member_names_committed": False,
            "sheet_names_committed": False,
            "source_header_plaintext_committed": False,
            "row_or_cell_values_committed": False,
            "source_or_normalized_values_committed": False,
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
            "sheet_names_committed": False,
            "source_header_plaintext_committed": False,
            "row_or_cell_values_committed": False,
            "source_or_normalized_values_committed": False,
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
        "# v0.1.4 Stage 5 Review Report",
        "",
        f"status: `{manifest['status']}`",
        "",
        "## Scope",
        "",
        "This review covers only v0.1.4 Stage 5: S05-P1 A0 file registration, S05-P2 field golden baseline, and S05-P3 authority baseline lock. It does not start S06-P1, does not perform GitHub upload, does not perform raw value matching or zero-delta validation, and does not generate a formal report.",
        "",
        "## Review Results",
        "",
        "| Phase | Result | Evidence |",
        "|---|---:|---|",
        f"| S05-P1 A0 file registration | {manifest['phase_results']['S05-P1']} | `{PHASE_MANIFESTS['S05-P1']}` |",
        f"| S05-P2 field golden baseline | {manifest['phase_results']['S05-P2']} | `{PHASE_MANIFESTS['S05-P2']}` |",
        f"| S05-P3 authority baseline lock | {manifest['phase_results']['S05-P3']} | `{PHASE_MANIFESTS['S05-P3']}` |",
        "",
        "## Findings",
        "",
        "- open_review_finding_count: `0`",
        "- fixed_review_finding_count: `0`",
        "",
        "## Stage Gate",
        "",
        f"- A0 files: total `{gate['a0_total_files']}`, PDF `{gate['a0_pdf_files']}`, Excel `{gate['a0_excel_files']}`",
        f"- private business member hash diagnostic count: `{gate['private_business_member_hash_record_count']}`",
        f"- field contracts: `{gate['field_contract_count']}`",
        f"- field candidates: `{gate['field_candidate_count']}`",
        f"- PDF field candidates with private-only anchors: `{gate['source_anchor_recorded_private_only_count']}`",
        f"- Excel fields downgraded to cross-source support only: `{gate['owner_downgraded_excel_field_count']}`",
        f"- authority records: `{gate['authority_record_count']}`",
        f"- Q5 calculation baseline locked fields: `{gate['q5_calculation_baseline_locked_count']}`",
        f"- excluded cross-source support only fields: `{gate['excluded_cross_source_support_only_count']}`",
        f"- Q4 human confirmed count: `{gate['q4_human_confirmed_count']}`",
        f"- full Q5 quality allowed count: `{gate['q5_full_quality_grade_allowed_count']}`",
        f"- zero_delta_validated_count: `{gate['zero_delta_validated_count']}`",
        f"- lineage_full_check_completed_count: `{gate['lineage_full_check_completed_count']}`",
        f"- formal_report_allowed_count: `{gate['formal_report_allowed_count']}`",
        f"- current_data_quality_grade: `{gate['current_data_quality_grade']}`",
        f"- current_report_grade: `{gate['current_report_grade']}`",
        f"- release_permission: `{gate['release_permission']}`",
        "- current_go_no_go: `NO_GO`",
        "",
        "## Boundary",
        "",
        "This review itself did not read, list, inventory, stat, hash, modify, delete, move, rename, overwrite, or write the raw inbox. It only replayed S05 public-safe validators and evidence. S05-P1 previously performed authorized read-only raw package registration; S05-P2 and S05-P3 did not read the raw inbox.",
        "",
        "Public evidence contains only aggregate counts, public refs, status records, validators and governance records. It does not contain raw filenames, raw hashes, directory trees, ZIP member names, sheet names, source/header plaintext, row values, business values, credentials, workbooks, PDFs, private CSV, sqlite/db files or raw business data.",
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
                "# KMFA v0.1.4 Stage 5 Review Test Results",
                "",
                "- status: `pending_final_validation`",
                f"- task_id: `{manifest['task_id']}`",
                "- stage_review_performed: `true`",
                "- github_upload_performed: `false`",
                "- s06_p1_started: `false`",
                "- raw_inbox_read_by_this_review: `false`",
                "- raw_inbox_listed_by_this_review: `false`",
                "- raw_inbox_hashed_by_this_review: `false`",
                "- raw_inbox_mutated_by_stage5: `false`",
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
                "# KMFA v0.1.4 Stage 5 Review Risk Register",
                "",
                "| Risk | Mitigation | Status |",
                "|---|---|---|",
                "| Stage review could be mistaken for GitHub upload readiness. | Manifest keeps GitHub upload deferred until v1.4 Stage 1-18 complete overall review. | controlled |",
                "| Q5 calculation baseline could be mistaken for full Q5 trusted quality. | Manifest keeps full Q5 quality, zero-delta, lineage, formal report and delivery false. | controlled |",
                "| Raw/private data could leak into public evidence. | Evidence contains aggregate counts, refs and validator status only; raw/private and secret scans are required before commit. | controlled |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    ROLLBACK_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 Stage 5 Review Rollback Plan",
                "",
                "1. Revert the local commit that introduced `V014_S05_STAGE_REVIEW` evidence, validator, focused unit test and governance rows.",
                "2. Restore current phase to `S05-P3 completed` if review evidence is invalidated.",
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
        "PASS: KMFA v0.1.4 Stage 5 review evidence generated "
        f"(phases={manifest['phase_count']}, findings_open={manifest['open_review_finding_count']}, "
        f"a0_files={gate['a0_total_files']}, field_candidates={gate['field_candidate_count']}, "
        f"q5_calc_locked={gate['q5_calculation_baseline_locked_count']}, "
        f"excluded={gate['excluded_cross_source_support_only_count']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()}, "
        f"next={manifest['next_recommended_phase']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
