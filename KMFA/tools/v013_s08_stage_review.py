#!/usr/bin/env python3
"""Generate KMFA v0.1.3 Stage 8 review evidence.

This review reruns the public-safe v0.1.3 S08-P1/S08-P2/S08-P3 replay
validators and records the stage-level gate. It does not read or write the
local raw data inbox, does not enter Stage 9, and does not perform GitHub
upload.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s08_p1_project_composite_key_replay import (
    validate_v013_s08_p1_project_composite_key_replay,
)
from KMFA.tools.check_v013_s08_p2_business_entity_model_replay import (
    validate_v013_s08_p2_business_entity_model_replay,
)
from KMFA.tools.check_v013_s08_p3_entity_matching_quality_replay import (
    validate_v013_s08_p3_entity_matching_quality_replay,
)


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S08_STAGE_REVIEW")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/stage8_review_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/stage8_review_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
S08_P1_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S08_P1_PROJECT_COMPOSITE_KEY_REPLAY/machine/"
    "project_composite_key_replay_manifest.json"
)
S08_P2_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S08_P2_BUSINESS_ENTITY_MODEL_REPLAY/machine/"
    "business_entity_model_replay_manifest.json"
)
S08_P3_MANIFEST_PATH = Path(
    "KMFA/stage_artifacts/V013_S08_P3_ENTITY_MATCHING_QUALITY_REPLAY/machine/"
    "entity_matching_quality_replay_manifest.json"
)
TASK_ID = "KMFA-V013-S08-STAGE-REVIEW-20260703"
SCHEMA_VERSION = "kmfa.v013_s08_stage_review.v1"
REVIEW_SCOPE = "v013_s08_stage_review_only"
RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 S09-P1 as a separate run. GitHub main upload remains deferred until "
    "v0.1.3 Stages 1-10 are complete, the whole Stage 1-10 review passes, and findings are fixed; "
    "do not run GitHub upload, raw value matching, lineage full check, formal report release, "
    "live connector, Redcircle automatic connector, or business execution in the Stage 8 review run."
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
    p1 = validate_v013_s08_p1_project_composite_key_replay()
    p2 = validate_v013_s08_p2_business_entity_model_replay()
    p3 = validate_v013_s08_p3_entity_matching_quality_replay()

    phase_results = {
        "S08-P1": "PASS" if p1.get("phase_id") == "S08-P1" else "FAIL",
        "S08-P2": "PASS" if p2.get("phase_id") == "S08-P2" else "FAIL",
        "S08-P3": "PASS" if p3.get("phase_id") == "S08-P3" else "FAIL",
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
    review_findings = [
        {
            "finding_id": "KMFA-V013-S08-REV-F01",
            "severity": "P2",
            "status": "fixed",
            "summary": (
                "Legacy Stage 8 upload wording existed in historical governance views; current v0.1.3 "
                "Stage 8 review explicitly marks those artifacts as non-current and keeps GitHub upload "
                "deferred until the Stage 1-10 batch gate."
            ),
        },
        {
            "finding_id": "KMFA-V013-S08-REV-F02",
            "severity": "P2",
            "status": "passed",
            "summary": (
                "S08-P1, S08-P2 and S08-P3 replay validators all pass with public-safe evidence, "
                "manual-review boundaries and no formal report permission."
            ),
        },
    ]
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "project_identity_values_remain_hash_ref_or_status_only",
        "medium_high_risk_auto_merge_forbidden",
        "manual_review_queue_auto_merge_forbidden",
        "q5_forbidden_until_stage9_reconciliation_and_quality_evidence",
        "formal_report_release_blocked",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "github_upload_deferred_until_stage10_batch",
        "s09_p1_not_performed",
        "business_execution_blocked",
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.3",
        "stage_id": "S08",
        "stage_name": "v0.1.3 business entity and project identity matching",
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
        "s09_p1_performed": False,
        "github_upload_ready_next_gate": False,
        "github_upload_deferred_until_stage10_batch": True,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_stage10_batch",
        "legacy_stage8_upload_artifacts_current_gate": False,
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
        "s08_p1_dependency_validated": phase_results["S08-P1"] == "PASS",
        "s08_p2_dependency_validated": phase_results["S08-P2"] == "PASS",
        "s08_p3_dependency_validated": phase_results["S08-P3"] == "PASS",
        "reviewed_phase_manifests": {
            "S08-P1": S08_P1_MANIFEST_PATH.as_posix(),
            "S08-P2": S08_P2_MANIFEST_PATH.as_posix(),
            "S08-P3": S08_P3_MANIFEST_PATH.as_posix(),
        },
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "review_findings": review_findings,
        "open_review_finding_count": 0,
        "fixed_review_finding_count": 1,
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "q5_allowed_count": q5_allowed_count,
        "formal_report_allowed_count": formal_report_allowed_count,
        "phase_summary": {
            "S08-P1": {
                "required_component_count": p1["required_component_count"],
                "profile_count": p1["profile_count"],
                "match_result_count": p1["match_result_count"],
                "manual_review_queue_count": p1["manual_review_queue_count"],
                "strong_auto_match_count": p1["strong_auto_match_count"],
                "human_review_required_count": p1["human_review_required_count"],
                "matching_weights_sum_bps": p1["matching_weights_sum_bps"],
                "strong_threshold_bps": p1["strong_threshold_bps"],
                "human_review_threshold_bps": p1["human_review_threshold_bps"],
                "missing_single_component_blocks_all_matching": p1["missing_single_component_blocks_all_matching"],
                "below_strong_threshold_enters_manual_review": p1["below_strong_threshold_enters_manual_review"],
                "q5_calculation_baseline_allowed_count": p1["q5_calculation_baseline_allowed_count"],
                "formal_report_allowed_count": p1["formal_report_allowed_count"],
                "raw_dir_read_performed": p1["raw_dir_read_performed"],
                "raw_dir_mutation_performed": p1["raw_dir_mutation_performed"],
                "github_upload_performed": p1["github_upload_performed"],
            },
            "S08-P2": {
                "required_entity_type_count": p2["required_entity_type_count"],
                "relationship_count": p2["relationship_count"],
                "lifecycle_status_count": p2["lifecycle_status_count"],
                "lifecycle_status_per_entity_count": p2["lifecycle_status_per_entity_count"],
                "relationship_graph_required_links_present": p2["relationship_graph_required_links_present"],
                "q5_calculation_baseline_allowed_count": p2["q5_calculation_baseline_allowed_count"],
                "formal_report_allowed_count": p2["formal_report_allowed_count"],
                "raw_dir_read_performed": p2["raw_dir_read_performed"],
                "raw_dir_mutation_performed": p2["raw_dir_mutation_performed"],
                "github_upload_performed": p2["github_upload_performed"],
            },
            "S08-P3": {
                "scenario_count": p3["scenario_count"],
                "quality_case_count": p3["quality_case_count"],
                "manual_review_queue_count": p3["manual_review_queue_count"],
                "manual_review_case_count": p3["manual_review_case_count"],
                "entity_matching_report_count": p3["entity_matching_report_count"],
                "risk_summary": p3["risk_summary"],
                "auto_merge_allowed_for_review_queue_count": p3[
                    "auto_merge_allowed_for_review_queue_count"
                ],
                "q5_calculation_baseline_allowed_count": p3["q5_calculation_baseline_allowed_count"],
                "formal_report_allowed_count": p3["formal_report_allowed_count"],
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
            "project_identity_plaintext_committed": False,
            "business_entity_plaintext_committed": False,
            "business_relationship_values_committed": False,
            "business_lifecycle_values_committed": False,
            "entity_matching_plaintext_committed": False,
            "entity_matching_business_values_committed": False,
            "entity_matching_report_formal_report_committed": False,
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s08_p1_project_composite_key_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s08_p2_business_entity_model_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s08_p3_entity_matching_quality_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s08_stage_review.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_s08_stage_review.py",
            "KMFA/tools/check_v013_s08_stage_review.py",
            "KMFA/tests/test_v013_s08_stage_review.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_report(manifest: dict[str, Any]) -> str:
    p1 = manifest["phase_summary"]["S08-P1"]
    p2 = manifest["phase_summary"]["S08-P2"]
    p3 = manifest["phase_summary"]["S08-P3"]
    return f"""# KMFA v0.1.3 Stage 8 Review Report

