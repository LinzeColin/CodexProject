#!/usr/bin/env python3
"""Build KMFA S18-P3 public-safe integration preparation artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "integration" / "integration_preparation_manifest.json"
DEFAULT_OUTPUT_CONNECTORS = ROOT / "metadata" / "integration" / "read_only_connector_plan.jsonl"
DEFAULT_OUTPUT_OPME = ROOT / "metadata" / "integration" / "opme_entry_integration_plan.json"
DEFAULT_OUTPUT_BACKLOG = ROOT / "metadata" / "integration" / "next_stage_backlog.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT
    / "stage_artifacts"
    / "S18_P3_integration_preparation"
    / "machine"
    / "s18_p3_manifest.json"
)
DEFAULT_OUTPUT_HUMAN_DIR = ROOT / "stage_artifacts" / "S18_P3_integration_preparation" / "human"

POLICY_VERSION = "KMFA-S18P3-INTEGRATION-PREPARATION-001"
ITERATION_ID = "ITER-20260701-KMFA-S18P3-INTEGRATION-PREPARATION"

REQUIRED_CONNECTOR_IDS = ("redcircle", "kingdee", "wps")
REQUIRED_OPME_ENTRY_SURFACES = ("read_only_entry", "report_index", "run_status", "handoff_link")
REQUIRED_BACKLOG_IDS = (
    "BL-KMFA-NEXT-001",
    "BL-KMFA-NEXT-002",
    "BL-KMFA-NEXT-003",
    "BL-KMFA-NEXT-004",
    "BL-KMFA-NEXT-005",
    "BL-KMFA-NEXT-006",
)

FORBIDDEN_PUBLIC_TEXT = (
    "raw_value",
    "normalized_value",
    "plaintext_value",
    "source_header_text",
    "original_filename",
    "private://",
    "private_ref://",
    "bank_statement",
    "contract_full_text",
    "salary_detail",
    "tax_filing",
    "recipient_email",
    "smtp",
    "sk-",
    "-----BEGIN",
)


class IntegrationPreparationError(ValueError):
    """Raised when S18-P3 integration preparation artifacts are invalid."""


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise IntegrationPreparationError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise IntegrationPreparationError(f"{path} contains a non-object JSONL record")
        rows.append(value)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def _public_repo_safety() -> dict[str, bool]:
    return {
        "raw_business_data_committed": False,
        "private_tabular_material_committed": False,
        "source_document_committed": False,
        "field_text_committed": False,
        "true_money_committed": False,
        "true_customer_project_committed": False,
        "true_account_committed": False,
        "credential_committed": False,
        "private_document_committed": False,
        "raw_file_committed": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "read_only_connector_plan_created": True,
        "opme_entry_plan_created": True,
        "next_stage_backlog_created": True,
        "stage18_review_next_required": True,
        "stage18_review_allowed_in_this_phase": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "external_connector_called": False,
        "external_connector_allowed": False,
        "live_connector_called": False,
        "source_mutation_allowed": False,
        "credential_required_now": False,
        "business_execution_allowed": False,
        "production_restore_allowed": False,
        "official_report_release_allowed": False,
        "business_decision_basis_allowed": False,
        "lineage_full_check_complete": False,
        "delivery_allowed": False,
        "s09_pending_reconciliation_count": 12,
        "maximum_report_grade": "D",
        "release_block_reason": "s18_stage_review_lineage_full_check_and_official_report_release_pending",
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s18_p1_scope_included": False,
        "s18_p2_scope_included": False,
        "s18_p3_scope_included": True,
        "stage18_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "formal_report_scope_included": False,
        "live_external_connector_scope_included": False,
        "production_restore_scope_included": False,
        "business_execution_scope_included": False,
    }


def _connector_rows() -> list[dict[str, Any]]:
    connector_labels = {
        "redcircle": "contract_collaboration_platform",
        "kingdee": "finance_erp_platform",
        "wps": "office_document_platform",
    }
    planned_entry_points = {
        "redcircle": "authorized_export_snapshot_or_contract_index",
        "kingdee": "authorized_read_only_finance_export",
        "wps": "authorized_read_only_document_export_or_watch_folder",
    }
    rows: list[dict[str, Any]] = []
    for connector_id in REQUIRED_CONNECTOR_IDS:
        rows.append(
            {
                "record_type": "s18_p3_read_only_connector_plan",
                "policy_version": POLICY_VERSION,
                "stage_id": "S18",
                "phase_id": "S18PC",
                "stage_phase": "S18-P3",
                "connector_id": connector_id,
                "connector_label": connector_labels[connector_id],
                "integration_mode": "read_only_future_connector",
                "lifecycle_state": "proposal_only",
                "planned_entry_point": planned_entry_points[connector_id],
                "allowed_operation_refs": [
                    "schema_manifest_read",
                    "hash_manifest_read",
                    "authorized_export_snapshot_read",
                ],
                "disallowed_operation_refs": [
                    "source_mutation",
                    "auto_writeback",
                    "payment_or_contract_action",
                    "credential_collection_in_public_repo",
                    "field_plaintext_publication",
                ],
                "manual_authorization_required": True,
                "hash_retention_required": True,
                "rollback_required": True,
                "source_mutation_allowed": False,
                "auto_write_allowed": False,
                "credential_required_now": False,
                "live_connector_called": False,
                "external_service_called": False,
                "raw_business_data_committed": False,
                "field_plaintext_committed": False,
                "github_upload_allowed": False,
                "business_execution_allowed": False,
                "next_gate": "future_owner_authorization_and_private_runtime_design",
            }
        )
    return rows


def _opme_plan() -> dict[str, Any]:
    return {
        "record_type": "s18_p3_opme_entry_integration_plan",
        "policy_version": POLICY_VERSION,
        "stage_id": "S18",
        "phase_id": "S18PC",
        "stage_phase": "S18-P3",
        "integration_mode": "entry_link_and_status_index_only",
        "coupling_level": "light_entry_only",
        "entry_surfaces": list(REQUIRED_OPME_ENTRY_SURFACES),
        "allowed_exchange_refs": [
            "public_safe_status_summary",
            "report_index_pointer",
            "handoff_pointer",
            "validator_command_pointer",
        ],
        "responsibility_split": {
            "kmfa_owner": "project_finance_operation",
            "opme_owner": "technical_service_entry_and_status",
        },
        "deep_coupling_allowed": False,
        "shared_database_allowed": False,
        "sensitive_data_mixing_allowed": False,
        "opme_controls_kmfa_business_logic": False,
        "kmfa_controls_opme_service_logic": False,
        "external_service_called": False,
        "raw_business_data_committed": False,
        "field_plaintext_committed": False,
        "credential_committed": False,
        "github_upload_allowed": False,
        "business_execution_allowed": False,
        "next_gate": "opme_shell_design_after_stage18_review",
    }


def _backlog_rows() -> list[dict[str, Any]]:
    specs = [
        (
            "BL-KMFA-NEXT-001",
            "future_connector_authorization_and_secret_handling_design",
            "Define private runtime authorization, secret vault boundary and no-public-credential controls.",
        ),
        (
            "BL-KMFA-NEXT-002",
            "redcircle_read_only_connector_spike",
            "Prototype a read-only export/index adapter after owner authorization.",
        ),
        (
            "BL-KMFA-NEXT-003",
            "kingdee_read_only_source_registry_spike",
            "Prototype a read-only finance export registry and hash evidence path after owner authorization.",
        ),
        (
            "BL-KMFA-NEXT-004",
            "wps_read_only_document_export_spike",
            "Prototype a read-only document export or watch-folder registry after owner authorization.",
        ),
        (
            "BL-KMFA-NEXT-005",
            "opme_light_entry_shell_design",
            "Design a light entry shell exposing status, report index and handoff pointers without shared runtime logic.",
        ),
        (
            "BL-KMFA-NEXT-006",
            "stage18_review_and_upload_gate",
            "Run Stage 18 overall review, fix findings, then prepare upload evidence only after all validators pass.",
        ),
    ]
    rows: list[dict[str, Any]] = []
    for priority, (backlog_id, title, description) in enumerate(specs, start=1):
        rows.append(
            {
                "record_type": "s18_p3_next_stage_backlog_item",
                "policy_version": POLICY_VERSION,
                "stage_id": "S18",
                "phase_id": "S18PC",
                "stage_phase": "S18-P3",
                "backlog_id": backlog_id,
                "priority": priority,
                "title": title,
                "description": description,
                "status": "backlog_proposed_not_started",
                "started": False,
                "owner_authorization_required": backlog_id != "BL-KMFA-NEXT-006",
                "stage18_review_required_first": backlog_id != "BL-KMFA-NEXT-006",
                "business_execution_allowed": False,
                "external_connector_allowed": False,
                "github_upload_allowed": False,
                "raw_business_data_required_in_public_repo": False,
                "next_gate": "stage18_review_first" if backlog_id != "BL-KMFA-NEXT-006" else "stage18_review",
            }
        )
    return rows


def build_default_integration_preparation_suite(
    *, generated_at: str
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    connector_plans = _connector_rows()
    opme_plan = _opme_plan()
    backlog_items = _backlog_rows()
    manifest: dict[str, Any] = {
        "record_type": "s18_p3_integration_preparation_manifest",
        "project_id": "KMFA",
        "stage_id": "S18",
        "phase_id": "S18PC",
        "stage_phase": "S18-P3",
        "policy_version": POLICY_VERSION,
        "iteration_id": ITERATION_ID,
        "generated_at": generated_at,
        "fact_level": "EXTRACTED",
        "required_connector_ids": list(REQUIRED_CONNECTOR_IDS),
        "required_opme_entry_surfaces": list(REQUIRED_OPME_ENTRY_SURFACES),
        "required_backlog_ids": list(REQUIRED_BACKLOG_IDS),
        "quality_gate": _quality_gate(),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "metadata_outputs": {
            "integration_preparation_manifest": "KMFA/metadata/integration/integration_preparation_manifest.json",
            "read_only_connector_plan": "KMFA/metadata/integration/read_only_connector_plan.jsonl",
            "opme_entry_integration_plan": "KMFA/metadata/integration/opme_entry_integration_plan.json",
            "next_stage_backlog": "KMFA/metadata/integration/next_stage_backlog.jsonl",
        },
        "stage_artifact_refs": {
            "machine_manifest": "KMFA/stage_artifacts/S18_P3_integration_preparation/machine/s18_p3_manifest.json",
            "completion_record": "KMFA/stage_artifacts/S18_P3_integration_preparation/human/s18_p3_completion_record.md",
            "connector_plan": "KMFA/stage_artifacts/S18_P3_integration_preparation/human/read_only_connector_plan.md",
            "opme_plan": "KMFA/stage_artifacts/S18_P3_integration_preparation/human/opme_entry_integration_plan.md",
            "backlog": "KMFA/stage_artifacts/S18_P3_integration_preparation/human/next_stage_backlog.md",
            "test_results": "KMFA/stage_artifacts/S18_P3_integration_preparation/human/test_results.md",
        },
        "summary": {
            "connector_plan_count": len(connector_plans),
            "read_only_connector_count": sum(
                1 for row in connector_plans if row["integration_mode"] == "read_only_future_connector"
            ),
            "opme_entry_surface_count": len(opme_plan["entry_surfaces"]),
            "backlog_item_count": len(backlog_items),
            "live_connector_call_count": sum(1 for row in connector_plans if row["live_connector_called"]),
            "github_upload_allowed": False,
            "delivery_allowed": False,
            "business_execution_allowed": False,
        },
    }
    content_for_hash = {
        "manifest_without_hash": manifest,
        "connector_plans": connector_plans,
        "opme_plan": opme_plan,
        "backlog_items": backlog_items,
    }
    manifest["content_hash"] = _sha256_json(content_for_hash)
    return manifest, connector_plans, opme_plan, backlog_items


def _validate_no_forbidden_public_text(payload: Any) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for forbidden_text in FORBIDDEN_PUBLIC_TEXT:
        if forbidden_text in encoded:
            raise IntegrationPreparationError(f"forbidden public text found: {forbidden_text}")


def _validate_manifest_hash(
    manifest: dict[str, Any],
    connector_plans: list[dict[str, Any]],
    opme_plan: dict[str, Any],
    backlog_items: list[dict[str, Any]],
) -> None:
    manifest_without_hash = dict(manifest)
    expected_hash = manifest_without_hash.pop("content_hash", None)
    actual_hash = _sha256_json(
        {
            "manifest_without_hash": manifest_without_hash,
            "connector_plans": connector_plans,
            "opme_plan": opme_plan,
            "backlog_items": backlog_items,
        }
    )
    if expected_hash != actual_hash:
        raise IntegrationPreparationError("manifest content_hash mismatch")


def validate_integration_preparation_artifacts(
    manifest: dict[str, Any],
    connector_plans: list[dict[str, Any]],
    opme_plan: dict[str, Any],
    backlog_items: list[dict[str, Any]],
) -> None:
    if manifest.get("stage_phase") != "S18-P3":
        raise IntegrationPreparationError("manifest stage_phase must be S18-P3")
    if tuple(manifest.get("required_connector_ids", ())) != REQUIRED_CONNECTOR_IDS:
        raise IntegrationPreparationError("manifest required_connector_ids mismatch")
    if tuple(manifest.get("required_opme_entry_surfaces", ())) != REQUIRED_OPME_ENTRY_SURFACES:
        raise IntegrationPreparationError("manifest required_opme_entry_surfaces mismatch")
    if tuple(manifest.get("required_backlog_ids", ())) != REQUIRED_BACKLOG_IDS:
        raise IntegrationPreparationError("manifest required_backlog_ids mismatch")

    connector_ids = {row.get("connector_id") for row in connector_plans}
    if connector_ids != set(REQUIRED_CONNECTOR_IDS):
        raise IntegrationPreparationError(f"connector ids mismatch: {sorted(connector_ids)}")
    if len(connector_plans) != len(REQUIRED_CONNECTOR_IDS):
        raise IntegrationPreparationError("connector plan count mismatch")
    for row in connector_plans:
        if row.get("record_type") != "s18_p3_read_only_connector_plan":
            raise IntegrationPreparationError("invalid connector record_type")
        if row.get("stage_phase") != "S18-P3":
            raise IntegrationPreparationError("connector row stage_phase must be S18-P3")
        if row.get("integration_mode") != "read_only_future_connector":
            raise IntegrationPreparationError("connector must be read_only_future_connector")
        if row.get("lifecycle_state") != "proposal_only":
            raise IntegrationPreparationError("connector lifecycle_state must be proposal_only")
        for flag in ("manual_authorization_required", "hash_retention_required", "rollback_required"):
            if row.get(flag) is not True:
                raise IntegrationPreparationError(f"connector {row.get('connector_id')} must keep {flag}=true")
        for flag in (
            "source_mutation_allowed",
            "auto_write_allowed",
            "credential_required_now",
            "live_connector_called",
            "external_service_called",
            "raw_business_data_committed",
            "field_plaintext_committed",
            "github_upload_allowed",
            "business_execution_allowed",
        ):
            if row.get(flag) is not False:
                raise IntegrationPreparationError(f"connector {row.get('connector_id')} must keep {flag}=false")

    if opme_plan.get("record_type") != "s18_p3_opme_entry_integration_plan":
        raise IntegrationPreparationError("invalid opme record_type")
    if opme_plan.get("stage_phase") != "S18-P3":
        raise IntegrationPreparationError("opme stage_phase must be S18-P3")
    if opme_plan.get("integration_mode") != "entry_link_and_status_index_only":
        raise IntegrationPreparationError("opme integration_mode mismatch")
    if opme_plan.get("coupling_level") != "light_entry_only":
        raise IntegrationPreparationError("opme coupling_level mismatch")
    if tuple(opme_plan.get("entry_surfaces", ())) != REQUIRED_OPME_ENTRY_SURFACES:
        raise IntegrationPreparationError("opme entry surfaces mismatch")
    if opme_plan.get("responsibility_split", {}).get("kmfa_owner") != "project_finance_operation":
        raise IntegrationPreparationError("opme kmfa responsibility mismatch")
    if opme_plan.get("responsibility_split", {}).get("opme_owner") != "technical_service_entry_and_status":
        raise IntegrationPreparationError("opme responsibility mismatch")
    for flag in (
        "deep_coupling_allowed",
        "shared_database_allowed",
        "sensitive_data_mixing_allowed",
        "opme_controls_kmfa_business_logic",
        "kmfa_controls_opme_service_logic",
        "external_service_called",
        "raw_business_data_committed",
        "field_plaintext_committed",
        "credential_committed",
        "github_upload_allowed",
        "business_execution_allowed",
    ):
        if opme_plan.get(flag) is not False:
            raise IntegrationPreparationError(f"opme plan must keep {flag}=false")

    backlog_ids = tuple(row.get("backlog_id") for row in backlog_items)
    if backlog_ids != REQUIRED_BACKLOG_IDS:
        raise IntegrationPreparationError(f"backlog ids mismatch: {backlog_ids}")
    for row in backlog_items:
        if row.get("record_type") != "s18_p3_next_stage_backlog_item":
            raise IntegrationPreparationError("invalid backlog record_type")
        if row.get("stage_phase") != "S18-P3":
            raise IntegrationPreparationError("backlog stage_phase must be S18-P3")
        if row.get("status") != "backlog_proposed_not_started":
            raise IntegrationPreparationError("backlog status must remain proposed not started")
        for flag in (
            "started",
            "business_execution_allowed",
            "external_connector_allowed",
            "github_upload_allowed",
            "raw_business_data_required_in_public_repo",
        ):
            if row.get(flag) is not False:
                raise IntegrationPreparationError(f"backlog {row.get('backlog_id')} must keep {flag}=false")

    if manifest.get("summary", {}).get("connector_plan_count") != len(REQUIRED_CONNECTOR_IDS):
        raise IntegrationPreparationError("manifest summary connector count mismatch")
    if manifest.get("summary", {}).get("opme_entry_surface_count") != len(REQUIRED_OPME_ENTRY_SURFACES):
        raise IntegrationPreparationError("manifest summary opme surface count mismatch")
    if manifest.get("summary", {}).get("backlog_item_count") != len(REQUIRED_BACKLOG_IDS):
        raise IntegrationPreparationError("manifest summary backlog count mismatch")
    if manifest.get("summary", {}).get("live_connector_call_count") != 0:
        raise IntegrationPreparationError("live connector calls must remain zero")
    for key in ("stage18_review_scope_included", "github_upload_scope_included"):
        if manifest.get("stage_scope", {}).get(key) is not False:
            raise IntegrationPreparationError(f"{key} must remain false")
    if manifest.get("stage_scope", {}).get("s18_p3_scope_included") is not True:
        raise IntegrationPreparationError("s18_p3_scope_included must be true")
    for key in (
        "github_upload_allowed",
        "external_connector_called",
        "business_execution_allowed",
        "official_report_release_allowed",
        "delivery_allowed",
    ):
        if manifest.get("quality_gate", {}).get(key) is not False:
            raise IntegrationPreparationError(f"quality gate {key} must remain false")
    for key, value in manifest.get("public_repo_safety", {}).items():
        if value is not False:
            raise IntegrationPreparationError(f"public_repo_safety {key} must be false")
    _validate_manifest_hash(manifest, connector_plans, opme_plan, backlog_items)
    _validate_no_forbidden_public_text([manifest, connector_plans, opme_plan, backlog_items])


def _write_human_artifacts(
    human_dir: Path,
    manifest: dict[str, Any],
    connector_plans: list[dict[str, Any]],
    opme_plan: dict[str, Any],
    backlog_items: list[dict[str, Any]],
) -> None:
    human_dir.mkdir(parents=True, exist_ok=True)
    connector_lines = "\n".join(
        f"- {row['connector_id']}: {row['integration_mode']}; live_connector_called={row['live_connector_called']}; "
        f"source_mutation_allowed={row['source_mutation_allowed']}; github_upload_allowed={row['github_upload_allowed']}"
        for row in connector_plans
    )
    backlog_lines = "\n".join(
        f"- {row['backlog_id']}: {row['title']}; status={row['status']}; started={row['started']}"
        for row in backlog_items
    )

    (human_dir / "s18_p3_completion_record.md").write_text(
        "\n".join(
            [
                "# KMFA S18-P3 Completion Record",
                "",
                f"- stage_phase: {manifest['stage_phase']}",
                f"- policy_version: {manifest['policy_version']}",
                f"- generated_at: {manifest['generated_at']}",
                "- scope: read-only future connector plans, OpMe light entry plan, next-stage backlog.",
                "- non_goals: Stage 18 review, GitHub upload, live connectors, production restore, formal report release, business execution.",
                "- public_safe: raw business data, field plaintext, credentials, private documents and true money values are not committed.",
                "- next_required_gate: Stage 18 overall review.",
                "",
                "## Summary",
                "",
                f"- connector_plan_count: {manifest['summary']['connector_plan_count']}",
                f"- opme_entry_surface_count: {manifest['summary']['opme_entry_surface_count']}",
                f"- backlog_item_count: {manifest['summary']['backlog_item_count']}",
                f"- delivery_allowed: {manifest['summary']['delivery_allowed']}",
                f"- github_upload_allowed: {manifest['summary']['github_upload_allowed']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (human_dir / "read_only_connector_plan.md").write_text(
        "\n".join(["# S18-P3 Read-Only Connector Plan", "", connector_lines, ""]),
        encoding="utf-8",
    )
    (human_dir / "opme_entry_integration_plan.md").write_text(
        "\n".join(
            [
                "# S18-P3 OpMe Entry Integration Plan",
                "",
                f"- integration_mode: {opme_plan['integration_mode']}",
                f"- coupling_level: {opme_plan['coupling_level']}",
                f"- entry_surfaces: {', '.join(opme_plan['entry_surfaces'])}",
                f"- deep_coupling_allowed: {opme_plan['deep_coupling_allowed']}",
                f"- shared_database_allowed: {opme_plan['shared_database_allowed']}",
                f"- sensitive_data_mixing_allowed: {opme_plan['sensitive_data_mixing_allowed']}",
                f"- kmfa_owner: {opme_plan['responsibility_split']['kmfa_owner']}",
                f"- opme_owner: {opme_plan['responsibility_split']['opme_owner']}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (human_dir / "next_stage_backlog.md").write_text(
        "\n".join(["# S18-P3 Next-Stage Backlog", "", backlog_lines, ""]),
        encoding="utf-8",
    )
    (human_dir / "test_results.md").write_text(
        "\n".join(
            [
                "# S18-P3 Test Results",
                "",
                "- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_integration_preparation.py",
                "- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/integration_preparation.py --generated-at 2026-07-01T23:59:59+10:00",
                "- PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s18_p3_integration_preparation.py",
                "",
                "Status: pending final gate rerun.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_integration_preparation_artifacts(
    *,
    generated_at: str,
    manifest_path: Path = DEFAULT_OUTPUT_MANIFEST,
    connectors_path: Path = DEFAULT_OUTPUT_CONNECTORS,
    opme_path: Path = DEFAULT_OUTPUT_OPME,
    backlog_path: Path = DEFAULT_OUTPUT_BACKLOG,
    stage_manifest_path: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    human_dir: Path | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    manifest, connector_plans, opme_plan, backlog_items = build_default_integration_preparation_suite(
        generated_at=generated_at
    )
    validate_integration_preparation_artifacts(manifest, connector_plans, opme_plan, backlog_items)
    write_json(manifest_path, manifest)
    write_jsonl(connectors_path, connector_plans)
    write_json(opme_path, opme_plan)
    write_jsonl(backlog_path, backlog_items)
    write_json(stage_manifest_path, manifest)
    if human_dir is not None:
        _write_human_artifacts(human_dir, manifest, connector_plans, opme_plan, backlog_items)
    return manifest, connector_plans, opme_plan, backlog_items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S18-P3 integration preparation artifacts.")
    parser.add_argument("--generated-at", default="2026-07-01T23:59:59+10:00")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--connectors", type=Path, default=DEFAULT_OUTPUT_CONNECTORS)
    parser.add_argument("--opme", type=Path, default=DEFAULT_OUTPUT_OPME)
    parser.add_argument("--backlog", type=Path, default=DEFAULT_OUTPUT_BACKLOG)
    parser.add_argument("--stage-manifest", type=Path, default=DEFAULT_OUTPUT_STAGE_MANIFEST)
    parser.add_argument("--human-dir", type=Path, default=DEFAULT_OUTPUT_HUMAN_DIR)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    if args.check_only:
        manifest = read_json(args.manifest)
        connector_plans = read_jsonl(args.connectors)
        opme_plan = read_json(args.opme)
        backlog_items = read_jsonl(args.backlog)
        validate_integration_preparation_artifacts(manifest, connector_plans, opme_plan, backlog_items)
    else:
        manifest, connector_plans, opme_plan, backlog_items = write_integration_preparation_artifacts(
            generated_at=args.generated_at,
            manifest_path=args.manifest,
            connectors_path=args.connectors,
            opme_path=args.opme,
            backlog_path=args.backlog,
            stage_manifest_path=args.stage_manifest,
            human_dir=args.human_dir,
        )
    print(
        "PASS: generated S18-P3 integration preparation artifacts "
        f"(connectors={len(connector_plans)}, "
        f"opme_surfaces={len(opme_plan['entry_surfaces'])}, "
        f"backlog={len(backlog_items)}, "
        "live_connector_called=false, stage18_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
