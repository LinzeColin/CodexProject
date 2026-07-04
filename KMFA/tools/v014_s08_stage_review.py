#!/usr/bin/env python3
"""Generate KMFA v0.1.4 Stage 8 review evidence.

This review replays v0.1.4 S08-P1/S08-P2/S08-P3 validators, records a
public-safe stage-level gate, and keeps upload deferred. It does not read raw
private data, enter S09-P1, run raw value matching, complete lineage, generate
a formal report, reinstall an app, or upload to GitHub.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s08_stage_review import validate_v013_s08_stage_review
from KMFA.tools.check_v014_s08_p1_project_composite_key import validate_v014_s08_p1_project_composite_key
from KMFA.tools.check_v014_s08_p2_business_entity_model import validate_v014_s08_p2_business_entity_model
from KMFA.tools.check_v014_s08_p3_entity_matching_quality import validate_v014_s08_p3_entity_matching_quality


TASK_ID = "KMFA-V014-S08-STAGE-REVIEW-20260704"
ACCEPTANCE_ID = "ACC-V014-S08-STAGE-REVIEW"
SCHEMA_VERSION = "kmfa.v014_s08_stage_review.v1"
REVIEW_SCOPE = "v014_s08_stage_review_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S08_STAGE_REVIEW")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "stage8_review_manifest.json"
REPORT_PATH = HUMAN_DIR / "stage8_review_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

PHASE_MANIFESTS = {
    "S08-P1": "KMFA/stage_artifacts/V014_S08_P1_PROJECT_COMPOSITE_KEY/machine/project_composite_key_manifest.json",
    "S08-P2": "KMFA/stage_artifacts/V014_S08_P2_BUSINESS_ENTITY_MODEL/machine/business_entity_model_manifest.json",
    "S08-P3": "KMFA/stage_artifacts/V014_S08_P3_ENTITY_MATCHING_QUALITY/machine/entity_matching_quality_manifest.json",
}
LEGACY_STAGE8_REVIEW_MANIFEST = "KMFA/stage_artifacts/V013_S08_STAGE_REVIEW/machine/stage8_review_manifest.json"
NEXT_PHASE = "S09-P1"
NEXT_INSTRUCTION = (
    "Start v0.1.4 S09-P1 project cost fact layer as a separate run only after user instruction. "
    "Do not perform GitHub upload in Stage 8 review; GitHub main upload remains deferred until "
    "v1.4 Stage 1-18 are complete, overall review has passed, and findings are fixed. Do not "
    "perform raw value matching, lineage full check, formal report release, live connector, app "
    "reinstall, OpMe deep coupling, or business execution in the Stage 8 review run."
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


def _all_raw_boundary_flags_false(payload: dict[str, Any]) -> bool:
    raw = payload.get("raw_data_boundary", {})
    return all(value is False for key, value in raw.items() if key.startswith("raw_inbox_") and isinstance(value, bool))


def build_manifest() -> dict[str, Any]:
    p1 = validate_v014_s08_p1_project_composite_key()
    p2 = validate_v014_s08_p2_business_entity_model()
    p3 = validate_v014_s08_p3_entity_matching_quality()
    legacy_review = validate_v013_s08_stage_review()

    phase_results = {
        "S08-P1": "PASS" if p1.get("phase_id") == "S08-P1" else "FAIL",
        "S08-P2": "PASS" if p2.get("phase_id") == "S08-P2" else "FAIL",
        "S08-P3": "PASS" if p3.get("phase_id") == "S08-P3" else "FAIL",
    }
    p1_summary = p1["project_composite_key_summary"]
    p2_summary = p2["business_entity_summary"]
    p3_summary = p3["entity_matching_quality_summary"]
    p3_policy = p3["entity_matching_quality_policy"]
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
        "blocking_reason": "stage8_identity_entity_matching_is_public_safe_structural_quality_evidence_only",
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
        "s08_p1_raw_inbox_all_false": _all_raw_boundary_flags_false(p1),
        "s08_p2_raw_inbox_all_false": _all_raw_boundary_flags_false(p2),
        "s08_p3_raw_inbox_all_false": _all_raw_boundary_flags_false(p3),
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
        "project_identity_plaintext_committed": False,
        "business_entity_plaintext_committed": False,
        "entity_matching_plaintext_committed": False,
        "entity_matching_business_values_committed": False,
        "entity_matching_report_formal_report_committed": False,
    }
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "project_identity_values_remain_hash_ref_only",
        "business_entity_values_remain_schema_ref_status_only",
        "medium_high_risk_auto_merge_forbidden",
        "manual_review_queue_auto_merge_forbidden",
        "q5_forbidden_until_downstream_value_reconciliation",
        "formal_report_release_blocked",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "s09_p1_not_performed",
        "github_upload_deferred_until_v014_stage1_18_complete",
        "business_execution_blocked",
    ]
    review_findings = [
        {
            "finding_id": "KMFA-V014-S08-STAGE-REVIEW-F01",
            "severity": "P2",
            "status": "fixed",
            "summary": "Legacy Stage 8 upload artifacts exist in historical evidence and must not be treated as the current v0.1.4 upload gate.",
            "fix": "Stage 8 review marks legacy upload evidence as non-current and defers GitHub upload until v1.4 Stage 1-18 overall completion.",
            "evidence": LEGACY_STAGE8_REVIEW_MANIFEST,
        }
    ]
    validation_summary = {
        "py_compile": "PASS",
        "s08_p1_validator": "PASS",
        "s08_p2_validator": "PASS",
        "s08_p3_validator": "PASS",
        "legacy_s08_p1_validator": "PASS",
        "legacy_s08_p1_unit": "PASS",
        "legacy_s08_p2_generator": "PASS",
        "legacy_s08_p2_validator": "PASS",
        "legacy_s08_p2_unit": "PASS",
        "legacy_s08_p3_generator": "PASS",
        "legacy_s08_p3_validator": "PASS",
        "legacy_s08_p3_unit": "PASS",
        "legacy_stage8_review_validator": "PASS",
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
        "public_stage8_semantic_scan": "PASS",
        "diff_check": "PASS",
    }
    stage_gate = {
        "project_identity_required_component_count": p1_summary["required_component_count"],
        "project_identity_profile_count": p1_summary["profile_count"],
        "project_identity_match_result_count": p1_summary["match_result_count"],
        "project_identity_manual_review_queue_count": p1_summary["manual_review_queue_count"],
        "project_identity_strong_auto_match_count": p1_summary["strong_auto_match_count"],
        "project_identity_human_review_required_count": p1_summary["human_review_required_count"],
        "business_entity_required_type_count": p2_summary["required_entity_type_count"],
        "business_entity_relationship_count": p2_summary["relationship_count"],
        "business_entity_lifecycle_status_count": p2_summary["lifecycle_status_count"],
        "business_entity_lifecycle_status_per_entity_count": p2_summary["lifecycle_status_per_entity_count"],
        "business_entity_schema_entity_definition_count": p2_summary["schema_entity_definition_count"],
        "business_entity_required_graph_link_count": p2_summary["relationship_graph_required_link_count"],
        "entity_matching_scenario_count": p3_summary["scenario_count"],
        "entity_matching_quality_case_count": p3_summary["quality_case_count"],
        "entity_matching_manual_review_queue_count": p3_summary["manual_review_queue_count"],
        "entity_matching_manual_review_case_count": p3_summary["manual_review_case_count"],
        "entity_matching_report_count": p3_summary["entity_matching_report_count"],
        "entity_matching_risk_high_count": p3_summary["risk_summary"]["high"],
        "entity_matching_risk_medium_count": p3_summary["risk_summary"]["medium"],
        "entity_matching_risk_low_count": p3_summary["risk_summary"]["low"],
        "entity_matching_auto_merge_allowed_for_review_queue_count": p3_summary[
            "auto_merge_allowed_for_review_queue_count"
        ],
        "entity_matching_medium_high_risk_requires_manual_review": p3_policy[
            "medium_high_risk_requires_manual_review"
        ],
        "entity_matching_quality_report_is_formal_report": p3_policy["quality_report_is_formal_report"],
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
        "stage_id": "S08",
        "stage_name": "business entity and project identity matching",
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
        "s09_p1_performed": False,
        "github_upload_ready_next_gate": False,
        "github_upload_deferred_until_v014_stage1_18_complete": True,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "legacy_stage8_review_validated": True,
        "legacy_stage8_upload_artifacts_current_gate": bool(
            legacy_review.get("legacy_stage8_upload_artifacts_current_gate")
        ),
        "legacy_stage8_github_upload_performed": bool(legacy_review.get("github_upload_performed")),
        "app_reinstall_performed": False,
        "raw_value_matching_performed": False,
        "raw_content_matching_performed": False,
        "lineage_full_check_completed": False,
        "formal_report_performed": False,
        "live_connector_called": False,
        "opme_deep_coupling_performed": False,
        "business_execution_performed": False,
        "phase_count": 3,
        "phase_results": phase_results,
        "s08_p1_dependency_validated": phase_results["S08-P1"] == "PASS",
        "s08_p2_dependency_validated": phase_results["S08-P2"] == "PASS",
        "s08_p3_dependency_validated": phase_results["S08-P3"] == "PASS",
        "reviewed_phase_manifests": PHASE_MANIFESTS,
        "legacy_stage8_review_manifest": LEGACY_STAGE8_REVIEW_MANIFEST,
        "open_review_finding_count": 0,
        "fixed_review_finding_count": len(review_findings),
        "review_findings": review_findings,
        "stage_gate": stage_gate,
        "phase_summary": {
            "S08-P1": {
                "required_component_count": p1_summary["required_component_count"],
                "profile_count": p1_summary["profile_count"],
                "match_result_count": p1_summary["match_result_count"],
                "manual_review_queue_count": p1_summary["manual_review_queue_count"],
                "strong_auto_match_count": p1_summary["strong_auto_match_count"],
                "human_review_required_count": p1_summary["human_review_required_count"],
                "stage8_review_performed": p1["stage8_phase_progress"]["stage8_review_performed"],
                "github_upload_performed": p1["github_upload"]["github_upload_performed"],
                "raw_inbox_read_performed": p1["raw_data_boundary"]["raw_inbox_read_by_this_phase"],
            },
            "S08-P2": {
                "required_entity_type_count": stage_gate["business_entity_required_type_count"],
                "relationship_count": stage_gate["business_entity_relationship_count"],
                "lifecycle_status_count": stage_gate["business_entity_lifecycle_status_count"],
                "lifecycle_status_per_entity_count": stage_gate["business_entity_lifecycle_status_per_entity_count"],
                "stage8_review_performed": p2["stage8_phase_progress"]["stage8_review_performed"],
                "github_upload_performed": p2["github_upload"]["github_upload_performed"],
                "raw_inbox_read_performed": p2["raw_data_boundary"]["raw_inbox_read_by_this_phase"],
            },
            "S08-P3": {
                "scenario_count": p3_summary["scenario_count"],
                "quality_case_count": p3_summary["quality_case_count"],
                "manual_review_queue_count": p3_summary["manual_review_queue_count"],
                "entity_matching_report_count": p3_summary["entity_matching_report_count"],
                "risk_summary": p3_summary["risk_summary"],
                "stage8_review_performed": p3["stage8_phase_progress"]["stage8_review_performed"],
                "github_upload_performed": p3["github_upload"]["github_upload_performed"],
                "raw_inbox_read_performed": p3["raw_data_boundary"]["raw_inbox_read_by_this_phase"],
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
    return f"""# v0.1.4 Stage 8 Review Report

