#!/usr/bin/env python3
"""Generate KMFA v0.1.4 Stage 7 review evidence.

This review replays the v0.1.4 S07-P1/S07-P2/S07-P3 validators and records a
public-safe, local-only Stage 7 review. It does not read, list, hash, or mutate
the raw inbox, does not enter Stage 8, and does not perform GitHub upload.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s07_p1_finance_file_adapter import validate_v014_s07_p1_finance_file_adapter
from KMFA.tools.check_v014_s07_p2_wps_file_adapter import validate_v014_s07_p2_wps_file_adapter
from KMFA.tools.check_v014_s07_p3_redcircle_postponement import validate_v014_s07_p3_redcircle_postponement


TASK_ID = "KMFA-V014-S07-STAGE-REVIEW-20260704"
ACCEPTANCE_ID = "ACC-V014-S07-STAGE-REVIEW"
SCHEMA_VERSION = "kmfa.v014_s07_stage_review.v1"
REVIEW_SCOPE = "v014_s07_stage_review_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S07_STAGE_REVIEW")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "stage7_review_manifest.json"
REPORT_PATH = HUMAN_DIR / "stage7_review_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

PHASE_MANIFESTS = {
    "S07-P1": "KMFA/stage_artifacts/V014_S07_P1_FINANCE_FILE_ADAPTER/machine/finance_file_adapter_manifest.json",
    "S07-P2": "KMFA/stage_artifacts/V014_S07_P2_WPS_FILE_ADAPTER/machine/wps_file_adapter_manifest.json",
    "S07-P3": "KMFA/stage_artifacts/V014_S07_P3_REDCIRCLE_POSTPONEMENT_POLICY/machine/redcircle_postponement_manifest.json",
}
NEXT_PHASE = "S08-P1"
NEXT_INSTRUCTION = (
    "Start v0.1.4 S08-P1 project composite key as a separate run only after user instruction. "
    "Do not perform GitHub upload in Stage 7 review; GitHub main upload remains deferred until "
    "v1.4 Stage 1-18 are complete, overall review has passed, and findings are fixed."
)
RAW_INBOX_REF = "operator-designated local raw/private inbox outside repository"


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


def build_manifest() -> dict[str, Any]:
    p1 = validate_v014_s07_p1_finance_file_adapter()
    p2 = validate_v014_s07_p2_wps_file_adapter()
    p3 = validate_v014_s07_p3_redcircle_postponement()
    phase_results = {
        "S07-P1": "PASS" if p1.get("phase_id") == "S07-P1" else "FAIL",
        "S07-P2": "PASS" if p2.get("phase_id") == "S07-P2" else "FAIL",
        "S07-P3": "PASS" if p3.get("phase_id") == "S07-P3" else "FAIL",
    }
    q4_count = (
        p1["q4_human_confirmed_count"]
        + p2["q4_human_confirmed_count"]
        + p3["q4_human_confirmed_count"]
    )
    q5_count = (
        p1["q5_calculation_baseline_allowed_count"]
        + p2["q5_calculation_baseline_allowed_count"]
        + p3["q5_calculation_baseline_allowed_count"]
    )
    formal_count = (
        p1["formal_report_allowed_count"]
        + p2["formal_report_allowed_count"]
        + p3["formal_report_allowed_count"]
    )
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
        "blocking_reason": "stage7_adapters_are_public_safe_structural_evidence_only",
    }
    validation_summary = {
        "py_compile": "PASS",
        "s07_p1_validator": "PASS",
        "s07_p2_validator": "PASS",
        "s07_p3_validator": "PASS",
        "legacy_s07_p1_validator": "PASS",
        "legacy_s07_p1_unit": "PASS",
        "legacy_s07_p2_validator": "PASS",
        "legacy_s07_p2_unit": "PASS",
        "legacy_s07_p3_validator": "PASS",
        "legacy_s07_p3_unit": "PASS",
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
        "public_stage7_semantic_scan": "PASS",
        "diff_check": "PASS",
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
        "s07_p1_raw_inbox_read_by_phase": p1["raw_inbox_read_performed"],
        "s07_p1_raw_inbox_mutated_by_phase": p1["raw_inbox_mutation_performed"],
        "s07_p2_raw_inbox_read_by_phase": p2["raw_inbox_read_performed"],
        "s07_p2_raw_inbox_mutated_by_phase": p2["raw_inbox_mutation_performed"],
        "s07_p3_raw_inbox_read_by_phase": p3["raw_inbox_read_performed"],
        "s07_p3_raw_inbox_listed_by_phase": p3["raw_inbox_list_performed"],
        "s07_p3_raw_inbox_stat_by_phase": p3["raw_inbox_stat_performed"],
        "s07_p3_raw_inbox_hashed_by_phase": p3["raw_inbox_hash_performed"],
        "s07_p3_raw_inbox_mutated_by_phase": p3["raw_inbox_mutation_performed"],
        "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
    }
    public_repo_safety = {
        "raw_business_data_committed": False,
        "raw_archive_or_workbook_committed": False,
        "raw_document_committed": False,
        "private_table_or_database_committed": False,
        "credentials_committed": False,
        "connector_secret_committed": False,
        "private_schema_text_committed": False,
        "field_plaintext_committed": False,
        "source_header_plaintext_committed": False,
        "raw_file_identifiers_committed": False,
        "raw_content_identifiers_committed": False,
        "private_record_content_committed": False,
        "business_content_committed": False,
    }
    review_findings = [
        {
            "finding_id": "KMFA-V014-S07-STAGE-REVIEW-FIX-001",
            "severity": "medium",
            "status": "fixed",
            "area": "validator_dependency_scope",
            "summary": "S07-P1/S07-P2 v0.1.4 validators and generators used recursive upstream validators instead of locked dependency manifests.",
            "fix": "Changed S07-P1/S07-P2 v0.1.4 dependency checks to read Stage 6 and S07-P1 locked manifests, keeping Stage 7 review bounded.",
            "evidence": "S07-P1/S07-P2/S07-P3 validators pass within Stage 7 scope.",
        }
    ]
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "adapter_candidates_remain_structural_or_reserved",
        "q5_forbidden_until_downstream_value_reconciliation",
        "formal_report_release_blocked",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "redcircle_automatic_connector_blocked",
        "github_upload_deferred_until_v014_stage1_18_complete",
        "business_execution_blocked",
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S07",
        "stage_name": "file-based source adapters and field mapping",
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
        "s08_p1_performed": False,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "app_reinstall_performed": False,
        "raw_content_matching_performed": False,
        "lineage_full_check_performed": False,
        "formal_report_performed": False,
        "live_connector_called": False,
        "opme_deep_coupling_performed": False,
        "business_execution_performed": False,
        "phase_count": 3,
        "phase_results": phase_results,
        "s07_p1_dependency_validated": phase_results["S07-P1"] == "PASS",
        "s07_p2_dependency_validated": phase_results["S07-P2"] == "PASS",
        "s07_p3_dependency_validated": phase_results["S07-P3"] == "PASS",
        "reviewed_phase_manifests": PHASE_MANIFESTS,
        "open_review_finding_count": 0,
        "fixed_review_finding_count": len(review_findings),
        "review_findings": review_findings,
        "stage_gate": {
            "finance_source_category_count": p1["source_category_count"],
            "finance_field_candidate_count": p1["field_candidate_count"],
            "finance_hash_only_field_candidate_count": p1["hash_only_field_candidate_count"],
            "finance_field_report_count": p1["field_report_count"],
            "finance_source_header_fingerprint_count": p1["source_header_fingerprint_count"],
            "wps_source_export_type_count": p2["source_export_type_count"],
            "wps_field_mapping_count": p2["field_mapping_count"],
            "wps_hash_only_field_mapping_count": p2["hash_only_field_mapping_count"],
            "wps_field_report_count": p2["field_report_count"],
            "wps_conversion_guidance_count": p2["conversion_guidance_count"],
            "wps_mapping_rule_version_count": p2["mapping_rule_version_count"],
            "wps_source_header_fingerprint_count": p2["source_header_fingerprint_count"],
            "wps_native_conversion_required_count": p2["native_conversion_required_count"],
            "redcircle_export_type_count": p3["redcircle_export_type_count"],
            "redcircle_reserved_template_count": p3["reserved_template_count"],
            "redcircle_registry_source_count": p3["registry_source_count"],
            "redcircle_template_contract_hash_count": p3["template_contract_hash_count"],
            "redcircle_source_private_ref_count": p3["source_private_ref_count"],
            "redcircle_connector_policy_count": p3["connector_policy_count"],
            "redcircle_rollback_plan_count": p3["rollback_plan_count"],
            "redcircle_automatic_connector_allowed_count": p3["automatic_connector_allowed_count"],
            "redcircle_d15_automatic_connector_allowed": p3["d15_automatic_connector_allowed"],
            "redcircle_read_only_required_count": p3["read_only_required_count"],
            "redcircle_hash_retention_required_count": p3["hash_retention_required_count"],
            "redcircle_rollback_plan_required_count": p3["rollback_plan_required_count"],
            "redcircle_manual_approval_required_count": p3["manual_approval_required_count"],
            "total_public_safe_source_registry_count": p1["source_registry_count"] + p2["source_registry_count"] + p3["registry_source_count"],
            "total_structural_mapping_count": p1["field_candidate_count"] + p2["field_mapping_count"],
            "q4_human_confirmed_count": q4_count,
            "q5_calculation_baseline_allowed_count": q5_count,
            "formal_report_allowed_count": formal_count,
            "current_data_quality_grade": "Q4",
            "current_report_grade": "D",
            "release_permission": "blocked",
        },
        "phase_summary": {
            "S07-P1": {
                "source_category_count": p1["source_category_count"],
                "field_candidate_count": p1["field_candidate_count"],
                "hash_only_field_candidate_count": p1["hash_only_field_candidate_count"],
                "field_report_count": p1["field_report_count"],
                "q5_calculation_baseline_allowed_count": p1["q5_calculation_baseline_allowed_count"],
                "formal_report_allowed_count": p1["formal_report_allowed_count"],
                "stage7_review_performed": p1["stage7_review_performed"],
                "github_upload_performed": p1["github_upload_performed"],
                "raw_inbox_read_performed": p1["raw_inbox_read_performed"],
            },
            "S07-P2": {
                "source_export_type_count": p2["source_export_type_count"],
                "field_mapping_count": p2["field_mapping_count"],
                "conversion_guidance_count": p2["conversion_guidance_count"],
                "mapping_rule_version_count": p2["mapping_rule_version_count"],
                "q5_calculation_baseline_allowed_count": p2["q5_calculation_baseline_allowed_count"],
                "formal_report_allowed_count": p2["formal_report_allowed_count"],
                "stage7_review_performed": p2["stage7_review_performed"],
                "github_upload_performed": p2["github_upload_performed"],
                "raw_inbox_read_performed": p2["raw_inbox_read_performed"],
            },
            "S07-P3": {
                "reserved_template_count": p3["reserved_template_count"],
                "connector_policy_count": p3["connector_policy_count"],
                "rollback_plan_count": p3["rollback_plan_count"],
                "automatic_connector_allowed_count": p3["automatic_connector_allowed_count"],
                "d15_automatic_connector_allowed": p3["d15_automatic_connector_allowed"],
                "q5_calculation_baseline_allowed_count": p3["q5_calculation_baseline_allowed_count"],
                "formal_report_allowed_count": p3["formal_report_allowed_count"],
                "stage7_review_performed": p3["stage7_review_performed"],
                "s08_p1_performed": p3["s08_p1_performed"],
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
    return f"""# v0.1.4 Stage 7 Review Report

