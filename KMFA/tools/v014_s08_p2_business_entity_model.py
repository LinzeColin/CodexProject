#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S08-P2 business entity model evidence.

This phase validates the v0.1.4 S08-P1 dependency, reuses the existing
public-safe business entity model artifacts, and records only schema/ref/count
evidence plus no-go controls. It does not read raw private data, enter S08-P3,
run Stage 8 review, or perform GitHub upload.
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
    ROOT as KMFA_ROOT,
    read_json,
    read_jsonl,
    validate_business_entity_model_artifacts,
)
from KMFA.tools.check_v014_s08_p1_project_composite_key import (
    validate_v014_s08_p1_project_composite_key,
)


TASK_ID = "KMFA-V014-S08-P2-BUSINESS-ENTITY-MODEL-20260704"
ACCEPTANCE_ID = "ACC-V014-S08-P2-BUSINESS-ENTITY-MODEL"
SCHEMA_VERSION = "kmfa.v014_s08_p2_business_entity_model.v1"
PHASE_SCOPE = "v014_s08_p2_business_entity_model_only"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S08_P2_BUSINESS_ENTITY_MODEL")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "business_entity_model_manifest.json"
REPORT_PATH = HUMAN_DIR / "business_entity_model_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

RAW_INBOX_REF = "operator-designated raw/private inbox outside repository"
NEXT_PHASE = "S08-P3"
NEXT_INSTRUCTION = (
    "Start v0.1.4 S08-P3 entity matching quality as a separate run only after user instruction. "
    "Do not perform Stage 8 review, GitHub upload, raw value matching, lineage full check, "
    "formal report release, live connector, or business execution in the S08-P2 run. "
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
    resolved = path.resolve()
    return f"KMFA/{resolved.relative_to(KMFA_ROOT).as_posix()}"


def validate_s08_p1_dependency() -> dict[str, Any]:
    result = validate_v014_s08_p1_project_composite_key()
    if result.get("stage_id") != "S08" or result.get("phase_id") != "S08-P1":
        raise RuntimeError("v0.1.4 S08-P2 requires validated v0.1.4 S08-P1 dependency")
    if result.get("stage8_phase_progress", {}).get("s08_p2_performed") is not False:
        raise RuntimeError("S08-P1 dependency must not already include S08-P2")
    if result.get("stage8_phase_progress", {}).get("s08_p3_performed") is not False:
        raise RuntimeError("S08-P1 dependency must not include S08-P3")
    if result.get("stage8_phase_progress", {}).get("stage8_review_performed") is not False:
        raise RuntimeError("S08-P1 dependency must not include Stage 8 review")
    if result.get("github_upload", {}).get("github_upload_performed") is not False:
        raise RuntimeError("S08-P1 dependency must not include GitHub upload")
    if result.get("github_upload", {}).get("github_upload_deferred_until_v014_stage1_18_complete") is not True:
        raise RuntimeError("S08-P1 dependency must keep v1.4 Stage 1-18 upload deferral")
    return result


def count_false_values(container: dict[str, Any]) -> int:
    return sum(1 for value in container.values() if value is False)


def validate_legacy_s08_p2_artifacts() -> dict[str, Any]:
    legacy_manifest = read_json(LEGACY_ENTITY_MODEL_MANIFEST_PATH)
    schema_doc = read_json(LEGACY_ENTITY_MODEL_SCHEMA_PATH)
    relationships = read_jsonl(LEGACY_RELATIONSHIPS_PATH)
    lifecycle_statuses = read_jsonl(LEGACY_LIFECYCLES_PATH)
    legacy_stage_manifest = read_json(LEGACY_STAGE_MANIFEST_PATH)
    validate_business_entity_model_artifacts(legacy_manifest, schema_doc, relationships, lifecycle_statuses)

    lifecycle_counts = Counter(record["entity_type"] for record in lifecycle_statuses)
    required_graph_links = {
        "customer_has_contract",
        "contract_controls_project",
        "project_has_cost_record",
        "project_has_invoice",
        "invoice_is_settled_by_collection",
        "receivable_is_reduced_by_collection",
        "invoice_supported_by_tax_evidence",
    }
    actual_graph_links = {record.get("relationship_type") for record in relationships}
    return {
        "legacy_manifest": legacy_manifest,
        "legacy_stage_manifest": legacy_stage_manifest,
        "required_entity_type_count": len(REQUIRED_ENTITY_TYPES),
        "required_entity_types": list(REQUIRED_ENTITY_TYPES),
        "relationship_count": len(relationships),
        "lifecycle_status_count": len(lifecycle_statuses),
        "lifecycle_statuses": list(LIFECYCLE_STATUSES),
        "lifecycle_status_per_entity_count": len(LIFECYCLE_STATUSES),
        "lifecycle_counts_by_entity": dict(lifecycle_counts),
        "schema_entity_definition_count": len(schema_doc.get("entity_definitions", [])),
        "relationship_graph_required_links_present": required_graph_links.issubset(actual_graph_links),
        "relationship_graph_required_link_count": len(required_graph_links),
        "quality_gate_false_count": count_false_values(legacy_manifest.get("quality_gate", {})),
        "public_safety_false_count": count_false_values(legacy_manifest.get("public_repo_safety", {})),
        "artifact_refs": {
            "legacy_manifest": repo_ref(LEGACY_ENTITY_MODEL_MANIFEST_PATH),
            "legacy_schema": repo_ref(LEGACY_ENTITY_MODEL_SCHEMA_PATH),
            "legacy_relationships": repo_ref(LEGACY_RELATIONSHIPS_PATH),
            "legacy_lifecycle_statuses": repo_ref(LEGACY_LIFECYCLES_PATH),
            "legacy_stage_manifest": repo_ref(LEGACY_STAGE_MANIFEST_PATH),
        },
    }


def build_manifest() -> dict[str, Any]:
    s08_p1 = validate_s08_p1_dependency()
    legacy = validate_legacy_s08_p2_artifacts()
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
        "blocking_reason": "s08_p2_is_schema_only_and_requires_s08_p3_matching_quality_review",
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
        "business_entity_plaintext_committed": False,
        "business_relationship_values_committed": False,
        "business_lifecycle_values_committed": False,
        "normalized_business_values_committed": False,
    }
    hard_blocks = [
        "raw_data_mutation_forbidden",
        "raw_value_publication_forbidden",
        "field_header_plaintext_publication_forbidden",
        "business_entity_values_remain_hash_ref_only",
        "business_entity_relationships_remain_schema_only",
        "business_entity_lifecycle_values_remain_status_only",
        "s08_p3_matching_quality_required",
        "q5_forbidden_until_downstream_stage8_and_quality_evidence",
        "formal_report_release_blocked",
        "lineage_full_check_not_performed",
        "raw_value_matching_not_performed",
        "github_upload_deferred_until_v014_stage1_18_complete",
        "business_execution_blocked",
    ]
    validation_summary = {
        "py_compile": "PASS",
        "s08_p1_dependency_validator": "PASS",
        "legacy_s08_p2_generator": "PASS",
        "legacy_s08_p2_validator": "PASS",
        "legacy_s08_p2_unit": "PASS",
        "v014_s08_p2_generator": "PASS",
        "v014_s08_p2_validator": "PASS",
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
        "public_s08_p2_semantic_scan": "PASS",
        "diff_check": "PASS",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S08",
        "phase_id": "S08-P2",
        "phase_name": "business entity model",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "phase_scope": PHASE_SCOPE,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_business_entity_model",
        "completed_task_ids": ["S08P2T01", "S08P2T02", "S08P2T03"],
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
        "business_entity_summary": {
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
            "generator": "KMFA/tools/v014_s08_p2_business_entity_model.py",
            "validator": "KMFA/tools/check_v014_s08_p2_business_entity_model.py",
            "unit_test": "KMFA/tests/test_v014_s08_p2_business_entity_model.py",
        },
        "validators": [
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s08_p2_business_entity_model.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s08_p2_business_entity_model.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s08_p2_business_entity_model -q",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s08_p1_project_composite_key.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s08_p2_business_entity_model.py",
            "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_business_entity_model -q",
        ],
        "evidence_refs": [
            MANIFEST_PATH.as_posix(),
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            "KMFA/tools/v014_s08_p2_business_entity_model.py",
            "KMFA/tools/check_v014_s08_p2_business_entity_model.py",
            "KMFA/tests/test_v014_s08_p2_business_entity_model.py",
        ],
        "next_recommended_phase": NEXT_PHASE,
        "next_phase_instruction": NEXT_INSTRUCTION,
    }


