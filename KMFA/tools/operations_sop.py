#!/usr/bin/env python3
"""Build KMFA S17-P3 public-safe operations SOP artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "operations" / "operations_sop_manifest.json"
DEFAULT_OUTPUT_RUNBOOKS = ROOT / "metadata" / "operations" / "operations_runbooks.jsonl"
DEFAULT_OUTPUT_KNOWLEDGE_INDEX = ROOT / "metadata" / "operations" / "finance_sop_knowledge_index.jsonl"
DEFAULT_OUTPUT_DRILL_LOG = ROOT / "metadata" / "operations" / "error_backup_drill_log.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT
    / "stage_artifacts"
    / "S17_P3_operations_sop"
    / "machine"
    / "s17_p3_manifest.json"
)

REQUIRED_RUNBOOK_TYPES = (
    "import",
    "review",
    "publish",
    "rollback",
)
REQUIRED_KNOWLEDGE_ITEM_TYPES = (
    "finance_sop",
    "handoff_materials",
)
REQUIRED_DRILL_TYPES = (
    "error_handling",
    "backup_recovery",
)

POLICY_VERSION = "KMFA-S17P3-OPERATIONS-SOP-PUBLIC-SAFE-001"
RUNBOOK_VERSION = "OPS-RUNBOOK-KMFA-S17P3-001"
KNOWLEDGE_VERSION = "OPS-KNOWLEDGE-KMFA-S17P3-001"
DRILL_VERSION = "OPS-DRILL-KMFA-S17P3-001"

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
    "full_report_body_text",
    "complete_report_body_text",
    "report_attachment_path",
    "recipient_email",
    "smtp",
    "sk-",
    "-----BEGIN",
)


class OperationsSopError(ValueError):
    """Raised when S17-P3 operations SOP artifacts are invalid."""


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise OperationsSopError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise OperationsSopError(f"{path} contains a non-object JSONL record")
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
        "full_report_body_committed": False,
        "report_attachment_committed": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s17_p1_scope_included": False,
        "s17_p2_scope_included": False,
        "s17_p3_scope_included": True,
        "stage17_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "formal_report_scope_included": False,
        "external_connector_scope_included": False,
        "business_execution_scope_included": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "operation_runbooks_complete": True,
        "finance_sop_indexed": True,
        "handoff_materials_indexed": True,
        "error_handling_drill_recorded": True,
        "backup_recovery_drill_recorded": True,
        "metadata_only": True,
        "manual_execution_only": True,
        "raw_payload_allowed": False,
        "private_document_allowed": False,
        "live_connector_allowed": False,
        "external_service_call_allowed": False,
        "production_restore_allowed": False,
        "formal_report_allowed": False,
        "full_report_email_allowed": False,
        "business_decision_basis_allowed": False,
        "business_execution_allowed": False,
        "automatic_payment_allowed": False,
        "bank_operation_allowed": False,
        "invoice_issue_allowed": False,
        "tax_formal_action_allowed": False,
        "legal_collection_allowed": False,
        "salary_action_allowed": False,
        "lineage_full_check_allowed": False,
        "stage17_review_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "release_block_reason": "s17_p3_is_local_public_safe_operations_sop_only",
    }


def _runbook_specs() -> list[dict[str, str]]:
    return [
        {
            "runbook_type": "import",
            "owner_role": "finance",
            "precheck_ref": "verify_source_registration_authorization_and_hash_refs",
            "primary_step_ref": "register_public_safe_import_metadata_then_run_import_validators",
            "rollback_step_ref": "append_import_reversal_event_and_restore_previous_metadata_snapshot",
            "evidence_ref": "KMFA/stage_artifacts/S03_P1_file_import/human/s03_p1_completion_record.md",
        },
        {
            "runbook_type": "review",
            "owner_role": "reviewer",
            "precheck_ref": "confirm_pending_items_quality_gate_and_evidence_refs",
            "primary_step_ref": "review_diff_queue_quality_gate_and_human_resolution_events",
            "rollback_step_ref": "append_review_correction_event_without_mutating_prior_records",
            "evidence_ref": "KMFA/stage_artifacts/S12_P1_manual_resolution_events/human/s12_p1_completion_record.md",
        },
        {
            "runbook_type": "publish",
            "owner_role": "management",
            "precheck_ref": "confirm_report_grade_stage_review_and_owner_approval",
            "primary_step_ref": "publish_public_safe_report_preview_only_after_quality_gate_pass",
            "rollback_step_ref": "withdraw_public_safe_preview_and_append_publish_reversal_event",
            "evidence_ref": "KMFA/stage_artifacts/S10_P3_report_export/human/s10_p3_completion_record.md",
        },
        {
            "runbook_type": "rollback",
            "owner_role": "reviewer",
            "precheck_ref": "identify_last_valid_metadata_version_and_reversal_reason",
            "primary_step_ref": "restore_previous_public_safe_metadata_refs_then_rerun_validators",
            "rollback_step_ref": "escalate_to_manual_recovery_record_if_restore_validation_fails",
            "evidence_ref": "KMFA/stage_artifacts/S12_P3_manual_rerun_mechanism/human/s12_p3_completion_record.md",
        },
    ]


def _operation_runbooks() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in _runbook_specs():
        runbook_type = spec["runbook_type"]
        rows.append(
            {
                "record_type": "operation_runbook",
                "policy_version": RUNBOOK_VERSION,
                "runbook_id": f"operation_runbook_s17p3_{runbook_type}",
                "runbook_type": runbook_type,
                "owner_role": spec["owner_role"],
                "execution_mode": "manual_sop_only",
                "precheck_required": True,
                "precheck_ref": spec["precheck_ref"],
                "primary_step_ref": spec["primary_step_ref"],
                "rollback_step_ref": spec["rollback_step_ref"],
                "append_only": True,
                "metadata_target": "KMFA/metadata/operations/operations_runbooks.jsonl",
                "evidence_ref": spec["evidence_ref"],
                "raw_business_data_required": False,
                "private_document_required": False,
                "live_connector_required": False,
                "external_service_required": False,
                "business_execution_allowed": False,
                "formal_report_release_allowed": False,
                "stage_review_allowed": False,
                "github_upload_allowed": False,
            }
        )
    return rows


def _operations_knowledge_index() -> list[dict[str, Any]]:
    return [
        {
            "record_type": "operations_knowledge_item",
            "policy_version": KNOWLEDGE_VERSION,
            "knowledge_item_id": "operations_knowledge_s17p3_finance_sop",
            "item_type": "finance_sop",
            "owner_role": "finance",
            "storage_mode": "public_safe_index_only",
            "knowledge_ref": "KMFA-KNOWLEDGE-S17P3-FINANCE-SOP",
            "handoff_required": True,
            "append_only": True,
            "metadata_target": "KMFA/metadata/operations/finance_sop_knowledge_index.jsonl",
            "evidence_ref": "KMFA/stage_artifacts/S17_P3_operations_sop/human/s17_p3_completion_record.md",
            "private_document_committed": False,
            "raw_business_data_committed": False,
            "credential_material_committed": False,
            "business_decision_basis_allowed": False,
        },
        {
            "record_type": "operations_knowledge_item",
            "policy_version": KNOWLEDGE_VERSION,
            "knowledge_item_id": "operations_knowledge_s17p3_handoff_materials",
            "item_type": "handoff_materials",
            "owner_role": "reviewer",
            "storage_mode": "public_safe_index_only",
            "knowledge_ref": "KMFA-KNOWLEDGE-S17P3-HANDOFF-MATERIALS",
            "handoff_required": True,
            "append_only": True,
            "metadata_target": "KMFA/metadata/operations/finance_sop_knowledge_index.jsonl",
            "evidence_ref": "KMFA/HANDOFF.md",
            "private_document_committed": False,
            "raw_business_data_committed": False,
            "credential_material_committed": False,
            "business_decision_basis_allowed": False,
        },
    ]


def _drill_logs(generated_at: str) -> list[dict[str, Any]]:
    return [
        {
            "record_type": "operations_drill_log",
            "policy_version": DRILL_VERSION,
            "drill_id": "operations_drill_s17p3_error_handling",
            "drill_type": "error_handling",
            "drill_time": generated_at,
            "scenario_ref": "metadata_validation_failure_or_missing_source",
            "execution_mode": "metadata_drill_only",
            "result_status": "simulated_passed",
            "recovery_evidence_ref": "KMFA/stage_artifacts/S17_P3_operations_sop/human/s17_p3_completion_record.md",
            "append_only": True,
            "metadata_target": "KMFA/metadata/operations/error_backup_drill_log.jsonl",
            "production_restore_executed": False,
            "raw_business_data_required": False,
            "private_document_required": False,
            "external_service_called": False,
            "live_connector_called": False,
            "business_execution_allowed": False,
        },
        {
            "record_type": "operations_drill_log",
            "policy_version": DRILL_VERSION,
            "drill_id": "operations_drill_s17p3_backup_recovery",
            "drill_type": "backup_recovery",
            "drill_time": generated_at,
            "scenario_ref": "public_safe_metadata_snapshot_restore",
            "execution_mode": "metadata_drill_only",
            "result_status": "simulated_passed",
            "recovery_evidence_ref": "KMFA/stage_artifacts/S17_P3_operations_sop/human/s17_p3_completion_record.md",
            "append_only": True,
            "metadata_target": "KMFA/metadata/operations/error_backup_drill_log.jsonl",
            "production_restore_executed": False,
            "raw_business_data_required": False,
            "private_document_required": False,
            "external_service_called": False,
            "live_connector_called": False,
            "business_execution_allowed": False,
        },
    ]


def _manifest(
    generated_at: str,
    runbooks: list[dict[str, Any]],
    knowledge_items: list[dict[str, Any]],
    drill_logs: list[dict[str, Any]],
) -> dict[str, Any]:
    summary = {
        "operation_runbook_count": len(runbooks),
        "knowledge_item_count": len(knowledge_items),
        "drill_log_count": len(drill_logs),
        "runbook_type_count": len({row["runbook_type"] for row in runbooks}),
        "knowledge_item_type_count": len({row["item_type"] for row in knowledge_items}),
        "drill_type_count": len({row["drill_type"] for row in drill_logs}),
    }
    payload_hash = _sha256_json(
        {
            "runbooks": runbooks,
            "knowledge_items": knowledge_items,
            "drill_logs": drill_logs,
            "summary": summary,
            "stage_scope": _stage_scope(),
            "quality_gate": _quality_gate(),
        }
    )
    return {
        "record_type": "s17_p3_operations_sop_manifest",
        "project_id": "KMFA",
        "stage_id": "S17",
        "stage_phase": "S17-P3",
        "phase_id": "S17PC",
        "iteration_id": "ITER-20260701-KMFA-S17P3-OPERATIONS-SOP",
        "policy_version": POLICY_VERSION,
        "generated_at": generated_at,
        "required_runbook_types": list(REQUIRED_RUNBOOK_TYPES),
        "required_knowledge_item_types": list(REQUIRED_KNOWLEDGE_ITEM_TYPES),
        "required_drill_types": list(REQUIRED_DRILL_TYPES),
        "summary": summary,
        "public_repo_safety": _public_repo_safety(),
        "stage_scope": _stage_scope(),
        "quality_gate": _quality_gate(),
        "metadata_outputs": {
            "operations_sop_manifest": "KMFA/metadata/operations/operations_sop_manifest.json",
            "operations_runbooks": "KMFA/metadata/operations/operations_runbooks.jsonl",
            "finance_sop_knowledge_index": "KMFA/metadata/operations/finance_sop_knowledge_index.jsonl",
            "error_backup_drill_log": "KMFA/metadata/operations/error_backup_drill_log.jsonl",
        },
        "stage_artifact_ref": "KMFA/stage_artifacts/S17_P3_operations_sop/machine/s17_p3_manifest.json",
        "content_hash": payload_hash,
        "fact_level": "EXTRACTED",
    }


def build_default_operations_sop(
    generated_at: str = "2026-07-01T23:59:30+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    runbooks = _operation_runbooks()
    knowledge_items = _operations_knowledge_index()
    drill_logs = _drill_logs(generated_at=generated_at)
    manifest = _manifest(
        generated_at=generated_at,
        runbooks=runbooks,
        knowledge_items=knowledge_items,
        drill_logs=drill_logs,
    )
    return manifest, runbooks, knowledge_items, drill_logs


def _scan_forbidden_payload(payload: Any) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        if forbidden in encoded:
            raise OperationsSopError(f"forbidden public payload text found: {forbidden}")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise OperationsSopError(message)


def validate_operations_sop_artifacts(
    manifest: dict[str, Any],
    runbooks: list[dict[str, Any]],
    knowledge_items: list[dict[str, Any]],
    drill_logs: list[dict[str, Any]],
) -> None:
    _scan_forbidden_payload([manifest, runbooks, knowledge_items, drill_logs])

    _require(manifest.get("stage_phase") == "S17-P3", "manifest must be S17-P3")
    _require(tuple(manifest.get("required_runbook_types", [])) == REQUIRED_RUNBOOK_TYPES, "required runbook types drift")
    _require(
        tuple(manifest.get("required_knowledge_item_types", [])) == REQUIRED_KNOWLEDGE_ITEM_TYPES,
        "required knowledge item types drift",
    )
    _require(tuple(manifest.get("required_drill_types", [])) == REQUIRED_DRILL_TYPES, "required drill types drift")

    quality_gate = manifest.get("quality_gate", {})
    stage_scope = manifest.get("stage_scope", {})
    for key in (
        "operation_runbooks_complete",
        "finance_sop_indexed",
        "handoff_materials_indexed",
        "error_handling_drill_recorded",
        "backup_recovery_drill_recorded",
        "metadata_only",
        "manual_execution_only",
    ):
        _require(quality_gate.get(key) is True, f"quality gate must enable {key}")
    for key in (
        "raw_payload_allowed",
        "private_document_allowed",
        "live_connector_allowed",
        "external_service_call_allowed",
        "production_restore_allowed",
        "formal_report_allowed",
        "full_report_email_allowed",
        "business_decision_basis_allowed",
        "business_execution_allowed",
        "automatic_payment_allowed",
        "bank_operation_allowed",
        "invoice_issue_allowed",
        "tax_formal_action_allowed",
        "legal_collection_allowed",
        "salary_action_allowed",
        "lineage_full_check_allowed",
        "stage17_review_allowed",
        "github_upload_allowed",
        "phase_completion_upload_allowed",
    ):
        _require(quality_gate.get(key) is False, f"quality gate must block {key}")
    _require(stage_scope.get("s17_p3_scope_included") is True, "S17-P3 scope must be included")
    for key, value in stage_scope.items():
        if key != "s17_p3_scope_included":
            _require(value is False, f"stage scope must exclude {key}")

    runbooks_by_type = {row.get("runbook_type"): row for row in runbooks}
    knowledge_by_type = {row.get("item_type"): row for row in knowledge_items}
    drills_by_type = {row.get("drill_type"): row for row in drill_logs}
    _require(set(runbooks_by_type) == set(REQUIRED_RUNBOOK_TYPES), "runbooks must cover required types")
    _require(set(knowledge_by_type) == set(REQUIRED_KNOWLEDGE_ITEM_TYPES), "knowledge index must cover required types")
    _require(set(drills_by_type) == set(REQUIRED_DRILL_TYPES), "drill logs must cover required types")
    _require(manifest.get("summary", {}).get("operation_runbook_count") == len(runbooks) == 4, "runbook count drift")
    _require(manifest.get("summary", {}).get("knowledge_item_count") == len(knowledge_items) == 2, "knowledge count drift")
    _require(manifest.get("summary", {}).get("drill_log_count") == len(drill_logs) == 2, "drill count drift")

    for runbook_type, row in runbooks_by_type.items():
        _require(row.get("record_type") == "operation_runbook", "runbook record type drift")
        _require(row.get("execution_mode") == "manual_sop_only", "runbooks must be manual SOP only")
        _require(row.get("metadata_target") == "KMFA/metadata/operations/operations_runbooks.jsonl", "runbook metadata target drift")
        _require(row.get("append_only") is True, "runbooks must be append-only")
        _require(row.get("precheck_required") is True, "runbook precheck required")
        _require(bool(row.get("precheck_ref")), "runbook precheck ref required")
        _require(bool(row.get("primary_step_ref")), "runbook primary step ref required")
        _require(bool(row.get("rollback_step_ref")), "runbook rollback step ref required")
        _require(bool(row.get("evidence_ref")), "runbook evidence ref required")
        _require(row.get("raw_business_data_required") is False, "runbook raw data must be absent")
        _require(row.get("private_document_required") is False, "runbook private document must be absent")
        _require(row.get("live_connector_required") is False, "runbook live connector must be absent")
        _require(row.get("external_service_required") is False, "runbook external service must be absent")
        _require(row.get("business_execution_allowed") is False, "runbook business execution must be blocked")
        _require(row.get("formal_report_release_allowed") is False, "runbook formal report release must be blocked")
        _require(row.get("stage_review_allowed") is False, "runbook stage review must be blocked")
        _require(row.get("github_upload_allowed") is False, "runbook GitHub upload must be blocked")
        _require(str(runbook_type) in str(row.get("runbook_id")), "runbook id must include type")

    for item_type, row in knowledge_by_type.items():
        _require(row.get("record_type") == "operations_knowledge_item", "knowledge record type drift")
        _require(row.get("metadata_target") == "KMFA/metadata/operations/finance_sop_knowledge_index.jsonl", "knowledge metadata target drift")
        _require(row.get("storage_mode") == "public_safe_index_only", "knowledge must be public-safe index only")
        _require(row.get("append_only") is True, "knowledge items must be append-only")
        _require(bool(row.get("owner_role")), "knowledge owner role required")
        _require(bool(row.get("knowledge_ref")), "knowledge ref required")
        _require(bool(row.get("evidence_ref")), "knowledge evidence ref required")
        _require(row.get("private_document_committed") is False, "knowledge private document must be absent")
        _require(row.get("raw_business_data_committed") is False, "knowledge raw data must be absent")
        _require(row.get("credential_material_committed") is False, "knowledge credential material must be absent")
        _require(row.get("business_decision_basis_allowed") is False, "knowledge decision basis must be blocked")
        _require(str(item_type) in str(row.get("knowledge_item_id")), "knowledge id must include type")

    for drill_type, row in drills_by_type.items():
        _require(row.get("record_type") == "operations_drill_log", "drill record type drift")
        _require(row.get("metadata_target") == "KMFA/metadata/operations/error_backup_drill_log.jsonl", "drill metadata target drift")
        _require(row.get("execution_mode") == "metadata_drill_only", "drill must be metadata-only")
        _require(row.get("result_status") == "simulated_passed", "drill result drift")
        _require(row.get("append_only") is True, "drill logs must be append-only")
        _require(bool(row.get("scenario_ref")), "drill scenario ref required")
        _require(bool(row.get("recovery_evidence_ref")), "drill recovery evidence ref required")
        _require(row.get("production_restore_executed") is False, "production restore must not execute")
        _require(row.get("raw_business_data_required") is False, "drill raw data must be absent")
        _require(row.get("private_document_required") is False, "drill private document must be absent")
        _require(row.get("external_service_called") is False, "drill external service must be absent")
        _require(row.get("live_connector_called") is False, "drill live connector must be absent")
        _require(row.get("business_execution_allowed") is False, "drill business execution must be blocked")
        _require(str(drill_type) in str(row.get("drill_id")), "drill id must include type")


def write_default_operations_sop(
    *,
    manifest_path: Path = DEFAULT_OUTPUT_MANIFEST,
    runbooks_path: Path = DEFAULT_OUTPUT_RUNBOOKS,
    knowledge_index_path: Path = DEFAULT_OUTPUT_KNOWLEDGE_INDEX,
    drill_log_path: Path = DEFAULT_OUTPUT_DRILL_LOG,
    stage_manifest_path: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    generated_at: str = "2026-07-01T23:59:30+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    manifest, runbooks, knowledge_items, drill_logs = build_default_operations_sop(generated_at=generated_at)
    validate_operations_sop_artifacts(manifest, runbooks, knowledge_items, drill_logs)
    write_json(manifest_path, manifest)
    write_jsonl(runbooks_path, runbooks)
    write_jsonl(knowledge_index_path, knowledge_items)
    write_jsonl(drill_log_path, drill_logs)
    stage_manifest = dict(manifest)
    stage_manifest["record_type"] = "s17_p3_stage_artifact_manifest"
    stage_manifest["metadata_manifest_ref"] = "KMFA/metadata/operations/operations_sop_manifest.json"
    write_json(stage_manifest_path, stage_manifest)
    return manifest, runbooks, knowledge_items, drill_logs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate KMFA S17-P3 public-safe operations SOP artifacts.")
    parser.add_argument("--generated-at", default="2026-07-01T23:59:30+10:00")
    parser.add_argument("--check-only", action="store_true", help="Validate generated defaults without writing files.")
    args = parser.parse_args(argv)

    manifest, runbooks, knowledge_items, drill_logs = build_default_operations_sop(generated_at=args.generated_at)
    validate_operations_sop_artifacts(manifest, runbooks, knowledge_items, drill_logs)
    if not args.check_only:
        write_default_operations_sop(generated_at=args.generated_at)
    print(
        "PASS: generated S17-P3 operations SOP artifacts "
        f"(runbooks={len(runbooks)}, knowledge_items={len(knowledge_items)}, drill_logs={len(drill_logs)}, "
        "metadata_only=true, manual_execution_only=true, stage17_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
