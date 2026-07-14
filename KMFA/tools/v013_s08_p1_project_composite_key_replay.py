#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S08-P1 project composite key replay evidence.

This replay validates the v0.1.3 Stage 7 review dependency, reuses the
public-safe legacy S08-P1 composite key artifacts, and records the phase-level
no-go / upload-deferred boundary for the v0.1.3 Stage 1-10 run.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s07_stage_review import validate_v013_s07_stage_review
from KMFA.tools.project_composite_key import (
    DEFAULT_OUTPUT_MANIFEST as LEGACY_COMPOSITE_MANIFEST_PATH,
    DEFAULT_OUTPUT_MATCHES as LEGACY_MATCHES_PATH,
    DEFAULT_OUTPUT_PROFILES as LEGACY_PROFILES_PATH,
    DEFAULT_OUTPUT_REVIEW_QUEUE as LEGACY_REVIEW_QUEUE_PATH,
    DEFAULT_OUTPUT_STAGE_MANIFEST as LEGACY_STAGE_MANIFEST_PATH,
    MATCHING_WEIGHTS_BPS,
    REQUIRED_COMPONENTS,
    THRESHOLDS_BPS,
    read_json,
    read_jsonl,
    validate_project_composite_key_artifacts,
)


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S08_P1_PROJECT_COMPOSITE_KEY_REPLAY")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/project_composite_key_replay_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/project_composite_key_replay_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
TASK_ID = "KMFA-V013-S08-P1-PROJECT-COMPOSITE-KEY-REPLAY-20260703"
SCHEMA_VERSION = "kmfa.v013_s08_p1_project_composite_key_replay.v1"
PHASE_SCOPE = "v013_s08_p1_project_composite_key_replay_only"
RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 S08-P2 as a separate run. GitHub main upload remains deferred until "
    "v0.1.3 Stages 1-10 are complete, the whole Stage 1-10 review passes, and findings are fixed; "
    "do not run S08-P3, Stage 8 review, GitHub upload, raw value matching, lineage full check, "
    "formal report release, live connector, Redcircle automatic connector, or business execution in "
    "the S08-P1 run."
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


def validate_stage7_dependency() -> dict[str, Any]:
    result = validate_v013_s07_stage_review()
    if result.get("stage_id") != "S07":
        raise RuntimeError("v0.1.3 S08-P1 requires validated Stage 7 review dependency")
    if result.get("stage_review_performed") is not True:
        raise RuntimeError("v0.1.3 S08-P1 requires Stage 7 review to be completed")
    if result.get("s08_p1_performed") is not False:
        raise RuntimeError("Stage 7 review dependency must not already include S08-P1")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("Stage 7 review dependency must not include GitHub upload")
    if result.get("github_upload_deferred_until_stage10_batch") is not True:
        raise RuntimeError("Stage 7 review dependency must keep upload deferred")
    return result


def _count_hash_only_profiles(profiles: list[dict[str, Any]]) -> int:
    count = 0
    for profile in profiles:
        component_records = profile.get("components", [])
        if len(component_records) != len(REQUIRED_COMPONENTS):
            continue
        if all("component_private_ref" in record for record in component_records):
            count += 1
    return count


