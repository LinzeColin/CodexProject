#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S09-P1 project cost fact layer replay evidence.

This replay validates the v0.1.3 Stage 8 review dependency, reuses the
public-safe legacy S09-P1 project cost fact layer artifacts, and records the
phase-level no-go / upload-deferred boundary for the v0.1.3 Stage 1-10 run.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s08_stage_review import validate_v013_s08_stage_review
from KMFA.tools.project_cost_fact_layer import (
    DEFAULT_OUTPUT_FACT_RECORDS as LEGACY_FACT_RECORDS_PATH,
    DEFAULT_OUTPUT_MANIFEST as LEGACY_FACT_LAYER_MANIFEST_PATH,
    DEFAULT_OUTPUT_STAGE_MANIFEST as LEGACY_STAGE_MANIFEST_PATH,
    DEFAULT_OUTPUT_UNALLOCATED_POOL as LEGACY_UNALLOCATED_POOL_PATH,
    REQUIRED_COST_CATEGORIES,
    REQUIRED_FACT_METRICS,
    read_json,
    read_jsonl,
    validate_project_cost_fact_layer_artifacts,
)


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S09_P1_PROJECT_COST_FACT_LAYER_REPLAY")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/project_cost_fact_layer_replay_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/project_cost_fact_layer_replay_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
TASK_ID = "KMFA-V013-S09-P1-PROJECT-COST-FACT-LAYER-REPLAY-20260703"
SCHEMA_VERSION = "kmfa.v013_s09_p1_project_cost_fact_layer_replay.v1"
PHASE_SCOPE = "v013_s09_p1_project_cost_fact_layer_replay_only"
RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 S09-P2 as a separate run. GitHub main upload remains deferred until "
    "v0.1.3 Stages 1-10 are complete, the whole Stage 1-10 review passes, and findings are fixed; "
    "do not run S09-P3, Stage 9 review, GitHub upload, raw value matching, lineage full check, "
    "formal report release, live connector, Redcircle automatic connector, or business execution "
    "in the S09-P1 run."
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


def validate_stage8_dependency() -> dict[str, Any]:
    result = validate_v013_s08_stage_review()
    if result.get("stage_id") != "S08":
        raise RuntimeError("v0.1.3 S09-P1 requires validated Stage 8 review dependency")
    if result.get("stage_review_performed") is not True:
        raise RuntimeError("v0.1.3 S09-P1 requires Stage 8 review to be completed")
    if result.get("s09_p1_performed") is not False:
        raise RuntimeError("Stage 8 review dependency must not already include S09-P1")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("Stage 8 review dependency must not include GitHub upload")
    if result.get("github_upload_deferred_until_stage10_batch") is not True:
        raise RuntimeError("Stage 8 review dependency must keep upload deferred")
    return result


def _count_false_values(container: dict[str, Any]) -> int:
    return sum(1 for value in container.values() if value is False)


