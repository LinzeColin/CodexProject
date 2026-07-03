#!/usr/bin/env python3
"""Generate KMFA v0.1.3 S08-P2 business entity model replay evidence.

This replay validates the v0.1.3 S08-P1 dependency, reuses the public-safe
legacy S08-P2 business entity model artifacts, and records the phase-level
no-go / upload-deferred boundary for the v0.1.3 Stage 1-10 run.
"""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.business_entity_model import (
    DEFAULT_OUTPUT_LIFECYCLES as LEGACY_LIFECYCLES_PATH,
    DEFAULT_OUTPUT_MANIFEST as LEGACY_ENTITY_MODEL_MANIFEST_PATH,
    DEFAULT_OUTPUT_RELATIONSHIPS as LEGACY_RELATIONSHIPS_PATH,
    DEFAULT_OUTPUT_SCHEMA as LEGACY_ENTITY_MODEL_SCHEMA_PATH,
    DEFAULT_OUTPUT_STAGE_MANIFEST as LEGACY_STAGE_MANIFEST_PATH,
    LIFECYCLE_STATUSES,
    REQUIRED_ENTITY_TYPES,
    read_json,
    read_jsonl,
    validate_business_entity_model_artifacts,
)
from KMFA.tools.check_v013_s08_p1_project_composite_key_replay import (
    validate_v013_s08_p1_project_composite_key_replay,
)


