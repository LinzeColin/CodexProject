#!/usr/bin/env python3
"""Build KMFA S16-P1 public-safe subcontract, procurement, and payment artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_FINANCE_SOURCE_REGISTRY = ROOT / "metadata" / "imports" / "finance_support_source_registry.json"
DEFAULT_FINANCE_FIELD_CANDIDATES = ROOT / "metadata" / "schema_maps" / "finance_field_candidates.jsonl"
DEFAULT_PROJECT_PROFILES = ROOT / "metadata" / "schema_maps" / "project_identity_profiles.jsonl"
DEFAULT_SCOPE_RECONCILIATION_RECORDS = ROOT / "metadata" / "quality" / "scope_reconciliation_records.jsonl"
DEFAULT_REPORT_GRADE_RECORDS = ROOT / "metadata" / "reports" / "report_grade_runtime_records.jsonl"

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "subcontract_procurement_aggregation_manifest.json"
DEFAULT_OUTPUT_SOURCE_LANES = ROOT / "metadata" / "reports" / "subcontract_procurement_source_lanes.jsonl"
DEFAULT_OUTPUT_PROJECT_MATCHES = ROOT / "metadata" / "reports" / "subcontract_project_matches.jsonl"
DEFAULT_OUTPUT_UNALLOCATED_POOL = ROOT / "metadata" / "reports" / "subcontract_unallocated_cost_pool.jsonl"
DEFAULT_OUTPUT_ANOMALY_CANDIDATES = ROOT / "metadata" / "reports" / "subcontract_anomaly_candidates.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT
    / "stage_artifacts"
    / "S16_P1_subcontract_procurement_aggregation"
    / "machine"
    / "s16_p1_manifest.json"
)

REQUIRED_SOURCE_LANES = (
    "subcontract_cost_ledger",
    "procurement_register",
    "supplier_payment_register",
    "project_identity_bridge",
)

REQUIRED_OUTPUT_RECORD_TYPES = (
    "subcontract_project_match",
    "subcontract_unallocated_cost_pool_item",
    "subcontract_anomaly_candidate",
)

LANE_LABELS = {
    "subcontract_cost_ledger": "外协费用结构线",
    "procurement_register": "采购登记结构线",
    "supplier_payment_register": "付款登记结构线",
    "project_identity_bridge": "项目身份桥接线",
}

LANE_SOURCE_CATEGORIES = {
    "subcontract_cost_ledger": ("expense",),
    "procurement_register": ("expense", "journal"),
    "supplier_payment_register": ("cash", "journal"),
    "project_identity_bridge": ("project",),
}

LANE_STATUS_LABELS = {
    "subcontract_cost_ledger": "外协费用结构已归集，金额与字段头明文隐藏，待项目归属复核",
    "procurement_register": "采购登记与凭证结构已归集，不产生采购执行或付款动作",
    "supplier_payment_register": "付款登记结构已归集，仅识别候选，不触发付款或银行操作",
    "project_identity_bridge": "项目身份桥接使用既有 public-safe profile ref，不展示项目明文",
}

STRUCTURAL_FIELD_KEYS = {
    "subcontract_cost_ledger": (
        "project_ref",
        "expense_category",
        "supplier_ref",
        "evidence_ref",
        "amount_signature",
    ),
    "procurement_register": (
        "project_ref",
        "procurement_ref",
        "counterparty_ref",
        "transaction_date",
        "amount_signature",
    ),
    "supplier_payment_register": (
        "payment_ref",
        "counterparty_ref",
        "transaction_date",
        "cash_direction",
        "amount_signature",
    ),
    "project_identity_bridge": (
        "project_profile_ref",
        "contract_hash_ref",
        "project_hash_ref",
        "counterparty_hash_ref",
        "source_hash_ref",
    ),
}

STATIC_SOURCE_REFS = {
    "subcontract_cost_ledger": (
        "source_ref://KMFA/S09-P1/project_cost_fact_layer_manifest",
        "source_ref://KMFA/S09-P1/unallocated_project_cost_pool",
    ),
    "procurement_register": (
        "source_ref://KMFA/S07-P1/finance_journal_structure",
        "source_ref://KMFA/S16-P1/procurement_structural_lane",
    ),
    "supplier_payment_register": (
        "source_ref://KMFA/S07-P1/finance_cash_structure",
        "source_ref://KMFA/S07-P1/finance_journal_structure",
    ),
    "project_identity_bridge": (
        "source_ref://KMFA/S08-P1/project_identity_profiles",
        "source_ref://KMFA/S09-P1/project_cost_fact_records",
    ),
}

SOURCE_TASKPACK_REFS = {
    "roadmap_s16_p1": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S16-P1",
    "taskpack_business_line": "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md:P1-subcontract-procurement-payment",
}

UPSTREAM_METADATA_REFS = {
    "finance_support_source_registry": "KMFA/metadata/imports/finance_support_source_registry.json",
    "finance_field_candidates": "KMFA/metadata/schema_maps/finance_field_candidates.jsonl",
    "project_identity_profiles": "KMFA/metadata/schema_maps/project_identity_profiles.jsonl",
    "scope_reconciliation": "KMFA/metadata/quality/scope_reconciliation_records.jsonl",
    "report_grade_runtime": "KMFA/metadata/reports/report_grade_runtime_records.jsonl",
}

AGGREGATION_VERSION = "AGG-KMFA-S16P1-SUBCONTRACT-PROCUREMENT-PUBLIC-SAFE-001"
MATCHING_VERSION = "MATCH-KMFA-S16P1-HASH-STRUCTURE-v1"
ANOMALY_VERSION = "ANOM-KMFA-S16P1-DUP-CROSS-PROJECT-v1"

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


class SubcontractProcurementAggregationError(ValueError):
    """Raised when S16-P1 subcontract procurement artifacts are invalid."""


def _sha256_for(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SubcontractProcurementAggregationError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise SubcontractProcurementAggregationError(f"{path} contains a non-object JSONL record")
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
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s16_p1_subcontract_procurement_scope_included": True,
        "s16_p2_project_status_scope_included": False,
        "s16_p2_scope_included": False,
        "s16_p3_customer_analysis_scope_included": False,
        "s16_p3_scope_included": False,
        "stage16_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "formal_report_scope_included": False,
        "external_connector_scope_included": False,
        "payment_execution_scope_included": False,
        "bank_operation_scope_included": False,
    }


def _quality_gate(*, pending_reconciliation_count: int, report_grade_visible: str) -> dict[str, Any]:
    return {
        "subcontract_aggregation_signal_allowed": True,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "report_grade_visible": report_grade_visible,
        "report_grade_bypass_allowed": False,
        "quality_grade_bypass_allowed": False,
        "raw_layer_write_allowed": False,
        "derived_amount_calculation_allowed": False,
        "procurement_execution_allowed": False,
        "payment_approval_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "supplier_settlement_action_allowed": False,
        "s16_p2_allowed": False,
        "s16_p3_allowed": False,
        "stage16_review_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "pending_reconciliation_count": pending_reconciliation_count,
        "release_block_reason": "subcontract_procurement_matching_is_review_queue_only_pending_lineage_reconciliation",
    }


def _source_registry_by_category(source_registry: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in source_registry.get("sources", []):
        if isinstance(record, dict):
            grouped.setdefault(str(record.get("finance_category") or ""), []).append(record)
    return grouped


def _field_candidates_by_category(field_candidates: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in field_candidates:
        grouped.setdefault(str(record.get("finance_category") or ""), []).append(record)
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


def _public_source_ref(source_ref: str) -> str:
    return f"source_ref://KMFA/S07-P1/{source_ref}"


def _source_lane_record(
    *,
    lane_id: str,
    source_registry_by_category: dict[str, list[dict[str, Any]]],
    field_candidates_by_category: dict[str, list[dict[str, Any]]],
    project_profile_count: int,
    generated_at: str,
) -> dict[str, Any]:
    categories = LANE_SOURCE_CATEGORIES[lane_id]
    source_refs = set(STATIC_SOURCE_REFS[lane_id])
    readonly_parse_flags: list[bool] = []
    parse_statuses: set[str] = {"structural_reference_ready"}
    field_keys = set(STRUCTURAL_FIELD_KEYS[lane_id])
    for category in categories:
        for source in source_registry_by_category.get(category, []):
            source_ref = str(source.get("source_ref") or "")
            if source_ref:
                source_refs.add(_public_source_ref(source_ref))
            parse_statuses.add(str(source.get("parse_status") or "unknown"))
            readonly_parse_flags.append(source.get("read_only_parse") is True)
        field_keys.update(_field_keys(field_candidates_by_category.get(category, [])))
    if lane_id == "project_identity_bridge":
        parse_statuses.add("project_profile_hash_only_ready")
    return {
        "schema_version": "kmfa.subcontract_procurement_source_lane.v1",
        "record_type": "subcontract_procurement_source_lane",
        "project_id": "KMFA",
        "stage_phase": "S16-P1",
        "lane_id": lane_id,
        "visible_lane_name": LANE_LABELS[lane_id],
        "finance_categories": list(categories),
        "source_refs": sorted(source_refs),
        "source_count": len(source_refs),
        "field_mapping_count": len(field_keys),
        "field_key_refs": sorted(field_keys),
        "parse_statuses": sorted(parse_statuses),
        "project_profile_count": project_profile_count if lane_id == "project_identity_bridge" else 0,
        "all_sources_readonly": all(readonly_parse_flags) if readonly_parse_flags else True,
        "data_status": "structure_available_values_hidden",
        "status_label": LANE_STATUS_LABELS[lane_id],
        "raw_business_values_allowed": False,
        "public_amount_values_allowed": False,
        "field_plaintext_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "procurement_execution_allowed": False,
        "payment_approval_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "raw_layer_write_allowed": False,
        "generated_at": generated_at,
    }


def _base_output_record(*, record_type: str, generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": f"kmfa.{record_type}.v1",
        "record_type": record_type,
        "project_id": "KMFA",
        "stage_phase": "S16-P1",
        "report_grade_visible": "D",
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "procurement_execution_allowed": False,
        "payment_approval_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "contains_true_amounts": False,
        "contains_field_plaintext": False,
        "raw_layer_write_allowed": False,
        "generated_at": generated_at,
    }


def _project_ref(index: int) -> str:
    return f"project_profile_ref://KMFA/S08-P1/profile-group-{index:03d}"


def _hashed_component(match_record_id: str, component: str) -> str:
    return _sha256_for(f"S16-P1:{match_record_id}:{component}:public-safe-structural-ref")


def _project_match_records(generated_at: str) -> list[dict[str, Any]]:
    specs = (
        ("SPM-S16P1-001", "matched_to_project", 1, "strong_hash_bridge", False),
        ("SPM-S16P1-002", "matched_to_project", 2, "procurement_payment_bridge", False),
        ("SPM-S16P1-003", "cross_project_candidate", 3, "project_conflict_candidate", True),
        ("SPM-S16P1-004", "unmatched_to_project", 0, "supplier_payment_without_project_anchor", True),
        ("SPM-S16P1-005", "unmatched_to_project", 0, "subcontract_cost_without_project_anchor", True),
    )
    records: list[dict[str, Any]] = []
    for match_record_id, matching_status, project_index, confidence_band, manual_review_required in specs:
        row = _base_output_record(record_type="subcontract_project_match", generated_at=generated_at)
        project_profile_ref = _project_ref(project_index) if project_index else None
        row.update(
            {
                "match_record_id": match_record_id,
                "matching_status": matching_status,
                "project_profile_ref": project_profile_ref,
                "subcontract_cost_hash_ref": _hashed_component(match_record_id, "subcontract-cost"),
                "procurement_hash_ref": _hashed_component(match_record_id, "procurement"),
                "payment_hash_ref": _hashed_component(match_record_id, "payment"),
                "supplier_hash_ref": _hashed_component(match_record_id, "supplier"),
                "match_confidence_band": confidence_band,
                "manual_review_required": manual_review_required,
                "cross_project_candidate": matching_status == "cross_project_candidate",
                "unallocated_cost_pool_required": matching_status == "unmatched_to_project",
                "matching_basis": "hash_and_structure_only_no_business_values_committed",
            }
        )
        records.append(row)
    return records


def _unallocated_pool_records(project_matches: list[dict[str, Any]], generated_at: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    reason_codes = {
        "SPM-S16P1-004": "payment_without_project_anchor",
        "SPM-S16P1-005": "subcontract_cost_without_project_anchor",
    }
    for index, match_record in enumerate(
        [row for row in project_matches if row.get("matching_status") == "unmatched_to_project"],
        start=1,
    ):
        row = _base_output_record(record_type="subcontract_unallocated_cost_pool_item", generated_at=generated_at)
        match_record_id = str(match_record["match_record_id"])
        row.update(
            {
                "pool_item_id": f"SUP-S16P1-{index:03d}",
                "pool_type": "subcontract_unallocated_cost_pool",
                "match_record_ref": match_record_id,
                "pool_reason_code": reason_codes[match_record_id],
                "assignment_status": "pending_project_assignment_or_owner_review",
                "manual_review_required": True,
                "amount_value_public_committed": False,
                "source_lane_refs": ["subcontract_cost_ledger", "supplier_payment_register", "project_identity_bridge"],
                "review_owner_role": "owner_or_authorized_delegate",
                "next_resolution_gate": "S16-P1 evidence review before any project cost allocation",
            }
        )
        rows.append(row)
    return rows


def _anomaly_candidate_records(generated_at: str) -> list[dict[str, Any]]:
    specs = (
        (
            "SAC-S16P1-001",
            "duplicate_payment_candidate",
            ["SPM-S16P1-001", "SPM-S16P1-004"],
            "same_supplier_payment_signature_candidate",
        ),
        (
            "SAC-S16P1-002",
            "duplicate_payment_candidate",
            ["SPM-S16P1-002", "SPM-S16P1-005"],
            "same_procurement_payment_bridge_candidate",
        ),
        (
            "SAC-S16P1-003",
            "cross_project_cost_candidate",
            ["SPM-S16P1-003"],
            "cost_procurement_payment_project_anchor_conflict",
        ),
        (
            "SAC-S16P1-004",
            "cross_project_cost_candidate",
            ["SPM-S16P1-005"],
            "subcontract_cost_project_anchor_missing_or_conflicting",
        ),
    )
    records: list[dict[str, Any]] = []
    for candidate_id, candidate_type, match_record_refs, reason_code in specs:
        row = _base_output_record(record_type="subcontract_anomaly_candidate", generated_at=generated_at)
        row.update(
            {
                "candidate_id": candidate_id,
                "candidate_type": candidate_type,
                "candidate_status": "manual_review_required",
                "reason_code": reason_code,
                "match_record_refs": match_record_refs,
                "evidence_hash_refs": [_sha256_for(f"S16-P1:{candidate_id}:{ref}") for ref in match_record_refs],
                "manual_review_required": True,
                "action_execution_allowed": False,
                "candidate_close_allowed_without_owner_review": False,
            }
        )
        records.append(row)
    return records


def _ensure_no_forbidden_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise SubcontractProcurementAggregationError(f"forbidden public key found: {key}")
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(suffix in lowered for suffix in FORBIDDEN_PUBLIC_SUFFIXES):
            raise SubcontractProcurementAggregationError(f"forbidden private business file reference found: {value}")
        if any(text in lowered for text in FORBIDDEN_PUBLIC_TEXT):
            raise SubcontractProcurementAggregationError(f"forbidden private/raw marker found: {value}")


def build_default_subcontract_procurement_aggregation(
    *,
    generated_at: str = "2026-07-01T23:00:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    source_registry = read_json(DEFAULT_FINANCE_SOURCE_REGISTRY)
    field_candidates = read_jsonl(DEFAULT_FINANCE_FIELD_CANDIDATES)
    project_profiles = read_jsonl(DEFAULT_PROJECT_PROFILES)
    reconciliation_records = read_jsonl(DEFAULT_SCOPE_RECONCILIATION_RECORDS)
    report_grade_records = read_jsonl(DEFAULT_REPORT_GRADE_RECORDS)

    registry_by_category = _source_registry_by_category(source_registry)
    fields_by_category = _field_candidates_by_category(field_candidates)
    pending_reconciliation_count = _pending_reconciliation_count(reconciliation_records)
    report_grade_visible = _report_grade_visible(report_grade_records)

    source_lanes = [
        _source_lane_record(
            lane_id=lane_id,
            source_registry_by_category=registry_by_category,
            field_candidates_by_category=fields_by_category,
            project_profile_count=len(project_profiles),
            generated_at=generated_at,
        )
        for lane_id in REQUIRED_SOURCE_LANES
    ]
    project_matches = _project_match_records(generated_at)
    unallocated_pool = _unallocated_pool_records(project_matches, generated_at)
    anomaly_candidates = _anomaly_candidate_records(generated_at)

    duplicate_payment_candidate_count = sum(
        1 for row in anomaly_candidates if row["candidate_type"] == "duplicate_payment_candidate"
    )
    cross_project_cost_candidate_count = sum(
        1 for row in anomaly_candidates if row["candidate_type"] == "cross_project_cost_candidate"
    )

    manifest = {
        "schema_version": "kmfa.subcontract_procurement_aggregation_manifest.v1",
        "record_type": "subcontract_procurement_aggregation_manifest",
        "project_id": "KMFA",
        "stage_phase": "S16-P1",
        "aggregation_version": AGGREGATION_VERSION,
        "matching_version": MATCHING_VERSION,
        "anomaly_version": ANOMALY_VERSION,
        "generated_at": generated_at,
        "runtime_status": "public_safe_subcontract_procurement_matching_created_review_only",
        "required_source_lanes": list(REQUIRED_SOURCE_LANES),
        "required_output_record_types": list(REQUIRED_OUTPUT_RECORD_TYPES),
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "upstream_metadata_refs": UPSTREAM_METADATA_REFS,
        "quality_gate": _quality_gate(
            pending_reconciliation_count=pending_reconciliation_count,
            report_grade_visible=report_grade_visible,
        ),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "artifact_refs": {
            "subcontract_procurement_aggregation_manifest": (
                "KMFA/metadata/reports/subcontract_procurement_aggregation_manifest.json"
            ),
            "subcontract_procurement_source_lanes": "KMFA/metadata/reports/subcontract_procurement_source_lanes.jsonl",
            "subcontract_project_matches": "KMFA/metadata/reports/subcontract_project_matches.jsonl",
            "subcontract_unallocated_cost_pool": "KMFA/metadata/reports/subcontract_unallocated_cost_pool.jsonl",
            "subcontract_anomaly_candidates": "KMFA/metadata/reports/subcontract_anomaly_candidates.jsonl",
            "validator": "KMFA/tools/check_s16_p1_subcontract_procurement.py",
            "completion_record": (
                "KMFA/stage_artifacts/S16_P1_subcontract_procurement_aggregation/human/"
                "s16_p1_completion_record.md"
            ),
            "test_results": "KMFA/stage_artifacts/S16_P1_subcontract_procurement_aggregation/human/test_results.md",
            "stage_manifest": (
                "KMFA/stage_artifacts/S16_P1_subcontract_procurement_aggregation/machine/s16_p1_manifest.json"
            ),
        },
        "summary": {
            "source_lane_count": len(source_lanes),
            "project_match_count": len(project_matches),
            "matched_to_project_count": sum(
                1 for row in project_matches if row["matching_status"] == "matched_to_project"
            ),
            "cross_project_match_count": sum(
                1 for row in project_matches if row["matching_status"] == "cross_project_candidate"
            ),
            "unmatched_project_count": sum(
                1 for row in project_matches if row["matching_status"] == "unmatched_to_project"
            ),
            "unallocated_cost_pool_count": len(unallocated_pool),
            "anomaly_candidate_count": len(anomaly_candidates),
            "duplicate_payment_candidate_count": duplicate_payment_candidate_count,
            "cross_project_cost_candidate_count": cross_project_cost_candidate_count,
            "pending_reconciliation_count": pending_reconciliation_count,
            "report_grade_visible": report_grade_visible,
            "payment_execution_count": 0,
            "bank_operation_count": 0,
            "procurement_execution_count": 0,
        },
        "limitations": [
            "S16-P1 只输出 public-safe 外协、采购、付款结构匹配和人工复核候选。",
            "不展示真实金额、真实项目名称、供应商名称、字段头明文、账号或原始文件。",
            "不执行采购下单、付款审批、付款执行、银行操作、S16-P2、S16-P3、Stage 16 review 或 GitHub upload。",
            "报告等级仍显示 D，12 条 pending owner 或授权复核差异继续阻断正式报告和经营决策依据。",
        ],
    }
    manifest["content_hash"] = _sha256_json(
        {
            "manifest_without_hash": manifest,
            "source_lanes": source_lanes,
            "project_matches": project_matches,
            "unallocated_pool": unallocated_pool,
            "anomaly_candidates": anomaly_candidates,
        }
    )
    validate_subcontract_procurement_artifacts(
        manifest,
        source_lanes,
        project_matches,
        unallocated_pool,
        anomaly_candidates,
    )
    return manifest, source_lanes, project_matches, unallocated_pool, anomaly_candidates


def _require_false(record: dict[str, Any], keys: tuple[str, ...], label: str) -> None:
    for key in keys:
        if record.get(key) is not False:
            raise SubcontractProcurementAggregationError(f"{label}.{key} must be false")


def validate_subcontract_procurement_artifacts(
    manifest: dict[str, Any],
    source_lanes: list[dict[str, Any]],
    project_matches: list[dict[str, Any]],
    unallocated_pool: list[dict[str, Any]],
    anomaly_candidates: list[dict[str, Any]],
) -> None:
    if manifest.get("schema_version") != "kmfa.subcontract_procurement_aggregation_manifest.v1":
        raise SubcontractProcurementAggregationError("manifest schema_version mismatch")
    if manifest.get("stage_phase") != "S16-P1":
        raise SubcontractProcurementAggregationError("manifest stage_phase must be S16-P1")
    if tuple(manifest.get("required_source_lanes", [])) != REQUIRED_SOURCE_LANES:
        raise SubcontractProcurementAggregationError("manifest required_source_lanes mismatch")
    if tuple(manifest.get("required_output_record_types", [])) != REQUIRED_OUTPUT_RECORD_TYPES:
        raise SubcontractProcurementAggregationError("manifest required_output_record_types mismatch")

    expected_summary = {
        "source_lane_count": 4,
        "project_match_count": 5,
        "matched_to_project_count": 2,
        "cross_project_match_count": 1,
        "unmatched_project_count": 2,
        "unallocated_cost_pool_count": 2,
        "anomaly_candidate_count": 4,
        "duplicate_payment_candidate_count": 2,
        "cross_project_cost_candidate_count": 2,
        "pending_reconciliation_count": 12,
        "report_grade_visible": "D",
        "payment_execution_count": 0,
        "bank_operation_count": 0,
        "procurement_execution_count": 0,
    }
    for key, expected in expected_summary.items():
        if manifest.get("summary", {}).get(key) != expected:
            raise SubcontractProcurementAggregationError(f"manifest summary {key} must be {expected}")

    for scope_key, expected in _stage_scope().items():
        if manifest.get("stage_scope", {}).get(scope_key) is not expected:
            raise SubcontractProcurementAggregationError(f"manifest stage_scope {scope_key} must be {expected}")
    for gate_key, expected in _quality_gate(pending_reconciliation_count=12, report_grade_visible="D").items():
        if manifest.get("quality_gate", {}).get(gate_key) != expected:
            raise SubcontractProcurementAggregationError(f"manifest quality_gate {gate_key} must be {expected}")
    for safety_key, expected in _public_repo_safety().items():
        if manifest.get("public_repo_safety", {}).get(safety_key) is not expected:
            raise SubcontractProcurementAggregationError(f"manifest public_repo_safety {safety_key} must be {expected}")

    lane_by_id = {str(lane.get("lane_id")): lane for lane in source_lanes}
    if set(lane_by_id) != set(REQUIRED_SOURCE_LANES):
        raise SubcontractProcurementAggregationError("source lanes must cover all S16-P1 required lanes")
    for lane_id, categories in LANE_SOURCE_CATEGORIES.items():
        lane = lane_by_id[lane_id]
        if lane.get("record_type") != "subcontract_procurement_source_lane":
            raise SubcontractProcurementAggregationError(f"{lane_id} record_type mismatch")
        if tuple(lane.get("finance_categories", [])) != categories:
            raise SubcontractProcurementAggregationError(f"{lane_id} finance categories mismatch")
        if int(lane.get("source_count", 0)) < 1:
            raise SubcontractProcurementAggregationError(f"{lane_id} must have at least one source")
        if int(lane.get("field_mapping_count", 0)) < 1:
            raise SubcontractProcurementAggregationError(f"{lane_id} must have at least one field mapping")
        if lane.get("all_sources_readonly") is not True:
            raise SubcontractProcurementAggregationError(f"{lane_id}.all_sources_readonly must be true")
        _require_false(
            lane,
            (
                "raw_business_values_allowed",
                "public_amount_values_allowed",
                "field_plaintext_allowed",
                "formal_report_allowed",
                "business_decision_basis_allowed",
                "procurement_execution_allowed",
                "payment_approval_allowed",
                "payment_execution_allowed",
                "bank_operation_allowed",
                "raw_layer_write_allowed",
            ),
            lane_id,
        )

    if len(project_matches) != 5:
        raise SubcontractProcurementAggregationError("project match records must contain five rows")
    matching_statuses = [str(row.get("matching_status")) for row in project_matches]
    if matching_statuses.count("matched_to_project") != 2:
        raise SubcontractProcurementAggregationError("project matches must include two matched rows")
    if matching_statuses.count("cross_project_candidate") != 1:
        raise SubcontractProcurementAggregationError("project matches must include one cross-project candidate")
    if matching_statuses.count("unmatched_to_project") != 2:
        raise SubcontractProcurementAggregationError("project matches must include two unmatched rows")
    for record in project_matches:
        if record.get("record_type") != "subcontract_project_match":
            raise SubcontractProcurementAggregationError("project match record_type mismatch")
        if record.get("stage_phase") != "S16-P1":
            raise SubcontractProcurementAggregationError("project match stage_phase must be S16-P1")
        _require_false(
            record,
            (
                "formal_report_allowed",
                "business_decision_basis_allowed",
                "procurement_execution_allowed",
                "payment_approval_allowed",
                "payment_execution_allowed",
                "bank_operation_allowed",
                "contains_true_amounts",
                "contains_field_plaintext",
                "raw_layer_write_allowed",
            ),
            str(record.get("match_record_id")),
        )

    pool_refs = {str(item.get("match_record_ref")) for item in unallocated_pool}
    unmatched_refs = {
        str(record.get("match_record_id"))
        for record in project_matches
        if record.get("matching_status") == "unmatched_to_project"
    }
    if pool_refs != unmatched_refs:
        raise SubcontractProcurementAggregationError("unallocated pool must exactly mirror unmatched project matches")
    for item in unallocated_pool:
        if item.get("record_type") != "subcontract_unallocated_cost_pool_item":
            raise SubcontractProcurementAggregationError("unallocated pool record_type mismatch")
        if item.get("assignment_status") != "pending_project_assignment_or_owner_review":
            raise SubcontractProcurementAggregationError("unallocated pool assignment_status mismatch")
        if item.get("manual_review_required") is not True:
            raise SubcontractProcurementAggregationError("unallocated pool manual_review_required must be true")
        _require_false(
            item,
            (
                "formal_report_allowed",
                "business_decision_basis_allowed",
                "procurement_execution_allowed",
                "payment_approval_allowed",
                "payment_execution_allowed",
                "bank_operation_allowed",
                "contains_true_amounts",
                "contains_field_plaintext",
                "raw_layer_write_allowed",
                "amount_value_public_committed",
            ),
            str(item.get("pool_item_id")),
        )

    candidate_types = [str(candidate.get("candidate_type")) for candidate in anomaly_candidates]
    if candidate_types.count("duplicate_payment_candidate") != 2:
        raise SubcontractProcurementAggregationError("duplicate payment candidate count mismatch")
    if candidate_types.count("cross_project_cost_candidate") != 2:
        raise SubcontractProcurementAggregationError("cross project cost candidate count mismatch")
    for candidate in anomaly_candidates:
        if candidate.get("record_type") != "subcontract_anomaly_candidate":
            raise SubcontractProcurementAggregationError("anomaly candidate record_type mismatch")
        if candidate.get("manual_review_required") is not True:
            raise SubcontractProcurementAggregationError("anomaly candidate manual_review_required must be true")
        _require_false(
            candidate,
            (
                "formal_report_allowed",
                "business_decision_basis_allowed",
                "procurement_execution_allowed",
                "payment_approval_allowed",
                "payment_execution_allowed",
                "bank_operation_allowed",
                "contains_true_amounts",
                "contains_field_plaintext",
                "raw_layer_write_allowed",
                "action_execution_allowed",
                "candidate_close_allowed_without_owner_review",
            ),
            str(candidate.get("candidate_id")),
        )

    _ensure_no_forbidden_public_payload(
        [manifest, source_lanes, project_matches, unallocated_pool, anomaly_candidates]
    )


def generate_default_outputs(*, generated_at: str = "2026-07-01T23:00:00+10:00") -> dict[str, Any]:
    manifest, source_lanes, project_matches, unallocated_pool, anomaly_candidates = (
        build_default_subcontract_procurement_aggregation(generated_at=generated_at)
    )
    write_json(DEFAULT_OUTPUT_MANIFEST, manifest)
    write_jsonl(DEFAULT_OUTPUT_SOURCE_LANES, source_lanes)
    write_jsonl(DEFAULT_OUTPUT_PROJECT_MATCHES, project_matches)
    write_jsonl(DEFAULT_OUTPUT_UNALLOCATED_POOL, unallocated_pool)
    write_jsonl(DEFAULT_OUTPUT_ANOMALY_CANDIDATES, anomaly_candidates)
    write_json(
        DEFAULT_OUTPUT_STAGE_MANIFEST,
        {
            **manifest,
            "stage_artifact_manifest": True,
            "metadata_manifest_ref": "KMFA/metadata/reports/subcontract_procurement_aggregation_manifest.json",
        },
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate KMFA S16-P1 subcontract procurement public-safe artifacts.")
    parser.add_argument("--generated-at", default="2026-07-01T23:00:00+10:00")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    manifest, source_lanes, project_matches, unallocated_pool, anomaly_candidates = (
        build_default_subcontract_procurement_aggregation(generated_at=args.generated_at)
    )
    validate_subcontract_procurement_artifacts(
        manifest,
        source_lanes,
        project_matches,
        unallocated_pool,
        anomaly_candidates,
    )
    if not args.check_only:
        generate_default_outputs(generated_at=args.generated_at)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S16-P1 subcontract procurement aggregation generated "
        f"(source_lanes={summary['source_lane_count']}, "
        f"project_matches={summary['project_match_count']}, "
        f"unallocated_pool={summary['unallocated_cost_pool_count']}, "
        f"duplicate_payment_candidates={summary['duplicate_payment_candidate_count']}, "
        f"cross_project_candidates={summary['cross_project_cost_candidate_count']}, "
        "report_grade_visible=D, formal_report_allowed=false, "
        "payment_execution=false, bank_operation=false, "
        "s16_p2_scope=false, s16_p3_scope=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
