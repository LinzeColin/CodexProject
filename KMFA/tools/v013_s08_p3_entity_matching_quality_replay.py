#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S08-P3 entity matching quality replay evidence.

This replay validates the v0.1.3 S08-P2 dependency, reuses the public-safe
legacy S08-P3 entity matching quality artifacts, and records the phase-level
no-go / upload-deferred boundary for the v0.1.3 Stage 1-10 run.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v013_s08_p2_business_entity_model_replay import (
    validate_v013_s08_p2_business_entity_model_replay,
)
from KMFA.tools.entity_matching_quality import (
    DEFAULT_OUTPUT_CASES as LEGACY_CASES_PATH,
    DEFAULT_OUTPUT_MANIFEST as LEGACY_QUALITY_MANIFEST_PATH,
    DEFAULT_OUTPUT_REPORT as LEGACY_REPORT_PATH,
    DEFAULT_OUTPUT_REVIEW_QUEUE as LEGACY_REVIEW_QUEUE_PATH,
    DEFAULT_OUTPUT_STAGE_MANIFEST as LEGACY_STAGE_MANIFEST_PATH,
    QUALITY_SCENARIOS,
    read_json,
    read_jsonl,
    validate_entity_matching_quality_artifacts,
)


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S08_P3_ENTITY_MATCHING_QUALITY_REPLAY")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/entity_matching_quality_replay_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/entity_matching_quality_replay_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
TASK_ID = "KMFA-V013-S08-P3-ENTITY-MATCHING-QUALITY-REPLAY-20260703"
SCHEMA_VERSION = "kmfa.v013_s08_p3_entity_matching_quality_replay.v1"
PHASE_SCOPE = "v013_s08_p3_entity_matching_quality_replay_only"
RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 Stage 8 review as a separate run. GitHub main upload remains deferred "
    "until v0.1.3 Stages 1-10 are complete, the whole Stage 1-10 review passes, and findings "
    "are fixed; do not run GitHub upload, raw value matching, lineage full check, formal report "
    "release, live connector, Redcircle automatic connector, or business execution in the S08-P3 run."
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


def validate_s08_p2_dependency() -> dict[str, Any]:
    result = validate_v013_s08_p2_business_entity_model_replay()
    if result.get("stage_id") != "S08" or result.get("phase_id") != "S08-P2":
        raise RuntimeError("v0.1.3 S08-P3 requires validated S08-P2 replay dependency")
    if result.get("s08_p1_performed") is not True:
        raise RuntimeError("S08-P2 dependency must include completed S08-P1")
    if result.get("s08_p2_performed") is not True:
        raise RuntimeError("S08-P2 dependency must be completed")
    if result.get("s08_p3_performed") is not False:
        raise RuntimeError("S08-P2 dependency must not already include S08-P3")
    if result.get("stage8_review_performed") is not False:
        raise RuntimeError("S08-P2 dependency must not include Stage 8 review")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("S08-P2 dependency must not include GitHub upload")
    if result.get("github_upload_deferred_until_stage10_batch") is not True:
        raise RuntimeError("S08-P2 dependency must keep upload deferred")
    return result


def _count_false_values(container: dict[str, Any]) -> int:
    return sum(1 for value in container.values() if value is False)