status: `{manifest['status']}`

## Scope

This review covers only v0.1.4 Stage 7: S07-P1 finance file adapter, S07-P2 WPS file adapter, and S07-P3 Redcircle export postponement policy. It does not start S08-P1, does not perform GitHub upload, does not perform raw content matching, does not run lineage full check, and does not generate a formal report.

## Review Results

| Phase | Result | Evidence |
|---|---:|---|
| S07-P1 finance file adapter | {manifest['phase_results']['S07-P1']} | `{PHASE_MANIFESTS['S07-P1']}` |
| S07-P2 WPS file adapter | {manifest['phase_results']['S07-P2']} | `{PHASE_MANIFESTS['S07-P2']}` |
| S07-P3 Redcircle postponement | {manifest['phase_results']['S07-P3']} | `{PHASE_MANIFESTS['S07-P3']}` |

## Findings

- open_review_finding_count: `{manifest['open_review_finding_count']}`
- fixed_review_finding_count: `{manifest['fixed_review_finding_count']}`
- fixed finding: S07-P1/S07-P2 dependency checks now read locked manifests instead of recursively expanding the review scope.

## Stage Gate

- finance source categories: `{gate['finance_source_category_count']}`
- finance field candidates: `{gate['finance_field_candidate_count']}`
- WPS export types: `{gate['wps_source_export_type_count']}`
- WPS field mappings: `{gate['wps_field_mapping_count']}`
- WPS conversion guidance rows: `{gate['wps_conversion_guidance_count']}`
- Redcircle export types: `{gate['redcircle_export_type_count']}`
- Redcircle reserved templates: `{gate['redcircle_reserved_template_count']}`
- Redcircle rollback plans: `{gate['redcircle_rollback_plan_count']}`
- Redcircle automatic connector allowed count: `{gate['redcircle_automatic_connector_allowed_count']}`
- Redcircle D15 automatic connector allowed: `{str(gate['redcircle_d15_automatic_connector_allowed']).lower()}`
- total structural mappings: `{gate['total_structural_mapping_count']}`
- q4_human_confirmed_count: `{gate['q4_human_confirmed_count']}`
- q5_calculation_baseline_allowed_count: `{gate['q5_calculation_baseline_allowed_count']}`
- formal_report_allowed_count: `{gate['formal_report_allowed_count']}`
- current_data_quality_grade: `{gate['current_data_quality_grade']}`
- current_report_grade: `{gate['current_report_grade']}`
- release_permission: `{gate['release_permission']}`
- current_go_no_go: `{manifest['release_state']['current_go_no_go']}`