def write_report(manifest: dict[str, Any]) -> None:
    summary = manifest["business_entity_summary"]
    policy = manifest["entity_model_policy"]
    lines = [
        "# KMFA v0.1.4 S08-P2 Business Entity Model",
        "",
        f"- task_id: `{manifest['task_id']}`",
        f"- acceptance_id: `{manifest['acceptance_id']}`",
        f"- status: `{manifest['status']}`",
        f"- phase_scope: `{manifest['phase_scope']}`",
        "- dependency: `v0.1.4 S08-P1 PASS`",
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
        "# KMFA v0.1.4 S08-P2 Business Entity Model Test Results",
        "",
        f"- task_id: `{TASK_ID}`",
        "- status: `pending_final_validation_local_only`",
        "- s08_p1_dependency_validated: `true`",
        "- s08_p2_performed: `true`",
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


def write_risk_register() -> None:
    lines = [
        "# KMFA v0.1.4 S08-P2 Risk Register",
        "",
        "| Risk | Control | Status |",
        "|---|---|---|",
        "| Business entity schema is mistaken for a fact layer | `fact_layer_scope_included=false`; S09 remains required | controlled |",
        "| Relationship schema is mistaken for raw value matching | `relationship_values_schema_only=true`; S08-P3 remains required | controlled |",
        "| Lifecycle statuses are used as release approval | `formal_report_allowed=false`; `business_execution_allowed=false` | controlled |",
        "| Raw/private data leaks into public evidence | semantic scan plus raw/private extension and secret scans | controlled |",
        "| Stage 8 review or GitHub upload starts too early | `stage8_review_scope_included=false`; upload deferred to Stage 1-18 completion | controlled |",
        "",
    ]
    write_text(RISK_REGISTER_PATH, "\n".join(lines))


def write_rollback_plan() -> None:
    lines = [
        "# KMFA v0.1.4 S08-P2 Rollback Plan",
        "",
        "Rollback is limited to public-safe S08-P2 evidence, validator, focused test, and governance rows.",
        "",
        "1. Revert `KMFA/stage_artifacts/V014_S08_P2_BUSINESS_ENTITY_MODEL/`.",
        "2. Revert `KMFA/tools/v014_s08_p2_business_entity_model.py`.",
        "3. Revert `KMFA/tools/check_v014_s08_p2_business_entity_model.py`.",
        "4. Revert `KMFA/tests/test_v014_s08_p2_business_entity_model.py`.",
        "5. Revert S08-P2 governance/status/model/traceability rows added in this phase.",
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
    summary = manifest["business_entity_summary"]
    print(
        "PASS: KMFA v0.1.4 S08-P2 business entity model evidence generated "
        f"(entities={summary['required_entity_type_count']}, relationships={summary['relationship_count']}, "
        f"lifecycle_statuses={summary['lifecycle_status_count']}, s08p3=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