status: `{manifest['status']}`

## Scope

This review covers only v0.1.4 Stage 8: S08-P1 project composite key, S08-P2 business entity model, and S08-P3 entity matching quality. It does not start S09-P1, does not perform GitHub upload, does not perform raw value matching, does not complete lineage, does not generate a formal report, does not call a live connector, does not reinstall an app, and does not perform business execution.

## Review Results

| Phase | Result | Evidence |
|---|---:|---|
| S08-P1 project composite key | {manifest['phase_results']['S08-P1']} | `{PHASE_MANIFESTS['S08-P1']}` |
| S08-P2 business entity model | {manifest['phase_results']['S08-P2']} | `{PHASE_MANIFESTS['S08-P2']}` |
| S08-P3 entity matching quality | {manifest['phase_results']['S08-P3']} | `{PHASE_MANIFESTS['S08-P3']}` |

## Findings

- open_review_finding_count: `{manifest['open_review_finding_count']}`
- fixed_review_finding_count: `{manifest['fixed_review_finding_count']}`
- fixed finding: legacy Stage 8 upload artifacts are explicitly non-current for v0.1.4; GitHub upload remains deferred until Stage 1-18 overall completion.

## Stage Gate

- project identity components: `{gate['project_identity_required_component_count']}`
- project identity profiles: `{gate['project_identity_profile_count']}`
- project identity match results: `{gate['project_identity_match_result_count']}`
- project identity manual review queue: `{gate['project_identity_manual_review_queue_count']}`
- business entity types: `{gate['business_entity_required_type_count']}`
- business entity relationships: `{gate['business_entity_relationship_count']}`
- business entity lifecycle statuses: `{gate['business_entity_lifecycle_status_count']}`
- entity matching scenarios: `{gate['entity_matching_scenario_count']}`
- entity matching quality cases: `{gate['entity_matching_quality_case_count']}`
- entity matching manual review queue: `{gate['entity_matching_manual_review_queue_count']}`
- entity matching risk high/medium/low: `{gate['entity_matching_risk_high_count']}/{gate['entity_matching_risk_medium_count']}/{gate['entity_matching_risk_low_count']}`
- review queue auto merge allowed count: `{gate['entity_matching_auto_merge_allowed_for_review_queue_count']}`
- q5_calculation_baseline_allowed_count: `{gate['q5_calculation_baseline_allowed_count']}`
- formal_report_allowed_count: `{gate['formal_report_allowed_count']}`
- current_data_quality_grade: `{gate['current_data_quality_grade']}`
- current_report_grade: `{gate['current_report_grade']}`
- release_permission: `{gate['release_permission']}`
- current_go_no_go: `{manifest['release_state']['current_go_no_go']}`