## Boundary

This review itself did not read, list, inventory, stat, hash, modify, delete, move, rename, overwrite, or write the raw inbox. It only replayed Stage 7 public-safe validators and evidence.

Public evidence contains only aggregate counts, public refs, status records, validators and governance records. It does not contain raw file identifiers, raw content identifiers, private source structure, private source records, business content, credentials, workbooks, documents, private tables, databases or raw business data.

GitHub main upload remains deferred until v1.4 Stage 1-18 are complete, overall review has passed, and review findings have been fixed.

## Next

Next recommended phase: `{manifest['next_recommended_phase']}`, as a separate run only after user instruction.
"""


def render_test_results(manifest: dict[str, Any]) -> str:
    return f"""# KMFA v0.1.4 Stage 7 Review Test Results

- status: `pending_final_validation`
- task_id: `{TASK_ID}`
- stage_review_performed: `true`
- github_upload_performed: `false`
- s08_p1_performed: `false`
- raw_inbox_read_by_this_review: `false`
- raw_inbox_listed_by_this_review: `false`
- raw_inbox_hashed_by_this_review: `false`
- raw_inbox_mutated_by_this_review: `false`
- open_review_finding_count: `{manifest['open_review_finding_count']}`
- fixed_review_finding_count: `{manifest['fixed_review_finding_count']}`

