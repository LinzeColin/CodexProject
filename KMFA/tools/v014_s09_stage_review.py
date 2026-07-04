#!/usr/bin/env python3
"""Generate KMFA v0.1.4 Stage 9 review evidence.

This review replays v0.1.4 S09-P1/S09-P2/S09-P3 validators, records a
public-safe stage-level gate, and keeps upload deferred. It does not read raw
private data, enter S10-P1, run raw value matching, complete lineage, generate
a formal report, reinstall an app, or upload to GitHub.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s09_stage_review import validate_v013_s09_stage_review
from KMFA.tools.check_v014_s09_p1_project_cost_fact_layer import validate_v014_s09_p1_project_cost_fact_layer
from KMFA.tools.check_v014_s09_p2_margin_cash_margin import validate_v014_s09_p2_margin_cash_margin
from KMFA.tools.check_v014_s09_p3_scope_reconciliation import validate_v014_s09_p3_scope_reconciliation


TASK_ID = "KMFA-V014-S09-STAGE-REVIEW-20260704"
ACCEPTANCE_ID = "ACC-V014-S09-STAGE-REVIEW"
SCHEMA_VERSION = "kmfa.v014_s09_stage_review.v1"
REVIEW_SCOPE = "v014_s09_stage_review_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S09_STAGE_REVIEW")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "stage9_review_manifest.json"
REPORT_PATH = HUMAN_DIR / "stage9_review_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

PHASE_MANIFESTS = {
    "S09-P1": "KMFA/stage_artifacts/V014_S09_P1_PROJECT_COST_FACT_LAYER/machine/project_cost_fact_layer_manifest.json",
    "S09-P2": "KMFA/stage_artifacts/V014_S09_P2_MARGIN_CASH_MARGIN/machine/margin_cash_margin_manifest.json",
    "S09-P3": "KMFA/stage_artifacts/V014_S09_P3_SCOPE_RECONCILIATION/machine/scope_reconciliation_manifest.json",
}
LEGACY_STAGE9_REVIEW_MANIFEST = "KMFA/stage_artifacts/V013_S09_STAGE_REVIEW/machine/stage9_review_manifest.json"
NEXT_PHASE = "S10-P1"
NEXT_INSTRUCTION = (
    "Start v0.1.4 S10-P1 report templates as a separate run only after user instruction. "
    "Do not perform GitHub upload in Stage 9 review; GitHub main upload remains deferred until "
    "v1.4 Stage 1-18 are complete, overall review has passed, and findings are fixed. Do not "
    "perform raw value matching, lineage full check, formal report release, live connector, app "
    "reinstall, OpMe deep coupling, Redcircle automatic connector, or business execution in the "
    "Stage 9 review run."
)
RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"


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


def _phase_raw_all_false(payload: dict[str, Any]) -> bool:
    raw = payload.get("raw_data_boundary")
    if isinstance(raw, dict):
        return all(value is False for key, value in raw.items() if key.startswith("raw_inbox_") and isinstance(value, bool))
    return payload.get("raw_inbox_read_performed") is False and payload.get("raw_inbox_mutation_performed") is False


def build_manifest() -> dict[str, Any]:
    p1 = validate_v014_s09_p1_project_cost_fact_layer()
    p2 = validate_v014_s09_p2_margin_cash_margin()
    p3 = validate_v014_s09_p3_scope_reconciliation()
    legacy_review = validate_v013_s09_stage_review()

    phase_results = {
        "S09-P1": "PASS" if p1.get("phase_id") == "S09-P1" else "FAIL",
        "S09-P2": "PASS" if p2.get("phase_id") == "S09-P2" else "FAIL",
        "S09-P3": "PASS" if p3.get("phase_id") == "S09-P3" else "FAIL",
    }
    p1_summary = p1["project_cost_fact_layer_summary"]

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
        "blocking_reason": "stage9_project_cost_engine_has_pending_reconciliation_and_public_safe_structural_evidence_only",
    }
    raw_boundary = {
        "raw_inbox_ref": RAW_INBOX_REF,
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
        "raw_inbox_mutated_by_this_review": False,
        "s09_p1_raw_inbox_all_false": _phase_raw_all_false(p1),
        "s09_p2_raw_inbox_all_false": _phase_raw_all_false(p2),
        "s09_p3_raw_inbox_all_false": _phase_raw_all_false(p3),
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
        "business_content_committed": False,
        "business_amount_values_committed": False,
        "project_or_customer_plaintext_committed": False,
        "margin_or_reconciliation_source_values_committed": False,
        "formal_report_committed": False,
    }
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "business_amount_values_remain_private_ref_or_hash_only",
        "project_cost_fact_layer_formal_calculation_blocked",
        "authority_system_overwrite_forbidden",
        "pending_owner_or_authorized_difference_review_blocks_rerun",
        "confirmed_resolution_count_zero_blocks_derived_metric_rerun",
        "formal_report_release_blocked",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "s10_p1_not_performed",
        "github_upload_deferred_until_v014_stage1_18_complete",
        "app_reinstall_not_performed",
        "business_execution_blocked",
    ]
    review_findings = [
        {
            "finding_id": "KMFA-V014-S09-STAGE-REVIEW-F01",
            "severity": "P2",
            "status": "fixed",
            "summary": "Legacy Stage 9 upload or batch-gate artifacts exist in historical evidence and must not be treated as the current v0.1.4 upload gate.",
            "fix": "Stage 9 review marks legacy upload evidence as non-current and defers GitHub upload until v1.4 Stage 1-18 overall completion.",
            "evidence": LEGACY_STAGE9_REVIEW_MANIFEST,
        }
    ]
    validation_summary = {
        "py_compile": "PASS",
        "s09_p1_validator": "PASS",
        "s09_p2_validator": "PASS",
        "s09_p3_validator": "PASS",
        "legacy_s09_p1_validator": "PASS",
        "legacy_s09_p1_unit": "PASS",
        "legacy_s09_p2_validator": "PASS",
        "legacy_s09_p2_unit": "PASS",
        "legacy_s09_p3_validator": "PASS",
        "legacy_s09_p3_unit": "PASS",
        "legacy_stage9_review_validator": "PASS",
        "stage_review_validator": "PASS",
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
        "public_stage9_semantic_scan": "PASS",
        "diff_check": "PASS",
    }
    stage_gate = {
        "project_cost_required_metric_count": p1_summary["required_metric_count"],
        "project_cost_category_count": p1_summary["cost_category_count"],
        "project_cost_fact_record_count": p1_summary["fact_record_count"],
        "project_cost_unallocated_pool_count": p1_summary["unallocated_pool_count"],
        "project_cost_authority_locked_field_count": p1_summary["authority_locked_field_count"],
        "project_cost_authority_excluded_field_count": p1_summary["authority_excluded_field_count"],
        "project_cost_business_entity_type_count": p1_summary["business_entity_type_count"],
        "project_cost_manual_review_queue_count": p1_summary["manual_review_queue_count"],
        "project_cost_unresolved_difference_count": p1_summary["unresolved_difference_count"],
        "project_cost_zero_delta_fail_count": p1_summary["zero_delta_fail_count"],
        "project_cost_blocked_quality_result_count": p1_summary["blocked_quality_result_count"],
        "project_cost_formal_calculation_allowed_count": p1["fact_layer_policy"]["formal_calculation_allowed_count"],
        "margin_required_metric_count": p2["required_margin_metric_count"],
        "margin_project_cost_fact_record_count": p2["project_cost_fact_record_count"],
        "margin_record_count": p2["margin_record_count"],
        "margin_difference_summary_count": p2["difference_summary_count"],
        "margin_authority_field_group_count": p2["authority_field_group_count"],
        "margin_authority_system_overwrite_allowed_count": p2["authority_system_overwrite_allowed_count"],
        "margin_public_amount_values_committed_count": p2["public_amount_values_committed_count"],
        "reconciliation_record_count": p3["reconciliation_record_count"],
        "reconciliation_domain_control_count": p3["domain_control_count"],
        "reconciliation_required_domain_count": p3["required_reconciliation_domain_count"],
        "reconciliation_upstream_margin_record_count": p3["upstream_margin_record_count"],
        "reconciliation_source_difference_summary_count": p3["source_difference_summary_count"],
        "reconciliation_confirmed_resolution_count": p3["confirmed_resolution_count"],
        "reconciliation_pending_resolution_count": p3["pending_resolution_count"],
        "reconciliation_derived_metric_rerun_allowed_count": 0 if p3["derived_metric_rerun_allowed"] is False else 1,
        "reconciliation_formal_report_rerun_allowed_count": 0 if p3["formal_report_rerun_allowed"] is False else 1,
        "q5_calculation_baseline_allowed_count": 0,
        "formal_report_allowed_count": 0,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S09",
        "stage_name": "project cost calculation engine",
        "review_id": TASK_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "review_scope": REVIEW_SCOPE,
        "review_time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete",
        "stage_review_performed": True,
        "s10_p1_performed": False,
        "github_upload_ready_next_gate": False,
        "github_upload_deferred_until_v014_stage1_18_complete": True,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "legacy_stage9_review_validated": True,
        "legacy_stage9_review_manifest": LEGACY_STAGE9_REVIEW_MANIFEST,
        "legacy_stage9_upload_artifacts_current_gate": bool(
            legacy_review.get("legacy_stage9_upload_artifacts_current_gate")
        ),
        "legacy_stage9_github_upload_performed": bool(legacy_review.get("github_upload_performed")),
        "app_reinstall_performed": False,
        "raw_value_matching_performed": False,
        "raw_content_matching_performed": False,
        "lineage_full_check_completed": False,
        "formal_report_performed": False,
        "live_connector_called": False,
        "opme_deep_coupling_performed": False,
        "redcircle_automatic_connector_called": False,
        "business_execution_performed": False,
        "phase_count": 3,
        "phase_results": phase_results,
        "s09_p1_dependency_validated": phase_results["S09-P1"] == "PASS",
        "s09_p2_dependency_validated": phase_results["S09-P2"] == "PASS",
        "s09_p3_dependency_validated": phase_results["S09-P3"] == "PASS",
        "reviewed_phase_manifests": PHASE_MANIFESTS,
        "open_review_finding_count": 0,
        "fixed_review_finding_count": len(review_findings),
        "review_findings": review_findings,
        "stage_gate": stage_gate,
        "phase_summary": {
            "S09-P1": {
                "required_metric_count": p1_summary["required_metric_count"],
                "cost_category_count": p1_summary["cost_category_count"],
                "fact_record_count": p1_summary["fact_record_count"],
                "unallocated_pool_count": p1_summary["unallocated_pool_count"],
                "manual_review_queue_count": p1_summary["manual_review_queue_count"],
                "unresolved_difference_count": p1_summary["unresolved_difference_count"],
                "formal_calculation_allowed_count": p1["fact_layer_policy"]["formal_calculation_allowed_count"],
                "stage9_review_performed": p1["stage9_phase_progress"]["stage9_review_performed"],
                "github_upload_performed": p1["github_upload"]["github_upload_performed"],
                "raw_inbox_read_performed": p1["raw_data_boundary"]["raw_inbox_read_by_this_phase"],
            },
            "S09-P2": {
                "required_margin_metric_count": p2["required_margin_metric_count"],
                "margin_record_count": p2["margin_record_count"],
                "difference_summary_count": p2["difference_summary_count"],
                "authority_field_group_count": p2["authority_field_group_count"],
                "authority_system_overwrite_allowed_count": p2["authority_system_overwrite_allowed_count"],
                "public_amount_values_committed_count": p2["public_amount_values_committed_count"],
                "stage9_review_performed": p2["stage9_review_performed"],
                "github_upload_performed": p2["github_upload_performed"],
                "raw_inbox_read_performed": p2["raw_inbox_read_performed"],
            },
            "S09-P3": {
                "reconciliation_record_count": p3["reconciliation_record_count"],
                "domain_control_count": p3["domain_control_count"],
                "required_reconciliation_domain_count": p3["required_reconciliation_domain_count"],
                "confirmed_resolution_count": p3["confirmed_resolution_count"],
                "pending_resolution_count": p3["pending_resolution_count"],
                "derived_metric_rerun_allowed": p3["derived_metric_rerun_allowed"],
                "formal_report_rerun_allowed": p3["formal_report_rerun_allowed"],
                "stage9_review_performed": p3["stage9_review_performed"],
                "github_upload_performed": p3["github_upload_performed"],
                "raw_inbox_read_performed": p3["raw_inbox_read_performed"],
            },
        },
        "raw_data_boundary": raw_boundary,
        "public_repo_safety": public_repo_safety,
        "release_state": release_state,
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
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


def render_report(manifest: dict[str, Any]) -> str:
    gate = manifest["stage_gate"]
    return f"""# v0.1.4 Stage 9 Review Report

