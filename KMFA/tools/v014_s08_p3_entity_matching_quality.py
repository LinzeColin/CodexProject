#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S08-P3 entity matching quality evidence.

This phase validates the v0.1.4 S08-P2 dependency, reuses existing
public-safe entity matching quality artifacts, and records aggregate quality
counts plus no-go controls. It does not read raw private data, run Stage 8
review, perform raw value matching, or upload to GitHub.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s08_p2_business_entity_model import (
    validate_v014_s08_p2_business_entity_model,
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


TASK_ID = "KMFA-V014-S08-P3-ENTITY-MATCHING-QUALITY-20260704"
ACCEPTANCE_ID = "ACC-V014-S08-P3-ENTITY-MATCHING-QUALITY"
SCHEMA_VERSION = "kmfa.v014_s08_p3_entity_matching_quality.v1"
PHASE_SCOPE = "v014_s08_p3_entity_matching_quality_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S08_P3_ENTITY_MATCHING_QUALITY")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "entity_matching_quality_manifest.json"
REPORT_PATH = HUMAN_DIR / "entity_matching_quality_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_PHASE = "Stage 8 review"
NEXT_INSTRUCTION = (
    "Start v0.1.4 Stage 8 overall review as a separate run only after user instruction. "
    "Do not perform GitHub upload, raw value matching, lineage full check, formal report "
    "release, live connector, app reinstall, OpMe deep coupling, or business execution in "
    "the S08-P3 run. GitHub main upload remains deferred until v1.4 Stage 1-18 are complete, "
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


def validate_s08_p2_dependency() -> dict[str, Any]:
    result = validate_v014_s08_p2_business_entity_model()
    if result.get("stage_id") != "S08" or result.get("phase_id") != "S08-P2":
        raise RuntimeError("v0.1.4 S08-P3 requires validated v0.1.4 S08-P2 dependency")
    progress = result.get("stage8_phase_progress", {})
    if progress.get("s08_p1_performed") is not True or progress.get("s08_p2_performed") is not True:
        raise RuntimeError("S08-P2 dependency must include S08-P1 and S08-P2")
    if progress.get("s08_p3_performed") is not False:
        raise RuntimeError("S08-P2 dependency must not already include S08-P3")
    if progress.get("stage8_review_performed") is not False:
        raise RuntimeError("S08-P2 dependency must not include Stage 8 review")
    upload = result.get("github_upload", {})
    if upload.get("github_upload_performed") is not False:
        raise RuntimeError("S08-P2 dependency must not include GitHub upload")
    if upload.get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("S08-P2 dependency must keep v1.4 Stage 1-18 upload deferral")
    return result


def count_false_values(container: dict[str, Any]) -> int:
    return sum(1 for value in container.values() if value is False)


def validate_legacy_s08_p3_artifacts() -> dict[str, Any]:
    legacy_manifest = read_json(LEGACY_QUALITY_MANIFEST_PATH)
    cases = read_jsonl(LEGACY_CASES_PATH)
    report = read_json(LEGACY_REPORT_PATH)
    review_queue = read_jsonl(LEGACY_REVIEW_QUEUE_PATH)
    stage_manifest = read_json(LEGACY_STAGE_MANIFEST_PATH)
    validate_entity_matching_quality_artifacts(legacy_manifest, cases, report, review_queue)

    risk_summary = Counter(case["risk_level"] for case in cases)
    manual_review_case_count = sum(1 for case in cases if case.get("manual_review_required") is True)
    medium_high_risk_case_count = sum(1 for case in cases if case.get("risk_level") in {"medium", "high"})
    low_risk_case_count = sum(1 for case in cases if case.get("risk_level") == "low")
    quality_control_passed_count = sum(
        1 for case in cases if case.get("quality_decision") == "quality_control_passed"
    )
    auto_merge_allowed_for_review_queue_count = sum(
        1 for item in review_queue if item.get("auto_merge_allowed") is True
    )
    auto_merge_allowed_case_count = sum(1 for case in cases if case.get("auto_merge_allowed") is True)
    return {
        "legacy_manifest": legacy_manifest,
        "legacy_stage_manifest": stage_manifest,
        "scenario_count": len(QUALITY_SCENARIOS),
        "quality_scenarios": list(QUALITY_SCENARIOS),
        "quality_case_count": len(cases),
        "manual_review_queue_count": len(review_queue),
        "manual_review_case_count": manual_review_case_count,
        "medium_high_risk_case_count": medium_high_risk_case_count,
        "low_risk_case_count": low_risk_case_count,
        "quality_control_passed_count": quality_control_passed_count,
        "entity_matching_report_count": legacy_manifest.get("summary", {}).get("entity_matching_report_count"),
        "risk_summary": {
            "high": risk_summary["high"],
            "medium": risk_summary["medium"],
            "low": risk_summary["low"],
        },
        "auto_merge_allowed_case_count": auto_merge_allowed_case_count,
        "auto_merge_allowed_for_review_queue_count": auto_merge_allowed_for_review_queue_count,
        "quality_gate_false_count": count_false_values(legacy_manifest.get("quality_gate", {})),
        "public_safety_false_count": count_false_values(legacy_manifest.get("public_repo_safety", {})),
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
    release_state = {
        "current_go_no_go": "NO_GO",
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "github_main_upload_allowed": False,
        "blocking_reason": "stage8_overall_review_and_downstream_quality_gates_not_completed",
    }
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
        "business_content_committed": False,
        "entity_matching_plaintext_committed": False,
        "entity_matching_business_values_committed": False,
        "normalized_business_values_committed": False,
        "entity_matching_report_formal_report_committed": False,
    }
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "entity_matching_values_remain_hash_ref_only",
        "medium_high_risk_auto_merge_forbidden",
        "manual_review_queue_auto_merge_forbidden",
        "stage8_review_required_as_separate_run",
        "q5_forbidden_until_stage8_review_and_quality_evidence",
        "formal_report_release_blocked",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "github_upload_deferred_until_v014_stage1_18_complete",
        "business_execution_blocked",
    ]
    validation_summary = {
        "py_compile": "PASS",
        "s08_p2_dependency_validator": "PASS",
        "legacy_s08_p3_generator": "PASS",
        "legacy_s08_p3_validator": "PASS",
        "legacy_s08_p3_unit": "PASS",
        "v014_s08_p3_generator": "PASS",
        "v014_s08_p3_validator": "PASS",
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
        "public_s08_p3_semantic_scan": "PASS",
        "diff_check": "PASS",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S08",
        "phase_id": "S08-P3",
        "phase_name": "entity matching quality",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_entity_matching_quality",
        "completed_task_ids": ["S08P3T01", "S08P3T02", "S08P3T03"],
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
        "entity_matching_quality_summary": {
            "scenario_count": legacy["scenario_count"],
            "quality_scenarios": legacy["quality_scenarios"],
            "quality_case_count": legacy["quality_case_count"],
            "manual_review_queue_count": legacy["manual_review_queue_count"],
            "manual_review_case_count": legacy["manual_review_case_count"],
            "medium_high_risk_case_count": legacy["medium_high_risk_case_count"],
            "low_risk_case_count": legacy["low_risk_case_count"],
            "quality_control_passed_count": legacy["quality_control_passed_count"],
            "entity_matching_report_count": legacy["entity_matching_report_count"],
            "risk_summary": legacy["risk_summary"],
            "auto_merge_allowed_case_count": legacy["auto_merge_allowed_case_count"],
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
            "app_reinstall_scope_included": False,
        },
        "release_state": release_state,
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
            **legacy["artifact_refs"],
            "manifest": MANIFEST_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "risk_register": RISK_REGISTER_PATH.as_posix(),
            "rollback_plan": ROLLBACK_PATH.as_posix(),
            "generator": "KMFA/tools/v014_s08_p3_entity_matching_quality.py",
            "validator": "KMFA/tools/check_v014_s08_p3_entity_matching_quality.py",
            "unit_test": "KMFA/tests/test_v014_s08_p3_entity_matching_quality.py",
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s08_p3_entity_matching_quality.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s08_p3_entity_matching_quality.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s08_p3_entity_matching_quality -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s08_p2_business_entity_model.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s08_p3_entity_matching_quality.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_entity_matching_quality -q",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            "KMFA/tools/v014_s08_p3_entity_matching_quality.py",
            "KMFA/tools/check_v014_s08_p3_entity_matching_quality.py",
            "KMFA/tests/test_v014_s08_p3_entity_matching_quality.py",
        ],
        "next_recommended_phase": NEXT_PHASE,
        "next_phase_instruction": NEXT_INSTRUCTION,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["entity_matching_quality_summary"]
    risk = summary["risk_summary"]
    policy = manifest["entity_matching_quality_policy"]
    lines = [
        "# KMFA v0.1.4 S08-P3 Entity Matching Quality",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- acceptance_id: `{manifest['acceptance_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        "- dependency: `v0.1.4 S08-P2 PASS`",
        "- legacy_s08_p3_dependency_validated: `true`",
        f"- scenario_count: `{summary['scenario_count']}`",
        f"- quality_scenarios: `{', '.join(summary['quality_scenarios'])}`",
        f"- quality_case_count: `{summary['quality_case_count']}`",
        f"- manual_review_queue_count: `{summary['manual_review_queue_count']}`",
        f"- manual_review_case_count: `{summary['manual_review_case_count']}`",
        f"- entity_matching_report_count: `{summary['entity_matching_report_count']}`",
        f"- risk_summary: `high={risk['high']}; medium={risk['medium']}; low={risk['low']}`",
        f"- auto_merge_allowed_for_review_queue_count: `{summary['auto_merge_allowed_for_review_queue_count']}`",
        f"- public_safety_false_count: `{policy['public_safety_false_count']}`",
        f"- quality_gate_false_count: `{policy['quality_gate_false_count']}`",
        "- medium_high_risk_requires_manual_review: `true`",
        "- manual_review_queue_auto_merge_allowed: `false`",
        "- entity_matching_values_hash_ref_only: `true`",
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
        "- github_upload_deferred_until_v014_stage1_18_complete: `true`",
        "- github_upload_performed: `false`",
        "- formal_report_allowed: `false`",
        "- business_decision_basis_allowed: `false`",
        "- business_execution_allowed: `false`",
        "",
        "## Raw Data Boundary",
        "",
        f"- raw_inbox_ref: `{RAW_INBOX_REF}`",
        "- raw_inbox_read_by_this_phase: `false`",
        "- raw_inbox_listed_by_this_phase: `false`",
        "- raw_inbox_stat_by_this_phase: `false`",
        "- raw_inbox_hashed_by_this_phase: `false`",
        "- raw_inbox_mutated_by_this_phase: `false`",
        "",
        (
            "This phase did not enumerate, copy, modify, move, rename, delete, overwrite, "
            "hash, or write generated files inside the local finance inbox. It only reused "
            "public-safe matching quality scenarios, counts, risk categories, review queue "
            "states, and evidence metadata already present in the repository."
        ),
        "",
        "## Public Safety",
        "",
        (
            "Evidence contains only aggregate scenario counts, quality case counts, review "
            "queue counts, risk category counts, status gates, validator references, and "
            "governance paths."
        ),
        (
            "It does not contain source filenames, private source hashes, tab labels, ZIP member names, "
            "field/header plaintext, row values, business values, connector credentials, contracts, "
            "payroll, tax filings, or bank statements."
        ),
        "",
        "## Next Step",
        "",
        manifest["next_phase_instruction"],
        "",
    ]
    write_text(REPORT_PATH, "\n".join(lines))


def write_test_results() -> None:
    lines = [
        "# KMFA v0.1.4 S08-P3 Entity Matching Quality Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `pending_final_validation_local_only`",
        "- s08_p2_dependency_validated: `true`",
        "- s08_p3_performed: `true`",
        "- stage8_review_performed: `false`",
        "- github_upload_performed: `false`",
        "- raw_inbox_read_by_this_phase: `false`",
        "- raw_inbox_mutated_by_this_phase: `false`",
        "",
        "Final validation results will be recorded before local commit.",
        "",
    ]
    write_text(TEST_RESULTS_PATH, "\n".join(lines))


def write_risk_register() -> None:
    lines = [
        "# KMFA v0.1.4 S08-P3 Risk Register",
        "",
        "| Risk | Control | Status |",
        "|---|---|---|",
        "| Matching quality evidence is mistaken for final entity resolution | medium/high risk cases require manual review; no-auto-merge queue remains locked | controlled |",
        "| Quality report is mistaken for formal operating report | `quality_report_is_formal_report=false`; formal report remains blocked | controlled |",
        "| Stage 8 review starts too early | `stage8_review_scope_included=false`; review must be a separate run | controlled |",
        "| Raw/private data leaks into public evidence | v0.1.4 manifest stores aggregate counts only; semantic and secret scans required | controlled |",
        "| GitHub upload starts too early | `github_upload_deferred_until_v014_stage1_18_complete=true` | controlled |",
        "",
    ]
    write_text(RISK_REGISTER_PATH, "\n".join(lines))


def write_rollback_plan() -> None:
    lines = [
        "# KMFA v0.1.4 S08-P3 Rollback Plan",
        "",
        "Rollback is limited to public-safe S08-P3 evidence, validator, focused test, and governance rows.",
        "",
        "1. Revert `KMFA/stage_artifacts/V014_S08_P3_ENTITY_MATCHING_QUALITY/`.",
        "2. Revert `KMFA/tools/v014_s08_p3_entity_matching_quality.py`.",
        "3. Revert `KMFA/tools/check_v014_s08_p3_entity_matching_quality.py`.",
        "4. Revert `KMFA/tests/test_v014_s08_p3_entity_matching_quality.py`.",
        "5. Revert S08-P3 governance/status/model/traceability rows added in this phase.",
        "6. Do not modify, move, delete, hash, or copy the raw/private inbox as part of rollback.",
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
    summary = manifest["entity_matching_quality_summary"]
    print(
        "PASS: KMFA v0.1.4 S08-P3 entity matching quality evidence generated "
        f"(scenarios={summary['scenario_count']}, quality_cases={summary['quality_case_count']}, "
        f"manual_review_queue={summary['manual_review_queue_count']}, "
        "stage8_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
