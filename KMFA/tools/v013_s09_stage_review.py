#!/usr/bin/env python3
"""Generate KMFA v0.1.3 Stage 9 review evidence.

This review reruns the public-safe v0.1.3 S09-P1/S09-P2/S09-P3 replay
validators and records the stage-level gate. It does not read or write the
local raw data inbox, does not enter Stage 10, and does not perform GitHub
upload.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s09_p1_project_cost_fact_layer_replay import (
    validate_v013_s09_p1_project_cost_fact_layer_replay,
)
from KMFA.tools.check_v013_s09_p2_margin_cash_margin_replay import (
    validate_v013_s09_p2_margin_cash_margin_replay,
)
from KMFA.tools.check_v013_s09_p3_scope_reconciliation_replay import (
    validate_v013_s09_p3_scope_reconciliation_replay,
)


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S09_STAGE_REVIEW")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/stage9_review_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/stage9_review_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
S09_P1_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S09_P1_PROJECT_COST_FACT_LAYER_REPLAY/machine/"
    "project_cost_fact_layer_replay_manifest.json"
)
S09_P2_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S09_P2_MARGIN_CASH_MARGIN_REPLAY/machine/"
    "margin_cash_margin_replay_manifest.json"
)
S09_P3_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S09_P3_SCOPE_RECONCILIATION_REPLAY/machine/"
    "scope_reconciliation_replay_manifest.json"
)
LEGACY_STAGE9_REVIEW_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/S09_STAGE_REVIEW/machine/stage9_review_manifest.json"
)
TASK_ID = "KMFA-V013-S09-STAGE-REVIEW-20260703"
SCHEMA_VERSION = "kmfa.v013_s09_stage_review.v1"
REVIEW_SCOPE = "v013_s09_stage_review_only"
RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 S10-P1 as a separate run. GitHub main upload remains deferred until "
    "v0.1.3 Stages 1-10 are complete, the whole Stage 1-10 review passes, and findings are fixed; "
    "do not run GitHub upload, raw value matching, lineage full check, formal report release, "
    "live connector, Redcircle automatic connector, or business execution in the Stage 9 review run."
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
        raise RuntimeError(f"{path} must contain a JSON object")
    return value


def _false_count(*values: bool) -> int:
    return sum(1 for value in values if value is False)


def build_manifest() -> dict[str, Any]:
    p1 = validate_v013_s09_p1_project_cost_fact_layer_replay()
    p2 = validate_v013_s09_p2_margin_cash_margin_replay()
    p3 = validate_v013_s09_p3_scope_reconciliation_replay()
    legacy_review = read_json(LEGACY_STAGE9_REVIEW_MANIFEST_PATH)

    phase_results = {
        "S09-P1": "PASS" if p1.get("phase_id") == "S09-P1" else "FAIL",
        "S09-P2": "PASS" if p2.get("phase_id") == "S09-P2" else "FAIL",
        "S09-P3": "PASS" if p3.get("phase_id") == "S09-P3" else "FAIL",
    }
    formal_calculation_allowed_count = 0 if p1["formal_calculation_allowed"] is False else 1
    formal_report_allowed_count = 3 - _false_count(
        p1["formal_report_allowed"],
        p2["formal_report_allowed"],
        p3["formal_report_allowed"],
    )
    derived_metric_rerun_allowed_count = 0 if p3["derived_metric_rerun_allowed"] is False else 1
    formal_report_rerun_allowed_count = 0 if p3["formal_report_rerun_allowed"] is False else 1
    raw_read_count = 3 - _false_count(
        p1["raw_dir_read_performed"],
        p2["raw_dir_read_performed"],
        p3["raw_dir_read_performed"],
    )
    raw_mutation_count = 3 - _false_count(
        p1["raw_dir_mutation_performed"],
        p2["raw_dir_mutation_performed"],
        p3["raw_dir_mutation_performed"],
    )
    github_upload_count = 3 - _false_count(
        p1["github_upload_performed"],
        p2["github_upload_performed"],
        p3["github_upload_performed"],
    )
    review_findings = [
        {
            "finding_id": "KMFA-V013-S09-REV-F01",
            "severity": "P2",
            "status": "fixed",
            "summary": (
                "Legacy Stage 9 upload-ready wording exists in historical v1.2 artifacts; current "
                "v0.1.3 Stage 9 review explicitly treats those artifacts as non-current and keeps "
                "GitHub upload deferred until the Stage 1-10 batch gate."
            ),
        },
        {
            "finding_id": "KMFA-V013-S09-REV-F02",
            "severity": "P2",
            "status": "passed",
            "summary": (
                "S09-P1, S09-P2 and S09-P3 replay validators all pass with public-safe evidence, "
                "pending reconciliation blockers and no formal report permission."
            ),
        },
    ]
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "business_amount_values_remain_private_ref_or_hash_only",
        "project_cost_fact_layer_formal_calculation_blocked",
        "pending_reconciliation_blocks_derived_metric_rerun",
        "confirmed_resolution_count_zero_blocks_rerun",
        "formal_report_release_blocked",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "github_upload_deferred_until_stage10_batch",
        "s10_p1_not_performed",
        "business_execution_blocked",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S09",
        "stage_name": "v0.1.3 project cost fact layer and reconciliation",
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
        "s10_p1_performed": False,
        "github_upload_ready_next_gate": False,
        "github_upload_deferred_until_stage10_batch": True,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_stage10_batch",
        "legacy_stage9_review_artifacts_validated": legacy_review.get("stage") == "S09",
        "legacy_stage9_upload_artifacts_current_gate": False,
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "lineage_full_check_completed": False,
        "raw_value_matching_performed": False,
        "raw_dir_read_performed_by_stage_review": False,
        "raw_dir_read_performed_by_dependency_validators": raw_read_count > 0,
        "raw_dir_mutation_performed": raw_mutation_count > 0,
        "phase_count": 3,
        "phase_results": phase_results,
        "s09_p1_dependency_validated": phase_results["S09-P1"] == "PASS",
        "s09_p2_dependency_validated": phase_results["S09-P2"] == "PASS",
        "s09_p3_dependency_validated": phase_results["S09-P3"] == "PASS",
        "reviewed_phase_manifests": {
            "S09-P1": S09_P1_MANIFEST_PATH.as_posix(),
            "S09-P2": S09_P2_MANIFEST_PATH.as_posix(),
            "S09-P3": S09_P3_MANIFEST_PATH.as_posix(),
            "legacy_S09_review": LEGACY_STAGE9_REVIEW_MANIFEST_PATH.as_posix(),
        },
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "review_findings": review_findings,
        "open_review_finding_count": 0,
        "fixed_review_finding_count": 1,
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "formal_calculation_allowed_count": formal_calculation_allowed_count,
        "formal_report_allowed_count": formal_report_allowed_count,
        "derived_metric_rerun_allowed_count": derived_metric_rerun_allowed_count,
        "formal_report_rerun_allowed_count": formal_report_rerun_allowed_count,
        "github_upload_count": github_upload_count,
        "pending_resolution_count": p3["pending_resolution_count"],
        "confirmed_resolution_count": p3["confirmed_resolution_count"],
        "phase_summary": {
            "S09-P1": {
                "required_metric_count": p1["required_metric_count"],
                "cost_category_count": p1["cost_category_count"],
                "fact_record_count": p1["fact_record_count"],
                "unallocated_pool_count": p1["unallocated_pool_count"],
                "authority_locked_field_count": p1["authority_locked_field_count"],
                "authority_excluded_field_count": p1["authority_excluded_field_count"],
                "business_entity_type_count": p1["business_entity_type_count"],
                "manual_review_queue_count": p1["manual_review_queue_count"],
                "unresolved_difference_count": p1["unresolved_difference_count"],
                "zero_delta_fail_count": p1["zero_delta_fail_count"],
                "blocked_quality_result_count": p1["blocked_quality_result_count"],
                "formal_calculation_allowed": p1["formal_calculation_allowed"],
                "formal_report_allowed": p1["formal_report_allowed"],
                "raw_dir_read_performed": p1["raw_dir_read_performed"],
                "raw_dir_mutation_performed": p1["raw_dir_mutation_performed"],
                "github_upload_performed": p1["github_upload_performed"],
            },
            "S09-P2": {
                "required_margin_metric_count": p2["required_margin_metric_count"],
                "project_cost_fact_record_count": p2["project_cost_fact_record_count"],
                "margin_record_count": p2["margin_record_count"],
                "difference_summary_count": p2["difference_summary_count"],
                "authority_field_group_count": p2["authority_field_group_count"],
                "upstream_manual_review_queue_count": p2["upstream_manual_review_queue_count"],
                "upstream_unresolved_difference_count": p2["upstream_unresolved_difference_count"],
                "zero_delta_fail_count": p2["zero_delta_fail_count"],
                "blocked_quality_result_count": p2["blocked_quality_result_count"],
                "authority_system_overwrite_allowed_count": p2["authority_system_overwrite_allowed_count"],
                "public_amount_values_committed_count": p2["public_amount_values_committed_count"],
                "formal_report_allowed": p2["formal_report_allowed"],
                "raw_dir_read_performed": p2["raw_dir_read_performed"],
                "raw_dir_mutation_performed": p2["raw_dir_mutation_performed"],
                "github_upload_performed": p2["github_upload_performed"],
            },
            "S09-P3": {
                "reconciliation_record_count": p3["reconciliation_record_count"],
                "domain_control_count": p3["domain_control_count"],
                "required_reconciliation_domain_count": p3["required_reconciliation_domain_count"],
                "upstream_margin_record_count": p3["upstream_margin_record_count"],
                "source_difference_summary_count": p3["source_difference_summary_count"],
                "reconciliation_records_by_domain": p3["reconciliation_records_by_domain"],
                "confirmed_resolution_count": p3["confirmed_resolution_count"],
                "pending_resolution_count": p3["pending_resolution_count"],
                "derived_metric_rerun_allowed": p3["derived_metric_rerun_allowed"],
                "formal_report_rerun_allowed": p3["formal_report_rerun_allowed"],
                "formal_report_allowed": p3["formal_report_allowed"],
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
            "source_record_payload_committed": False,
            "normalized_source_values_committed": False,
            "business_amount_values_committed": False,
            "project_or_customer_plaintext_committed": False,
            "business_fact_values_committed": False,
            "scope_reconciliation_business_values_committed": False,
            "formal_report_committed": False,
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s09_p1_project_cost_fact_layer_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s09_p2_margin_cash_margin_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s09_p3_scope_reconciliation_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s09_p1_project_cost_fact_layer.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s09_p2_margin_cash_margin.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s09_p3_scope_reconciliation.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s09_stage_review.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s09_stage_review.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_s09_stage_review.py",
            "KMFA/tools/check_v013_s09_stage_review.py",
            "KMFA/tests/test_v013_s09_stage_review.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.3 Stage 9 Review",
        "",
        f"- review_id: `{manifest['review_id']}`",
        f"- status: `{manifest['status']}`",
        f"- review_scope: `{manifest['review_scope']}`",
        f"- phase_results: `{json.dumps(manifest['phase_results'], ensure_ascii=False, sort_keys=True)}`",
        f"- open_review_finding_count: `{manifest['open_review_finding_count']}`",
        f"- fixed_review_finding_count: `{manifest['fixed_review_finding_count']}`",
        f"- formal_calculation_allowed_count: `{manifest['formal_calculation_allowed_count']}`",
        f"- formal_report_allowed_count: `{manifest['formal_report_allowed_count']}`",
        f"- derived_metric_rerun_allowed_count: `{manifest['derived_metric_rerun_allowed_count']}`",
        f"- pending_resolution_count: `{manifest['pending_resolution_count']}`",
        f"- current_data_quality_grade: `{manifest['current_data_quality_grade']}`",
        f"- current_report_grade: `{manifest['current_report_grade']}`",
        f"- release_permission: `{manifest['release_permission']}`",
        "",
        "## Boundary",
        "",
        f"- stage_review_performed: `{str(manifest['stage_review_performed']).lower()}`",
        f"- s10_p1_performed: `{str(manifest['s10_p1_performed']).lower()}`",
        f"- github_upload_deferred_until_stage10_batch: `{str(manifest['github_upload_deferred_until_stage10_batch']).lower()}`",
        f"- github_upload_performed: `{str(manifest['github_upload_performed']).lower()}`",
        f"- legacy_stage9_upload_artifacts_current_gate: `{str(manifest['legacy_stage9_upload_artifacts_current_gate']).lower()}`",
        f"- delivery_allowed: `{str(manifest['delivery_allowed']).lower()}`",
        f"- formal_report_allowed: `{str(manifest['formal_report_allowed']).lower()}`",
        f"- business_execution_allowed: `{str(manifest['business_execution_allowed']).lower()}`",
        "",
        "## Raw Data Boundary",
        "",
        f"- local_raw_data_dir: `{RAW_DIR}`",
        "- codex_read_required_by_this_stage_review: `false`",
        "- codex_read_performed_by_this_stage_review: `false`",
        "- codex_modify_allowed: `false`",
        "- codex_delete_allowed: `false`",
        "- codex_move_allowed: `false`",
        "- codex_rename_allowed: `false`",
        "- codex_generate_inside_allowed: `false`",
        "- github_commit_allowed: `false`",
        "",
        "This Stage 9 review did not enumerate, copy, modify, move, rename, delete, overwrite, or write generated files inside the local finance inbox.",
        "",
        "## Findings",
        "",
    ]
    for finding in manifest["review_findings"]:
        lines.append(f"- `{finding['finding_id']}` {finding['status']}: {finding['summary']}")
    lines.extend(
        [
            "",
            "## Next Step",
            "",
            manifest["next_required_step"],
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_pending_test_results(manifest: dict[str, Any]) -> None:
    lines = [
        "# KMFA v0.1.3 Stage 9 Review Test Results",
        "",
        f"- review_id: `{manifest['review_id']}`",
        "- status: `pending_final_validation_local_only`",
        "- github_upload_performed: `false`",
        "- raw_dir_read_performed_by_this_stage_review: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- s10_p1_performed: `false`",
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
    write_pending_test_results(manifest)
    return manifest


def main() -> int:
    manifest = generate()
    print(
        "PASS: KMFA v0.1.3 Stage 9 review generated "
        f"(phase_results={manifest['phase_results']}, "
        f"open_findings={manifest['open_review_finding_count']}, "
        f"pending_resolutions={manifest['pending_resolution_count']}, "
        "s10_p1=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