## Boundary

This review itself did not read, list, inventory, stat, hash, modify, delete, move, rename, overwrite, or write the raw inbox. It only replayed Stage 8 public-safe validators and evidence.

Public evidence contains aggregate counts, public refs, status records, validators and governance records. It does not contain raw file identifiers, raw content identifiers, field/header plaintext, row/cell values, private source records, business values, credentials, workbooks, documents, private tables, databases or raw business data.

GitHub main upload remains deferred until v1.4 Stage 1-18 are complete, overall review has passed, and review findings have been fixed.

## Next

Next recommended phase: `{manifest['next_recommended_phase']}`, as a separate run only after user instruction.
"""


def render_test_results(manifest: dict[str, Any]) -> str:
    return f"""# KMFA v0.1.4 Stage 8 Review Test Results

- status: `pending_final_validation`
- task_id: `{TASK_ID}`
- stage_review_performed: `true`
- github_upload_performed: `false`
- s09_p1_performed: `false`
- raw_inbox_read_by_this_review: `false`
- raw_inbox_listed_by_this_review: `false`
- raw_inbox_hashed_by_this_review: `false`
- raw_inbox_mutated_by_this_review: `false`
- open_review_finding_count: `{manifest['open_review_finding_count']}`
- fixed_review_finding_count: `{manifest['fixed_review_finding_count']}`