def validate_legacy_s08_p3_artifacts() -> dict[str, Any]:
    legacy_manifest = read_json(LEGACY_QUALITY_MANIFEST_PATH)
    cases = read_jsonl(LEGACY_CASES_PATH)
    report = read_json(LEGACY_REPORT_PATH)
    review_queue = read_jsonl(LEGACY_REVIEW_QUEUE_PATH)
    stage_manifest = read_json(LEGACY_STAGE_MANIFEST_PATH)
    validate_entity_matching_quality_artifacts(legacy_manifest, cases, report, review_queue)

    risk_summary = Counter(case["risk_level"] for case in cases)
    quality_gate = legacy_manifest.get("quality_gate", {})
    public_safety = legacy_manifest.get("public_repo_safety", {})
    manual_review_case_count = sum(1 for case in cases if case.get("manual_review_required") is True)
    auto_merge_allowed_for_queue_count = sum(1 for item in review_queue if item.get("auto_merge_allowed") is True)

    return {
        "legacy_manifest": legacy_manifest,
        "legacy_stage_manifest": stage_manifest,
        "scenario_count": len(QUALITY_SCENARIOS),
        "quality_scenarios": list(QUALITY_SCENARIOS),
        "quality_case_count": len(cases),
        "manual_review_queue_count": len(review_queue),
        "manual_review_case_count": manual_review_case_count,
        "entity_matching_report_count": legacy_manifest.get("summary", {}).get("entity_matching_report_count"),
        "risk_summary": {
            "high": risk_summary["high"],
            "medium": risk_summary["medium"],
            "low": risk_summary["low"],
        },
        "auto_merge_allowed_for_review_queue_count": auto_merge_allowed_for_queue_count,
        "quality_gate_false_count": _count_false_values(quality_gate),
        "public_safety_false_count": _count_false_values(public_safety),
        "stage_scope": legacy_manifest.get("stage_scope", {}),
        "quality_gate": quality_gate,
        "public_repo_safety": public_safety,
        "artifact_refs": {
            "legacy_manifest": LEGACY_QUALITY_MANIFEST_PATH.as_posix(),
            "legacy_cases": LEGACY_CASES_PATH.as_posix(),
            "legacy_review_queue": LEGACY_REVIEW_QUEUE_PATH.as_posix(),
            "legacy_report": LEGACY_REPORT_PATH.as_posix(),
            "legacy_stage_manifest": LEGACY_STAGE_MANIFEST_PATH.as_posix(),
        },
    }