def validate_legacy_s09_p1_artifacts() -> dict[str, Any]:
    legacy_manifest = read_json(LEGACY_FACT_LAYER_MANIFEST_PATH)
    fact_records = read_jsonl(LEGACY_FACT_RECORDS_PATH)
    unallocated_pool = read_jsonl(LEGACY_UNALLOCATED_POOL_PATH)
    legacy_stage_manifest = read_json(LEGACY_STAGE_MANIFEST_PATH)
    validate_project_cost_fact_layer_artifacts(legacy_manifest, fact_records, unallocated_pool)

    summary = legacy_manifest.get("summary", {})
    upstream = legacy_manifest.get("upstream_quality_summary", {})
    metric_hash_ref_count = sum(len(record.get("metric_hash_refs", {})) for record in fact_records)
    metric_private_ref_count = sum(len(record.get("metric_private_refs", {})) for record in fact_records)
    cost_category_hash_ref_count = sum(len(record.get("cost_category_hash_refs", {})) for record in fact_records)
    cost_category_private_ref_count = sum(len(record.get("cost_category_private_refs", {})) for record in fact_records)
    formal_calculation_allowed_count = sum(
        1 for record in fact_records if record.get("formal_calculation_allowed") is True
    )
    metric_values_public_committed_count = sum(
        1 for record in fact_records if record.get("metric_values_public_committed") is True
    )
    fact_raw_layer_write_allowed_count = sum(
        1 for record in fact_records if record.get("raw_layer_write_allowed") is True
    )
    pool_amount_public_committed_count = sum(
        1 for item in unallocated_pool if item.get("amount_value_public_committed") is True
    )
    pool_raw_layer_write_allowed_count = sum(
        1 for item in unallocated_pool if item.get("raw_layer_write_allowed") is True
    )
    pending_pool_assignment_count = sum(
        1
        for item in unallocated_pool
        if item.get("assignment_status") == "pending_project_assignment_or_quality_resolution"
    )

    return {
        "legacy_manifest": legacy_manifest,
        "legacy_stage_manifest": legacy_stage_manifest,
        "required_metric_count": len(REQUIRED_FACT_METRICS),
        "required_metrics": list(REQUIRED_FACT_METRICS),
        "cost_category_count": len(REQUIRED_COST_CATEGORIES),
        "required_cost_categories": list(REQUIRED_COST_CATEGORIES),
        "fact_record_count": len(fact_records),
        "unallocated_pool_count": len(unallocated_pool),
        "authority_locked_field_count": summary.get("authority_locked_field_count"),
        "authority_excluded_field_count": summary.get("authority_excluded_field_count"),
        "business_entity_type_count": summary.get("business_entity_type_count"),
        "project_identity_profile_count": summary.get("project_identity_profile_count"),
        "manual_review_queue_count": upstream.get("manual_review_queue_count"),
        "unresolved_difference_count": upstream.get("unresolved_difference_count"),
        "zero_delta_fail_count": upstream.get("zero_delta_fail_count"),
        "blocked_quality_result_count": upstream.get("blocked_quality_result_count"),
        "formal_calculation_blocked": upstream.get("formal_calculation_blocked"),
        "metric_hash_ref_count": metric_hash_ref_count,
        "metric_private_ref_count": metric_private_ref_count,
        "cost_category_hash_ref_count": cost_category_hash_ref_count,
        "cost_category_private_ref_count": cost_category_private_ref_count,
        "formal_calculation_allowed_count": formal_calculation_allowed_count,
        "metric_values_public_committed_count": metric_values_public_committed_count,
        "fact_raw_layer_write_allowed_count": fact_raw_layer_write_allowed_count,
        "pool_amount_public_committed_count": pool_amount_public_committed_count,
        "pool_raw_layer_write_allowed_count": pool_raw_layer_write_allowed_count,
        "pending_pool_assignment_count": pending_pool_assignment_count,
        "fact_layer_status": legacy_manifest.get("fact_layer_status"),
        "mapping_version": legacy_manifest.get("mapping_version"),
        "formula_version": legacy_manifest.get("formula_version"),
        "stage_scope": legacy_manifest.get("stage_scope", {}),
        "quality_gate": legacy_manifest.get("quality_gate", {}),
        "public_repo_safety": legacy_manifest.get("public_repo_safety", {}),
        "quality_gate_false_count": _count_false_values(legacy_manifest.get("quality_gate", {})),
        "public_safety_false_count": _count_false_values(legacy_manifest.get("public_repo_safety", {})),
        "artifact_refs": {
            "legacy_manifest": LEGACY_FACT_LAYER_MANIFEST_PATH.as_posix(),
            "legacy_fact_records": LEGACY_FACT_RECORDS_PATH.as_posix(),
            "legacy_unallocated_pool": LEGACY_UNALLOCATED_POOL_PATH.as_posix(),
            "legacy_stage_manifest": LEGACY_STAGE_MANIFEST_PATH.as_posix(),
        },
    }


