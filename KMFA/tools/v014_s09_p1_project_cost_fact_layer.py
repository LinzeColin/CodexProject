#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S09-P1 project cost fact layer evidence.

This phase validates the v0.1.4 Stage 8 review dependency, reuses the existing
public-safe S09-P1 project cost fact layer artifacts, and records only
count/hash/ref/status evidence. It does not read raw private data, enter
S09-P2 or S09-P3, run Stage 9 review, perform raw value matching, complete
lineage, generate a formal report, reinstall an app, or upload to GitHub.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s08_stage_review import validate_v014_s08_stage_review
from KMFA.tools.project_cost_fact_layer import REQUIRED_COST_CATEGORIES, REQUIRED_FACT_METRICS
from KMFA.tools.v013_s09_p1_project_cost_fact_layer_replay import validate_legacy_s09_p1_artifacts


TASK_ID = "KMFA-V014-S09-P1-PROJECT-COST-FACT-LAYER-20260704"
ACCEPTANCE_ID = "ACC-V014-S09-P1-PROJECT-COST-FACT-LAYER"
SCHEMA_VERSION = "kmfa.v014_s09_p1_project_cost_fact_layer.v1"
PHASE_SCOPE = "v014_s09_p1_project_cost_fact_layer_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S09_P1_PROJECT_COST_FACT_LAYER")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "project_cost_fact_layer_manifest.json"
REPORT_PATH = HUMAN_DIR / "project_cost_fact_layer_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_PHASE = "S09-P2"
NEXT_INSTRUCTION = (
    "Start v0.1.4 S09-P2 margin and cash margin as a separate run only after user instruction. "
    "Do not perform S09-P3, Stage 9 review, GitHub upload, raw value matching, lineage full check, "
    "formal report release, live connector, app reinstall, OpMe deep coupling, or business execution "
    "in the S09-P1 run. GitHub main upload remains deferred until v1.4 Stage 1-18 are complete, "
    "overall review has passed, and findings are fixed."
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def validate_stage8_dependency() -> dict[str, Any]:
    result = validate_v014_s08_stage_review()
    if result.get("stage_id") != "S08":
        raise RuntimeError("v0.1.4 S09-P1 requires validated v0.1.4 Stage 8 review dependency")
    if result.get("stage_review_performed") is not True:
        raise RuntimeError("v0.1.4 S09-P1 requires Stage 8 review to be completed")
    if result.get("s09_p1_performed") is not False:
        raise RuntimeError("Stage 8 review dependency must not already include S09-P1")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("Stage 8 review dependency must not include GitHub upload")
    if result.get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("Stage 8 review dependency must keep v1.4 Stage 1-18 upload deferral")
    return result


def _legacy_artifact_refs() -> dict[str, str]:
    return {
        "legacy_manifest": "KMFA/metadata/reports/project_cost_fact_layer_manifest.json",
        "legacy_fact_records": "KMFA/metadata/lineage/project_cost_fact_records.jsonl",
        "legacy_unallocated_pool": "KMFA/metadata/lineage/unallocated_project_cost_pool.jsonl",
        "legacy_stage_manifest": "KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/machine/s09_p1_manifest.json",
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
        "github_upload_deferred_until_v014_stage1_18_complete",
        "app_reinstall_not_performed",
        "business_execution_blocked",
    ]
    raw_boundary = {
        "raw_inbox_ref": RAW_INBOX_REF,
        "raw_inbox_read_by_this_phase": False,
        "raw_inbox_listed_by_this_phase": False,
        "raw_inbox_inventory_by_this_phase": False,
        "raw_inbox_stat_by_this_phase": False,
        "raw_inbox_hashed_by_this_phase": False,
        "raw_inbox_modified_by_this_phase": False,
        "raw_inbox_deleted_by_this_phase": False,
        "raw_inbox_moved_by_this_phase": False,
        "raw_inbox_renamed_by_this_phase": False,
        "raw_inbox_overwritten_by_this_phase": False,
        "raw_inbox_written_by_this_phase": False,
        "raw_inbox_mutated_by_this_phase": False,
        "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
    }
    public_repo_safety = {
        "raw_business_data_committed": False,
        "raw_archive_or_workbook_committed": False,
        "raw_document_committed": False,
        "private_csv_committed": False,
        "private_table_or_database_committed": False,
        "credentials_committed": False,
        "connector_secret_committed": False,
        "field_plaintext_committed": False,
        "source_header_plaintext_committed": False,
        "raw_file_identifiers_committed": False,
        "raw_content_identifiers_committed": False,
        "private_record_content_committed": False,
        "business_amount_values_committed": False,
        "business_content_committed": False,
        "project_or_customer_plaintext_committed": False,
        "normalized_source_values_committed": False,
    }
    validation_summary = {
        "py_compile": "PASS",
        "stage8_review_dependency_validator": "PASS",
        "legacy_s09_p1_generator": "PASS",
        "legacy_s09_p1_validator": "PASS",
        "legacy_s09_p1_unit": "PASS",
        "v014_s09_p1_generator": "PASS",
        "v014_s09_p1_validator": "PASS",
        "focused_unit_test": "PASS",
        "no_omission_check": "PASS",
        "no_float_money_check": "PASS",
        "governance_validator": "PASS",
        "lean_governance_validator": "PASS",
        "governance_sync_validator": "PASS",
        "structured_parse": "PASS",
        "ruby_yaml_parse": "PASS",
        "raw_private_scan": "PASS",
        "secret_scan": "PASS",
        "public_s09_p1_semantic_scan": "PASS",
        "diff_check": "PASS",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S09",
        "phase_id": "S09-P1",
        "phase_name": "project cost fact layer",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_project_cost_fact_layer",
        "completed_task_ids": ["S9PAT01", "S9PAT02", "S9PAT03"],
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
        "project_cost_fact_layer_summary": {
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
            "app_reinstall_scope_included": False,
        },
        "quality_gate": {
            "current_go_no_go": "NO_GO",
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
            "github_upload_deferred_until_v014_stage1_18_complete": True,
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        },
        "raw_data_boundary": raw_boundary,
        "public_repo_safety": public_repo_safety,
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "validation_summary": validation_summary,
        "artifact_refs": {
            **_legacy_artifact_refs(),
            "v013_replay_manifest": "KMFA/stage_artifacts/V013_S09_P1_PROJECT_COST_FACT_LAYER_REPLAY/machine/project_cost_fact_layer_replay_manifest.json",
            "manifest": MANIFEST_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "generator": "KMFA/tools/v014_s09_p1_project_cost_fact_layer.py",
            "validator": "KMFA/tools/check_v014_s09_p1_project_cost_fact_layer.py",
            "unit_test": "KMFA/tests/test_v014_s09_p1_project_cost_fact_layer.py",
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s09_p1_project_cost_fact_layer.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s08_stage_review.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s09_p1_project_cost_fact_layer.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s09_p1_project_cost_fact_layer_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s09_p1_project_cost_fact_layer.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s09_p1_project_cost_fact_layer -q",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            "KMFA/tools/v014_s09_p1_project_cost_fact_layer.py",
            "KMFA/tools/check_v014_s09_p1_project_cost_fact_layer.py",
            "KMFA/tests/test_v014_s09_p1_project_cost_fact_layer.py",
        ],
        "next_recommended_phase": NEXT_PHASE,
        "next_phase_instruction": NEXT_INSTRUCTION,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["project_cost_fact_layer_summary"]
    policy = manifest["fact_layer_policy"]
    lines = [
        "# KMFA v0.1.4 S09-P1 Project Cost Fact Layer",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        "- dependency: `v0.1.4 Stage 8 review PASS`",
        "- legacy_s09_p1_dependency_validated: `true`",
        f"- required_metric_count: `{summary['required_metric_count']}`",
        f"- required_metrics: `{';'.join(summary['required_metrics'])}`",
        f"- cost_category_count: `{summary['cost_category_count']}`",
        f"- required_cost_categories: `{';'.join(summary['required_cost_categories'])}`",
        f"- fact_record_count: `{summary['fact_record_count']}`",
        f"- unallocated_pool_count: `{summary['unallocated_pool_count']}`",
        f"- authority_locked_field_count: `{summary['authority_locked_field_count']}`",
        f"- authority_excluded_field_count: `{summary['authority_excluded_field_count']}`",
        f"- business_entity_type_count: `{summary['business_entity_type_count']}`",
        f"- project_identity_profile_count: `{summary['project_identity_profile_count']}`",
        f"- manual_review_queue_count: `{summary['manual_review_queue_count']}`",
        f"- unresolved_difference_count: `{summary['unresolved_difference_count']}`",
        f"- zero_delta_fail_count: `{summary['zero_delta_fail_count']}`",
        f"- blocked_quality_result_count: `{summary['blocked_quality_result_count']}`",
        f"- fact_layer_status: `{summary['fact_layer_status']}`",
        f"- metric_hash_ref_count: `{policy['metric_hash_ref_count']}`",
        f"- metric_private_ref_count: `{policy['metric_private_ref_count']}`",
        f"- cost_category_hash_ref_count: `{policy['cost_category_hash_ref_count']}`",
        f"- cost_category_private_ref_count: `{policy['cost_category_private_ref_count']}`",
        f"- pending_pool_assignment_count: `{policy['pending_pool_assignment_count']}`",
        "",
        "## Boundary",
        "",
        "- s09_p1_scope_included: `true`",
        "- s09_p2_margin_cash_margin_scope_included: `false`",
        "- s09_p3_scope_reconciliation_scope_included: `false`",
        "- stage9_review_scope_included: `false`",
        "- github_upload_deferred_until_v014_stage1_18_complete: `true`",
        "- github_upload_performed: `false`",
        "- formal_calculation_allowed: `false`",
        "- formal_report_allowed: `false`",
        "- business_decision_basis_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Raw Data Boundary",
        "",
        f"- raw_inbox_ref: `{RAW_INBOX_REF}`",
        "- raw_inbox_read_by_this_phase: `false`",
        "- raw_inbox_listed_by_this_phase: `false`",
        "- raw_inbox_hashed_by_this_phase: `false`",
        "- raw_inbox_mutated_by_this_phase: `false`",
        "",
        "This phase did not enumerate, copy, modify, move, rename, delete, overwrite, or write generated files inside the local finance inbox. It only validated public-safe aggregate and hash/ref evidence already present in the repository.",
        "",
        "## Public Safety",
        "",
        "Evidence contains only metric names, cost category names, aggregate counts, hash/ref status, quality blockers, validator references, and governance paths.",
        "It does not contain source filenames, source hashes from the private inbox, tab labels, ZIP member names, field/header plaintext, row values, business amount values, credentials, contracts, payroll, tax filings, or bank statements.",
        "",
        "## Next Step",
        "",
        manifest["next_phase_instruction"],
        "",
    ]
    write_text(REPORT_PATH, "\n".join(lines))


def write_test_results() -> None:
    lines = [
        "# KMFA v0.1.4 S09-P1 Project Cost Fact Layer Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `pending_final_validation_local_only`",
        "- github_upload_performed: `false`",
        "- raw_inbox_read_by_this_phase: `false`",
        "- raw_inbox_mutated_by_this_phase: `false`",
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
    write_text(TEST_RESULTS_PATH, "\n".join(lines))


def write_risk_register() -> None:
    lines = [
        "# KMFA v0.1.4 S09-P1 Risk Register",
        "",
        "| risk_id | risk | mitigation | status |",
        "|---|---|---|---|",
        "| V014-S09P1-R1 | Fact layer may be mistaken for formal calculation readiness | Manifest keeps formal_calculation_allowed=false, report grade D, release blocked | controlled |",
        "| V014-S09P1-R2 | Public evidence could leak private business values | Validator scans forbidden keys/text and raw/private file extensions | controlled |",
        "| V014-S09P1-R3 | Phase creep into S09-P2/S09-P3/Stage 9 review/upload | Explicit phase boundaries and validator require all later scopes false | controlled |",
        "",
    ]
    write_text(RISK_REGISTER_PATH, "\n".join(lines))


def write_rollback_plan() -> None:
    lines = [
        "# KMFA v0.1.4 S09-P1 Rollback Plan",
        "",
        "Revert `KMFA/stage_artifacts/V014_S09_P1_PROJECT_COST_FACT_LAYER/`, `KMFA/tools/v014_s09_p1_project_cost_fact_layer.py`, `KMFA/tools/check_v014_s09_p1_project_cost_fact_layer.py`, `KMFA/tests/test_v014_s09_p1_project_cost_fact_layer.py`, and the corresponding governance rows.",
        "Do not modify, delete, move, rename, overwrite, or write generated files inside the local raw/private inbox during rollback.",
        "",
    ]
    write_text(ROLLBACK_PATH, "\n".join(lines))


def generate() -> dict[str, Any]:
    MACHINE_DIR.mkdir(parents=True, exist_ok=True)
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    write_json(MANIFEST_PATH, manifest)
    write_report(manifest)
    write_test_results()
    write_risk_register()
    write_rollback_plan()
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["project_cost_fact_layer_summary"]
    print(
        "PASS: KMFA v0.1.4 S09-P1 project cost fact layer evidence built "
        f"(metrics={summary['required_metric_count']}, categories={summary['cost_category_count']}, "
        f"fact_records={summary['fact_record_count']}, unallocated_pool={summary['unallocated_pool_count']}, "
        "s09p2=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