def validate_legacy_s08_p1_artifacts() -> dict[str, Any]:
    legacy_manifest = read_json(LEGACY_COMPOSITE_MANIFEST_PATH)
    profiles = read_jsonl(LEGACY_PROFILES_PATH)
    match_results = read_jsonl(LEGACY_MATCHES_PATH)
    review_queue = read_jsonl(LEGACY_REVIEW_QUEUE_PATH)
    stage_manifest = read_json(LEGACY_STAGE_MANIFEST_PATH)
    validate_project_composite_key_artifacts(legacy_manifest, profiles, match_results, review_queue)

    decision_counts = Counter(result["match_decision"] for result in match_results)
    auto_merge_allowed_for_queue = sum(1 for item in review_queue if item.get("auto_merge_allowed") is True)
    blocked_by_missing_single = sum(1 for result in match_results if result.get("blocked_by_missing_single_field") is True)
    below_strong_review_count = sum(
        1
        for result in match_results
        if result.get("score_bps", 0) < THRESHOLDS_BPS["strong_auto_match"]
        and result.get("manual_review_required") is True
    )
    return {
        "legacy_manifest": legacy_manifest,
        "legacy_stage_manifest": stage_manifest,
        "required_component_count": len(REQUIRED_COMPONENTS),
        "profile_count": len(profiles),
        "match_result_count": len(match_results),
        "manual_review_queue_count": len(review_queue),
        "strong_auto_match_count": decision_counts["strong_auto_match"],
        "human_review_required_count": decision_counts["human_review_required"],
        "hash_only_profile_count": _count_hash_only_profiles(profiles),
        "component_private_ref_count": sum(len(profile.get("components", [])) for profile in profiles),
        "matching_weights_sum_bps": sum(MATCHING_WEIGHTS_BPS.values()),
        "strong_threshold_bps": THRESHOLDS_BPS["strong_auto_match"],
        "human_review_threshold_bps": THRESHOLDS_BPS["human_review"],
        "weak_candidate_threshold_bps": THRESHOLDS_BPS["weak_candidate"],
        "match_decision_counts": dict(decision_counts),
        "auto_merge_allowed_for_review_queue_count": auto_merge_allowed_for_queue,
        "blocked_by_missing_single_field_count": blocked_by_missing_single,
        "below_strong_threshold_manual_review_count": below_strong_review_count,
        "stage_scope": legacy_manifest.get("stage_scope", {}),
        "quality_gate": legacy_manifest.get("quality_gate", {}),
        "artifact_refs": {
            "legacy_manifest": LEGACY_COMPOSITE_MANIFEST_PATH.as_posix(),
            "legacy_profiles": LEGACY_PROFILES_PATH.as_posix(),
            "legacy_match_results": LEGACY_MATCHES_PATH.as_posix(),
            "legacy_manual_review_queue": LEGACY_REVIEW_QUEUE_PATH.as_posix(),
            "legacy_stage_manifest": LEGACY_STAGE_MANIFEST_PATH.as_posix(),
        },
    }


