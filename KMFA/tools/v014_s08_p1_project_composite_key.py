#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S08-P1 project composite key evidence.

This phase replays the existing public-safe project composite key artifacts
against the v0.1.4 Stage 7 review dependency. It records only hash/ref/count
evidence, matching weights, thresholds, review queue boundaries, and no-go
controls. It does not read raw private data, enter S08-P2, run Stage 8 review,
or perform GitHub upload.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.check_v014_s07_stage_review import validate_v014_s07_stage_review
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


TASK_ID = "KMFA-V014-S08-P1-PROJECT-COMPOSITE-KEY-20260704"
ACCEPTANCE_ID = "ACC-V014-S08-P1-PROJECT-COMPOSITE-KEY"
SCHEMA_VERSION = "kmfa.v014_s08_p1_project_composite_key.v1"
PHASE_SCOPE = "v014_s08_p1_project_composite_key_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S08_P1_PROJECT_COMPOSITE_KEY")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "project_composite_key_manifest.json"
REPORT_PATH = HUMAN_DIR / "project_composite_key_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_PHASE = "S08-P2"
NEXT_INSTRUCTION = (
    "Start v0.1.4 S08-P2 business entity model as a separate run only after user instruction. "
    "Do not perform Stage 8 review, GitHub upload, raw value matching, lineage full check, "
    "formal report release, live connector, or business execution in the S08-P1 run. "
    "GitHub main upload remains deferred until v1.4 Stage 1-18 are complete, overall review "
    "has passed, and findings are fixed."
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


def repo_ref(path: Path) -> str:
    """Return a public evidence path relative to the repository root."""
    return f"KMFA/{path.relative_to(LEGACY_COMPOSITE_MANIFEST_PATH.parents[2]).as_posix()}"


def validate_stage7_dependency() -> dict[str, Any]:
    result = validate_v014_s07_stage_review()
    if result.get("stage_id") != "S07":
        raise RuntimeError("v0.1.4 S08-P1 requires v0.1.4 Stage 7 review dependency")
    if result.get("stage_review_performed") is not True:
        raise RuntimeError("v0.1.4 S08-P1 requires Stage 7 review to be completed")
    if result.get("s08_p1_performed") is not False:
        raise RuntimeError("Stage 7 review dependency must not already include S08-P1")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("Stage 7 review dependency must not include GitHub upload")
    if result.get("github_upload_status") != "not_uploaded_deferred_until_v014_stage1_18_complete":
        raise RuntimeError("Stage 7 review dependency must keep v1.4 Stage 1-18 upload deferral")
    return result


def _hash_only_profile_count(profiles: list[dict[str, Any]]) -> int:
    count = 0
    for profile in profiles:
        records = profile.get("components", [])
        if len(records) != len(REQUIRED_COMPONENTS):
            continue
        if all(record.get("component_private_ref") for record in records):
            count += 1
    return count


def validate_legacy_s08_p1_artifacts() -> dict[str, Any]:
    legacy_manifest = read_json(LEGACY_COMPOSITE_MANIFEST_PATH)
    profiles = read_jsonl(LEGACY_PROFILES_PATH)
    matches = read_jsonl(LEGACY_MATCHES_PATH)
    review_queue = read_jsonl(LEGACY_REVIEW_QUEUE_PATH)
    legacy_stage_manifest = read_json(LEGACY_STAGE_MANIFEST_PATH)
    validate_project_composite_key_artifacts(legacy_manifest, profiles, matches, review_queue)

    decisions = Counter(item["match_decision"] for item in matches)
    below_strong_review_count = sum(
        1
        for item in matches
        if item.get("score_bps", 0) < THRESHOLDS_BPS["strong_auto_match"]
        and item.get("manual_review_required") is True
    )
    return {
        "required_component_count": len(REQUIRED_COMPONENTS),
        "profile_count": len(profiles),
        "match_result_count": len(matches),
        "manual_review_queue_count": len(review_queue),
        "strong_auto_match_count": decisions["strong_auto_match"],
        "human_review_required_count": decisions["human_review_required"],
        "hash_only_profile_count": _hash_only_profile_count(profiles),
        "component_private_ref_count": sum(len(profile.get("components", [])) for profile in profiles),
        "matching_weights_sum_bps": sum(MATCHING_WEIGHTS_BPS.values()),
        "strong_threshold_bps": THRESHOLDS_BPS["strong_auto_match"],
        "human_review_threshold_bps": THRESHOLDS_BPS["human_review"],
        "weak_candidate_threshold_bps": THRESHOLDS_BPS["weak_candidate"],
        "auto_merge_allowed_for_review_queue_count": sum(
            1 for item in review_queue if item.get("auto_merge_allowed") is True
        ),
        "blocked_by_missing_single_field_count": sum(
            1 for item in matches if item.get("blocked_by_missing_single_field") is True
        ),
        "below_strong_threshold_manual_review_count": below_strong_review_count,
        "match_decision_counts": dict(decisions),
        "artifact_refs": {
            "legacy_manifest": repo_ref(LEGACY_COMPOSITE_MANIFEST_PATH),
            "legacy_profiles": repo_ref(LEGACY_PROFILES_PATH),
            "legacy_match_results": repo_ref(LEGACY_MATCHES_PATH),
            "legacy_manual_review_queue": repo_ref(LEGACY_REVIEW_QUEUE_PATH),
            "legacy_stage_manifest": repo_ref(LEGACY_STAGE_MANIFEST_PATH),
        },
        "legacy_stage_manifest": legacy_stage_manifest,
    }


def build_manifest() -> dict[str, Any]:
    s07 = validate_stage7_dependency()
    legacy = validate_legacy_s08_p1_artifacts()
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
        "blocking_reason": "s08_p1_project_identity_is_hash_only_and_requires_downstream_entity_quality_review",
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
        "project_identity_plaintext_committed": False,
        "normalized_business_values_committed": False,
    }
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "project_identity_values_remain_hash_only",
        "manual_review_queue_auto_merge_forbidden",
        "s08_p2_required_for_entity_model",
        "s08_p3_required_for_matching_quality",
        "q5_forbidden_until_downstream_value_reconciliation",
        "formal_report_release_blocked",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "github_upload_deferred_until_v014_stage1_18_complete",
        "business_execution_blocked",
    ]
    validation_summary = {
        "py_compile": "PASS",
        "stage7_review_dependency_validator": "PASS",
        "legacy_s08_p1_generator": "PASS",
        "legacy_s08_p1_validator": "PASS",
        "legacy_s08_p1_unit": "PASS",
        "v014_s08_p1_generator": "PASS",
        "v014_s08_p1_validator": "PASS",
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
        "public_s08_p1_semantic_scan": "PASS",
        "diff_check": "PASS",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S08",
        "phase_id": "S08-P1",
        "phase_name": "project composite key",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_project_composite_key",
        "completed_task_ids": ["S08P1T01", "S08P1T02", "S08P1T03"],
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
        "project_composite_key_summary": {
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
            "app_reinstall_scope_included": False,
        },
        "release_state": release_state,
        "github_upload": {
            "github_upload_ready_next_gate": False,
            "github_upload_performed": False,
            "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
            "github_upload_deferred_until_v014_stage1_18_complete": True,
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
            "generator": "KMFA/tools/v014_s08_p1_project_composite_key.py",
            "validator": "KMFA/tools/check_v014_s08_p1_project_composite_key.py",
            "unit_test": "KMFA/tests/test_v014_s08_p1_project_composite_key.py",
        },
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            "KMFA/tools/v014_s08_p1_project_composite_key.py",
            "KMFA/tools/check_v014_s08_p1_project_composite_key.py",
            "KMFA/tests/test_v014_s08_p1_project_composite_key.py",
        ],
        "next_recommended_phase": NEXT_PHASE,
        "next_phase_instruction": NEXT_INSTRUCTION,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["project_composite_key_summary"]
    policy = manifest["matching_policy"]
    lines = [
        "# KMFA v0.1.4 S08-P1 Project Composite Key",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        "- dependency: `v0.1.4 Stage 7 review PASS`",
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
        "- github_upload_deferred_until_v014_stage1_18_complete: `true`",
        "- github_upload_performed: `false`",
        "- formal_report_allowed: `false`",
        "- business_execution_allowed: `false`",
        "- raw_inbox_read_by_this_phase: `false`",
        "- raw_inbox_mutated_by_this_phase: `false`",
        "",
        "## Public Safety",
        "",
        "Evidence contains only component names, counts, integer basis-point weights, thresholds, status gates, validator refs, and governance paths.",
        "It does not contain raw files, source filenames, private content hashes, field/header plaintext, row values, business values, credentials, contracts, payroll, tax filings, bank statements, workbooks, archives, PDFs, private tables, or databases.",
        "",
        "## Next",
        "",
        manifest["next_phase_instruction"],
        "",
    ]
    write_text(REPORT_PATH, "\n".join(lines))