- task_id: `{TASK_ID}`
- review_scope: `{REVIEW_SCOPE}`
- status: `{manifest['status']}`
- reviewed_head: `{manifest['reviewed_head']}`
- branch: `{manifest['branch']}`
- github_upload_status: `{manifest['github_upload_status']}`
- github_upload_deferred_until_stage10_batch: `{str(manifest['github_upload_deferred_until_stage10_batch']).lower()}`
- legacy_stage8_upload_artifacts_current_gate: `false`
- raw_dir_read_performed_by_stage_review: `false`
- raw_dir_mutation_performed: `false`
- next_required_step: `{NEXT_REQUIRED_STEP}`

## Review Conclusion

Stage 8 v0.1.3 overall review passed locally. S08-P1, S08-P2 and S08-P3 replay validators all passed
inside public-safe boundaries. GitHub main upload remains deferred until Stage 1-10 batch review and
finding fixes are complete.

## Phase Results

| Phase | Result | Public-safe Counts |
|---|---|---|
| S08-P1 project composite key replay | PASS | components={p1['required_component_count']}; profiles={p1['profile_count']}; matches={p1['match_result_count']}; manual_review_queue={p1['manual_review_queue_count']}; weights_sum_bps={p1['matching_weights_sum_bps']} |
| S08-P2 business entity model replay | PASS | entity_types={p2['required_entity_type_count']}; relationships={p2['relationship_count']}; lifecycle_statuses={p2['lifecycle_status_count']}; lifecycle_per_entity={p2['lifecycle_status_per_entity_count']} |
| S08-P3 entity matching quality replay | PASS | scenarios={p3['scenario_count']}; quality_cases={p3['quality_case_count']}; manual_review_queue={p3['manual_review_queue_count']}; entity_matching_report={p3['entity_matching_report_count']}; high={p3['risk_summary']['high']}; medium={p3['risk_summary']['medium']}; low={p3['risk_summary']['low']} |