def build_manifest() -> dict[str, Any]:
    s08_p2 = validate_s08_p2_dependency()
    legacy = validate_legacy_s08_p3_artifacts()
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "entity_matching_values_remain_hash_ref_only",
        "medium_high_risk_auto_merge_forbidden",
        "manual_review_queue_auto_merge_forbidden",
        "stage8_review_not_performed",
        "q5_forbidden_until_stage8_review_and_quality_evidence",
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
        "phase_id": "S08-P3",
        "phase_name": "v0.1.3 entity matching quality replay",
        "task_id": TASK_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_entity_matching_quality_replayed",
        "completed_task_ids": ["S8PCT01", "S8PCT02", "S8PCT03"],
        "acceptance_ids": ["ACC-V013-S08-P3-ENTITY-MATCHING-QUALITY-REPLAY"],
        "s08_p2_dependency_validated": True,
        "s08_p2_dependency_status": s08_p2["status"],
        "legacy_s08_p3_dependency_validated": True,
        "stage8_phase_progress": {
            "completed_phase_count": 3,
            "total_phase_count": 3,
            "derived_percent_bps": 10000,
            "derived_percent_label": "100.00%",
            "s08_p1_performed": True,
            "s08_p2_performed": True,
            "s08_p3_performed": True,
            "stage8_review_performed": False,
        },
        "legacy_s08_p3_summary": {
            "scenario_count": legacy["scenario_count"],
            "quality_scenarios": legacy["quality_scenarios"],
            "quality_case_count": legacy["quality_case_count"],
            "manual_review_queue_count": legacy["manual_review_queue_count"],
            "manual_review_case_count": legacy["manual_review_case_count"],
            "entity_matching_report_count": legacy["entity_matching_report_count"],
            "risk_summary": legacy["risk_summary"],
            "auto_merge_allowed_for_review_queue_count": legacy["auto_merge_allowed_for_review_queue_count"],
        },
        "entity_matching_quality_policy": {
            "scenario_coverage": legacy["quality_scenarios"],
            "medium_high_risk_requires_manual_review": True,
            "manual_review_queue_auto_merge_allowed": False,
            "entity_matching_values_hash_ref_only": True,
            "quality_report_is_formal_report": False,
            "quality_gate_false_count": legacy["quality_gate_false_count"],
            "public_safety_false_count": legacy["public_safety_false_count"],
        },
        "phase_boundaries": {
            "s08_p2_dependency_validated": True,
            "s08_p3_scope_included": True,
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
            "entity_matching_plaintext_committed": False,
            "entity_matching_business_values_committed": False,
            "entity_matching_report_formal_report_committed": False,
        },
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "artifact_refs": {
            **legacy["artifact_refs"],
            "manifest": MANIFEST_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "generator": "KMFA/tools/v013_s08_p3_entity_matching_quality_replay.py",
            "validator": "KMFA/tools/check_v013_s08_p3_entity_matching_quality_replay.py",
            "unit_test": "KMFA/tests/test_v013_s08_p3_entity_matching_quality_replay.py",
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s08_p3_entity_matching_quality_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s08_p3_entity_matching_quality_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s08_p3_entity_matching_quality_replay -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s08_p3_entity_matching_quality.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_entity_matching_quality -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s08_p2_business_entity_model_replay.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_s08_p3_entity_matching_quality_replay.py",
            "KMFA/tools/check_v013_s08_p3_entity_matching_quality_replay.py",
            "KMFA/tests/test_v013_s08_p3_entity_matching_quality_replay.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["legacy_s08_p3_summary"]
    policy = manifest["entity_matching_quality_policy"]
    risk = summary["risk_summary"]
    lines = [
        "# KMFA v0.1.3 S08-P3 Entity Matching Quality Replay",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        "- dependency: `v0.1.3 S08-P2 replay PASS`",
        "- legacy_s08_p3_dependency_validated: `true`",
        f"- scenario_count: `{summary['scenario_count']}`",
        f"- quality_scenarios: `{', '.join(summary['quality_scenarios'])}`",
        f"- quality_case_count: `{summary['quality_case_count']}`",
        f"- manual_review_queue_count: `{summary['manual_review_queue_count']}`",
        f"- entity_matching_report_count: `{summary['entity_matching_report_count']}`",
        f"- risk_summary: `high={risk['high']}; medium={risk['medium']}; low={risk['low']}`",
        f"- auto_merge_allowed_for_review_queue_count: `{summary['auto_merge_allowed_for_review_queue_count']}`",
        f"- public_safety_false_count: `{policy['public_safety_false_count']}`",
        f"- quality_gate_false_count: `{policy['quality_gate_false_count']}`",
        "- medium_high_risk_requires_manual_review: `true`",
        "- manual_review_queue_auto_merge_allowed: `false`",
        "- quality_report_is_formal_report: `false`",
        "",
        "## Boundary",
        "",
        "- s08_p2_dependency_validated: `true`",
        "- s08_p3_scope_included: `true`",
        "- stage8_review_scope_included: `false`",
        "- fact_layer_scope_included: `false`",
        "- lineage_full_check_scope_included: `false`",
        "- report_scope_included: `false`",
        "- ui_scope_included: `false`",
        "- external_connector_scope_included: `false`",
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
            "public-safe matching quality scenarios, risk status, review queue counts, "
            "and validator evidence already present in the repository."
        ),
        "",
        "## Public Safety",
        "",
        (
            "Evidence contains only scenario names, aggregate counts, risk levels, status gates, "
            "validator references, and governance paths."
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
        "# KMFA v0.1.3 S08-P3 Entity Matching Quality Replay Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `pending_final_validation_local_only`",
        "- github_upload_performed: `false`",
        "- raw_dir_read_performed_by_this_phase: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- s08_p2_dependency_validated: `true`",
        "- s08_p3_performed: `true`",
        "- stage8_review_performed: `false`",
        "- fact_layer_scope_included: `false`",
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
    summary = manifest["legacy_s08_p3_summary"]
    print(
        "PASS: KMFA v0.1.3 S08-P3 entity matching quality replay generated "
        f"(scenarios={summary['scenario_count']}, cases={summary['quality_case_count']}, "
        f"review_queue={summary['manual_review_queue_count']}, stage8_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