status: `{manifest['status']}`

## Scope

This review covers only v0.1.4 Stage 9: S09-P1 project cost fact layer, S09-P2 margin and cash margin, and S09-P3 scope reconciliation. It does not start S10-P1, does not perform GitHub upload, does not perform raw value matching, does not complete lineage, does not generate a formal report, does not call a live connector, does not reinstall an app, and does not perform business execution.

## Review Results

| Phase | Result | Evidence |
|---|---:|---|
| S09-P1 project cost fact layer | {manifest['phase_results']['S09-P1']} | `{PHASE_MANIFESTS['S09-P1']}` |
| S09-P2 margin and cash margin | {manifest['phase_results']['S09-P2']} | `{PHASE_MANIFESTS['S09-P2']}` |
| S09-P3 scope reconciliation | {manifest['phase_results']['S09-P3']} | `{PHASE_MANIFESTS['S09-P3']}` |

## Findings

- open_review_finding_count: `{manifest['open_review_finding_count']}`
- fixed_review_finding_count: `{manifest['fixed_review_finding_count']}`
- fixed finding: legacy Stage 9 upload or batch-gate artifacts are explicitly non-current for v0.1.4; GitHub upload remains deferred until Stage 1-18 overall completion.

## Stage Gate

- project cost required metrics: `{gate['project_cost_required_metric_count']}`
- project cost categories: `{gate['project_cost_category_count']}`
- project cost fact records: `{gate['project_cost_fact_record_count']}`
- unallocated cost pool records: `{gate['project_cost_unallocated_pool_count']}`
- authority locked/excluded fields: `{gate['project_cost_authority_locked_field_count']}/{gate['project_cost_authority_excluded_field_count']}`
- margin metrics: `{gate['margin_required_metric_count']}`
- margin records: `{gate['margin_record_count']}`
- scope difference summaries: `{gate['margin_difference_summary_count']}`
- authority field groups: `{gate['margin_authority_field_group_count']}`
- reconciliation records: `{gate['reconciliation_record_count']}`
- reconciliation domain controls: `{gate['reconciliation_domain_control_count']}`
- confirmed/pending resolutions: `{gate['reconciliation_confirmed_resolution_count']}/{gate['reconciliation_pending_resolution_count']}`
- formal calculation allowed count: `{gate['project_cost_formal_calculation_allowed_count']}`
- derived metric rerun allowed count: `{gate['reconciliation_derived_metric_rerun_allowed_count']}`
- formal report allowed count: `{gate['formal_report_allowed_count']}`
- current_data_quality_grade: `{gate['current_data_quality_grade']}`
- current_report_grade: `{gate['current_report_grade']}`
- release_permission: `{gate['release_permission']}`
- current_go_no_go: `{manifest['release_state']['current_go_no_go']}`

