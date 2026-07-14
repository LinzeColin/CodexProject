#!/usr/bin/env python3
"""Generate KMFA v0.1.4 S07-P3 public-safe Redcircle postponement evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from KMFA.tools.redcircle_postponement_policy import (
    REQUIRED_REDCIRCLE_EXPORT_TYPES,
    build_default_redcircle_postponement_policy,
    build_source_registry,
    validate_redcircle_postponement_policy,
)


TASK_ID = "KMFA-V014-S07-P3-REDCIRCLE-POSTPONEMENT-20260704"
ACCEPTANCE_ID = "ACC-V014-S07-P3-REDCIRCLE-POSTPONEMENT"
SCHEMA_VERSION = "kmfa.v014_s07_p3_redcircle_postponement.v1"
PHASE_SCOPE = "v014_s07_p3_redcircle_postponement_only"
EVIDENCE_TIME = "2026-07-04T11:30:00+10:00"

OUTPUT_DIR = Path("KMFA/stage_artifacts/V014_S07_P3_REDCIRCLE_POSTPONEMENT_POLICY")
MACHINE_DIR = OUTPUT_DIR / "machine"
HUMAN_DIR = OUTPUT_DIR / "human"
MANIFEST_PATH = MACHINE_DIR / "redcircle_postponement_manifest.json"
TEMPLATES_PATH = MACHINE_DIR / "redcircle_reserved_export_templates.jsonl"
CONNECTOR_POLICY_PATH = MACHINE_DIR / "redcircle_connector_postponement_policy.json"
ROLLBACK_PLAN_PATH = MACHINE_DIR / "redcircle_future_rollback_plan.jsonl"
REPORT_PATH = HUMAN_DIR / "redcircle_postponement_report.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_MANIFEST_PATH = Path("KMFA/metadata/schema_maps/v014_s07_p3_redcircle_postponement_manifest.json")
METADATA_TEMPLATES_PATH = Path("KMFA/metadata/schema_maps/v014_s07_p3_redcircle_reserved_export_templates.jsonl")
METADATA_POLICY_PATH = Path("KMFA/metadata/schema_maps/v014_s07_p3_redcircle_postponement_policy.yaml")
METADATA_SOURCE_REGISTRY_PATH = Path("KMFA/metadata/imports/v014_s07_p3_redcircle_export_source_registry.json")

S06_STAGE_REVIEW_MANIFEST_PATH = Path("KMFA/stage_artifacts/V014_S06_STAGE_REVIEW/machine/stage6_review_manifest.json")
S07_P1_MANIFEST_PATH = Path("KMFA/stage_artifacts/V014_S07_P1_FINANCE_FILE_ADAPTER/machine/finance_file_adapter_manifest.json")
S07_P2_MANIFEST_PATH = Path("KMFA/stage_artifacts/V014_S07_P2_WPS_FILE_ADAPTER/machine/wps_file_adapter_manifest.json")

NEXT_PHASE = "S07_STAGE_REVIEW"
NEXT_INSTRUCTION = (
    "Run v0.1.4 Stage 7 review as a separate run after S07-P3 is committed. "
    "Do not perform S08, GitHub upload, app reinstall, raw value matching, formal report, live connector, "
    "or business execution in S07-P3. GitHub main upload remains deferred until v1.4 Stage 1-18 are complete, "
    "overall review has passed, and findings are fixed."
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


def sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def future_controls() -> dict[str, bool]:
    return {
        "read_only_required": True,
        "hash_retention_required": True,
        "rollback_plan_required": True,
        "manual_approval_required": True,
        "source_payload_values_committed": False,
        "source_header_plaintext_committed": False,
        "source_file_committed": False,
    }


def public_repo_safety() -> dict[str, bool]:
    return {
        "source_payload_values_committed": False,
        "source_header_plaintext_committed": False,
        "field_plaintext_committed": False,
        "source_file_committed": False,
        "private_csv_committed": False,
        "redcircle_native_file_committed": False,
        "xlsx_committed": False,
        "pdf_committed": False,
        "zip_committed": False,
        "credentials_committed": False,
    }


def validate_stage6_dependency() -> dict[str, Any]:
    stage6 = read_json(S06_STAGE_REVIEW_MANIFEST_PATH)
    if stage6.get("stage_id") != "S06":
        raise ValueError("Stage 6 dependency manifest did not return S06")
    if stage6.get("status") != "review_passed_local_only_no_go_upload_deferred_until_v014_stage1_18_complete":
        raise ValueError("Stage 6 dependency must be review-passed local-only")
    if stage6.get("github_upload_performed") is not False:
        raise ValueError("Stage 6 dependency must not upload to GitHub")
    if stage6.get("s07_p1_started") is not False:
        raise ValueError("Stage 6 dependency must not have started S07-P1")
    return stage6


def validate_s07_p1_dependency() -> dict[str, Any]:
    s07_p1 = read_json(S07_P1_MANIFEST_PATH)
    if s07_p1.get("stage_id") != "S07" or s07_p1.get("phase_id") != "S07-P1":
        raise ValueError("S07-P1 dependency manifest did not return S07-P1")
    if s07_p1.get("status") != "completed_validated_local_only_no_go_upload_deferred_finance_file_adapter":
        raise ValueError("S07-P1 dependency must be completed and validated")
    if s07_p1.get("s07_p2_performed") is not False:
        raise ValueError("S07-P1 dependency must not perform S07-P2")
    if s07_p1.get("github_upload_performed") is not False:
        raise ValueError("S07-P1 dependency must not upload to GitHub")
    return s07_p1


def validate_s07_p2_dependency() -> dict[str, Any]:
    s07_p2 = read_json(S07_P2_MANIFEST_PATH)
    if s07_p2.get("stage_id") != "S07" or s07_p2.get("phase_id") != "S07-P2":
        raise ValueError("S07-P2 dependency manifest did not return S07-P2")
    if s07_p2.get("status") != "completed_validated_local_only_no_go_upload_deferred_wps_file_adapter":
        raise ValueError("S07-P2 dependency must be completed and validated")
    if s07_p2.get("s07_p3_performed") is not False:
        raise ValueError("S07-P2 dependency must not perform S07-P3")
    if s07_p2.get("github_upload_performed") is not False:
        raise ValueError("S07-P2 dependency must not upload to GitHub")
    return s07_p2


def load_public_safe_redcircle_baseline() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, Any],
]:
    baseline_manifest, templates, connector_policy, rollback_plan = build_default_redcircle_postponement_policy(
        generated_at=EVIDENCE_TIME
    )
    registry = build_source_registry(templates, EVIDENCE_TIME)
    validate_redcircle_postponement_policy(
        baseline_manifest,
        templates,
        connector_policy,
        rollback_plan,
        registry=registry,
    )
    return baseline_manifest, templates, connector_policy, rollback_plan, registry


def build_v014_outputs(
    baseline_templates: list[dict[str, Any]],
    baseline_connector_policy: dict[str, Any],
    baseline_rollback_plan: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], dict[str, Any], str]:
    templates: list[dict[str, Any]] = []
    for template in baseline_templates:
        templates.append(
            {
                "record_type": "v014_redcircle_reserved_export_template",
                "schema_version": "kmfa.v014_redcircle_reserved_export_template.v1",
                "project_id": "KMFA",
                "stage_phase": "S07-P3",
                "generated_at": EVIDENCE_TIME,
                "template_id": template["template_id"],
                "template_status": "reserved_postponed",
                "export_type": template["export_type"],
                "source_ref": template["source_ref"],
                "source_file_private_ref": template["source_file_private_ref"],
                "template_contract_hash": template["template_contract_hash"],
                "template_section_ref_count": len(template.get("template_section_refs", [])),
                "template_contract_ref": "contract:" + sha256_text(
                    f"{template['export_type']}:{template['template_id']}:{template['template_contract_hash']}"
                ).removeprefix("sha256:"),
                "manual_export_file_allowed": True,
                "automatic_connector_allowed": False,
                "d15_file_mvp_automatic_connector_allowed": False,
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
                "future_ingestion_controls": future_controls(),
                "quality_state": {
                    "machine_candidate_quality_grade": "Q1_reserved_template",
                    "q4_human_confirmed": False,
                    "q5_calculation_baseline_allowed": False,
                    "formal_report_allowed": False,
                },
                "public_repo_safety": public_repo_safety(),
                "next_required_phase": "Stage 7 review before downstream lineage or fact layer use",
            }
        )

    connector_policy = {
        "record_type": "v014_redcircle_connector_postponement_policy",
        "schema_version": "kmfa.v014_redcircle_connector_postponement_policy.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P3",
        "generated_at": EVIDENCE_TIME,
        "connector_status": baseline_connector_policy["connector_status"],
        "d15_file_mvp_automatic_connector_allowed": False,
        "automatic_connector_allowed": False,
        "external_connector_included": False,
        "manual_export_file_allowed": True,
        "covered_export_types": list(REQUIRED_REDCIRCLE_EXPORT_TYPES),
        "future_connector_controls": future_controls(),
        "hard_block_refs": [
            "block:redcircle-automatic-connector-before-stage7-review",
            "block:missing-readonly-contract",
            "block:missing-hash-retention",
            "block:missing-rollback-plan",
            "block:missing-manual-approval",
        ],
        "public_repo_safety": public_repo_safety(),
    }

    rollback_plan: list[dict[str, Any]] = []
    for item in baseline_rollback_plan:
        rollback_plan.append(
            {
                "record_type": "v014_redcircle_future_rollback_plan",
                "schema_version": "kmfa.v014_redcircle_future_rollback_plan.v1",
                "project_id": "KMFA",
                "stage_phase": "S07-P3",
                "generated_at": EVIDENCE_TIME,
                "rollback_plan_id": item["rollback_plan_id"],
                "export_type": item["export_type"],
                "source_ref": item["source_ref"],
                "rollback_status": "required_before_ingestion",
                "read_only_required": True,
                "hash_retention_required": True,
                "rollback_plan_required": True,
                "manual_approval_required": True,
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
                "trigger_ref_count": len(item.get("rollback_trigger_refs", [])),
                "action_ref_count": len(item.get("rollback_actions", [])),
            }
        )

    registry = {
        "record_type": "v014_redcircle_export_source_registry",
        "schema_version": "kmfa.v014_redcircle_export_source_registry.v1",
        "project_id": "KMFA",
        "stage_phase": "S07-P3",
        "generated_at": EVIDENCE_TIME,
        "registry_status": "reserved_templates_only_no_connector",
        "sources": [
            {
                "record_type": "v014_redcircle_export_source",
                "schema_version": "kmfa.v014_redcircle_export_source.v1",
                "project_id": "KMFA",
                "stage_phase": "S07-P3",
                "source_ref": template["source_ref"],
                "export_type": template["export_type"],
                "template_id": template["template_id"],
                "template_contract_hash": template["template_contract_hash"],
                "source_file_private_ref": template["source_file_private_ref"],
                "template_status": template["template_status"],
                "manual_export_file_allowed": True,
                "automatic_connector_allowed": False,
                "read_only_required": True,
                "hash_retention_required": True,
                "rollback_plan_required": True,
                "manual_approval_required": True,
                "raw_layer_write_allowed": False,
                "raw_source_mutation_allowed": False,
                "public_repo_safety": public_repo_safety(),
            }
            for template in templates
        ],
        "public_repo_safety": public_repo_safety(),
    }
    policy_yaml = "\n".join(
        [
            'schema_version: "kmfa.v014_redcircle_postponement_policy.v1"',
            'project_id: "KMFA"',
            'stage_phase: "S07-P3"',
            'policy_status: "reserved_templates_only_no_connector"',
            "required_export_type_count: 4",
            "mvp_scope:",
            "  d15_file_mvp_automatic_connector_allowed: false",
            "  manual_export_file_allowed: true",
            "future_connector_controls:",
            "  read_only_required: true",
            "  hash_retention_required: true",
            "  rollback_plan_required: true",
            "  manual_approval_required: true",
            "public_repo_policy:",
            "  source_payload_values_committed: false",
            "  source_header_plaintext_committed: false",
            "  source_file_committed: false",
            "  private_csv_committed: false",
            "out_of_scope:",
            "  automatic_connector_included: false",
            "  facts_layer_write_included: false",
            "  formal_report_generation_included: false",
            "  stage7_review_included: false",
            "  s08_p1_included: false",
            "  github_upload_included: false",
            "",
        ]
    )
    return templates, connector_policy, rollback_plan, registry, policy_yaml


def build_manifest(
    stage6: dict[str, Any],
    s07_p1: dict[str, Any],
    s07_p2: dict[str, Any],
    legacy_manifest: dict[str, Any],
    templates: list[dict[str, Any]],
    connector_policy: dict[str, Any],
    rollback_plan: list[dict[str, Any]],
    registry: dict[str, Any],
) -> dict[str, Any]:
    redcircle_summary = {
        "redcircle_export_type_count": len(REQUIRED_REDCIRCLE_EXPORT_TYPES),
        "reserved_template_count": len(templates),
        "registry_source_count": len(registry["sources"]),
        "template_contract_hash_count": sum(1 for row in templates if str(row["template_contract_hash"]).startswith("sha256:")),
        "source_private_ref_count": sum(1 for row in registry["sources"] if row.get("source_file_private_ref")),
        "connector_policy_count": 1,
        "rollback_plan_count": len(rollback_plan),
        "automatic_connector_allowed_count": sum(1 for row in templates if row.get("automatic_connector_allowed") is True),
        "d15_automatic_connector_allowed": connector_policy["d15_file_mvp_automatic_connector_allowed"],
        "read_only_required_count": sum(1 for row in templates if row["future_ingestion_controls"]["read_only_required"]),
        "hash_retention_required_count": sum(1 for row in templates if row["future_ingestion_controls"]["hash_retention_required"]),
        "rollback_plan_required_count": sum(1 for row in templates if row["future_ingestion_controls"]["rollback_plan_required"]),
        "manual_approval_required_count": sum(1 for row in templates if row["future_ingestion_controls"]["manual_approval_required"]),
        "q4_human_confirmed_count": sum(1 for row in templates if row["quality_state"]["q4_human_confirmed"]),
        "q5_calculation_baseline_allowed_count": sum(
            1 for row in templates if row["quality_state"]["q5_calculation_baseline_allowed"]
        ),
        "formal_report_allowed_count": sum(1 for row in templates if row["quality_state"]["formal_report_allowed"]),
        "legacy_reserved_template_count": legacy_manifest["summary"]["reserved_template_count"],
        "legacy_rollback_plan_count": legacy_manifest["summary"]["rollback_plan_count"],
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": "KMFA",
        "version": "0.1.4",
        "stage_id": "S07",
        "stage_name": "file-based source adapters and field mapping",
        "phase_id": "S07-P3",
        "phase_name": "Redcircle export postponement policy",
        "phase_scope": PHASE_SCOPE,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "evidence_time": EVIDENCE_TIME,
        "reviewed_head": git_output(["rev-parse", "HEAD"]),
        "worktree": git_output(["rev-parse", "--show-toplevel"]),
        "branch": git_output(["branch", "--show-current"]),
        "remote": git_output(["remote", "get-url", "origin"]),
        "status": "completed_validated_local_only_no_go_upload_deferred_redcircle_postponement",
        "completed_task_ids": ["S07P3T01", "S07P3T02", "S07P3T03"],
        "s06_stage_review_dependency_validated": True,
        "s06_dependency_ref": S06_STAGE_REVIEW_MANIFEST_PATH.as_posix(),
        "s06_dependency_status": stage6["status"],
        "s07_p1_dependency_validated": True,
        "s07_p1_dependency_ref": S07_P1_MANIFEST_PATH.as_posix(),
        "s07_p1_dependency_status": s07_p1["status"],
        "s07_p2_dependency_validated": True,
        "s07_p2_dependency_ref": S07_P2_MANIFEST_PATH.as_posix(),
        "s07_p2_dependency_status": s07_p2["status"],
        "legacy_redcircle_postponement_validated": True,
        "redcircle_summary": redcircle_summary,
        "metadata_outputs": {
            "manifest_ref": METADATA_MANIFEST_PATH.as_posix(),
            "source_registry_ref": METADATA_SOURCE_REGISTRY_PATH.as_posix(),
            "reserved_templates_ref": METADATA_TEMPLATES_PATH.as_posix(),
            "postponement_policy_ref": METADATA_POLICY_PATH.as_posix(),
            "connector_policy_ref": CONNECTOR_POLICY_PATH.as_posix(),
            "rollback_plan_ref": ROLLBACK_PLAN_PATH.as_posix(),
        },
        "stage_scope": {
            "redcircle_postponement_policy": True,
            "finance_scope_included": False,
            "wps_scope_included": False,
            "stage7_review_included": False,
            "s08_p1_included": False,
            "external_connector_included": False,
            "facts_layer_write_included": False,
            "lineage_full_check_included": False,
            "formal_report_generation_included": False,
            "github_upload_included": False,
        },
        "mvp_scope": {
            "d15_file_mvp_automatic_connector_allowed": False,
            "manual_export_file_allowed": True,
            "reserved_templates_only": True,
        },
        "quality_gate": {
            "candidate_quality_grade": "Q1_reserved_template",
            "requires_stage7_review_before_downstream_use": True,
            "q4_human_confirmed_count": 0,
            "q5_calculation_baseline_allowed_count": 0,
            "formal_report_allowed_count": 0,
            "current_data_quality_grade": "Q4",
            "current_report_grade": "D",
            "release_permission": "blocked",
        },
        "raw_data_boundary": {
            "raw_inbox_ref": RAW_INBOX_REF,
            "codex_read_required_by_this_phase": False,
            "codex_read_performed_by_this_phase": False,
            "codex_list_performed_by_this_phase": False,
            "codex_stat_performed_by_this_phase": False,
            "codex_hash_performed_by_this_phase": False,
            "codex_modify_allowed": False,
            "codex_delete_allowed": False,
            "codex_move_allowed": False,
            "codex_rename_allowed": False,
            "codex_overwrite_allowed": False,
            "codex_generate_inside_allowed": False,
            "github_commit_allowed": False,
            "private_runtime_output_dir": "KMFA/.codex_private_runtime/",
        },
        "raw_inbox_read_performed": False,
        "raw_inbox_list_performed": False,
        "raw_inbox_stat_performed": False,
        "raw_inbox_hash_performed": False,
        "raw_inbox_mutation_performed": False,
        "raw_layer_write_allowed": False,
        "raw_source_mutation_allowed": False,
        "raw_content_matching_performed": False,
        "business_field_value_parsing_performed": False,
        "source_header_plaintext_committed": False,
        "field_plaintext_committed": False,
        "s07_p1_performed": False,
        "s07_p2_performed": False,
        "s07_p3_performed": True,
        "stage7_review_performed": False,
        "s08_p1_performed": False,
        "github_upload_performed": False,
        "github_upload_status": "not_uploaded_deferred_until_v014_stage1_18_complete",
        "delivery_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "current_data_quality_grade": "Q4",
        "current_report_grade": "D",
        "release_permission": "blocked",
        "public_repo_safety": public_repo_safety(),
        "validation_summary": {
            "generator": "PASS",
            "s06_stage_review_dependency": "PASS",
            "s07_p1_dependency": "PASS",
            "s07_p2_dependency": "PASS",
            "legacy_redcircle_postponement": "PASS",
            "s07_p3_validator": "PENDING_FINAL_VALIDATION",
            "focused_unit_test": "PENDING_FINAL_VALIDATION",
            "legacy_redcircle_validator": "PENDING_FINAL_VALIDATION",
            "legacy_redcircle_unit_test": "PENDING_FINAL_VALIDATION",
            "no_omission_check": "PENDING_FINAL_VALIDATION",
            "no_float_money_check": "PENDING_FINAL_VALIDATION",
            "governance_validator": "PENDING_FINAL_VALIDATION",
            "lean_governance_validator": "PENDING_FINAL_VALIDATION",
            "governance_sync_validator": "PENDING_FINAL_VALIDATION",
            "structured_parse": "PENDING_FINAL_VALIDATION",
            "raw_private_scan": "PENDING_FINAL_VALIDATION",
            "secret_scan": "PENDING_FINAL_VALIDATION",
            "public_s07_p3_semantic_scan": "PENDING_FINAL_VALIDATION",
            "diff_check": "PENDING_FINAL_VALIDATION",
        },
        "evidence_refs": [
            REPORT_PATH.as_posix(),
            TEST_RESULTS_PATH.as_posix(),
            RISK_REGISTER_PATH.as_posix(),
            ROLLBACK_PATH.as_posix(),
            MANIFEST_PATH.as_posix(),
            TEMPLATES_PATH.as_posix(),
            CONNECTOR_POLICY_PATH.as_posix(),
            ROLLBACK_PLAN_PATH.as_posix(),
            METADATA_MANIFEST_PATH.as_posix(),
            METADATA_SOURCE_REGISTRY_PATH.as_posix(),
            METADATA_TEMPLATES_PATH.as_posix(),
            METADATA_POLICY_PATH.as_posix(),
            "KMFA/tools/v014_s07_p3_redcircle_postponement.py",
            "KMFA/tools/check_v014_s07_p3_redcircle_postponement.py",
            "KMFA/tests/test_v014_s07_p3_redcircle_postponement.py",
        ],
        "next_recommended_phase": NEXT_PHASE,
        "next_phase_instruction": NEXT_INSTRUCTION,
    }


def write_policy_yaml(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_human_evidence(manifest: dict[str, Any]) -> None:
    summary = manifest["redcircle_summary"]
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S07-P3 Redcircle Postponement",
                "",
                f"- task_id: `{TASK_ID}`",
                "- status: `completed_validated_local_only_no_go_upload_deferred_redcircle_postponement`",
                "- scope: `S07-P3 only`",
                f"- s06_stage_review_dependency_validated: `{str(manifest['s06_stage_review_dependency_validated']).lower()}`",
                f"- s07_p1_dependency_validated: `{str(manifest['s07_p1_dependency_validated']).lower()}`",
                f"- s07_p2_dependency_validated: `{str(manifest['s07_p2_dependency_validated']).lower()}`",
                f"- redcircle_export_type_count: `{summary['redcircle_export_type_count']}`",
                f"- reserved_template_count: `{summary['reserved_template_count']}`",
                f"- registry_source_count: `{summary['registry_source_count']}`",
                f"- template_contract_hash_count: `{summary['template_contract_hash_count']}`",
                f"- rollback_plan_count: `{summary['rollback_plan_count']}`",
                f"- automatic_connector_allowed_count: `{summary['automatic_connector_allowed_count']}`",
                f"- read_only_required_count: `{summary['read_only_required_count']}`",
                f"- hash_retention_required_count: `{summary['hash_retention_required_count']}`",
                f"- rollback_plan_required_count: `{summary['rollback_plan_required_count']}`",
                f"- manual_approval_required_count: `{summary['manual_approval_required_count']}`",
                f"- q4_human_confirmed_count: `{summary['q4_human_confirmed_count']}`",
                f"- q5_calculation_baseline_allowed_count: `{summary['q5_calculation_baseline_allowed_count']}`",
                f"- formal_report_allowed_count: `{summary['formal_report_allowed_count']}`",
                f"- current_data_quality_grade: `{manifest['current_data_quality_grade']}`",
                f"- current_report_grade: `{manifest['current_report_grade']}`",
                f"- release_permission: `{manifest['release_permission']}`",
                f"- github_upload_status: `{manifest['github_upload_status']}`",
                "",
                "## Boundary",
                "",
                "- This phase reserves Redcircle export template contracts and keeps automatic Redcircle connector access postponed.",
                "- It does not read, list, inventory, stat, hash, modify, delete, move, rename, overwrite, or write the operator-designated raw/private inbox.",
                "- Public evidence keeps export types, template ids, private refs, hashes, aggregate counts and control flags only.",
                "- It does not publish source headers, raw file names, source values, credentials, workbooks, documents, private tables, databases or raw business data.",
                "- Stage 7 review, S08, GitHub upload, raw content matching, formal report, live connector and business execution remain out of scope.",
                "",
                "## Next",
                "",
                manifest["next_phase_instruction"],
                "",
            ]
        ),
        encoding="utf-8",
    )
    TEST_RESULTS_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S07-P3 Redcircle Postponement Test Results",
                "",
                "- status: `pending_final_validation`",
                f"- task_id: `{TASK_ID}`",
                "- generator: `PASS`",
                "- s06_stage_review_dependency: `PASS`",
                "- s07_p1_dependency: `PASS`",
                "- s07_p2_dependency: `PASS`",
                "- legacy_redcircle_postponement: `PASS`",
                "- stage7_review_performed: `false`",
                "- s08_p1_performed: `false`",
                "- github_upload_performed: `false`",
                "- raw_inbox_read_performed: `false`",
                "- raw_inbox_mutation_performed: `false`",
                "",
                "Final command results are captured after validator, focused unit test, governance checks and safety scans pass in this run.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    RISK_REGISTER_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S07-P3 Risk Register",
                "",
                "| Risk | Mitigation | Status |",
                "|---|---|---|",
                "| Redcircle reserved templates could be mistaken for connector readiness. | Connector policy explicitly blocks automatic access during the D15 file MVP. | controlled |",
                "| Future ingestion could mutate source or derived state. | Read-only, hash retention, rollback plan and manual approval are required before future use. | controlled |",
                "| Phase completion could be mistaken for Stage 7 completion. | Manifest keeps Stage 7 review and S08 false; next phase is Stage 7 review. | controlled |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    ROLLBACK_PATH.write_text(
        "\n".join(
            [
                "# KMFA v0.1.4 S07-P3 Rollback Plan",
                "",
                "1. Revert the local commit containing `V014_S07_P3_REDCIRCLE_POSTPONEMENT_POLICY` artifacts and v014 Redcircle metadata rows.",
                "2. Re-run S07-P1 and S07-P2 validators to confirm dependency evidence is unchanged.",
                "3. Re-run S07-P3 after the reserved template contract or connector postponement policy is corrected.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_outputs() -> dict[str, Any]:
    stage6 = validate_stage6_dependency()
    s07_p1 = validate_s07_p1_dependency()
    s07_p2 = validate_s07_p2_dependency()
    legacy_manifest, baseline_templates, baseline_connector_policy, baseline_rollback_plan, _legacy_registry = (
        load_public_safe_redcircle_baseline()
    )
    templates, connector_policy, rollback_plan, registry, policy_yaml = build_v014_outputs(
        baseline_templates,
        baseline_connector_policy,
        baseline_rollback_plan,
    )
    manifest = build_manifest(
        stage6,
        s07_p1,
        s07_p2,
        legacy_manifest,
        templates,
        connector_policy,
        rollback_plan,
        registry,
    )
    write_json(MANIFEST_PATH, manifest)
    write_jsonl(TEMPLATES_PATH, templates)
    write_json(CONNECTOR_POLICY_PATH, connector_policy)
    write_jsonl(ROLLBACK_PLAN_PATH, rollback_plan)
    write_json(METADATA_MANIFEST_PATH, manifest)
    write_json(METADATA_SOURCE_REGISTRY_PATH, registry)
    write_jsonl(METADATA_TEMPLATES_PATH, templates)
    write_policy_yaml(METADATA_POLICY_PATH, policy_yaml)
    write_human_evidence(manifest)
    return manifest


def main() -> int:
    manifest = write_outputs()
    summary = manifest["redcircle_summary"]
    print(
        "PASS: KMFA v0.1.4 S07-P3 Redcircle postponement evidence built "
        f"(templates={summary['reserved_template_count']}, "
        f"rollback_plans={summary['rollback_plan_count']}, "
        "d15_connector_allowed=false, stage7_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