def build_manifest() -> dict[str, Any]:
    s07 = validate_stage7_dependency()
    legacy = validate_legacy_s08_p1_artifacts()
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "project_identity_values_remain_hash_only",
        "manual_review_queue_auto_merge_forbidden",
        "q5_forbidden_until_downstream_stage8_and_quality_evidence",
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
        "stage_id": "S08",
        "phase_id": "S08-P1",
        "phase_name": "v0.1.3 project composite key replay",
        "task_id": TASK_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_project_composite_key_replayed",
        "completed_task_ids": ["S8PAT01", "S8PAT02", "S8PAT03"],
        "acceptance_ids": ["ACC-V013-S08-P1-PROJECT-COMPOSITE-KEY-REPLAY"],
        "s07_stage_review_dependency_validated": True,
        "s07_stage_review_status": s07["status"],
        "legacy_s08_p1_dependency_validated": True,
        "stage8_phase_progress": {
            "completed_phase_count": 1,
            "total_phase_count": 3,
            "derived_percent_bps": 3333,
            "derived_percent_label": "33.33%",
            "s08_p1_performed": True,
            "s08_p2_performed": False,
            "s08_p3_performed": False,
            "stage8_review_performed": False,
        },
        "legacy_s08_p1_summary": {
            "required_component_count": legacy["required_component_count"],
            "profile_count": legacy["profile_count"],
            "match_result_count": legacy["match_result_count"],
            "manual_review_queue_count": legacy["manual_review_queue_count"],
            "strong_auto_match_count": legacy["strong_auto_match_count"],
            "human_review_required_count": legacy["human_review_required_count"],
            "hash_only_profile_count": legacy["hash_only_profile_count"],
            "component_private_ref_count": legacy["component_private_ref_count"],
            "match_decision_counts": legacy["match_decision_counts"],
        },
        "matching_policy": {
            "required_components": list(REQUIRED_COMPONENTS),
            "matching_weights_bps": dict(MATCHING_WEIGHTS_BPS),
            "matching_weights_sum_bps": legacy["matching_weights_sum_bps"],
            "thresholds_bps": dict(THRESHOLDS_BPS),
            "strong_threshold_bps": legacy["strong_threshold_bps"],
            "human_review_threshold_bps": legacy["human_review_threshold_bps"],
            "weak_candidate_threshold_bps": legacy["weak_candidate_threshold_bps"],
            "missing_single_component_blocks_all_matching": False,
            "below_strong_threshold_enters_manual_review": True,
            "auto_merge_allowed_for_review_queue_count": legacy["auto_merge_allowed_for_review_queue_count"],
            "blocked_by_missing_single_field_count": legacy["blocked_by_missing_single_field_count"],
            "below_strong_threshold_manual_review_count": legacy["below_strong_threshold_manual_review_count"],
        },
        "phase_boundaries": {
            "s08_p1_scope_included": True,
            "s08_p2_entity_model_scope_included": False,
            "s08_p3_matching_quality_scope_included": False,
            "stage8_review_scope_included": False,
            "fact_layer_scope_included": False,
            "lineage_full_check_scope_included": False,
            "report_scope_included": False,
            "ui_scope_included": False,
            "external_connector_scope_included": False,
            "github_upload_scope_included": False,
        },
        "quality_gate": {
            "current_data_quality_grade": "Q4",
            "current_report_grade": "D",
            "release_permission": "blocked",
            "q5_calculation_baseline_allowed": False,
            "q5_calculation_baseline_allowed_count": 0,
            "formal_report_allowed": False,
            "formal_report_allowed_count": 0,
            "business_decision_basis_allowed": False,
            "business_execution_allowed": False,
            "delivery_allowed": False,
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
            "project_identity_plaintext_committed": False,
        },
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "artifact_refs": {
            **legacy["artifact_refs"],
            "manifest": MANIFEST_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "generator": "KMFA/tools/v013_s08_p1_project_composite_key_replay.py",
            "validator": "KMFA/tools/check_v013_s08_p1_project_composite_key_replay.py",
            "unit_test": "KMFA/tests/test_v013_s08_p1_project_composite_key_replay.py",
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s08_p1_project_composite_key_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s08_p1_project_composite_key_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s08_p1_project_composite_key_replay -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s08_p1_project_composite_key.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_project_composite_key -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_stage_review.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_s08_p1_project_composite_key_replay.py",
            "KMFA/tools/check_v013_s08_p1_project_composite_key_replay.py",
            "KMFA/tests/test_v013_s08_p1_project_composite_key_replay.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["legacy_s08_p1_summary"]
    policy = manifest["matching_policy"]
    lines = [
        "# KMFA v0.1.3 S08-P1 Project Composite Key Replay",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        "- dependency: `v0.1.3 Stage 7 review PASS`",
        "- legacy_s08_p1_dependency_validated: `true`",
        f"- required_component_count: `{summary['required_component_count']}`",
        f"- profile_count: `{summary['profile_count']}`",
        f"- match_result_count: `{summary['match_result_count']}`",
        f"- manual_review_queue_count: `{summary['manual_review_queue_count']}`",
        f"- strong_auto_match_count: `{summary['strong_auto_match_count']}`",
        f"- human_review_required_count: `{summary['human_review_required_count']}`",
        f"- hash_only_profile_count: `{summary['hash_only_profile_count']}`",
        f"- matching_weights_sum_bps: `{policy['matching_weights_sum_bps']}`",
        f"- strong_threshold_bps: `{policy['strong_threshold_bps']}`",
        f"- human_review_threshold_bps: `{policy['human_review_threshold_bps']}`",
        f"- weak_candidate_threshold_bps: `{policy['weak_candidate_threshold_bps']}`",
        f"- missing_single_component_blocks_all_matching: `{str(policy['missing_single_component_blocks_all_matching']).lower()}`",
        f"- below_strong_threshold_enters_manual_review: `{str(policy['below_strong_threshold_enters_manual_review']).lower()}`",
        f"- auto_merge_allowed_for_review_queue_count: `{policy['auto_merge_allowed_for_review_queue_count']}`",
        "",
        "## Boundary",
        "",
        "- s08_p1_scope_included: `true`",
        "- s08_p2_entity_model_scope_included: `false`",
        "- s08_p3_matching_quality_scope_included: `false`",
        "- stage8_review_scope_included: `false`",
        "- github_upload_deferred_until_stage10_batch: `true`",
        "- github_upload_performed: `false`",
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
            "Evidence contains only component names, counts, integer bps weights, thresholds, "
            "status gates, validator references, and governance paths."
        ),
        (
            "It does not contain source filenames, source hashes from the private inbox, tab labels, "
            "ZIP member names, field/header plaintext, row values, business values, credentials, "
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
        "# KMFA v0.1.3 S08-P1 Project Composite Key Replay Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `pending_final_validation_local_only`",
        "- github_upload_performed: `false`",
        "- raw_dir_read_performed_by_this_phase: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- s08_p2_performed: `false`",
        "- s08_p3_performed: `false`",
        "- stage8_review_performed: `false`",
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
    summary = manifest["legacy_s08_p1_summary"]
    print(
        "PASS: KMFA v0.1.3 S08-P1 project composite key replay generated "
        f"(components={summary['required_component_count']}, profiles={summary['profile_count']}, "
        f"matches={summary['match_result_count']}, review_queue={summary['manual_review_queue_count']}, "
        "s08p2=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