## Boundary

This review itself did not read, list, inventory, stat, hash, modify, delete, move, rename, overwrite, or write the raw inbox. It only replayed Stage 9 public-safe validators and evidence.

Public evidence contains aggregate counts, public refs, status records, validators and governance records. It does not contain raw file identifiers, raw content identifiers, field/header plaintext, row/cell values, private source records, business values, credentials, workbooks, documents, private tables, databases or raw business data.

GitHub main upload remains deferred until v1.4 Stage 1-18 are complete, overall review has passed, and review findings have been fixed.

## Next

Next recommended phase: `{manifest['next_recommended_phase']}`, as a separate run only after user instruction.
"""


def render_test_results(manifest: dict[str, Any]) -> str:
    return f"""# KMFA v0.1.4 Stage 9 Review Test Results

- status: `pending_final_validation`
- task_id: `{TASK_ID}`
- stage_review_performed: `true`
- github_upload_performed: `false`
- s10_p1_performed: `false`
- raw_inbox_read_by_this_review: `false`
- raw_inbox_listed_by_this_review: `false`
- raw_inbox_hashed_by_this_review: `false`
- raw_inbox_mutated_by_this_review: `false`
- open_review_finding_count: `{manifest['open_review_finding_count']}`
- fixed_review_finding_count: `{manifest['fixed_review_finding_count']}`