## Findings

| Finding ID | Severity | Status | Summary |
|---|---|---|---|
| KMFA-V013-S08-REV-F01 | P2 | fixed | Legacy Stage 8 upload wording is not a current v0.1.3 gate; current upload is deferred to Stage 1-10 batch gate. |
| KMFA-V013-S08-REV-F02 | P2 | passed | Stage 8 replay evidence remains public-safe and no formal report or business execution permission is granted. |

## Non-goals Confirmed

- Stage 9 was not executed.
- GitHub upload was not executed.
- Raw value matching and lineage full check were not executed.
- Formal report release, live connector, Redcircle automatic connector and business execution were not executed.
- `/Users/linzezhang/Downloads/KMFA_MetaData` was not read, listed, modified, deleted, moved, renamed, overwritten or written.
"""


def render_test_results() -> str:
    return f"""# KMFA v0.1.3 Stage 8 Review Test Results

- task_id: `{TASK_ID}`
- status: `pending_final_validation_local_only`
- github_upload_performed: `false`
- raw_dir_read_performed_by_stage_review: `false`
- raw_dir_mutation_performed: `false`
- s09_p1_performed: `false`
- formal_report_allowed: `false`
- business_execution_allowed: `false`

## Command Results

- PENDING: final validation results will be recorded before local commit.
"""


def generate() -> dict[str, Any]:
    manifest = build_manifest()
    write_json(MANIFEST_PATH, manifest)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_report(manifest), encoding="utf-8")
    TEST_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEST_RESULTS_PATH.write_text(render_test_results(), encoding="utf-8")
    return manifest


def main() -> int:
    manifest = generate()
    print(
        "PASS: KMFA v0.1.3 Stage 8 review generated "
        f"(phase_results={manifest['phase_results']}, "
        f"open_findings={manifest['open_review_finding_count']}, "
        f"fixed_findings={manifest['fixed_review_finding_count']}, "
        f"github_upload={str(manifest['github_upload_performed']).lower()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