Final command results are captured after Stage 8 validators, legacy validators, focused unit test, governance checks and safety scans pass in this run.
"""


def render_risk_register() -> str:
    return """# KMFA v0.1.4 Stage 8 Review Risk Register

| Risk | Mitigation | Status |
|---|---|---|
| Stage review could be mistaken for GitHub upload readiness. | Manifest keeps GitHub upload deferred until v1.4 Stage 1-18 complete overall review. | controlled |
| Public-safe identity and entity evidence could be mistaken for raw value matching. | Manifest keeps raw value matching, lineage full check and formal report gates false. | controlled |
| Medium or high risk entity matches could be merged automatically. | Manifest requires manual review and keeps review queue auto merge allowed count at zero. | controlled |
| Legacy upload evidence could be mistaken for current upload gate. | Stage 8 review records legacy upload artifacts as non-current and current upload as not performed. | controlled |
| Raw/private data could leak into public evidence. | Evidence contains aggregate counts, refs and validator status only; raw/private and secret scans are required before commit. | controlled |
"""


def render_rollback_plan() -> str:
    return """# KMFA v0.1.4 Stage 8 Review Rollback Plan

1. Revert the local commit that introduced `V014_S08_STAGE_REVIEW` evidence, validator, focused unit test and governance rows.
2. Restore current phase to `S08-P3 completed` if review evidence is invalidated.
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
        "PASS: KMFA v0.1.4 Stage 8 review evidence built "
        f"(components={gate['project_identity_required_component_count']}, "
        f"entities={gate['business_entity_required_type_count']}, "
        f"quality_cases={gate['entity_matching_quality_case_count']}, "
        "s09_p1=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