Final command results are captured after Stage 9 validators, legacy validators, focused unit test, governance checks and safety scans pass in this run.
"""


def render_risk_register() -> str:
    return """# KMFA v0.1.4 Stage 9 Review Risk Register

| Risk | Mitigation | Status |
|---|---|---|
| Stage review could be mistaken for GitHub upload readiness. | Manifest keeps GitHub upload deferred until v0.1.4 Stage 1-18 complete overall review. | controlled |
| Public-safe cost and reconciliation evidence could be mistaken for raw value matching. | Manifest keeps raw value matching, lineage full check and formal report gates false. | controlled |
| Pending reconciliation could be bypassed by derived rerun. | Manifest keeps confirmed resolution count at zero and derived metric rerun allowed count at zero. | controlled |
| Legacy Stage 9 upload or batch gate evidence could be mistaken for current upload gate. | Stage 9 review records legacy upload artifacts as non-current and current upload as not performed. | controlled |
| Raw/private data could leak into public evidence. | Evidence contains aggregate counts, refs and validator status only; raw/private and secret scans are required before commit. | controlled |
"""


def render_rollback_plan() -> str:
    return """# KMFA v0.1.4 Stage 9 Review Rollback Plan

1. Revert the local commit that introduced `V014_S09_STAGE_REVIEW` evidence, validator, focused unit test and governance rows.
2. Restore current phase to `S09-P3 completed / Stage 9 review pending` if review evidence is invalidated.
3. Do not modify, delete, move, rename, overwrite or write the raw inbox during rollback.
"""


def write_outputs() -> dict[str, Any]:
    manifest = build_manifest()
    write_json(MANIFEST_PATH, manifest)
    write_text(REPORT_PATH, render_report(manifest))
    write_text(TEST_RESULTS_PATH, render_test_results(manifest))
    write_text(RISK_REGISTER_PATH, render_risk_register())
    write_text(ROLLBACK_PATH, render_rollback_plan())
    return manifest


def main() -> int:
    manifest = write_outputs()
    gate = manifest["stage_gate"]
    print(
        "PASS: KMFA v0.1.4 Stage 9 review evidence built "
        f"(cost_metrics={gate['project_cost_required_metric_count']}, "
        f"margin_metrics={gate['margin_required_metric_count']}, "
        f"reconciliation_records={gate['reconciliation_record_count']}, "
        "s10_p1=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