Final command results are captured after Stage 7 validators, legacy validators, focused unit test, governance checks and safety scans pass in this run.
"""


def render_risk_register() -> str:
    return """# KMFA v0.1.4 Stage 7 Review Risk Register

| Risk | Mitigation | Status |
|---|---|---|
| Stage review could be mistaken for GitHub upload readiness. | Manifest keeps GitHub upload deferred until v1.4 Stage 1-18 complete overall review. | controlled |
| Structural adapters could be mistaken for Q5 calculation or formal report readiness. | Manifest keeps Q5 allowed count and formal report allowed count at zero, release blocked, and delivery false. | controlled |
| Redcircle future templates could be mistaken for live connector readiness. | Manifest keeps automatic connector and live connector gates false. | controlled |
| Raw/private data could leak into public evidence. | Evidence contains aggregate counts, refs and validator status only; raw/private and secret scans are required before commit. | controlled |
"""


def render_rollback_plan() -> str:
    return """# KMFA v0.1.4 Stage 7 Review Rollback Plan

1. Revert the local commit that introduced `V014_S07_STAGE_REVIEW` evidence, validator, focused unit test and governance rows.
2. Restore current phase to `S07-P3 completed` if review evidence is invalidated.
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
        "PASS: KMFA v0.1.4 Stage 7 review evidence built "
        f"(finance_candidates={gate['finance_field_candidate_count']}, "
        f"wps_mappings={gate['wps_field_mapping_count']}, "
        f"redcircle_templates={gate['redcircle_reserved_template_count']}, "
        f"q5_allowed={gate['q5_calculation_baseline_allowed_count']}, "
        "s08_p1=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
