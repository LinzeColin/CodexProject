#!/usr/bin/env python3
"""Build KMFA S15-P1 public-safe performance fact field artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_PROJECT_COST_FACT_MANIFEST = ROOT / "metadata" / "reports" / "project_cost_fact_layer_manifest.json"
DEFAULT_PROJECT_COST_FACT_RECORDS = ROOT / "metadata" / "lineage" / "project_cost_fact_records.jsonl"
DEFAULT_MARGIN_MANIFEST = ROOT / "metadata" / "reports" / "project_margin_cash_margin_manifest.json"
DEFAULT_MARGIN_RECORDS = ROOT / "metadata" / "lineage" / "project_margin_cash_margin_records.jsonl"
DEFAULT_COLLECTION_MANIFEST = ROOT / "metadata" / "reports" / "collection_receivable_aging_manifest.json"
DEFAULT_COLLECTION_PRIORITY_ITEMS = ROOT / "metadata" / "reports" / "collection_receivable_aging_priority_items.jsonl"
DEFAULT_INVOICE_TAX_MANIFEST = ROOT / "metadata" / "reports" / "invoice_tax_plan_manifest.json"
DEFAULT_INVOICE_TAX_ISSUE_CANDIDATES = ROOT / "metadata" / "reports" / "invoice_tax_issue_candidates.jsonl"
DEFAULT_CROSS_TABLE_MANIFEST = ROOT / "metadata" / "reports" / "cross_table_review_manifest.json"
DEFAULT_CROSS_TABLE_DIFFERENCE_QUEUE = ROOT / "metadata" / "reports" / "cross_table_difference_queue.jsonl"

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "performance_fact_fields_manifest.json"
DEFAULT_OUTPUT_FIELD_DEFINITIONS = ROOT / "metadata" / "reports" / "performance_fact_field_definitions.jsonl"
DEFAULT_OUTPUT_FIELD_BINDINGS = ROOT / "metadata" / "reports" / "performance_fact_field_bindings.jsonl"
DEFAULT_OUTPUT_MANUAL_REVIEW_FIELDS = ROOT / "metadata" / "reports" / "performance_fact_manual_review_fields.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S15_P1_performance_fact_fields" / "machine" / "s15_p1_manifest.json"
)

REQUIRED_PERFORMANCE_FACT_FIELDS = (
    "invoice_amount",
    "gross_margin_rate",
    "settlement_speed",
    "collection_speed",
    "audit_variance",
    "customer_relationship_rate",
)

REQUIRED_MANUAL_REVIEW_FIELDS = (
    "settlement_speed",
    "collection_speed",
    "audit_variance",
    "customer_relationship_rate",
)

FIELD_LABELS = {
    "invoice_amount": "开票金额",
    "gross_margin_rate": "毛利率",
    "settlement_speed": "结算速度",
    "collection_speed": "回款速度",
    "audit_variance": "审计偏差",
    "customer_relationship_rate": "客情费率",
}

FIELD_FACT_KIND = {
    "invoice_amount": "amount_fact_hash_slot",
    "gross_margin_rate": "ratio_fact_hash_slot",
    "settlement_speed": "review_required_speed_slot",
    "collection_speed": "review_required_speed_slot",
    "audit_variance": "review_required_variance_slot",
    "customer_relationship_rate": "missing_source_rate_slot",
}

FIELD_STATUS = {
    "invoice_amount": "bound_to_project_cost_invoice_hash_and_invoice_plan",
    "gross_margin_rate": "bound_to_margin_rate_hash_pending_formal_report_gate",
    "settlement_speed": "source_bound_manual_review_required_missing_authoritative_settlement_window",
    "collection_speed": "source_bound_manual_review_required_missing_authoritative_collection_window",
    "audit_variance": "source_bound_manual_review_required_pending_cross_table_differences",
    "customer_relationship_rate": "missing_public_safe_source_manual_review_required",
}

FIELD_SOURCE_ARTIFACT_REFS = {
    "invoice_amount": (
        "KMFA/metadata/lineage/project_cost_fact_records.jsonl",
        "KMFA/metadata/reports/project_cost_fact_layer_manifest.json",
        "KMFA/metadata/reports/invoice_tax_plan_manifest.json",
        "KMFA/metadata/reports/invoice_tax_issue_candidates.jsonl",
    ),
    "gross_margin_rate": (
        "KMFA/metadata/lineage/project_margin_cash_margin_records.jsonl",
        "KMFA/metadata/reports/project_margin_cash_margin_manifest.json",
        "KMFA/metadata/lineage/project_cost_fact_records.jsonl",
    ),
    "settlement_speed": (
        "KMFA/metadata/reports/collection_receivable_aging_manifest.json",
        "KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl",
        "KMFA/metadata/reports/cross_table_review_manifest.json",
    ),
    "collection_speed": (
        "KMFA/metadata/reports/collection_receivable_aging_manifest.json",
        "KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl",
        "KMFA/metadata/lineage/project_cost_fact_records.jsonl",
    ),
    "audit_variance": (
        "KMFA/metadata/reports/cross_table_review_manifest.json",
        "KMFA/metadata/reports/cross_table_difference_queue.jsonl",
        "KMFA/metadata/reports/operating_report_quality_report.json",
    ),
    "customer_relationship_rate": (),
}

MANUAL_REVIEW_REASON = {
    "settlement_speed": "settlement_window_not_locked_to_authoritative_project_completion_and_invoice_cutoff",
    "collection_speed": "collection_window_not_locked_to_authoritative_collection_and_aging_cutoff",
    "audit_variance": "cross_table_amount_time_project_customer_differences_pending_owner_review",
    "customer_relationship_rate": "no_public_safe_authoritative_source_mapping_available_in_s15_p1",
}

MANUAL_REVIEW_OWNER = {
    "settlement_speed": "project_owner",
    "collection_speed": "finance_owner",
    "audit_variance": "finance_owner",
    "customer_relationship_rate": "sales_owner",
}

PERFORMANCE_FACT_FIELDS_VERSION = "FACT-KMFA-S15P1-PERFORMANCE-FIELDS-PUBLIC-SAFE-001"
FORMULA_VERSION = "FORM-KMFA-S15P1-PERFORMANCE-FACT-FIELD-SLOTS-001"
MAPPING_VERSION = "MAP-KMFA-S15P1-PUBLIC-SAFE-v1"

SOURCE_TASKPACK_REFS = {
    "roadmap_s15_p1": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S15-P1",
    "taskpack_req": "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md:REQ-P1-011",
}

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


class PerformanceFactFieldError(ValueError):
    """Raised when S15-P1 performance fact field artifacts are invalid."""


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PerformanceFactFieldError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise PerformanceFactFieldError(f"{path} contains a non-object JSONL record")
            records.append(value)
    return records


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True) for record in records) + "\n",
        encoding="utf-8",
    )


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _sha256_for(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


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
        "payroll_or_salary_data_committed": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s15_p1_performance_fact_fields_scope_included": True,
        "s15_p2_review_list_scope_included": False,
        "s15_p3_salary_boundary_scope_included": False,
        "stage15_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "external_connector_scope_included": False,
        "salary_system_scope_included": False,
        "payroll_export_scope_included": False,
        "bonus_approval_scope_included": False,
        "payment_execution_scope_included": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "performance_fact_field_binding_allowed": True,
        "manual_review_marker_allowed": True,
        "performance_fact_table_output_allowed": False,
        "abnormal_project_review_list_allowed": False,
        "salary_calculation_allowed": False,
        "wage_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "payment_execution_allowed": False,
        "business_decision_basis_allowed": False,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "raw_layer_write_allowed": False,
        "public_numeric_value_display_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "stage15_review_allowed": False,
        "s15_p2_allowed": False,
        "s15_p3_allowed": False,
        "report_grade_visible": "D",
        "release_block_reason": "performance_fact_fields_only_pending_s15_p2_review_list_s15_p3_salary_boundary_stage_review_and_upload",
    }


def _require_upstream(
    *,
    fact_manifest: dict[str, Any],
    fact_records: list[dict[str, Any]],
    margin_manifest: dict[str, Any],
    margin_records: list[dict[str, Any]],
    collection_manifest: dict[str, Any],
    collection_priority_items: list[dict[str, Any]],
    invoice_tax_manifest: dict[str, Any],
    invoice_tax_issue_candidates: list[dict[str, Any]],
    cross_table_manifest: dict[str, Any],
    cross_table_difference_queue: list[dict[str, Any]],
) -> None:
    if fact_manifest.get("stage_phase") != "S09-P1":
        raise PerformanceFactFieldError("S15-P1 requires S09-P1 project cost fact layer")
    if len(fact_records) < 1:
        raise PerformanceFactFieldError("S15-P1 requires project cost fact records")
    if margin_manifest.get("stage_phase") != "S09-P2":
        raise PerformanceFactFieldError("S15-P1 requires S09-P2 margin/cash margin layer")
    if len(margin_records) < 1:
        raise PerformanceFactFieldError("S15-P1 requires margin records")
    if collection_manifest.get("stage_phase") != "S13-P2":
        raise PerformanceFactFieldError("S15-P1 requires S13-P2 collection receivable aging")
    if len(collection_priority_items) < 1:
        raise PerformanceFactFieldError("S15-P1 requires collection priority items")
    if invoice_tax_manifest.get("stage_phase") != "S14-P2":
        raise PerformanceFactFieldError("S15-P1 requires S14-P2 invoice tax plan")
    if len(invoice_tax_issue_candidates) < 1:
        raise PerformanceFactFieldError("S15-P1 requires invoice tax issue candidates")
    if cross_table_manifest.get("stage_phase") != "S13-P3":
        raise PerformanceFactFieldError("S15-P1 requires S13-P3 cross table review")
    if len(cross_table_difference_queue) < 1:
        raise PerformanceFactFieldError("S15-P1 requires cross table difference queue")


def _hash_refs_from_fact_records(fact_records: list[dict[str, Any]], metric_key: str) -> list[str]:
    refs: list[str] = []
    for record in fact_records:
        value = record.get("metric_hash_refs", {}).get(metric_key)
        if isinstance(value, str) and value.startswith("sha256:"):
            refs.append(value)
    if not refs:
        raise PerformanceFactFieldError(f"missing project cost fact metric hash refs for {metric_key}")
    return refs


def _hash_refs_from_margin_records(margin_records: list[dict[str, Any]], group_key: str, metric_key: str) -> list[str]:
    refs: list[str] = []
    for record in margin_records:
        value = record.get(group_key, {}).get(metric_key)
        if isinstance(value, str) and value.startswith("sha256:"):
            refs.append(value)
    if not refs:
        raise PerformanceFactFieldError(f"missing margin hash refs for {group_key}.{metric_key}")
    return refs


def _manual_review_ref(field_key: str) -> str | None:
    if field_key not in REQUIRED_MANUAL_REVIEW_FIELDS:
        return None
    return f"KMFA/metadata/reports/performance_fact_manual_review_fields.jsonl#{field_key}"


def _field_definition(field_key: str, *, generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.performance_fact_field_definition.v1",
        "record_type": "performance_fact_field_definition",
        "project_id": "KMFA",
        "stage_phase": "S15-P1",
        "field_key": field_key,
        "visible_field_label": FIELD_LABELS[field_key],
        "fact_kind": FIELD_FACT_KIND[field_key],
        "generated_at": generated_at,
        "value_policy": "public_safe_refs_hashes_and_status_only",
        "public_numeric_values_allowed": False,
        "raw_business_values_allowed": False,
        "field_plaintext_allowed": False,
        "salary_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "manual_review_required": field_key in REQUIRED_MANUAL_REVIEW_FIELDS,
        "manual_review_ref": _manual_review_ref(field_key),
    }


def _binding_evidence_hashes(
    *,
    field_key: str,
    fact_records: list[dict[str, Any]],
    margin_records: list[dict[str, Any]],
    collection_manifest: dict[str, Any],
    collection_priority_items: list[dict[str, Any]],
    invoice_tax_manifest: dict[str, Any],
    invoice_tax_issue_candidates: list[dict[str, Any]],
    cross_table_manifest: dict[str, Any],
    cross_table_difference_queue: list[dict[str, Any]],
) -> dict[str, Any]:
    if field_key == "invoice_amount":
        return {
            "project_cost_invoice_hash_refs": _hash_refs_from_fact_records(fact_records, "invoice_amount"),
            "invoice_tax_manifest_hash": invoice_tax_manifest.get("content_hash"),
            "invoice_tax_candidate_count_hash": _sha256_for(
                f"S15-P1:invoice-tax-candidates:{len(invoice_tax_issue_candidates)}"
            ),
        }
    if field_key == "gross_margin_rate":
        return {
            "authority_gross_margin_rate_hash_refs": _hash_refs_from_margin_records(
                margin_records, "authority_value_hash_refs", "gross_margin_rate"
            ),
            "system_gross_margin_rate_hash_refs": _hash_refs_from_margin_records(
                margin_records, "system_recomputed_value_hash_refs", "gross_margin_rate"
            ),
        }
    if field_key == "settlement_speed":
        source_issue_types = [
            str(item.get("issue_type"))
            for item in collection_priority_items
            if item.get("issue_type") in {"completed_not_settled", "settled_not_invoiced"}
        ]
        return {
            "settlement_issue_type_count_hash": _sha256_for(
                "S15-P1:settlement-speed:" + ",".join(sorted(source_issue_types))
            ),
            "collection_manifest_hash": collection_manifest.get("content_hash"),
        }
    if field_key == "collection_speed":
        source_issue_types = [
            str(item.get("issue_type"))
            for item in collection_priority_items
            if item.get("issue_type") in {"invoiced_not_collected", "overdue_receivable"}
        ]
        return {
            "collection_issue_type_count_hash": _sha256_for(
                "S15-P1:collection-speed:" + ",".join(sorted(source_issue_types))
            ),
            "collection_amount_hash_refs": _hash_refs_from_fact_records(fact_records, "collection_amount"),
        }
    if field_key == "audit_variance":
        difference_ids = [str(item.get("queue_item_id")) for item in cross_table_difference_queue]
        return {
            "cross_table_manifest_hash": cross_table_manifest.get("content_hash"),
            "difference_queue_count_hash": _sha256_for("S15-P1:audit-variance:" + ",".join(sorted(difference_ids))),
        }
    if field_key == "customer_relationship_rate":
        return {
            "missing_source_hash": _sha256_for("S15-P1:customer-relationship-rate:missing-public-safe-source")
        }
    raise PerformanceFactFieldError(f"unknown field_key: {field_key}")


def _field_binding(
    *,
    field_key: str,
    generated_at: str,
    fact_records: list[dict[str, Any]],
    margin_records: list[dict[str, Any]],
    collection_manifest: dict[str, Any],
    collection_priority_items: list[dict[str, Any]],
    invoice_tax_manifest: dict[str, Any],
    invoice_tax_issue_candidates: list[dict[str, Any]],
    cross_table_manifest: dict[str, Any],
    cross_table_difference_queue: list[dict[str, Any]],
) -> dict[str, Any]:
    binding_index = REQUIRED_PERFORMANCE_FACT_FIELDS.index(field_key) + 1
    manual_review_required = field_key in REQUIRED_MANUAL_REVIEW_FIELDS
    return {
        "schema_version": "kmfa.performance_fact_field_binding.v1",
        "record_type": "performance_fact_field_binding",
        "project_id": "KMFA",
        "stage_phase": "S15-P1",
        "binding_id": f"S15P1-FIELD-{binding_index:03d}",
        "field_key": field_key,
        "visible_field_label": FIELD_LABELS[field_key],
        "generated_at": generated_at,
        "field_status": FIELD_STATUS[field_key],
        "source_artifact_refs": list(FIELD_SOURCE_ARTIFACT_REFS[field_key]),
        "evidence_hash_refs": _binding_evidence_hashes(
            field_key=field_key,
            fact_records=fact_records,
            margin_records=margin_records,
            collection_manifest=collection_manifest,
            collection_priority_items=collection_priority_items,
            invoice_tax_manifest=invoice_tax_manifest,
            invoice_tax_issue_candidates=invoice_tax_issue_candidates,
            cross_table_manifest=cross_table_manifest,
            cross_table_difference_queue=cross_table_difference_queue,
        ),
        "project_cost_fact_binding": {
            "required": True,
            "artifact_ref": "KMFA/metadata/lineage/project_cost_fact_records.jsonl",
            "record_count": len(fact_records),
            "metric_slots_used": ["invoice_amount", "collection_amount", "cost_total", "revenue"],
        },
        "collection_fact_binding": {
            "required": True,
            "artifact_ref": "KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl",
            "priority_item_count": len(collection_priority_items),
            "source_issue_types": sorted({str(item.get("issue_type")) for item in collection_priority_items}),
        },
        "manual_review_required": manual_review_required,
        "manual_review_ref": _manual_review_ref(field_key),
        "raw_business_values_allowed": False,
        "public_numeric_values_allowed": False,
        "field_plaintext_allowed": False,
        "auto_fill_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "salary_calculation_allowed": False,
        "wage_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "payment_execution_allowed": False,
    }


def _manual_review_field(field_key: str, *, generated_at: str) -> dict[str, Any]:
    review_index = REQUIRED_MANUAL_REVIEW_FIELDS.index(field_key) + 1
    return {
        "schema_version": "kmfa.performance_fact_manual_review_field.v1",
        "record_type": "performance_fact_manual_review_field",
        "project_id": "KMFA",
        "stage_phase": "S15-P1",
        "review_field_id": f"S15P1-MRF-{review_index:03d}",
        "field_key": field_key,
        "visible_field_label": FIELD_LABELS[field_key],
        "generated_at": generated_at,
        "manual_review_required": True,
        "reason_code": MANUAL_REVIEW_REASON[field_key],
        "responsible_role": MANUAL_REVIEW_OWNER[field_key],
        "review_mode": "owner_or_authorized_delegate_review_only",
        "required_review_action": "provide_authoritative_public_safe_mapping_or_keep_blocked",
        "source_artifact_refs": list(FIELD_SOURCE_ARTIFACT_REFS[field_key]),
        "auto_fill_allowed": False,
        "auto_calculation_allowed": False,
        "auto_approval_allowed": False,
        "salary_or_bonus_action_allowed": False,
        "s15_p2_review_list_created": False,
        "raw_business_values_allowed": False,
        "public_numeric_values_allowed": False,
        "field_plaintext_allowed": False,
    }


def build_default_performance_fact_field_artifacts(
    *,
    generated_at: str = "2026-07-01T23:30:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    fact_manifest = read_json(DEFAULT_PROJECT_COST_FACT_MANIFEST)
    fact_records = read_jsonl(DEFAULT_PROJECT_COST_FACT_RECORDS)
    margin_manifest = read_json(DEFAULT_MARGIN_MANIFEST)
    margin_records = read_jsonl(DEFAULT_MARGIN_RECORDS)
    collection_manifest = read_json(DEFAULT_COLLECTION_MANIFEST)
    collection_priority_items = read_jsonl(DEFAULT_COLLECTION_PRIORITY_ITEMS)
    invoice_tax_manifest = read_json(DEFAULT_INVOICE_TAX_MANIFEST)
    invoice_tax_issue_candidates = read_jsonl(DEFAULT_INVOICE_TAX_ISSUE_CANDIDATES)
    cross_table_manifest = read_json(DEFAULT_CROSS_TABLE_MANIFEST)
    cross_table_difference_queue = read_jsonl(DEFAULT_CROSS_TABLE_DIFFERENCE_QUEUE)

    _require_upstream(
        fact_manifest=fact_manifest,
        fact_records=fact_records,
        margin_manifest=margin_manifest,
        margin_records=margin_records,
        collection_manifest=collection_manifest,
        collection_priority_items=collection_priority_items,
        invoice_tax_manifest=invoice_tax_manifest,
        invoice_tax_issue_candidates=invoice_tax_issue_candidates,
        cross_table_manifest=cross_table_manifest,
        cross_table_difference_queue=cross_table_difference_queue,
    )

    field_definitions = [_field_definition(field_key, generated_at=generated_at) for field_key in REQUIRED_PERFORMANCE_FACT_FIELDS]
    field_bindings = [
        _field_binding(
            field_key=field_key,
            generated_at=generated_at,
            fact_records=fact_records,
            margin_records=margin_records,
            collection_manifest=collection_manifest,
            collection_priority_items=collection_priority_items,
            invoice_tax_manifest=invoice_tax_manifest,
            invoice_tax_issue_candidates=invoice_tax_issue_candidates,
            cross_table_manifest=cross_table_manifest,
            cross_table_difference_queue=cross_table_difference_queue,
        )
        for field_key in REQUIRED_PERFORMANCE_FACT_FIELDS
    ]
    manual_review_fields = [
        _manual_review_field(field_key, generated_at=generated_at) for field_key in REQUIRED_MANUAL_REVIEW_FIELDS
    ]

    manifest = {
        "schema_version": "kmfa.performance_fact_fields_manifest.v1",
        "record_type": "performance_fact_fields_manifest",
        "project_id": "KMFA",
        "stage_phase": "S15-P1",
        "generated_at": generated_at,
        "fact_fields_version": PERFORMANCE_FACT_FIELDS_VERSION,
        "formula_version": FORMULA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "runtime_status": "public_safe_performance_fact_field_bindings_created_review_required_fields_marked",
        "required_performance_fact_fields": list(REQUIRED_PERFORMANCE_FACT_FIELDS),
        "required_manual_review_fields": list(REQUIRED_MANUAL_REVIEW_FIELDS),
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "upstream_metadata_refs": {
            "project_cost_fact_manifest": "KMFA/metadata/reports/project_cost_fact_layer_manifest.json",
            "project_cost_fact_records": "KMFA/metadata/lineage/project_cost_fact_records.jsonl",
            "project_margin_cash_margin_manifest": "KMFA/metadata/reports/project_margin_cash_margin_manifest.json",
            "project_margin_cash_margin_records": "KMFA/metadata/lineage/project_margin_cash_margin_records.jsonl",
            "collection_receivable_aging_manifest": "KMFA/metadata/reports/collection_receivable_aging_manifest.json",
            "collection_receivable_aging_priority_items": (
                "KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl"
            ),
            "invoice_tax_plan_manifest": "KMFA/metadata/reports/invoice_tax_plan_manifest.json",
            "invoice_tax_issue_candidates": "KMFA/metadata/reports/invoice_tax_issue_candidates.jsonl",
            "cross_table_review_manifest": "KMFA/metadata/reports/cross_table_review_manifest.json",
            "cross_table_difference_queue": "KMFA/metadata/reports/cross_table_difference_queue.jsonl",
        },
        "quality_gate": _quality_gate(),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "artifact_refs": {
            "performance_fact_fields_manifest": "KMFA/metadata/reports/performance_fact_fields_manifest.json",
            "performance_fact_field_definitions": "KMFA/metadata/reports/performance_fact_field_definitions.jsonl",
            "performance_fact_field_bindings": "KMFA/metadata/reports/performance_fact_field_bindings.jsonl",
            "performance_fact_manual_review_fields": (
                "KMFA/metadata/reports/performance_fact_manual_review_fields.jsonl"
            ),
            "validator": "KMFA/tools/check_s15_p1_performance_fact_fields.py",
            "completion_record": (
                "KMFA/stage_artifacts/S15_P1_performance_fact_fields/human/s15_p1_completion_record.md"
            ),
            "test_results": "KMFA/stage_artifacts/S15_P1_performance_fact_fields/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S15_P1_performance_fact_fields/machine/s15_p1_manifest.json",
        },
        "summary": {
            "field_definition_count": len(field_definitions),
            "field_binding_count": len(field_bindings),
            "manual_review_field_count": len(manual_review_fields),
            "project_cost_fact_record_count": len(fact_records),
            "margin_record_count": len(margin_records),
            "collection_priority_item_count": len(collection_priority_items),
            "invoice_issue_candidate_count": len(invoice_tax_issue_candidates),
            "cross_table_difference_count": len(cross_table_difference_queue),
            "performance_fact_table_count": 0,
            "abnormal_project_review_list_count": 0,
            "salary_calculation_count": 0,
            "bonus_approval_count": 0,
            "payroll_export_count": 0,
            "report_grade_visible": "D",
        },
        "limitations": [
            "S15-P1 只锁定绩效事实字段定义、source binding 和缺失/未锁定字段人工复核标记。",
            "本 phase 不输出绩效事实表、不输出异常项目复核清单、不计算工资或奖金。",
            "所有字段值只保留 public-safe hash/ref/status，不提交真实金额、比例、日期、人员或客户项目明文。",
        ],
    }
    manifest["content_hash"] = _sha256_json(
        {
            "manifest": manifest,
            "field_definitions": field_definitions,
            "field_bindings": field_bindings,
            "manual_review_fields": manual_review_fields,
        }
    )
    validate_performance_fact_field_artifacts(manifest, field_definitions, field_bindings, manual_review_fields)
    return manifest, field_definitions, field_bindings, manual_review_fields


def _walk_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                hits.append(f"{path}.{key}")
            hits.extend(_walk_forbidden_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(_walk_forbidden_keys(child, f"{path}[{index}]"))
    return hits


def _walk_forbidden_text(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            hits.extend(_walk_forbidden_text(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(_walk_forbidden_text(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        text = value.lower()
        for forbidden in FORBIDDEN_PUBLIC_TEXT:
            if forbidden in text:
                hits.append(f"{path}:{forbidden}")
        for forbidden_suffix in FORBIDDEN_PUBLIC_SUFFIXES:
            if text.endswith(forbidden_suffix):
                hits.append(f"{path}:{forbidden_suffix}")
    return hits


def _expect_bool_map(container: dict[str, Any], expected: dict[str, Any], path: str) -> None:
    for key, expected_value in expected.items():
        if container.get(key) != expected_value:
            raise PerformanceFactFieldError(f"{path}.{key} must be {expected_value}")


def validate_performance_fact_field_artifacts(
    manifest: dict[str, Any],
    field_definitions: list[dict[str, Any]],
    field_bindings: list[dict[str, Any]],
    manual_review_fields: list[dict[str, Any]],
) -> None:
    if manifest.get("schema_version") != "kmfa.performance_fact_fields_manifest.v1":
        raise PerformanceFactFieldError("manifest schema_version mismatch")
    if manifest.get("stage_phase") != "S15-P1":
        raise PerformanceFactFieldError("manifest stage_phase must be S15-P1")
    if tuple(manifest.get("required_performance_fact_fields", [])) != REQUIRED_PERFORMANCE_FACT_FIELDS:
        raise PerformanceFactFieldError("required performance fact fields mismatch")
    if tuple(manifest.get("required_manual_review_fields", [])) != REQUIRED_MANUAL_REVIEW_FIELDS:
        raise PerformanceFactFieldError("required manual review fields mismatch")

    expected_summary = {
        "field_definition_count": 6,
        "field_binding_count": 6,
        "manual_review_field_count": 4,
        "performance_fact_table_count": 0,
        "abnormal_project_review_list_count": 0,
        "salary_calculation_count": 0,
        "bonus_approval_count": 0,
        "payroll_export_count": 0,
        "report_grade_visible": "D",
    }
    for key, expected in expected_summary.items():
        if manifest.get("summary", {}).get(key) != expected:
            raise PerformanceFactFieldError(f"manifest summary {key} must be {expected}")
    for key in (
        "project_cost_fact_record_count",
        "margin_record_count",
        "collection_priority_item_count",
        "invoice_issue_candidate_count",
        "cross_table_difference_count",
    ):
        if int(manifest.get("summary", {}).get(key, 0)) < 1:
            raise PerformanceFactFieldError(f"manifest summary {key} must be >= 1")

    _expect_bool_map(manifest.get("stage_scope", {}), _stage_scope(), "manifest.stage_scope")
    _expect_bool_map(manifest.get("quality_gate", {}), _quality_gate(), "manifest.quality_gate")
    _expect_bool_map(manifest.get("public_repo_safety", {}), _public_repo_safety(), "manifest.public_repo_safety")

    if [item.get("field_key") for item in field_definitions] != list(REQUIRED_PERFORMANCE_FACT_FIELDS):
        raise PerformanceFactFieldError("field definition order mismatch")
    for definition in field_definitions:
        field_key = str(definition.get("field_key"))
        if definition.get("schema_version") != "kmfa.performance_fact_field_definition.v1":
            raise PerformanceFactFieldError(f"{field_key} definition schema mismatch")
        if definition.get("record_type") != "performance_fact_field_definition":
            raise PerformanceFactFieldError(f"{field_key} definition record_type mismatch")
        if definition.get("stage_phase") != "S15-P1":
            raise PerformanceFactFieldError(f"{field_key} definition stage_phase mismatch")
        if definition.get("visible_field_label") != FIELD_LABELS[field_key]:
            raise PerformanceFactFieldError(f"{field_key} visible label mismatch")
        if definition.get("manual_review_required") is not (field_key in REQUIRED_MANUAL_REVIEW_FIELDS):
            raise PerformanceFactFieldError(f"{field_key} manual_review_required mismatch")
        for false_key in (
            "public_numeric_values_allowed",
            "raw_business_values_allowed",
            "field_plaintext_allowed",
            "salary_calculation_allowed",
            "bonus_approval_allowed",
            "payroll_export_allowed",
        ):
            if definition.get(false_key) is not False:
                raise PerformanceFactFieldError(f"{field_key} definition {false_key} must be false")

    if [item.get("field_key") for item in field_bindings] != list(REQUIRED_PERFORMANCE_FACT_FIELDS):
        raise PerformanceFactFieldError("field binding order mismatch")
    for binding in field_bindings:
        field_key = str(binding.get("field_key"))
        if binding.get("schema_version") != "kmfa.performance_fact_field_binding.v1":
            raise PerformanceFactFieldError(f"{field_key} binding schema mismatch")
        if binding.get("record_type") != "performance_fact_field_binding":
            raise PerformanceFactFieldError(f"{field_key} binding record_type mismatch")
        if binding.get("stage_phase") != "S15-P1":
            raise PerformanceFactFieldError(f"{field_key} binding stage_phase mismatch")
        if binding.get("source_artifact_refs") != list(FIELD_SOURCE_ARTIFACT_REFS[field_key]):
            raise PerformanceFactFieldError(f"{field_key} source_artifact_refs mismatch")
        if binding.get("manual_review_required") is not (field_key in REQUIRED_MANUAL_REVIEW_FIELDS):
            raise PerformanceFactFieldError(f"{field_key} binding manual review flag mismatch")
        if field_key in REQUIRED_MANUAL_REVIEW_FIELDS:
            if binding.get("manual_review_ref") != _manual_review_ref(field_key):
                raise PerformanceFactFieldError(f"{field_key} manual_review_ref mismatch")
        else:
            if binding.get("manual_review_ref") is not None:
                raise PerformanceFactFieldError(f"{field_key} manual_review_ref must be null")
        if binding.get("project_cost_fact_binding", {}).get("artifact_ref") != (
            "KMFA/metadata/lineage/project_cost_fact_records.jsonl"
        ):
            raise PerformanceFactFieldError(f"{field_key} project cost fact binding missing")
        if binding.get("collection_fact_binding", {}).get("artifact_ref") != (
            "KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl"
        ):
            raise PerformanceFactFieldError(f"{field_key} collection fact binding missing")
        for false_key in (
            "raw_business_values_allowed",
            "public_numeric_values_allowed",
            "field_plaintext_allowed",
            "auto_fill_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "salary_calculation_allowed",
            "wage_calculation_allowed",
            "bonus_approval_allowed",
            "payroll_export_allowed",
            "payment_execution_allowed",
        ):
            if binding.get(false_key) is not False:
                raise PerformanceFactFieldError(f"{field_key} binding {false_key} must be false")

    if [item.get("field_key") for item in manual_review_fields] != list(REQUIRED_MANUAL_REVIEW_FIELDS):
        raise PerformanceFactFieldError("manual review field order mismatch")
    for item in manual_review_fields:
        field_key = str(item.get("field_key"))
        if item.get("schema_version") != "kmfa.performance_fact_manual_review_field.v1":
            raise PerformanceFactFieldError(f"{field_key} manual review schema mismatch")
        if item.get("record_type") != "performance_fact_manual_review_field":
            raise PerformanceFactFieldError(f"{field_key} manual review record_type mismatch")
        if item.get("manual_review_required") is not True:
            raise PerformanceFactFieldError(f"{field_key} manual_review_required must be true")
        if item.get("reason_code") != MANUAL_REVIEW_REASON[field_key]:
            raise PerformanceFactFieldError(f"{field_key} manual review reason mismatch")
        if item.get("review_mode") != "owner_or_authorized_delegate_review_only":
            raise PerformanceFactFieldError(f"{field_key} review mode mismatch")
        for false_key in (
            "auto_fill_allowed",
            "auto_calculation_allowed",
            "auto_approval_allowed",
            "salary_or_bonus_action_allowed",
            "s15_p2_review_list_created",
            "raw_business_values_allowed",
            "public_numeric_values_allowed",
            "field_plaintext_allowed",
        ):
            if item.get(false_key) is not False:
                raise PerformanceFactFieldError(f"{field_key} manual review {false_key} must be false")

    public_payload = [manifest, field_definitions, field_bindings, manual_review_fields]
    forbidden_key_hits = _walk_forbidden_keys(public_payload)
    if forbidden_key_hits:
        raise PerformanceFactFieldError("forbidden public keys found: " + ", ".join(forbidden_key_hits))
    forbidden_text_hits = _walk_forbidden_text(public_payload)
    if forbidden_text_hits:
        raise PerformanceFactFieldError("forbidden public text found: " + ", ".join(forbidden_text_hits))


def write_default_performance_fact_field_artifacts(
    *,
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    output_field_definitions: Path = DEFAULT_OUTPUT_FIELD_DEFINITIONS,
    output_field_bindings: Path = DEFAULT_OUTPUT_FIELD_BINDINGS,
    output_manual_review_fields: Path = DEFAULT_OUTPUT_MANUAL_REVIEW_FIELDS,
    output_stage_manifest: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    generated_at: str = "2026-07-01T23:30:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    manifest, field_definitions, field_bindings, manual_review_fields = build_default_performance_fact_field_artifacts(
        generated_at=generated_at
    )
    write_json(output_manifest, manifest)
    write_jsonl(output_field_definitions, field_definitions)
    write_jsonl(output_field_bindings, field_bindings)
    write_jsonl(output_manual_review_fields, manual_review_fields)
    stage_manifest = {
        "schema_version": "kmfa.s15_p1_stage_manifest.v1",
        "record_type": "s15_p1_performance_fact_fields_stage_manifest",
        "project_id": "KMFA",
        "stage_phase": "S15-P1",
        "generated_at": generated_at,
        "status": "completed_validated_local_only",
        "content_hash": manifest["content_hash"],
        "artifact_refs": manifest["artifact_refs"],
        "summary": manifest["summary"],
        "quality_gate": manifest["quality_gate"],
        "stage_scope": manifest["stage_scope"],
        "public_repo_safety": manifest["public_repo_safety"],
    }
    write_json(output_stage_manifest, stage_manifest)
    return manifest, field_definitions, field_bindings, manual_review_fields


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S15-P1 performance fact field artifacts.")
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-field-definitions", type=Path, default=DEFAULT_OUTPUT_FIELD_DEFINITIONS)
    parser.add_argument("--output-field-bindings", type=Path, default=DEFAULT_OUTPUT_FIELD_BINDINGS)
    parser.add_argument("--output-manual-review-fields", type=Path, default=DEFAULT_OUTPUT_MANUAL_REVIEW_FIELDS)
    parser.add_argument("--output-stage-manifest", type=Path, default=DEFAULT_OUTPUT_STAGE_MANIFEST)
    parser.add_argument("--generated-at", default="2026-07-01T23:30:00+10:00")
    args = parser.parse_args(argv)

    manifest, field_definitions, field_bindings, manual_review_fields = write_default_performance_fact_field_artifacts(
        output_manifest=args.output_manifest,
        output_field_definitions=args.output_field_definitions,
        output_field_bindings=args.output_field_bindings,
        output_manual_review_fields=args.output_manual_review_fields,
        output_stage_manifest=args.output_stage_manifest,
        generated_at=args.generated_at,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S15-P1 performance fact field artifacts generated "
        f"(fields={len(field_definitions)}, bindings={len(field_bindings)}, "
        f"manual_reviews={len(manual_review_fields)}, "
        f"project_cost_records={summary['project_cost_fact_record_count']}, "
        f"collection_items={summary['collection_priority_item_count']}, "
        "performance_fact_table=false, salary_calculation=false, "
        "bonus_approval=false, s15_p2_scope=false, stage15_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