def build_manifest() -> dict[str, Any]:
    s08 = validate_stage8_dependency()
    legacy = validate_legacy_s09_p1_artifacts()
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "business_amount_values_remain_private_ref_or_hash_only",
        "project_cost_fact_layer_structural_only",
        "upstream_zero_delta_failure_blocks_formal_calculation",
        "upstream_source_difference_blocks_formal_calculation",
        "upstream_entity_matching_review_queue_blocks_formal_calculation",
        "s09_p2_margin_cash_margin_not_performed",
        "s09_p3_scope_reconciliation_not_performed",
        "stage9_review_not_performed",
        "formal_report_release_blocked",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "github_upload_deferred_until_stage10_batch",
        "business_execution_blocked",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S09",
        "phase_id": "S09-P1",
        "phase_name": "v0.1.3 project cost fact layer replay",
        "task_id": TASK_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_project_cost_fact_layer_replayed",
        "completed_task_ids": ["S9PAT01", "S9PAT02", "S9PAT03"],
        "acceptance_ids": ["ACC-V013-S09-P1-PROJECT-COST-FACT-LAYER-REPLAY"],
        "s08_stage_review_dependency_validated": True,
        "s08_stage_review_status": s08["status"],
        "legacy_s09_p1_dependency_validated": True,
        "stage9_phase_progress": {
            "completed_phase_count": 1,
            "total_phase_count": 3,
            "derived_percent_bps": 3333,
            "derived_percent_label": "33.33%",
            "s09_p1_performed": True,
            "s09_p2_performed": False,
            "s09_p3_performed": False,
            "stage9_review_performed": False,
        },
        "legacy_s09_p1_summary": {
            "required_metric_count": legacy["required_metric_count"],
            "required_metrics": legacy["required_metrics"],
            "cost_category_count": legacy["cost_category_count"],
            "required_cost_categories": legacy["required_cost_categories"],
            "fact_record_count": legacy["fact_record_count"],
            "unallocated_pool_count": legacy["unallocated_pool_count"],
            "authority_locked_field_count": legacy["authority_locked_field_count"],
            "authority_excluded_field_count": legacy["authority_excluded_field_count"],
            "business_entity_type_count": legacy["business_entity_type_count"],
            "project_identity_profile_count": legacy["project_identity_profile_count"],
            "manual_review_queue_count": legacy["manual_review_queue_count"],
            "unresolved_difference_count": legacy["unresolved_difference_count"],
            "zero_delta_fail_count": legacy["zero_delta_fail_count"],
            "blocked_quality_result_count": legacy["blocked_quality_result_count"],
            "formal_calculation_blocked": legacy["formal_calculation_blocked"],
            "fact_layer_status": legacy["fact_layer_status"],
        },
        "fact_layer_policy": {
            "mapping_version": legacy["mapping_version"],
            "formula_version": legacy["formula_version"],
            "metric_hash_ref_count": legacy["metric_hash_ref_count"],
            "metric_private_ref_count": legacy["metric_private_ref_count"],
            "cost_category_hash_ref_count": legacy["cost_category_hash_ref_count"],
            "cost_category_private_ref_count": legacy["cost_category_private_ref_count"],
            "formal_calculation_allowed": False,
            "formal_calculation_allowed_count": legacy["formal_calculation_allowed_count"],
            "metric_values_public_committed_count": legacy["metric_values_public_committed_count"],
            "fact_raw_layer_write_allowed_count": legacy["fact_raw_layer_write_allowed_count"],
            "pool_amount_public_committed_count": legacy["pool_amount_public_committed_count"],
            "pool_raw_layer_write_allowed_count": legacy["pool_raw_layer_write_allowed_count"],
            "pending_pool_assignment_count": legacy["pending_pool_assignment_count"],
            "quality_gate_false_count": legacy["quality_gate_false_count"],
            "public_safety_false_count": legacy["public_safety_false_count"],
        },
        "phase_boundaries": {
            "s09_p1_scope_included": True,
            "s09_p2_margin_cash_margin_scope_included": False,
            "s09_p3_scope_reconciliation_scope_included": False,
            "stage9_review_scope_included": False,
            "s10_report_scope_included": False,
            "lineage_full_check_scope_included": False,
            "formal_report_scope_included": False,
            "ui_scope_included": False,
            "external_connector_scope_included": False,
            "github_upload_scope_included": False,
        },
        "quality_gate": {
            "current_data_quality_grade": "Q4",
            "current_report_grade": "D",
            "release_permission": "blocked",
            "q5_formal_calculation_allowed": False,
            "q5_formal_calculation_allowed_count": 0,
            "formal_report_allowed": False,
            "formal_report_allowed_count": 0,
            "business_decision_basis_allowed": False,
            "business_execution_allowed": False,
            "delivery_allowed": False,
            "raw_layer_write_allowed": False,
            "automatic_external_action_allowed": False,
        },
        "github_upload": {
            "github_upload_ready_next_gate": False,
            "github_upload_deferred_until_stage10_batch": True,
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_stage10_batch",
        },
        "raw_data_boundary": {
            "local_raw_data_dir": RAW_DIR,
            "local_raw_data_dir_role": "user_finance_raw_private_inbox",
            "codex_read_allowed_only_when_phase_requires": True,
            "codex_read_required_by_this_phase": False,
            "codex_read_performed_by_this_phase": False,
            "codex_list_performed_by_this_phase": False,
            "codex_modify_allowed": False,
            "codex_delete_allowed": False,
            "codex_move_allowed": False,
            "codex_rename_allowed": False,
            "codex_overwrite_allowed": False,
            "codex_generate_inside_allowed": False,
            "codex_create_extra_files_inside_allowed": False,
            "github_commit_allowed": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
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
        },
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "artifact_refs": {
            **legacy["artifact_refs"],
            "manifest": MANIFEST_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "generator": "KMFA/tools/v013_s09_p1_project_cost_fact_layer_replay.py",
            "validator": "KMFA/tools/check_v013_s09_p1_project_cost_fact_layer_replay.py",
            "unit_test": "KMFA/tests/test_v013_s09_p1_project_cost_fact_layer_replay.py",
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s09_p1_project_cost_fact_layer_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s09_p1_project_cost_fact_layer_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s09_p1_project_cost_fact_layer_replay -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s09_p1_project_cost_fact_layer.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_project_cost_fact_layer -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s08_stage_review.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_s09_p1_project_cost_fact_layer_replay.py",
            "KMFA/tools/check_v013_s09_p1_project_cost_fact_layer_replay.py",
            "KMFA/tests/test_v013_s09_p1_project_cost_fact_layer_replay.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["legacy_s09_p1_summary"]
    policy = manifest["fact_layer_policy"]
    lines = [
        "# KMFA v0.1.3 S09-P1 Project Cost Fact Layer Replay",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        "- dependency: `v0.1.3 Stage 8 review PASS`",
        "- legacy_s09_p1_dependency_validated: `true`",
        f"- required_metric_count: `{summary['required_metric_count']}`",
        f"- cost_category_count: `{summary['cost_category_count']}`",
        f"- fact_record_count: `{summary['fact_record_count']}`",
        f"- unallocated_pool_count: `{summary['unallocated_pool_count']}`",
        f"- authority_locked_field_count: `{summary['authority_locked_field_count']}`",
        f"- authority_excluded_field_count: `{summary['authority_excluded_field_count']}`",
        f"- business_entity_type_count: `{summary['business_entity_type_count']}`",
        f"- manual_review_queue_count: `{summary['manual_review_queue_count']}`",
        f"- unresolved_difference_count: `{summary['unresolved_difference_count']}`",
        f"- zero_delta_fail_count: `{summary['zero_delta_fail_count']}`",
        f"- blocked_quality_result_count: `{summary['blocked_quality_result_count']}`",
        f"- fact_layer_status: `{summary['fact_layer_status']}`",
        f"- metric_hash_ref_count: `{policy['metric_hash_ref_count']}`",
        f"- cost_category_hash_ref_count: `{policy['cost_category_hash_ref_count']}`",
        f"- pending_pool_assignment_count: `{policy['pending_pool_assignment_count']}`",
        "",
        "## Boundary",
        "",
        "- s09_p1_scope_included: `true`",
        "- s09_p2_margin_cash_margin_scope_included: `false`",
        "- s09_p3_scope_reconciliation_scope_included: `false`",
        "- stage9_review_scope_included: `false`",
        "- github_upload_deferred_until_stage10_batch: `true`",
        "- github_upload_performed: `false`",
        "- formal_calculation_allowed: `false`",
        "- formal_report_allowed: `false`",
        "- business_decision_basis_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Raw Data Boundary",
        "",
        f"- local_raw_data_dir: `{RAW_DIR}`",
        "- local_raw_data_dir_role: `user_finance_raw_private_inbox`",
        "- codex_read_required_by_this_phase: `false`",
        "- codex_read_performed_by_this_phase: `false`",
        "- codex_list_performed_by_this_phase: `false`",
        "- codex_modify_allowed: `false`",
        "- codex_delete_allowed: `false`",
        "- codex_move_allowed: `false`",
        "- codex_rename_allowed: `false`",
        "- codex_generate_inside_allowed: `false`",
        "- codex_create_extra_files_inside_allowed: `false`",
        "- github_commit_allowed: `false`",
        "",
        (
            "This phase did not enumerate, copy, modify, move, rename, delete, overwrite, "
            "or write generated files inside the local finance inbox. It only replayed "
            "public-safe aggregate and hash/ref evidence already present in the repository."
        ),
        "",
        "## Public Safety",
        "",
        (
            "Evidence contains only metric names, cost category names, aggregate counts, "
            "hash/ref status, quality blockers, validator references, and governance paths."
        ),
        (
            "It does not contain source filenames, source hashes from the private inbox, tab labels, "
            "ZIP member names, field/header plaintext, row values, business amount values, credentials, "
            "contracts, payroll, tax filings, or bank statements."
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
        "# KMFA v0.1.3 S09-P1 Project Cost Fact Layer Replay Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `pending_final_validation_local_only`",
        "- github_upload_performed: `false`",
        "- raw_dir_read_performed_by_this_phase: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- s09_p2_performed: `false`",
        "- s09_p3_performed: `false`",
        "- stage9_review_performed: `false`",
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
    summary = manifest["legacy_s09_p1_summary"]
    print(
        "PASS: KMFA v0.1.3 S09-P1 project cost fact layer replay generated "
        f"(metrics={summary['required_metric_count']}, categories={summary['cost_category_count']}, "
        f"fact_records={summary['fact_record_count']}, unallocated_pool={summary['unallocated_pool_count']}, "
        "s09p2=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
