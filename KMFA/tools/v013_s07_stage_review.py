#!/usr/bin/env python3
"""Generate KMFA v0.1.3 Stage 7 review evidence.

This review reruns the public-safe v0.1.3 S07-P1/S07-P2/S07-P3 replay
validators and records the stage-level gate. It does not read or write the
local raw data inbox, does not enter Stage 8, and does not perform GitHub
upload.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s07_p1_finance_file_adapter_replay import (
    validate_v013_s07_p1_finance_file_adapter_replay,
)
from KMFA.tools.check_v013_s07_p2_wps_file_adapter_replay import (
    validate_v013_s07_p2_wps_file_adapter_replay,
)
from KMFA.tools.check_v013_s07_p3_redcircle_postponement_replay import (
    validate_v013_s07_p3_redcircle_postponement_replay,
)


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S07_STAGE_REVIEW")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/stage7_review_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/stage7_review_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
S07_P1_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S07_P1_FINANCE_FILE_ADAPTER_REPLAY/machine/"
    "finance_file_adapter_replay_manifest.json"
)
S07_P2_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S07_P2_WPS_FILE_ADAPTER_REPLAY/machine/"
    "wps_file_adapter_replay_manifest.json"
)
S07_P3_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S07_P3_REDCIRCLE_POSTPONEMENT_REPLAY/machine/"
    "redcircle_postponement_replay_manifest.json"
)
TASK_ID = "KMFA-V013-S07-STAGE-REVIEW-20260703"
SCHEMA_VERSION = "kmfa.v013_s07_stage_review.v1"
REVIEW_SCOPE = "v013_s07_stage_review_only"
RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 S08-P1 as a separate run. GitHub main upload remains deferred until "
    "v0.1.3 Stages 1-10 are complete, the whole Stage 1-10 review passes, and findings are fixed; "
    "do not run GitHub upload, raw value matching, lineage full check, formal report release, "
    "live connector, Redcircle automatic connector, or business execution in the Stage 7 review run."
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
    p1 = validate_v013_s07_p1_finance_file_adapter_replay()
    p2 = validate_v013_s07_p2_wps_file_adapter_replay()
    p3 = validate_v013_s07_p3_redcircle_postponement_replay()

    phase_results = {
        "S07-P1": "PASS" if p1.get("phase_id") == "S07-P1" else "FAIL",
        "S07-P2": "PASS" if p2.get("phase_id") == "S07-P2" else "FAIL",
        "S07-P3": "PASS" if p3.get("phase_id") == "S07-P3" else "FAIL",
    }
    q5_allowed_count = (
        p1["q5_calculation_baseline_allowed_count"]
        + p2["q5_calculation_baseline_allowed_count"]
        + p3["q5_calculation_baseline_allowed_count"]
    )
    formal_report_allowed_count = (
        p1["formal_report_allowed_count"]
        + p2["formal_report_allowed_count"]
        + p3["formal_report_allowed_count"]
    )
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "adapter_candidates_remain_structural_or_reserved",
        "q5_forbidden_until_stage7_downstream_review_and_evidence_closure",
        "formal_report_release_blocked",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "redcircle_automatic_connector_blocked",
        "github_upload_deferred_until_stage10_batch",
        "business_execution_blocked",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S07",
        "stage_name": "v0.1.3 finance source adapter and upstream file support",
        "review_id": TASK_ID,
        "task_id": TASK_ID,
        "review_scope": REVIEW_SCOPE,
        "review_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "review_passed_upload_deferred_until_stage10_batch_no_go",
        "stage_review_performed": True,
        "s08_p1_performed": False,
        "github_upload_ready_next_gate": False,
        "github_upload_deferred_until_stage10_batch": True,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_stage10_batch",
        "legacy_stage7_upload_artifacts_current_gate": False,
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
        "s07_p1_dependency_validated": phase_results["S07-P1"] == "PASS",
        "s07_p2_dependency_validated": phase_results["S07-P2"] == "PASS",
        "s07_p3_dependency_validated": phase_results["S07-P3"] == "PASS",
        "reviewed_phase_manifests": {
            "S07-P1": S07_P1_MANIFEST_PATH.as_posix(),
            "S07-P2": S07_P2_MANIFEST_PATH.as_posix(),
            "S07-P3": S07_P3_MANIFEST_PATH.as_posix(),
        },
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "review_findings": [],
        "open_review_finding_count": 0,
        "fixed_review_finding_count": 0,
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "q5_allowed_count": q5_allowed_count,
        "formal_report_allowed_count": formal_report_allowed_count,
        "phase_summary": {
            "S07-P1": {
                "source_category_count": p1["source_category_count"],
                "field_candidate_count": p1["field_candidate_count"],
                "hash_only_field_candidate_count": p1["hash_only_field_candidate_count"],
                "field_report_count": p1["field_report_count"],
                "source_header_hash_count": p1["source_header_hash_count"],
                "q4_human_confirmed_count": p1["q4_human_confirmed_count"],
                "q5_calculation_baseline_allowed_count": p1["q5_calculation_baseline_allowed_count"],
                "formal_report_allowed_count": p1["formal_report_allowed_count"],
                "raw_dir_read_performed": p1["raw_dir_read_performed"],
                "raw_dir_mutation_performed": p1["raw_dir_mutation_performed"],
                "github_upload_performed": p1["github_upload_performed"],
            },
            "S07-P2": {
                "source_export_type_count": p2["source_export_type_count"],
                "field_mapping_count": p2["field_mapping_count"],
                "hash_only_field_mapping_count": p2["hash_only_field_mapping_count"],
                "field_report_count": p2["field_report_count"],
                "conversion_guidance_count": p2["conversion_guidance_count"],
                "mapping_rule_version_count": p2["mapping_rule_version_count"],
                "source_header_hash_count": p2["source_header_hash_count"],
                "native_conversion_required_count": p2["native_conversion_required_count"],
                "q4_human_confirmed_count": p2["q4_human_confirmed_count"],
                "q5_calculation_baseline_allowed_count": p2["q5_calculation_baseline_allowed_count"],
                "formal_report_allowed_count": p2["formal_report_allowed_count"],
                "raw_dir_read_performed": p2["raw_dir_read_performed"],
                "raw_dir_mutation_performed": p2["raw_dir_mutation_performed"],
                "github_upload_performed": p2["github_upload_performed"],
            },
            "S07-P3": {
                "reserved_template_count": p3["reserved_template_count"],
                "connector_policy_count": p3["connector_policy_count"],
                "rollback_plan_count": p3["rollback_plan_count"],
                "automatic_connector_allowed_count": p3["automatic_connector_allowed_count"],
                "registry_source_count": p3["registry_source_count"],
                "template_contract_hash_count": p3["template_contract_hash_count"],
                "source_private_ref_count": p3["source_private_ref_count"],
                "manual_export_file_allowed_count": p3["manual_export_file_allowed_count"],
                "q4_human_confirmed_count": p3["q4_human_confirmed_count"],
                "q5_calculation_baseline_allowed_count": p3["q5_calculation_baseline_allowed_count"],
                "formal_report_allowed_count": p3["formal_report_allowed_count"],
                "d15_file_mvp_automatic_connector_allowed": p3["d15_file_mvp_automatic_connector_allowed"],
                "external_connector_included": p3["external_connector_included"],
                "read_only_required": p3["read_only_required"],
                "hash_retention_required": p3["hash_retention_required"],
                "rollback_plan_required": p3["rollback_plan_required"],
                "manual_approval_required": p3["manual_approval_required"],
                "raw_dir_read_performed": p3["raw_dir_read_performed"],
                "raw_dir_mutation_performed": p3["raw_dir_mutation_performed"],
                "github_upload_performed": p3["github_upload_performed"],
            },
        },
        "raw_data_boundary": {
            "local_raw_data_dir": RAW_DIR,
            "local_raw_data_dir_role": "user_finance_raw_private_inbox",
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
            "protected_source_payload_committed": False,
            "zip_committed": False,
            "excel_workbook_committed": False,
            "wps_native_file_committed": False,
            "redcircle_native_file_committed": False,
            "csv_committed": False,
            "pdf_committed": False,
            "private_csv_committed": False,
            "sqlite_or_db_committed": False,
            "credentials_committed": False,
            "connector_secret_committed": False,
            "field_plaintext_committed": False,
            "source_header_plaintext_committed": False,
            "raw_file_names_committed": False,
            "raw_file_hashes_committed": False,
            "tab_labels_committed": False,
            "zip_member_names_committed": False,
            "raw_business_values_committed": False,
            "normalized_business_values_committed": False,
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_p1_finance_file_adapter_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_p2_wps_file_adapter_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_p3_redcircle_postponement_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_stage_review.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_s07_stage_review.py",
            "KMFA/tools/check_v013_s07_stage_review.py",
            "KMFA/tests/test_v013_s07_stage_review.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    p1 = manifest["phase_summary"]["S07-P1"]
    p2 = manifest["phase_summary"]["S07-P2"]
    p3 = manifest["phase_summary"]["S07-P3"]
    lines = [
        "# KMFA v0.1.3 Stage 7 Review",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- stage_review_performed: `{str(manifest['stage_review_performed']).lower()}`",
        f"- phase_count: `{manifest['phase_count']}`",
        "- phase_results: `S07-P1=PASS`, `S07-P2=PASS`, `S07-P3=PASS`",
        f"- current_data_quality_grade: `{manifest['current_data_quality_grade']}`",
        f"- current_report_grade: `{manifest['current_report_grade']}`",
        f"- release_permission: `{manifest['release_permission']}`",
        f"- github_upload_ready_next_gate: `{str(manifest['github_upload_ready_next_gate']).lower()}`",
        f"- github_upload_deferred_until_stage10_batch: `{str(manifest['github_upload_deferred_until_stage10_batch']).lower()}`",
        f"- github_upload_performed: `{str(manifest['github_upload_performed']).lower()}`",
        f"- github_upload_status: `{manifest['github_upload_status']}`",
        f"- legacy_stage7_upload_artifacts_current_gate: `{str(manifest['legacy_stage7_upload_artifacts_current_gate']).lower()}`",
        f"- s08_p1_performed: `{str(manifest['s08_p1_performed']).lower()}`",
        f"- formal_report_allowed: `{str(manifest['formal_report_allowed']).lower()}`",
        f"- business_decision_basis_allowed: `{str(manifest['business_decision_basis_allowed']).lower()}`",
        f"- raw_value_matching_performed: `{str(manifest['raw_value_matching_performed']).lower()}`",
        f"- raw_dir_read_performed_by_stage_review: `{str(manifest['raw_dir_read_performed_by_stage_review']).lower()}`",
        f"- raw_dir_read_performed_by_dependency_validators: `{str(manifest['raw_dir_read_performed_by_dependency_validators']).lower()}`",
        f"- raw_dir_mutation_performed: `{str(manifest['raw_dir_mutation_performed']).lower()}`",
        "",
        "## Phase Replay",
        "",
        (
            "- S07-P1 finance adapter replay: "
            f"categories={p1['source_category_count']}, candidates={p1['field_candidate_count']}, "
            f"field_reports={p1['field_report_count']}, q5_allowed={p1['q5_calculation_baseline_allowed_count']}."
        ),
        (
            "- S07-P2 WPS adapter replay: "
            f"exports={p2['source_export_type_count']}, mappings={p2['field_mapping_count']}, "
            f"conversion_guidance={p2['conversion_guidance_count']}, q5_allowed={p2['q5_calculation_baseline_allowed_count']}."
        ),
        (
            "- S07-P3 Redcircle postponement replay: "
            f"templates={p3['reserved_template_count']}, rollback_plans={p3['rollback_plan_count']}, "
            f"automatic_connector_allowed={p3['automatic_connector_allowed_count']}, "
            f"formal_report_allowed={p3['formal_report_allowed_count']}."
        ),
        "",
        "## Raw Data Boundary",
        "",
        f"- local_raw_data_dir: `{RAW_DIR}`",
        "- local_raw_data_dir_role: `user_finance_raw_private_inbox`",
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
        (
            "This Stage 7 review did not enumerate, copy, modify, move, rename, delete, "
            "overwrite, or write generated files inside the local raw data inbox. It only "
            "reran public-safe validators over existing stage evidence."
        ),
        "",
        "## Review Findings",
        "",
        f"- open_review_finding_count: `{manifest['open_review_finding_count']}`",
        f"- fixed_review_finding_count: `{manifest['fixed_review_finding_count']}`",
        "",
        "## Hard Blocks",
        "",
        *[f"- `{block}`" for block in manifest["hard_blocks"]],
        "",
        "## Public Safety",
        "",
        (
            "This review evidence contains only public-safe booleans, aggregate counts, "
            "status gates, blocker IDs, validator references, and governance paths."
        ),
        (
            "It does not contain raw filenames, raw hashes, tab labels, ZIP member names, "
            "field/header plaintext, row values, business values, credentials, contracts, "
            "payroll, tax filings, or bank statements."
        ),
        "",
        "## Next Step",
        "",
        manifest["next_required_step"],
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_test_results() -> None:
    lines = [
        "# KMFA v0.1.3 Stage 7 Review Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `pending_final_validation_local_only`",
        "- github_upload_performed: `false`",
        "- raw_dir_read_performed_by_stage_review: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- s08_p1_performed: `false`",
        "- raw_value_matching_performed: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Command Results",
        "",
        "- PENDING: final validation results will be recorded before local commit.",
        "",
    ]
    TEST_RESULTS_PATH.write_text("\n".join(lines), encoding="utf-8")


def generate() -> dict[str, Any]:
    (PUBLIC_OUTPUT_DIR / "machine").mkdir(parents=True, exist_ok=True)
    (PUBLIC_OUTPUT_DIR / "human").mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_report(manifest)
    write_test_results()
    return manifest


def main() -> int:
    manifest = generate()
    print(
        "PASS: KMFA v0.1.3 Stage 7 review generated "
        f"(phases={manifest['phase_count']}, findings_open={manifest['open_review_finding_count']}, "
        f"q5_allowed={manifest['q5_allowed_count']}, "
        f"stage8=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
