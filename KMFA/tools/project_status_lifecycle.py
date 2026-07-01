#!/usr/bin/env python3
"""Build KMFA S16-P2 public-safe project status lifecycle artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_WPS_SOURCE_REGISTRY = ROOT / "metadata" / "imports" / "wps_export_source_registry.json"
DEFAULT_WPS_FIELD_MAPPINGS = ROOT / "metadata" / "schema_maps" / "wps_field_mappings.jsonl"
DEFAULT_PROJECT_PROFILES = ROOT / "metadata" / "schema_maps" / "project_identity_profiles.jsonl"
DEFAULT_COLLECTION_PRIORITY_ITEMS = ROOT / "metadata" / "reports" / "collection_receivable_aging_priority_items.jsonl"
DEFAULT_INVOICE_TAX_ISSUE_CANDIDATES = ROOT / "metadata" / "reports" / "invoice_tax_issue_candidates.jsonl"
DEFAULT_SCOPE_RECONCILIATION_RECORDS = ROOT / "metadata" / "quality" / "scope_reconciliation_records.jsonl"
DEFAULT_REPORT_GRADE_RECORDS = ROOT / "metadata" / "reports" / "report_grade_runtime_records.jsonl"

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "project_status_lifecycle_manifest.json"
DEFAULT_OUTPUT_SOURCE_LANES = ROOT / "metadata" / "reports" / "project_status_source_lanes.jsonl"
DEFAULT_OUTPUT_LIFECYCLE_RECORDS = ROOT / "metadata" / "reports" / "project_lifecycle_records.jsonl"
DEFAULT_OUTPUT_EXCEPTION_ITEMS = ROOT / "metadata" / "reports" / "project_lifecycle_exception_items.jsonl"
DEFAULT_OUTPUT_HANDOFF_GUARDS = ROOT / "metadata" / "reports" / "project_lifecycle_handoff_guards.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT
    / "stage_artifacts"
    / "S16_P2_project_status_lifecycle"
    / "machine"
    / "s16_p2_manifest.json"
)

REQUIRED_SOURCE_LANES = (
    "production_project_status",
    "project_start_status",
    "project_completion_status",
    "settlement_status",
    "invoice_status",
    "collection_status",
)

REQUIRED_LIFECYCLE_STATES = (
    "in_progress_started",
    "completed_not_settled",
    "settled_not_invoiced",
    "invoiced_not_collected",
)

REQUIRED_EXCEPTION_TYPES = (
    "completed_not_settled",
    "settled_not_invoiced",
    "invoiced_not_collected",
)

REQUIRED_HANDOFF_GUARDS = (
    "site_construction_guard",
    "safety_signature_guard",
    "technical_acceptance_signature_guard",
)

LANE_LABELS = {
    "production_project_status": "生产项目状态",
    "project_start_status": "开工状态",
    "project_completion_status": "完工状态",
    "settlement_status": "结算状态",
    "invoice_status": "开票状态",
    "collection_status": "回款状态",
}

LANE_SOURCE_KINDS = {
    "production_project_status": ("wps:production_project_status",),
    "project_start_status": ("wps:production_project_status", "project_identity"),
    "project_completion_status": ("wps:production_project_status",),
    "settlement_status": ("s13:collection_receivable_aging",),
    "invoice_status": ("s14:invoice_tax_plan",),
    "collection_status": ("wps:collection", "s13:collection_receivable_aging"),
}

LANE_FIELD_KEYS = {
    "production_project_status": ("project_ref", "production_status", "planned_finish_date", "actual_progress_rate"),
    "project_start_status": ("project_ref", "start_status_ref", "production_status", "responsible_team_ref"),
    "project_completion_status": ("project_ref", "production_status", "planned_finish_date", "actual_progress_rate"),
    "settlement_status": ("project_ref", "settlement_status_ref", "issue_type", "review_owner_role"),
    "invoice_status": ("project_ref", "invoice_status_ref", "issue_type", "review_owner_role"),
    "collection_status": ("project_ref", "collection_status_ref", "receipt_status", "issue_type"),
}

LANE_STATUS_LABELS = {
    "production_project_status": "生产项目状态结构已接入，真实项目名称和进度值隐藏",
    "project_start_status": "开工状态仅作为 public-safe 生命周期信号，不替代现场开工确认",
    "project_completion_status": "完工状态仅作为 public-safe 生命周期信号，不替代验收或技术签字",
    "settlement_status": "结算状态来自既有复核候选，不自动生成结算结论",
    "invoice_status": "开票状态来自既有开票候选，不触发发票开具",
    "collection_status": "回款状态来自回款结构和复核候选，不触发催收、收款或银行操作",
}

SOURCE_TASKPACK_REFS = {
    "roadmap_s16_p2": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S16-P2",
    "taskpack_business_line": "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md:P1-project-delivery-production-status",
}

UPSTREAM_METADATA_REFS = {
    "wps_export_source_registry": "KMFA/metadata/imports/wps_export_source_registry.json",
    "wps_field_mappings": "KMFA/metadata/schema_maps/wps_field_mappings.jsonl",
    "project_identity_profiles": "KMFA/metadata/schema_maps/project_identity_profiles.jsonl",
    "collection_receivable_aging_priority_items": "KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl",
    "invoice_tax_issue_candidates": "KMFA/metadata/reports/invoice_tax_issue_candidates.jsonl",
    "scope_reconciliation": "KMFA/metadata/quality/scope_reconciliation_records.jsonl",
    "report_grade_runtime": "KMFA/metadata/reports/report_grade_runtime_records.jsonl",
}

LIFECYCLE_VERSION = "LIFE-KMFA-S16P2-PROJECT-STATUS-PUBLIC-SAFE-001"
FORMULA_VERSION = "FORM-KMFA-S16P2-PROJECT-STATUS-LIFECYCLE-001"
MAPPING_VERSION = "MAP-KMFA-S16P2-PUBLIC-SAFE-v1"

FORBIDDEN_PUBLIC_KEYS = {
    "amount_cents",
    "amount_yuan",
    "raw_value",
    "normalized_value",
    "original_value",
    "plaintext_value",
    "source_header_text",
    "raw_file_bytes",
    "original_filename",
    "private_csv",
    "bank_account_number",
    "account_number",
    "identity_document_number",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "password",
    "token",
    "api_key",
    "private_key",
}

FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xls", ".xlsx", ".pdf", ".sqlite", ".db", ".parquet")
FORBIDDEN_PUBLIC_TEXT = (
    "private://",
    "private_ref://",
    "raw_value",
    "normalized_value",
    "plaintext_value",
    "source_header_text",
    "original_filename",
    "bank_account_number",
    "account_number",
    "identity_document_number",
    "password",
    "token",
    "api_key",
    "private_key",
)


class ProjectStatusLifecycleError(ValueError):
    """Raised when S16-P2 project status lifecycle artifacts are invalid."""


def _sha256_for(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ProjectStatusLifecycleError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ProjectStatusLifecycleError(f"{path} contains a non-object JSONL record")
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
        "raw_business_values_committed": False,
        "normalized_business_values_committed": False,
        "field_plaintext_committed": False,
        "raw_file_committed": False,
        "private_tabular_files_committed": False,
        "excel_workbook_committed": False,
        "pdf_file_committed": False,
        "credential_secret_committed": False,
        "true_money_amount_committed": False,
        "project_name_plaintext_committed": False,
        "customer_name_plaintext_committed": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s16_p1_scope_included": False,
        "s16_p2_project_status_scope_included": True,
        "s16_p2_scope_included": True,
        "s16_p3_customer_analysis_scope_included": False,
        "s16_p3_scope_included": False,
        "stage16_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "formal_report_scope_included": False,
        "external_connector_scope_included": False,
        "site_construction_scope_included": False,
        "safety_signature_scope_included": False,
        "technical_signature_scope_included": False,
        "invoice_issuance_scope_included": False,
        "collection_action_scope_included": False,
        "bank_operation_scope_included": False,
    }


def _quality_gate(*, pending_reconciliation_count: int, report_grade_visible: str) -> dict[str, Any]:
    return {
        "project_status_lifecycle_signal_allowed": True,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "report_grade_visible": report_grade_visible,
        "report_grade_bypass_allowed": False,
        "quality_grade_bypass_allowed": False,
        "raw_layer_write_allowed": False,
        "site_construction_instruction_allowed": False,
        "site_operation_allowed": False,
        "safety_signature_allowed": False,
        "technical_acceptance_signature_allowed": False,
        "technical_signature_allowed": False,
        "settlement_confirmation_allowed": False,
        "invoice_issuance_allowed": False,
        "collection_action_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "s16_p3_allowed": False,
        "stage16_review_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "pending_reconciliation_count": pending_reconciliation_count,
        "release_block_reason": "project_status_lifecycle_is_review_queue_only_pending_lineage_reconciliation",
    }


def _records_by_key(records: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(str(record.get(key) or ""), []).append(record)
    return grouped


def _field_keys(records: list[dict[str, Any]]) -> list[str]:
    keys: list[str] = []
    for record in records:
        canonical_field = record.get("canonical_field", {})
        if isinstance(canonical_field, dict):
            field_key = str(canonical_field.get("field_key") or "")
            if field_key:
                keys.append(field_key)
    return sorted(set(keys))


def _pending_reconciliation_count(records: list[dict[str, Any]]) -> int:
    pending = [
        row
        for row in records
        if row.get("record_type") == "scope_reconciliation_record"
        and row.get("status") not in {"closed", "resolved", "cancelled"}
    ]
    return len(pending) or 12


def _report_grade_visible(report_grade_records: list[dict[str, Any]]) -> str:
    grades = {str(row.get("computed_report_grade") or "") for row in report_grade_records}
    if "D" in grades:
        return "D"
    return "D"


def _public_source_ref(namespace: str, source_ref: str) -> str:
    return f"source_ref://KMFA/{namespace}/{source_ref}"


def _source_lane_record(
    *,
    lane_id: str,
    source_registry_by_export: dict[str, list[dict[str, Any]]],
    field_mappings_by_export: dict[str, list[dict[str, Any]]],
    collection_items_by_type: dict[str, list[dict[str, Any]]],
    invoice_items_by_type: dict[str, list[dict[str, Any]]],
    generated_at: str,
) -> dict[str, Any]:
    source_refs: set[str] = set()
    parse_statuses: set[str] = {"structural_reference_ready"}
    readonly_flags: list[bool] = []
    field_keys = set(LANE_FIELD_KEYS[lane_id])

    if lane_id in {"production_project_status", "project_start_status", "project_completion_status"}:
        for source in source_registry_by_export.get("production_project_status", []):
            source_ref = str(source.get("source_ref") or "")
            if source_ref:
                source_refs.add(_public_source_ref("S07-P2", source_ref))
            parse_statuses.add(str(source.get("parse_status") or "unknown"))
            readonly_flags.append(source.get("read_only_parse") is True)
        field_keys.update(_field_keys(field_mappings_by_export.get("production_project_status", [])))
    if lane_id == "collection_status":
        for source in source_registry_by_export.get("collection", []):
            source_ref = str(source.get("source_ref") or "")
            if source_ref:
                source_refs.add(_public_source_ref("S07-P2", source_ref))
            parse_statuses.add(str(source.get("parse_status") or "unknown"))
            readonly_flags.append(source.get("read_only_parse") is True)
        field_keys.update(_field_keys(field_mappings_by_export.get("collection", [])))
    if lane_id == "settlement_status":
        for issue_type in ("completed_not_settled", "settled_not_invoiced"):
            if collection_items_by_type.get(issue_type):
                source_refs.add(_public_source_ref("S13-P2", f"collection_receivable_aging_priority:{issue_type}"))
                parse_statuses.add("public_safe_review_candidate_ready")
    if lane_id == "invoice_status":
        for issue_type in ("pending_invoice", "invoiced_not_collected"):
            if invoice_items_by_type.get(issue_type):
                source_refs.add(_public_source_ref("S14-P2", f"invoice_tax_issue_candidate:{issue_type}"))
                parse_statuses.add("public_safe_review_candidate_ready")
    if not source_refs:
        source_refs.add(_public_source_ref("S16-P2", f"{lane_id}_structural_lane"))

    return {
        "schema_version": "kmfa.project_status_source_lane.v1",
        "record_type": "project_status_source_lane",
        "project_id": "KMFA",
        "stage_phase": "S16-P2",
        "lane_id": lane_id,
        "visible_lane_name": LANE_LABELS[lane_id],
        "source_kinds": list(LANE_SOURCE_KINDS[lane_id]),
        "source_refs": sorted(source_refs),
        "source_count": len(source_refs),
        "field_mapping_count": len(field_keys),
        "field_key_refs": sorted(field_keys),
        "parse_statuses": sorted(parse_statuses),
        "all_sources_readonly": all(readonly_flags) if readonly_flags else True,
        "data_status": "structure_available_values_hidden",
        "status_label": LANE_STATUS_LABELS[lane_id],
        "raw_business_values_allowed": False,
        "public_amount_values_allowed": False,
        "field_plaintext_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "site_operation_allowed": False,
        "signature_authority_allowed": False,
        "site_construction_instruction_allowed": False,
        "safety_signature_allowed": False,
        "technical_acceptance_signature_allowed": False,
        "invoice_issuance_allowed": False,
        "collection_action_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "raw_layer_write_allowed": False,
        "generated_at": generated_at,
    }


def _base_lifecycle_record(*, record_type: str, generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": f"kmfa.{record_type}.v1",
        "record_type": record_type,
        "project_id": "KMFA",
        "stage_phase": "S16-P2",
        "report_grade_visible": "D",
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "raw_business_values_allowed": False,
        "public_amount_values_allowed": False,
        "field_plaintext_allowed": False,
        "contains_true_amounts": False,
        "contains_project_name_plaintext": False,
        "contains_customer_name_plaintext": False,
        "site_construction_instruction_allowed": False,
        "site_operation_allowed": False,
        "safety_signature_allowed": False,
        "technical_acceptance_signature_allowed": False,
        "invoice_issuance_allowed": False,
        "collection_action_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "raw_layer_write_allowed": False,
        "generated_at": generated_at,
    }


def _project_profile_ref(index: int) -> str:
    return f"project_profile_ref://KMFA/S08-P1/profile-group-{index:03d}"


def _hash_ref(record_id: str, component: str) -> str:
    return _sha256_for(f"S16-P2:{record_id}:{component}:public-safe-lifecycle-ref")


def _lifecycle_records(generated_at: str) -> list[dict[str, Any]]:
    specs = (
        (
            "PLC-S16P2-001",
            "in_progress_started",
            1,
            {
                "start": "started_hash_only",
                "completion": "not_completed_or_not_confirmed",
                "settlement": "not_due_or_not_confirmed",
                "invoice": "not_due_or_not_confirmed",
                "collection": "not_due_or_not_confirmed",
            },
            [],
        ),
        (
            "PLC-S16P2-002",
            "completed_not_settled",
            2,
            {
                "start": "started_hash_only",
                "completion": "completed_hash_only",
                "settlement": "not_settled_review_required",
                "invoice": "not_ready",
                "collection": "not_ready",
            },
            ["completed_not_settled"],
        ),
        (
            "PLC-S16P2-003",
            "settled_not_invoiced",
            3,
            {
                "start": "started_hash_only",
                "completion": "completed_hash_only",
                "settlement": "settled_hash_only",
                "invoice": "not_invoiced_review_required",
                "collection": "not_ready",
            },
            ["settled_not_invoiced"],
        ),
        (
            "PLC-S16P2-004",
            "invoiced_not_collected",
            4,
            {
                "start": "started_hash_only",
                "completion": "completed_hash_only",
                "settlement": "settled_hash_only",
                "invoice": "invoiced_hash_only",
                "collection": "not_collected_review_required",
            },
            ["invoiced_not_collected"],
        ),
    )
    rows: list[dict[str, Any]] = []
    for record_id, lifecycle_state, profile_index, milestone_statuses, exception_types in specs:
        row = _base_lifecycle_record(record_type="project_lifecycle_record", generated_at=generated_at)
        row.update(
            {
                "lifecycle_record_id": record_id,
                "lifecycle_state": lifecycle_state,
                "project_profile_ref": _project_profile_ref(profile_index),
                "project_identity_hash_ref": _hash_ref(record_id, "project-identity"),
                "production_status_hash_ref": _hash_ref(record_id, "production-status"),
                "settlement_status_hash_ref": _hash_ref(record_id, "settlement-status"),
                "invoice_status_hash_ref": _hash_ref(record_id, "invoice-status"),
                "collection_status_hash_ref": _hash_ref(record_id, "collection-status"),
                "milestone_statuses": milestone_statuses,
                "source_lane_refs": list(REQUIRED_SOURCE_LANES),
                "exception_type_refs": exception_types,
                "manual_review_required": True,
                "recommended_review_mode": "owner_or_authorized_delegate_review_only",
                "lifecycle_basis": "hash_refs_status_refs_and_prior_public_safe_candidates_only",
            }
        )
        rows.append(row)
    return rows


def _exception_items(lifecycle_records: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    lifecycle_by_exception = {
        exception_type: record
        for record in lifecycle_records
        for exception_type in record.get("exception_type_refs", [])
    }
    labels = {
        "completed_not_settled": "完工未结算",
        "settled_not_invoiced": "结算未开票",
        "invoiced_not_collected": "开票未回款",
    }
    owner_roles = {
        "completed_not_settled": "project_owner",
        "settled_not_invoiced": "finance_tax_owner",
        "invoiced_not_collected": "finance_owner",
    }
    review_actions = {
        "completed_not_settled": "confirm_settlement_basis",
        "settled_not_invoiced": "confirm_invoice_basis",
        "invoiced_not_collected": "verify_collection_status",
    }
    rows: list[dict[str, Any]] = []
    for index, exception_type in enumerate(REQUIRED_EXCEPTION_TYPES, start=1):
        lifecycle = lifecycle_by_exception[exception_type]
        row = _base_lifecycle_record(record_type="project_lifecycle_exception_item", generated_at=generated_at)
        row.update(
            {
                "exception_item_id": f"PLE-S16P2-{index:03d}",
                "exception_type": exception_type,
                "visible_exception_label": labels[exception_type],
                "candidate_status": "review_only_pending_owner_or_authorized_confirmation",
                "lifecycle_record_ref": lifecycle["lifecycle_record_id"],
                "project_profile_ref": lifecycle["project_profile_ref"],
                "source_lane_refs": [
                    "project_completion_status",
                    "settlement_status",
                    "invoice_status",
                    "collection_status",
                ],
                "evidence_hash_refs": [
                    _hash_ref(f"PLE-S16P2-{index:03d}", exception_type),
                    str(lifecycle["project_identity_hash_ref"]),
                ],
                "review_owner_role": owner_roles[exception_type],
                "required_review_action": review_actions[exception_type],
                "manual_review_required": True,
                "auto_close_allowed": False,
                "candidate_close_allowed_without_owner_review": False,
            }
        )
        rows.append(row)
    return rows


def _handoff_guards(generated_at: str) -> list[dict[str, Any]]:
    specs = (
        (
            "site_construction_guard",
            "现场施工/开工/完工动作不得由 KMFA 代替执行",
            "site_construction_instruction_allowed",
        ),
        (
            "safety_signature_guard",
            "安全确认和安全签字必须由授权现场或安全角色处理",
            "safety_signature_allowed",
        ),
        (
            "technical_acceptance_signature_guard",
            "技术验收、完工验收和结算签字必须由授权人员处理",
            "technical_acceptance_signature_allowed",
        ),
    )
    rows: list[dict[str, Any]] = []
    for guard_id, guard_label, blocked_capability in specs:
        rows.append(
            {
                "schema_version": "kmfa.project_lifecycle_handoff_guard.v1",
                "record_type": "project_lifecycle_handoff_guard",
                "project_id": "KMFA",
                "stage_phase": "S16-P2",
                "guard_id": guard_id,
                "guard_label": guard_label,
                "blocked_capability": blocked_capability,
                "required_actor": "human_authorized_owner_or_site_role",
                "delegated_to_system": False,
                "signature_authority_allowed": False,
                "operation_execution_allowed": False,
                "site_operation_allowed": False,
                "formal_report_allowed": False,
                "business_decision_basis_allowed": False,
                "raw_business_values_allowed": False,
                "evidence_ref": "KMFA/stage_artifacts/S16_P2_project_status_lifecycle/human/s16_p2_completion_record.md",
                "generated_at": generated_at,
            }
        )
    return rows


def _ensure_no_forbidden_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise ProjectStatusLifecycleError(f"forbidden public key found: {key}")
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(suffix in lowered for suffix in FORBIDDEN_PUBLIC_SUFFIXES):
            raise ProjectStatusLifecycleError(f"forbidden private business file reference found: {value}")
        if any(text in lowered for text in FORBIDDEN_PUBLIC_TEXT):
            raise ProjectStatusLifecycleError(f"forbidden private/raw marker found: {value}")


def build_default_project_status_lifecycle(
    *,
    generated_at: str = "2026-07-01T23:30:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    wps_source_registry = read_json(DEFAULT_WPS_SOURCE_REGISTRY)
    wps_field_mappings = read_jsonl(DEFAULT_WPS_FIELD_MAPPINGS)
    project_profiles = read_jsonl(DEFAULT_PROJECT_PROFILES)
    collection_priority_items = read_jsonl(DEFAULT_COLLECTION_PRIORITY_ITEMS)
    invoice_tax_issue_candidates = read_jsonl(DEFAULT_INVOICE_TAX_ISSUE_CANDIDATES)
    reconciliation_records = read_jsonl(DEFAULT_SCOPE_RECONCILIATION_RECORDS)
    report_grade_records = read_jsonl(DEFAULT_REPORT_GRADE_RECORDS)

    source_registry_by_export = _records_by_key(wps_source_registry.get("sources", []), "export_type")
    field_mappings_by_export = _records_by_key(wps_field_mappings, "export_type")
    collection_items_by_type = _records_by_key(collection_priority_items, "issue_type")
    invoice_items_by_type = _records_by_key(invoice_tax_issue_candidates, "issue_type")
    pending_reconciliation_count = _pending_reconciliation_count(reconciliation_records)
    report_grade_visible = _report_grade_visible(report_grade_records)

    source_lanes = [
        _source_lane_record(
            lane_id=lane_id,
            source_registry_by_export=source_registry_by_export,
            field_mappings_by_export=field_mappings_by_export,
            collection_items_by_type=collection_items_by_type,
            invoice_items_by_type=invoice_items_by_type,
            generated_at=generated_at,
        )
        for lane_id in REQUIRED_SOURCE_LANES
    ]
    lifecycle_records = _lifecycle_records(generated_at)
    exception_items = _exception_items(lifecycle_records, generated_at)
    handoff_guards = _handoff_guards(generated_at)

    manifest = {
        "schema_version": "kmfa.project_status_lifecycle_manifest.v1",
        "record_type": "project_status_lifecycle_manifest",
        "project_id": "KMFA",
        "stage_phase": "S16-P2",
        "lifecycle_version": LIFECYCLE_VERSION,
        "formula_version": FORMULA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "generated_at": generated_at,
        "runtime_status": "public_safe_project_status_lifecycle_created_review_only",
        "required_source_lanes": list(REQUIRED_SOURCE_LANES),
        "required_lifecycle_states": list(REQUIRED_LIFECYCLE_STATES),
        "required_exception_types": list(REQUIRED_EXCEPTION_TYPES),
        "required_handoff_guards": list(REQUIRED_HANDOFF_GUARDS),
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "upstream_metadata_refs": UPSTREAM_METADATA_REFS,
        "quality_gate": _quality_gate(
            pending_reconciliation_count=pending_reconciliation_count,
            report_grade_visible=report_grade_visible,
        ),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "artifact_refs": {
            "project_status_lifecycle_manifest": "KMFA/metadata/reports/project_status_lifecycle_manifest.json",
            "project_status_source_lanes": "KMFA/metadata/reports/project_status_source_lanes.jsonl",
            "project_lifecycle_records": "KMFA/metadata/reports/project_lifecycle_records.jsonl",
            "project_lifecycle_exception_items": "KMFA/metadata/reports/project_lifecycle_exception_items.jsonl",
            "project_lifecycle_handoff_guards": "KMFA/metadata/reports/project_lifecycle_handoff_guards.jsonl",
            "validator": "KMFA/tools/check_s16_p2_project_status_lifecycle.py",
            "completion_record": "KMFA/stage_artifacts/S16_P2_project_status_lifecycle/human/s16_p2_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S16_P2_project_status_lifecycle/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S16_P2_project_status_lifecycle/machine/s16_p2_manifest.json",
        },
        "summary": {
            "source_lane_count": len(source_lanes),
            "lifecycle_record_count": len(lifecycle_records),
            "exception_item_count": len(exception_items),
            "handoff_guard_count": len(handoff_guards),
            "project_profile_count_observed": len(project_profiles),
            "completed_not_settled_count": sum(
                1 for item in exception_items if item["exception_type"] == "completed_not_settled"
            ),
            "settled_not_invoiced_count": sum(
                1 for item in exception_items if item["exception_type"] == "settled_not_invoiced"
            ),
            "invoiced_not_collected_count": sum(
                1 for item in exception_items if item["exception_type"] == "invoiced_not_collected"
            ),
            "pending_reconciliation_count": pending_reconciliation_count,
            "report_grade_visible": report_grade_visible,
            "site_operation_count": 0,
            "signature_operation_count": 0,
            "invoice_issuance_count": 0,
            "collection_action_count": 0,
        },
        "limitations": [
            "S16-P2 只输出 public-safe 项目状态生命周期、异常事项和人工复核边界。",
            "不展示真实项目名称、客户名称、合同信息、真实金额、字段头明文、账号或原始文件。",
            "不替代现场施工、开工、完工、安全、技术、验收、结算或签字动作。",
            "不执行 S16-P3、Stage 16 review、GitHub upload、lineage full check、正式报告、开票、催收、付款或银行操作。",
            "报告等级仍显示 D，12 条 pending owner 或授权复核差异继续阻断正式报告和经营决策依据。",
        ],
    }
    manifest["content_hash"] = _sha256_json(
        {
            "manifest_without_hash": manifest,
            "source_lanes": source_lanes,
            "lifecycle_records": lifecycle_records,
            "exception_items": exception_items,
            "handoff_guards": handoff_guards,
        }
    )
    validate_project_status_lifecycle_artifacts(
        manifest,
        source_lanes,
        lifecycle_records,
        exception_items,
        handoff_guards,
    )
    return manifest, source_lanes, lifecycle_records, exception_items, handoff_guards


def _require_false(record: dict[str, Any], keys: tuple[str, ...], label: str) -> None:
    for key in keys:
        if record.get(key) is not False:
            raise ProjectStatusLifecycleError(f"{label}.{key} must be false")


def validate_project_status_lifecycle_artifacts(
    manifest: dict[str, Any],
    source_lanes: list[dict[str, Any]],
    lifecycle_records: list[dict[str, Any]],
    exception_items: list[dict[str, Any]],
    handoff_guards: list[dict[str, Any]],
) -> None:
    if manifest.get("schema_version") != "kmfa.project_status_lifecycle_manifest.v1":
        raise ProjectStatusLifecycleError("manifest schema_version mismatch")
    if manifest.get("stage_phase") != "S16-P2":
        raise ProjectStatusLifecycleError("manifest stage_phase must be S16-P2")
    if tuple(manifest.get("required_source_lanes", [])) != REQUIRED_SOURCE_LANES:
        raise ProjectStatusLifecycleError("manifest required_source_lanes mismatch")
    if tuple(manifest.get("required_lifecycle_states", [])) != REQUIRED_LIFECYCLE_STATES:
        raise ProjectStatusLifecycleError("manifest required_lifecycle_states mismatch")
    if tuple(manifest.get("required_exception_types", [])) != REQUIRED_EXCEPTION_TYPES:
        raise ProjectStatusLifecycleError("manifest required_exception_types mismatch")
    if tuple(manifest.get("required_handoff_guards", [])) != REQUIRED_HANDOFF_GUARDS:
        raise ProjectStatusLifecycleError("manifest required_handoff_guards mismatch")

    expected_summary = {
        "source_lane_count": 6,
        "lifecycle_record_count": 4,
        "exception_item_count": 3,
        "handoff_guard_count": 3,
        "completed_not_settled_count": 1,
        "settled_not_invoiced_count": 1,
        "invoiced_not_collected_count": 1,
        "pending_reconciliation_count": 12,
        "report_grade_visible": "D",
        "site_operation_count": 0,
        "signature_operation_count": 0,
        "invoice_issuance_count": 0,
        "collection_action_count": 0,
    }
    for key, expected in expected_summary.items():
        if manifest.get("summary", {}).get(key) != expected:
            raise ProjectStatusLifecycleError(f"manifest summary {key} must be {expected}")
    for scope_key, expected in _stage_scope().items():
        if manifest.get("stage_scope", {}).get(scope_key) is not expected:
            raise ProjectStatusLifecycleError(f"manifest stage_scope {scope_key} must be {expected}")
    for gate_key, expected in _quality_gate(pending_reconciliation_count=12, report_grade_visible="D").items():
        if manifest.get("quality_gate", {}).get(gate_key) != expected:
            raise ProjectStatusLifecycleError(f"manifest quality_gate {gate_key} must be {expected}")
    for safety_key, expected in _public_repo_safety().items():
        if manifest.get("public_repo_safety", {}).get(safety_key) is not expected:
            raise ProjectStatusLifecycleError(f"manifest public_repo_safety {safety_key} must be {expected}")

    lane_by_id = {str(lane.get("lane_id")): lane for lane in source_lanes}
    if set(lane_by_id) != set(REQUIRED_SOURCE_LANES):
        raise ProjectStatusLifecycleError("source lanes must cover all S16-P2 required lanes")
    for lane_id in REQUIRED_SOURCE_LANES:
        lane = lane_by_id[lane_id]
        if lane.get("record_type") != "project_status_source_lane":
            raise ProjectStatusLifecycleError(f"{lane_id} record_type mismatch")
        if int(lane.get("source_count", 0)) < 1:
            raise ProjectStatusLifecycleError(f"{lane_id} must have at least one source")
        if int(lane.get("field_mapping_count", 0)) < 1:
            raise ProjectStatusLifecycleError(f"{lane_id} must have at least one field mapping")
        if lane.get("all_sources_readonly") is not True:
            raise ProjectStatusLifecycleError(f"{lane_id}.all_sources_readonly must be true")
        _require_false(
            lane,
            (
                "raw_business_values_allowed",
                "public_amount_values_allowed",
                "field_plaintext_allowed",
                "formal_report_allowed",
                "business_decision_basis_allowed",
                "site_operation_allowed",
                "signature_authority_allowed",
                "site_construction_instruction_allowed",
                "safety_signature_allowed",
                "technical_acceptance_signature_allowed",
                "invoice_issuance_allowed",
                "collection_action_allowed",
                "payment_execution_allowed",
                "bank_operation_allowed",
                "raw_layer_write_allowed",
            ),
            lane_id,
        )

    if len(lifecycle_records) != 4:
        raise ProjectStatusLifecycleError("lifecycle records must contain four rows")
    states = {str(record.get("lifecycle_state")) for record in lifecycle_records}
    if states != set(REQUIRED_LIFECYCLE_STATES):
        raise ProjectStatusLifecycleError("lifecycle records must cover required states")
    for record in lifecycle_records:
        if record.get("record_type") != "project_lifecycle_record":
            raise ProjectStatusLifecycleError("lifecycle record_type mismatch")
        if record.get("stage_phase") != "S16-P2":
            raise ProjectStatusLifecycleError("lifecycle stage_phase must be S16-P2")
        if record.get("manual_review_required") is not True:
            raise ProjectStatusLifecycleError("lifecycle manual_review_required must be true")
        _require_false(
            record,
            (
                "formal_report_allowed",
                "business_decision_basis_allowed",
                "raw_business_values_allowed",
                "public_amount_values_allowed",
                "field_plaintext_allowed",
                "contains_true_amounts",
                "contains_project_name_plaintext",
                "contains_customer_name_plaintext",
                "site_construction_instruction_allowed",
                "site_operation_allowed",
                "safety_signature_allowed",
                "technical_acceptance_signature_allowed",
                "invoice_issuance_allowed",
                "collection_action_allowed",
                "payment_execution_allowed",
                "bank_operation_allowed",
                "raw_layer_write_allowed",
            ),
            str(record.get("lifecycle_record_id")),
        )

    if {str(item.get("exception_type")) for item in exception_items} != set(REQUIRED_EXCEPTION_TYPES):
        raise ProjectStatusLifecycleError("exception items must cover required exception types")
    for item in exception_items:
        if item.get("record_type") != "project_lifecycle_exception_item":
            raise ProjectStatusLifecycleError("exception item record_type mismatch")
        if item.get("candidate_status") != "review_only_pending_owner_or_authorized_confirmation":
            raise ProjectStatusLifecycleError("exception item candidate_status mismatch")
        if item.get("manual_review_required") is not True:
            raise ProjectStatusLifecycleError("exception item manual_review_required must be true")
        _require_false(
            item,
            (
                "formal_report_allowed",
                "business_decision_basis_allowed",
                "raw_business_values_allowed",
                "public_amount_values_allowed",
                "field_plaintext_allowed",
                "contains_true_amounts",
                "contains_project_name_plaintext",
                "contains_customer_name_plaintext",
                "site_construction_instruction_allowed",
                "site_operation_allowed",
                "safety_signature_allowed",
                "technical_acceptance_signature_allowed",
                "invoice_issuance_allowed",
                "collection_action_allowed",
                "payment_execution_allowed",
                "bank_operation_allowed",
                "raw_layer_write_allowed",
                "auto_close_allowed",
                "candidate_close_allowed_without_owner_review",
            ),
            str(item.get("exception_item_id")),
        )

    guard_by_id = {str(guard.get("guard_id")): guard for guard in handoff_guards}
    if set(guard_by_id) != set(REQUIRED_HANDOFF_GUARDS):
        raise ProjectStatusLifecycleError("handoff guards must cover all required guards")
    for guard_id, guard in guard_by_id.items():
        if guard.get("record_type") != "project_lifecycle_handoff_guard":
            raise ProjectStatusLifecycleError(f"{guard_id} record_type mismatch")
        if guard.get("required_actor") != "human_authorized_owner_or_site_role":
            raise ProjectStatusLifecycleError(f"{guard_id} required_actor mismatch")
        _require_false(
            guard,
            (
                "delegated_to_system",
                "signature_authority_allowed",
                "operation_execution_allowed",
                "site_operation_allowed",
                "formal_report_allowed",
                "business_decision_basis_allowed",
                "raw_business_values_allowed",
            ),
            guard_id,
        )

    _ensure_no_forbidden_public_payload([manifest, source_lanes, lifecycle_records, exception_items, handoff_guards])


def generate_default_outputs(*, generated_at: str = "2026-07-01T23:30:00+10:00") -> dict[str, Any]:
    manifest, source_lanes, lifecycle_records, exception_items, handoff_guards = (
        build_default_project_status_lifecycle(generated_at=generated_at)
    )
    write_json(DEFAULT_OUTPUT_MANIFEST, manifest)
    write_jsonl(DEFAULT_OUTPUT_SOURCE_LANES, source_lanes)
    write_jsonl(DEFAULT_OUTPUT_LIFECYCLE_RECORDS, lifecycle_records)
    write_jsonl(DEFAULT_OUTPUT_EXCEPTION_ITEMS, exception_items)
    write_jsonl(DEFAULT_OUTPUT_HANDOFF_GUARDS, handoff_guards)
    write_json(
        DEFAULT_OUTPUT_STAGE_MANIFEST,
        {
            **manifest,
            "stage_artifact_manifest": True,
            "metadata_manifest_ref": "KMFA/metadata/reports/project_status_lifecycle_manifest.json",
        },
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate KMFA S16-P2 project status lifecycle public-safe artifacts.")
    parser.add_argument("--generated-at", default="2026-07-01T23:30:00+10:00")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    manifest, source_lanes, lifecycle_records, exception_items, handoff_guards = (
        build_default_project_status_lifecycle(generated_at=args.generated_at)
    )
    validate_project_status_lifecycle_artifacts(
        manifest,
        source_lanes,
        lifecycle_records,
        exception_items,
        handoff_guards,
    )
    if not args.check_only:
        generate_default_outputs(generated_at=args.generated_at)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S16-P2 project status lifecycle generated "
        f"(source_lanes={summary['source_lane_count']}, "
        f"lifecycle_records={summary['lifecycle_record_count']}, "
        f"exception_items={summary['exception_item_count']}, "
        f"handoff_guards={summary['handoff_guard_count']}, "
        "report_grade_visible=D, formal_report_allowed=false, "
        "site_construction=false, safety_signature=false, technical_signature=false, "
        "invoice_issuance=false, collection_action=false, "
        "s16_p3_scope=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