PUBLIC_OUTPUT_DIR = Path("KMFA/stage_artifacts/V013_S08_P2_BUSINESS_ENTITY_MODEL_REPLAY")
MANIFEST_PATH = PUBLIC_OUTPUT_DIR / "machine/business_entity_model_replay_manifest.json"
REPORT_PATH = PUBLIC_OUTPUT_DIR / "human/business_entity_model_replay_report.md"
TEST_RESULTS_PATH = PUBLIC_OUTPUT_DIR / "human/test_results.md"
TASK_ID = "KMFA-V013-S08-P2-BUSINESS-ENTITY-MODEL-REPLAY-20260703"
SCHEMA_VERSION = "kmfa.v013_s08_p2_business_entity_model_replay.v1"
PHASE_SCOPE = "v013_s08_p2_business_entity_model_replay_only"
RAW_DIR = "/Users/linzezhang/Downloads/KMFA_MetaData"
NEXT_REQUIRED_STEP = (
    "Proceed to v0.1.3 S08-P3 as a separate run. GitHub main upload remains deferred until "
    "v0.1.3 Stages 1-10 are complete, the whole Stage 1-10 review passes, and findings are fixed; "
    "do not run Stage 8 review, GitHub upload, raw value matching, lineage full check, formal report "
    "release, live connector, Redcircle automatic connector, or business execution in the S08-P2 run."
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


def validate_s08_p1_dependency() -> dict[str, Any]:
    result = validate_v013_s08_p1_project_composite_key_replay()
    if result.get("stage_id") != "S08" or result.get("phase_id") != "S08-P1":
        raise RuntimeError("v0.1.3 S08-P2 requires validated S08-P1 replay dependency")
    if result.get("s08_p2_performed") is not False:
        raise RuntimeError("S08-P1 dependency must not already include S08-P2")
    if result.get("s08_p3_performed") is not False:
        raise RuntimeError("S08-P1 dependency must not include S08-P3")
    if result.get("stage8_review_performed") is not False:
        raise RuntimeError("S08-P1 dependency must not include Stage 8 review")
    if result.get("github_upload_performed") is not False:
        raise RuntimeError("S08-P1 dependency must not include GitHub upload")
    if result.get("github_upload_deferred_until_stage10_batch") is not True:
        raise RuntimeError("S08-P1 dependency must keep upload deferred")
    return result


def _count_false_values(container: dict[str, Any]) -> int:
    return sum(1 for value in container.values() if value is False)


def validate_legacy_s08_p2_artifacts() -> dict[str, Any]:
    legacy_manifest = read_json(LEGACY_ENTITY_MODEL_MANIFEST_PATH)
    schema_doc = read_json(LEGACY_ENTITY_MODEL_SCHEMA_PATH)
    relationships = read_jsonl(LEGACY_RELATIONSHIPS_PATH)
    lifecycle_statuses = read_jsonl(LEGACY_LIFECYCLES_PATH)
    stage_manifest = read_json(LEGACY_STAGE_MANIFEST_PATH)
    validate_business_entity_model_artifacts(legacy_manifest, schema_doc, relationships, lifecycle_statuses)

    lifecycle_counts = Counter(record["entity_type"] for record in lifecycle_statuses)
    public_safety = legacy_manifest.get("public_repo_safety", {})
    quality_gate = legacy_manifest.get("quality_gate", {})
    required_graph_pairs = {
        "customer_has_contract",
        "contract_controls_project",
        "project_has_cost_record",
        "project_has_invoice",
        "invoice_is_settled_by_collection",
        "receivable_is_reduced_by_collection",
        "invoice_supported_by_tax_evidence",
    }
    actual_graph_pairs = {record.get("relationship_type") for record in relationships}

    return {
        "legacy_manifest": legacy_manifest,
        "legacy_stage_manifest": stage_manifest,
        "required_entity_type_count": len(REQUIRED_ENTITY_TYPES),
        "required_entity_types": list(REQUIRED_ENTITY_TYPES),
        "relationship_count": len(relationships),
        "lifecycle_status_count": len(lifecycle_statuses),
        "lifecycle_statuses": list(LIFECYCLE_STATUSES),
        "lifecycle_status_per_entity_count": len(LIFECYCLE_STATUSES),
        "lifecycle_counts_by_entity": dict(lifecycle_counts),
        "relationship_graph_required_links_present": required_graph_pairs.issubset(actual_graph_pairs),
        "relationship_graph_required_link_count": len(required_graph_pairs),
        "schema_entity_definition_count": len(schema_doc.get("entity_definitions", [])),
        "stage_scope": legacy_manifest.get("stage_scope", {}),
        "quality_gate": quality_gate,
        "public_repo_safety": public_safety,
        "quality_gate_false_count": _count_false_values(quality_gate),
        "public_safety_false_count": _count_false_values(public_safety),
        "artifact_refs": {
            "legacy_manifest": LEGACY_ENTITY_MODEL_MANIFEST_PATH.as_posix(),
            "legacy_schema": LEGACY_ENTITY_MODEL_SCHEMA_PATH.as_posix(),
            "legacy_relationships": LEGACY_RELATIONSHIPS_PATH.as_posix(),
            "legacy_lifecycle_statuses": LEGACY_LIFECYCLES_PATH.as_posix(),
            "legacy_stage_manifest": LEGACY_STAGE_MANIFEST_PATH.as_posix(),
        },
    }


def build_manifest() -> dict[str, Any]:
    s08_p1 = validate_s08_p1_dependency()
    legacy = validate_legacy_s08_p2_artifacts()
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "business_entity_values_remain_hash_ref_only",
        "business_entity_relationships_remain_schema_only",
        "business_entity_lifecycle_values_remain_status_only",
        "s08_p3_matching_quality_not_performed",
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
        "phase_id": "S08-P2",
        "phase_name": "v0.1.3 business entity model replay",
        "task_id": TASK_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_business_entity_model_replayed",
        "completed_task_ids": ["S8PBT01", "S8PBT02", "S8PBT03"],
        "acceptance_ids": ["ACC-V013-S08-P2-BUSINESS-ENTITY-MODEL-REPLAY"],
        "s08_p1_dependency_validated": True,
        "s08_p1_dependency_status": s08_p1["status"],
        "legacy_s08_p2_dependency_validated": True,
        "stage8_phase_progress": {
            "completed_phase_count": 2,
            "total_phase_count": 3,
            "derived_percent_bps": 6667,
            "derived_percent_label": "66.67%",
            "s08_p1_performed": True,
            "s08_p2_performed": True,
            "s08_p3_performed": False,
            "stage8_review_performed": False,
        },
        "legacy_s08_p2_summary": {
            "required_entity_type_count": legacy["required_entity_type_count"],
            "required_entity_types": legacy["required_entity_types"],
            "relationship_count": legacy["relationship_count"],
            "lifecycle_status_count": legacy["lifecycle_status_count"],
            "lifecycle_statuses": legacy["lifecycle_statuses"],
            "lifecycle_status_per_entity_count": legacy["lifecycle_status_per_entity_count"],
            "lifecycle_counts_by_entity": legacy["lifecycle_counts_by_entity"],
            "schema_entity_definition_count": legacy["schema_entity_definition_count"],
            "relationship_graph_required_links_present": legacy["relationship_graph_required_links_present"],
            "relationship_graph_required_link_count": legacy["relationship_graph_required_link_count"],
        },
        "entity_model_policy": {
            "public_safe_common_fields": [
                "entity_ref",
                "source_ref",
                "source_hash",
                "lifecycle_status",
                "quality_status",
                "evidence_ref",
            ],
            "private_ref_required": True,
            "entity_values_hash_ref_only": True,
            "relationship_values_schema_only": True,
            "lifecycle_values_status_only": True,
            "relationship_graph_required_links_present": legacy["relationship_graph_required_links_present"],
            "quality_gate_false_count": legacy["quality_gate_false_count"],
            "public_safety_false_count": legacy["public_safety_false_count"],
        },
        "phase_boundaries": {
            "s08_p1_dependency_validated": True,
            "s08_p2_scope_included": True,
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
            "business_entity_plaintext_committed": False,
            "business_relationship_values_committed": False,
            "business_lifecycle_values_committed": False,
        },
        "hard_blocks": hard_blocks,
        "hard_block_count": len(hard_blocks),
        "artifact_refs": {
            **legacy["artifact_refs"],
            "manifest": MANIFEST_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "generator": "KMFA/tools/v013_s08_p2_business_entity_model_replay.py",
            "validator": "KMFA/tools/check_v013_s08_p2_business_entity_model_replay.py",
            "unit_test": "KMFA/tests/test_v013_s08_p2_business_entity_model_replay.py",
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s08_p2_business_entity_model_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s08_p2_business_entity_model_replay.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s08_p2_business_entity_model_replay -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s08_p2_business_entity_model.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_business_entity_model -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s08_p1_project_composite_key_replay.py",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            "KMFA/tools/v013_s08_p2_business_entity_model_replay.py",
            "KMFA/tools/check_v013_s08_p2_business_entity_model_replay.py",
            "KMFA/tests/test_v013_s08_p2_business_entity_model_replay.py",
        ],
        "next_required_step": NEXT_REQUIRED_STEP,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["legacy_s08_p2_summary"]
    policy = manifest["entity_model_policy"]
    lines = [
        "# KMFA v0.1.3 S08-P2 Business Entity Model Replay",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        "- dependency: `v0.1.3 S08-P1 replay PASS`",
        "- legacy_s08_p2_dependency_validated: `true`",
        f"- required_entity_type_count: `{summary['required_entity_type_count']}`",
        f"- required_entity_types: `{', '.join(summary['required_entity_types'])}`",
        f"- relationship_count: `{summary['relationship_count']}`",
        f"- lifecycle_status_count: `{summary['lifecycle_status_count']}`",
        f"- lifecycle_status_per_entity_count: `{summary['lifecycle_status_per_entity_count']}`",
        f"- relationship_graph_required_links_present: `{str(summary['relationship_graph_required_links_present']).lower()}`",
        f"- public_safety_false_count: `{policy['public_safety_false_count']}`",
        f"- quality_gate_false_count: `{policy['quality_gate_false_count']}`",
        "- entity_values_hash_ref_only: `true`",
        "- relationship_values_schema_only: `true`",
        "- lifecycle_values_status_only: `true`",
        "",
        "## Boundary",
        "",
        "- s08_p1_dependency_validated: `true`",
        "- s08_p2_scope_included: `true`",
        "- s08_p3_matching_quality_scope_included: `false`",
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
            "public-safe schema, relationship, lifecycle, status, and evidence metadata "
            "already present in the repository."
        ),
        "",
        "## Public Safety",
        "",
        (
            "Evidence contains only entity type names, relationship names, lifecycle status names, "
            "counts, status gates, validator references, and governance paths."
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
        "# KMFA v0.1.3 S08-P2 Business Entity Model Replay Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `pending_final_validation_local_only`",
        "- github_upload_performed: `false`",
        "- raw_dir_read_performed_by_this_phase: `false`",
        "- raw_dir_mutation_performed: `false`",
        "- s08_p1_dependency_validated: `true`",
        "- s08_p2_performed: `true`",
        "- s08_p3_performed: `false`",
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
    summary = manifest["legacy_s08_p2_summary"]
    print(
        "PASS: KMFA v0.1.3 S08-P2 business entity model replay generated "
        f"(entities={summary['required_entity_type_count']}, relationships={summary['relationship_count']}, "
        f"lifecycle_statuses={summary['lifecycle_status_count']}, s08p3=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