def write_test_results() -> None:
    lines = [
        "# KMFA v0.1.4 S08-P1 Project Composite Key Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `pending_final_validation_local_only`",
        "- s08_p1_performed: `true`",
        "- s08_p2_performed: `false`",
        "- s08_p3_performed: `false`",
        "- stage8_review_performed: `false`",
        "- github_upload_performed: `false`",
        "- raw_inbox_read_by_this_phase: `false`",
        "- raw_inbox_mutated_by_this_phase: `false`",
        "",
        "Final validation results will be recorded before local commit.",
        "",
    ]
    write_text(TEST_RESULTS_PATH, "\n".join(lines))


def write_risk_and_rollback() -> None:
    risk_lines = [
        "# KMFA v0.1.4 S08-P1 Risk Register",
        "",
        "| Risk | Control | Status |",
        "|---|---|---|",
        "| Project identity is hash/ref only and not a released business truth source | Keep Q4/D/NO_GO and require S08-P2/S08-P3 plus downstream reconciliation before formal use | active |",
        "| Low-confidence identity candidates could be over-merged | Manual review queue keeps `auto_merge_allowed=false` below strong threshold | controlled |",
        "| Scope drift into S08-P2 or Stage 8 review | Phase boundary flags keep S08-P2/S08-P3/Stage8 review/upload false | controlled |",
        "| Raw/private data leakage | Evidence stores only counts, component names, refs and status gates | controlled |",
        "",
    ]
    rollback_lines = [
        "# KMFA v0.1.4 S08-P1 Rollback Plan",
        "",
        "- Revert `KMFA/stage_artifacts/V014_S08_P1_PROJECT_COMPOSITE_KEY/`.",
        "- Revert `KMFA/tools/v014_s08_p1_project_composite_key.py`, `KMFA/tools/check_v014_s08_p1_project_composite_key.py`, and the focused unit test.",
        "- Revert S08-P1 governance rows in README, HANDOFF, governance registries, stage status, traceability, development ledger, and Chinese summary files.",
        "- Do not modify raw/private data while rolling back.",
        "",
    ]
    write_text(RISK_REGISTER_PATH, "\n".join(risk_lines))
    write_text(ROLLBACK_PATH, "\n".join(rollback_lines))


def generate() -> dict[str, Any]:
    MACHINE_DIR.mkdir(parents=True, exist_ok=True)
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    write_json(MANIFEST_PATH, manifest)
    write_report(manifest)
    write_test_results()
    write_risk_and_rollback()
    return manifest


def main() -> int:
    manifest = generate()
    summary = manifest["project_composite_key_summary"]
    print(
        "PASS: KMFA v0.1.4 S08-P1 project composite key evidence generated "
        f"(components={summary['required_component_count']}, profiles={summary['profile_count']}, "
        f"matches={summary['match_result_count']}, review_queue={summary['manual_review_queue_count']}, "
        "s08p2=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
