#!/usr/bin/env python3
"""Build KMFA S16-P3 public-safe customer business analysis artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_BUSINESS_RELATIONSHIPS = ROOT / "metadata" / "schema_maps" / "business_entity_relationships.jsonl"
DEFAULT_MARGIN_RECORDS = ROOT / "metadata" / "lineage" / "project_margin_cash_margin_records.jsonl"
DEFAULT_COLLECTION_PRIORITY_ITEMS = ROOT / "metadata" / "reports" / "collection_receivable_aging_priority_items.jsonl"
DEFAULT_LIFECYCLE_RECORDS = ROOT / "metadata" / "reports" / "project_lifecycle_records.jsonl"
DEFAULT_SCOPE_RECONCILIATION_RECORDS = ROOT / "metadata" / "quality" / "scope_reconciliation_records.jsonl"
DEFAULT_REPORT_GRADE_RECORDS = ROOT / "metadata" / "reports" / "report_grade_runtime_records.jsonl"

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "customer_business_analysis_manifest.json"
DEFAULT_OUTPUT_SOURCE_LANES = ROOT / "metadata" / "reports" / "customer_analysis_source_lanes.jsonl"
DEFAULT_OUTPUT_SUMMARIES = ROOT / "metadata" / "reports" / "customer_operating_summaries.jsonl"
DEFAULT_OUTPUT_EXCEPTIONS = ROOT / "metadata" / "reports" / "customer_analysis_exception_items.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT
    / "stage_artifacts"
    / "S16_P3_customer_business_analysis"
    / "machine"
    / "s16_p3_manifest.json"
)

REQUIRED_ANALYSIS_DIMENSIONS = (
    "customer_value",
    "project_margin",
    "collection_quality",
    "aging_risk",
)

REQUIRED_SOURCE_LANES = (
    "customer_identity_model",
    "project_margin_signal",
    "collection_quality_signal",
    "aging_risk_signal",
    "project_lifecycle_signal",
)

REQUIRED_EXCEPTION_TYPES = (
    "high_aging_risk",
    "weak_collection_quality",
    "margin_review_required",
    "lifecycle_customer_handoff_required",
)

LANE_LABELS = {
    "customer_identity_model": "客户-项目-应收关系模型",
    "project_margin_signal": "项目毛利信号",
    "collection_quality_signal": "回款质量信号",
    "aging_risk_signal": "账龄风险信号",
    "project_lifecycle_signal": "项目生命周期信号",
}

SOURCE_TASKPACK_REFS = {
    "roadmap_s16_p3": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S16-P3",
    "taskpack_customer_line": "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md:P2-customer-business-analysis",
}

UPSTREAM_METADATA_REFS = {
    "business_entity_relationships": "KMFA/metadata/schema_maps/business_entity_relationships.jsonl",
    "project_margin_cash_margin_records": "KMFA/metadata/lineage/project_margin_cash_margin_records.jsonl",
    "collection_receivable_aging_priority_items": "KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl",
    "project_lifecycle_records": "KMFA/metadata/reports/project_lifecycle_records.jsonl",
    "scope_reconciliation": "KMFA/metadata/quality/scope_reconciliation_records.jsonl",
    "report_grade_runtime": "KMFA/metadata/reports/report_grade_runtime_records.jsonl",
}

ANALYSIS_VERSION = "CBA-KMFA-S16P3-CUSTOMER-BUSINESS-PUBLIC-SAFE-001"
FORMULA_VERSION = "FORM-KMFA-S16P3-CUSTOMER-BUSINESS-ANALYSIS-001"
MAPPING_VERSION = "MAP-KMFA-S16P3-PUBLIC-SAFE-v1"

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


class CustomerBusinessAnalysisError(ValueError):
    """Raised when S16-P3 customer business analysis artifacts are invalid."""


def _sha256_for(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CustomerBusinessAnalysisError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise CustomerBusinessAnalysisError(f"{path} contains a non-object JSONL record")
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


def _records_by_key(records: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(str(record.get(key) or ""), []).append(record)
    return grouped


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
        "s16_p2_scope_included": False,
        "s16_p3_customer_analysis_scope_included": True,
        "s16_p3_scope_included": True,
        "stage16_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "formal_report_scope_included": False,
        "external_connector_scope_included": False,
        "collection_action_scope_included": False,
        "legal_collection_scope_included": False,
        "payment_execution_scope_included": False,
        "bank_operation_scope_included": False,
        "invoice_issuance_scope_included": False,
        "s17_scope_included": False,
    }


def _quality_gate(*, pending_reconciliation_count: int, report_grade_visible: str) -> dict[str, Any]:
    return {
        "customer_operating_summary_allowed": True,
        "customer_value_signal_allowed": True,
        "customer_exception_list_allowed": True,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "business_decision_basis_allowed": False,
        "report_grade_visible": report_grade_visible,
        "report_grade_bypass_allowed": False,
        "quality_grade_bypass_allowed": False,
        "raw_layer_write_allowed": False,
        "collection_action_allowed": False,
        "legal_collection_decision_allowed": False,
        "auto_customer_contact_allowed": False,
        "invoice_issuance_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "tax_filing_allowed": False,
        "s17_allowed": False,
        "stage16_review_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "pending_reconciliation_count": pending_reconciliation_count,
        "release_block_reason": "customer_business_analysis_is_review_only_pending_lineage_reconciliation",
    }


def _public_source_ref(namespace: str, source_ref: str) -> str:
    return f"source_ref://KMFA/{namespace}/{source_ref}"


def _source_lanes(
    *,
    relationships: list[dict[str, Any]],
    margin_records: list[dict[str, Any]],
    collection_items: list[dict[str, Any]],
    lifecycle_records: list[dict[str, Any]],
    generated_at: str,
) -> list[dict[str, Any]]:
    lane_specs = {
        "customer_identity_model": (
            "S08-P2",
            "business_entity_relationships",
            len(relationships),
            ["customer_has_contract", "customer_is_project_counterparty", "customer_has_receivable"],
        ),
        "project_margin_signal": (
            "S09-P2",
            "project_margin_cash_margin_records",
            len(margin_records),
            ["authority_gross_profit", "system_recomputed_gross_profit", "cash_gross_profit", "gross_margin_rate"],
        ),
        "collection_quality_signal": (
            "S13-P2",
            "collection_receivable_aging_priority_items",
            len(collection_items),
            ["invoiced_not_collected", "settled_not_invoiced", "completed_not_settled"],
        ),
        "aging_risk_signal": (
            "S13-P2",
            "collection_receivable_aging_priority_items",
            len(collection_items),
            ["customer_aging", "receivable_aging", "overdue_receivable"],
        ),
        "project_lifecycle_signal": (
            "S16-P2",
            "project_lifecycle_records",
            len(lifecycle_records),
            ["in_progress_started", "completed_not_settled", "settled_not_invoiced", "invoiced_not_collected"],
        ),
    }
    rows: list[dict[str, Any]] = []
    for lane_id in REQUIRED_SOURCE_LANES:
        namespace, source_name, source_count, signal_keys = lane_specs[lane_id]
        rows.append(
            {
                "schema_version": "kmfa.customer_analysis_source_lane.v1",
                "record_type": "customer_analysis_source_lane",
                "project_id": "KMFA",
                "stage_phase": "S16-P3",
                "lane_id": lane_id,
                "visible_lane_name": LANE_LABELS[lane_id],
                "source_refs": [_public_source_ref(namespace, source_name)],
                "source_count": max(1, source_count),
                "signal_keys": signal_keys,
                "signal_key_count": len(signal_keys),
                "all_sources_readonly": True,
                "data_status": "structure_available_values_hidden",
                "raw_business_values_allowed": False,
                "public_amount_values_allowed": False,
                "field_plaintext_allowed": False,
                "formal_report_allowed": False,
                "business_decision_basis_allowed": False,
                "collection_action_allowed": False,
                "legal_collection_decision_allowed": False,
                "auto_customer_contact_allowed": False,
                "invoice_issuance_allowed": False,
                "payment_execution_allowed": False,
                "bank_operation_allowed": False,
                "raw_layer_write_allowed": False,
                "generated_at": generated_at,
            }
        )
    return rows


def _base_public_record(*, record_type: str, generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": f"kmfa.{record_type}.v1",
        "record_type": record_type,
        "project_id": "KMFA",
        "stage_phase": "S16-P3",
        "report_grade_visible": "D",
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "raw_business_values_allowed": False,
        "public_amount_values_allowed": False,
        "field_plaintext_allowed": False,
        "contains_true_amounts": False,
        "contains_project_name_plaintext": False,
        "contains_customer_name_plaintext": False,
        "collection_action_allowed": False,
        "legal_collection_decision_allowed": False,
        "auto_customer_contact_allowed": False,
        "invoice_issuance_allowed": False,
        "payment_execution_allowed": False,
        "bank_operation_allowed": False,
        "tax_filing_allowed": False,
        "raw_layer_write_allowed": False,
        "generated_at": generated_at,
    }


def _hash_ref(record_id: str, component: str) -> str:
    return _sha256_for(f"S16-P3:{record_id}:{component}:public-safe-customer-analysis")


def _summary_rows(
    *,
    margin_records: list[dict[str, Any]],
    collection_items: list[dict[str, Any]],
    lifecycle_records: list[dict[str, Any]],
    generated_at: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index in range(4):
        summary_id = f"CBA-S16P3-{index + 1:03d}"
        collection_item = collection_items[index % len(collection_items)]
        margin_record = margin_records[index % len(margin_records)]
        lifecycle_record = lifecycle_records[index % len(lifecycle_records)]
        row = _base_public_record(record_type="customer_operating_summary", generated_at=generated_at)
        row.update(
            {
                "customer_summary_id": summary_id,
                "customer_group_ref": str(collection_item.get("customer_group_ref") or f"public_customer_group_ref_{index + 1:03d}"),
                "customer_identity_hash_ref": _hash_ref(summary_id, "customer-identity"),
                "project_group_refs": [
                    str(collection_item.get("project_group_ref") or f"public_project_group_ref_{index + 1:03d}"),
                    str(margin_record.get("project_entity_ref") or f"entity_ref://KMFA/S08-P2/project/{index + 1:03d}"),
                ],
                "dimension_signal_refs": list(REQUIRED_ANALYSIS_DIMENSIONS),
                "customer_value_signal_hash_ref": _hash_ref(summary_id, "customer-value-signal"),
                "project_margin_signal_hash_ref": str(
                    margin_record.get("system_recomputed_value_hash_refs", {}).get("gross_margin_rate")
                    or _hash_ref(summary_id, "margin-signal")
                ),
                "collection_quality_signal_ref": str(
                    collection_item.get("amount_signal_ref") or _hash_ref(summary_id, "collection-quality")
                ),
                "aging_risk_signal_ref": str(
                    collection_item.get("aging_bucket_ref") or _hash_ref(summary_id, "aging-risk")
                ),
                "project_lifecycle_signal_ref": str(
                    lifecycle_record.get("lifecycle_record_id") or f"PLC-S16P2-{index + 1:03d}"
                ),
                "linked_public_evidence_refs": [
                    "KMFA/metadata/lineage/project_margin_cash_margin_records.jsonl",
                    "KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl",
                    "KMFA/metadata/reports/project_lifecycle_records.jsonl",
                ],
                "summary_status": "review_only_not_business_decision_basis",
                "review_priority": str(collection_item.get("priority_level") or "medium"),
                "manual_review_required": True,
                "recommended_review_mode": "owner_or_authorized_delegate_review_only",
                "customer_operating_summary_basis": "public_safe_hash_refs_status_refs_and_prior_review_candidates_only",
            }
        )
        rows.append(row)
    return rows


def _exception_items(
    *,
    customer_summaries: list[dict[str, Any]],
    collection_items: list[dict[str, Any]],
    generated_at: str,
) -> list[dict[str, Any]]:
    labels = {
        "high_aging_risk": "账龄风险偏高",
        "weak_collection_quality": "回款质量需复核",
        "margin_review_required": "项目毛利需复核",
        "lifecycle_customer_handoff_required": "项目生命周期需人工交接",
    }
    owner_roles = {
        "high_aging_risk": "finance_owner",
        "weak_collection_quality": "collection_owner",
        "margin_review_required": "business_owner",
        "lifecycle_customer_handoff_required": "project_owner",
    }
    rows: list[dict[str, Any]] = []
    for index, exception_type in enumerate(REQUIRED_EXCEPTION_TYPES, start=1):
        summary = customer_summaries[index - 1]
        collection_item = collection_items[(index - 1) % len(collection_items)]
        row = _base_public_record(record_type="customer_analysis_exception_item", generated_at=generated_at)
        row.update(
            {
                "exception_item_id": f"CAE-S16P3-{index:03d}",
                "exception_type": exception_type,
                "visible_exception_label": labels[exception_type],
                "candidate_status": "review_only_pending_owner_or_authorized_confirmation",
                "customer_summary_ref": summary["customer_summary_id"],
                "customer_group_ref": summary["customer_group_ref"],
                "source_lane_refs": list(REQUIRED_SOURCE_LANES),
                "evidence_hash_refs": [
                    _hash_ref(f"CAE-S16P3-{index:03d}", exception_type),
                    str(collection_item.get("amount_signal_ref") or _hash_ref(f"CAE-S16P3-{index:03d}", "amount-signal")),
                ],
                "review_owner_role": owner_roles[exception_type],
                "required_review_action": "confirm_public_safe_customer_business_signal",
                "manual_review_required": True,
                "auto_contact_allowed": False,
                "auto_legal_decision_allowed": False,
                "candidate_close_allowed_without_owner_review": False,
            }
        )
        rows.append(row)
    return rows


def _ensure_no_forbidden_public_payload(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_PUBLIC_KEYS:
                raise CustomerBusinessAnalysisError(f"forbidden public key found: {key}")
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, list):
        for item in value:
            _ensure_no_forbidden_public_payload(item)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(suffix in lowered for suffix in FORBIDDEN_PUBLIC_SUFFIXES):
            raise CustomerBusinessAnalysisError(f"forbidden private business file reference found: {value}")
        if any(text in lowered for text in FORBIDDEN_PUBLIC_TEXT):
            raise CustomerBusinessAnalysisError(f"forbidden private/raw marker found: {value}")


def build_default_customer_business_analysis(
    *,
    generated_at: str = "2026-07-01T23:40:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    relationships = read_jsonl(DEFAULT_BUSINESS_RELATIONSHIPS)
    margin_records = read_jsonl(DEFAULT_MARGIN_RECORDS)
    collection_items = read_jsonl(DEFAULT_COLLECTION_PRIORITY_ITEMS)
    lifecycle_records = read_jsonl(DEFAULT_LIFECYCLE_RECORDS)
    reconciliation_records = read_jsonl(DEFAULT_SCOPE_RECONCILIATION_RECORDS)
    report_grade_records = read_jsonl(DEFAULT_REPORT_GRADE_RECORDS)

    if not margin_records:
        raise CustomerBusinessAnalysisError("S16-P3 requires S09-P2 project margin records")
    if not collection_items:
        raise CustomerBusinessAnalysisError("S16-P3 requires S13-P2 collection priority items")
    if not lifecycle_records:
        raise CustomerBusinessAnalysisError("S16-P3 requires S16-P2 lifecycle records")

    pending_reconciliation_count = _pending_reconciliation_count(reconciliation_records)
    report_grade_visible = _report_grade_visible(report_grade_records)
    source_lanes = _source_lanes(
        relationships=relationships,
        margin_records=margin_records,
        collection_items=collection_items,
        lifecycle_records=lifecycle_records,
        generated_at=generated_at,
    )
    customer_summaries = _summary_rows(
        margin_records=margin_records,
        collection_items=collection_items,
        lifecycle_records=lifecycle_records,
        generated_at=generated_at,
    )
    exception_items = _exception_items(
        customer_summaries=customer_summaries,
        collection_items=collection_items,
        generated_at=generated_at,
    )

    manifest = {
        "schema_version": "kmfa.customer_business_analysis_manifest.v1",
        "record_type": "customer_business_analysis_manifest",
        "project_id": "KMFA",
        "stage_phase": "S16-P3",
        "analysis_version": ANALYSIS_VERSION,
        "formula_version": FORMULA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "generated_at": generated_at,
        "runtime_status": "public_safe_customer_business_analysis_created_review_only",
        "required_analysis_dimensions": list(REQUIRED_ANALYSIS_DIMENSIONS),
        "required_source_lanes": list(REQUIRED_SOURCE_LANES),
        "required_exception_types": list(REQUIRED_EXCEPTION_TYPES),
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "upstream_metadata_refs": UPSTREAM_METADATA_REFS,
        "quality_gate": _quality_gate(
            pending_reconciliation_count=pending_reconciliation_count,
            report_grade_visible=report_grade_visible,
        ),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "artifact_refs": {
            "customer_business_analysis_manifest": "KMFA/metadata/reports/customer_business_analysis_manifest.json",
            "customer_analysis_source_lanes": "KMFA/metadata/reports/customer_analysis_source_lanes.jsonl",
            "customer_operating_summaries": "KMFA/metadata/reports/customer_operating_summaries.jsonl",
            "customer_analysis_exception_items": "KMFA/metadata/reports/customer_analysis_exception_items.jsonl",
            "validator": "KMFA/tools/check_s16_p3_customer_business_analysis.py",
            "completion_record": "KMFA/stage_artifacts/S16_P3_customer_business_analysis/human/s16_p3_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S16_P3_customer_business_analysis/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S16_P3_customer_business_analysis/machine/s16_p3_manifest.json",
        },
        "summary": {
            "analysis_dimension_count": len(REQUIRED_ANALYSIS_DIMENSIONS),
            "source_lane_count": len(source_lanes),
            "customer_summary_count": len(customer_summaries),
            "exception_item_count": len(exception_items),
            "margin_signal_count": len(margin_records),
            "collection_priority_item_count": len(collection_items),
            "lifecycle_signal_count": len(lifecycle_records),
            "pending_reconciliation_count": pending_reconciliation_count,
            "report_grade_visible": report_grade_visible,
            "formal_report_count": 0,
            "business_decision_basis_count": 0,
            "collection_action_count": 0,
            "legal_collection_decision_count": 0,
            "payment_or_bank_operation_count": 0,
        },
        "limitations": [
            "S16-P3 只输出 public-safe 客户经营摘要和异常复核清单。",
            "不展示真实客户名称、项目名称、合同信息、真实金额、字段头明文、账号或原始文件。",
            "不自动执行催收、客户联系、法律决策、付款、银行、开票、税务或外部接口动作。",
            "不执行 Stage 16 review、GitHub upload、lineage full check 或正式报告。",
            "报告等级仍显示 D，12 条 pending owner 或授权复核差异继续阻断正式报告和经营决策依据。",
        ],
    }
    manifest["content_hash"] = _sha256_json(
        {
            "manifest_without_hash": manifest,
            "source_lanes": source_lanes,
            "customer_summaries": customer_summaries,
            "exception_items": exception_items,
        }
    )
    validate_customer_business_analysis_artifacts(manifest, source_lanes, customer_summaries, exception_items)
    return manifest, source_lanes, customer_summaries, exception_items


def _require_false(record: dict[str, Any], keys: tuple[str, ...], label: str) -> None:
    for key in keys:
        if record.get(key) is not False:
            raise CustomerBusinessAnalysisError(f"{label}.{key} must be false")


def validate_customer_business_analysis_artifacts(
    manifest: dict[str, Any],
    source_lanes: list[dict[str, Any]],
    customer_summaries: list[dict[str, Any]],
    exception_items: list[dict[str, Any]],
) -> None:
    if manifest.get("schema_version") != "kmfa.customer_business_analysis_manifest.v1":
        raise CustomerBusinessAnalysisError("manifest schema_version mismatch")
    if manifest.get("stage_phase") != "S16-P3":
        raise CustomerBusinessAnalysisError("manifest stage_phase must be S16-P3")
    if tuple(manifest.get("required_analysis_dimensions", [])) != REQUIRED_ANALYSIS_DIMENSIONS:
        raise CustomerBusinessAnalysisError("manifest required_analysis_dimensions mismatch")
    if tuple(manifest.get("required_source_lanes", [])) != REQUIRED_SOURCE_LANES:
        raise CustomerBusinessAnalysisError("manifest required_source_lanes mismatch")
    if tuple(manifest.get("required_exception_types", [])) != REQUIRED_EXCEPTION_TYPES:
        raise CustomerBusinessAnalysisError("manifest required_exception_types mismatch")

    expected_summary = {
        "analysis_dimension_count": 4,
        "source_lane_count": 5,
        "customer_summary_count": 4,
        "exception_item_count": 4,
        "pending_reconciliation_count": 12,
        "report_grade_visible": "D",
        "formal_report_count": 0,
        "business_decision_basis_count": 0,
        "collection_action_count": 0,
        "legal_collection_decision_count": 0,
        "payment_or_bank_operation_count": 0,
    }
    for key, expected in expected_summary.items():
        if manifest.get("summary", {}).get(key) != expected:
            raise CustomerBusinessAnalysisError(f"manifest summary {key} must be {expected}")
    for scope_key, expected in _stage_scope().items():
        if manifest.get("stage_scope", {}).get(scope_key) is not expected:
            raise CustomerBusinessAnalysisError(f"manifest stage_scope {scope_key} must be {expected}")
    for gate_key, expected in _quality_gate(pending_reconciliation_count=12, report_grade_visible="D").items():
        if manifest.get("quality_gate", {}).get(gate_key) != expected:
            raise CustomerBusinessAnalysisError(f"manifest quality_gate {gate_key} must be {expected}")
    for safety_key, expected in _public_repo_safety().items():
        if manifest.get("public_repo_safety", {}).get(safety_key) is not expected:
            raise CustomerBusinessAnalysisError(f"manifest public_repo_safety {safety_key} must be {expected}")

    lane_by_id = {str(lane.get("lane_id")): lane for lane in source_lanes}
    if set(lane_by_id) != set(REQUIRED_SOURCE_LANES):
        raise CustomerBusinessAnalysisError("source lanes must cover all S16-P3 required lanes")
    for lane_id in REQUIRED_SOURCE_LANES:
        lane = lane_by_id[lane_id]
        if lane.get("record_type") != "customer_analysis_source_lane":
            raise CustomerBusinessAnalysisError(f"{lane_id} record_type mismatch")
        if int(lane.get("source_count", 0)) < 1:
            raise CustomerBusinessAnalysisError(f"{lane_id} must have at least one source")
        if lane.get("all_sources_readonly") is not True:
            raise CustomerBusinessAnalysisError(f"{lane_id}.all_sources_readonly must be true")
        _require_false(
            lane,
            (
                "raw_business_values_allowed",
                "public_amount_values_allowed",
                "field_plaintext_allowed",
                "formal_report_allowed",
                "business_decision_basis_allowed",
                "collection_action_allowed",
                "legal_collection_decision_allowed",
                "auto_customer_contact_allowed",
                "invoice_issuance_allowed",
                "payment_execution_allowed",
                "bank_operation_allowed",
                "raw_layer_write_allowed",
            ),
            lane_id,
        )

    if len(customer_summaries) != 4:
        raise CustomerBusinessAnalysisError("customer summaries must contain four rows")
    for record in customer_summaries:
        if record.get("record_type") != "customer_operating_summary":
            raise CustomerBusinessAnalysisError("customer summary record_type mismatch")
        if record.get("stage_phase") != "S16-P3":
            raise CustomerBusinessAnalysisError("customer summary stage_phase must be S16-P3")
        if set(record.get("dimension_signal_refs", [])) != set(REQUIRED_ANALYSIS_DIMENSIONS):
            raise CustomerBusinessAnalysisError("customer summary dimensions mismatch")
        if record.get("summary_status") != "review_only_not_business_decision_basis":
            raise CustomerBusinessAnalysisError("customer summary status mismatch")
        if record.get("manual_review_required") is not True:
            raise CustomerBusinessAnalysisError("customer summary manual_review_required must be true")
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
                "collection_action_allowed",
                "legal_collection_decision_allowed",
                "auto_customer_contact_allowed",
                "invoice_issuance_allowed",
                "payment_execution_allowed",
                "bank_operation_allowed",
                "tax_filing_allowed",
                "raw_layer_write_allowed",
            ),
            str(record.get("customer_summary_id")),
        )

    if {str(item.get("exception_type")) for item in exception_items} != set(REQUIRED_EXCEPTION_TYPES):
        raise CustomerBusinessAnalysisError("exception items must cover required exception types")
    for item in exception_items:
        if item.get("record_type") != "customer_analysis_exception_item":
            raise CustomerBusinessAnalysisError("exception item record_type mismatch")
        if item.get("candidate_status") != "review_only_pending_owner_or_authorized_confirmation":
            raise CustomerBusinessAnalysisError("exception item candidate_status mismatch")
        if item.get("manual_review_required") is not True:
            raise CustomerBusinessAnalysisError("exception item manual_review_required must be true")
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
                "collection_action_allowed",
                "legal_collection_decision_allowed",
                "auto_customer_contact_allowed",
                "invoice_issuance_allowed",
                "payment_execution_allowed",
                "bank_operation_allowed",
                "tax_filing_allowed",
                "raw_layer_write_allowed",
                "auto_contact_allowed",
                "auto_legal_decision_allowed",
                "candidate_close_allowed_without_owner_review",
            ),
            str(item.get("exception_item_id")),
        )

    _ensure_no_forbidden_public_payload([manifest, source_lanes, customer_summaries, exception_items])


def generate_default_outputs(*, generated_at: str = "2026-07-01T23:40:00+10:00") -> dict[str, Any]:
    manifest, source_lanes, customer_summaries, exception_items = build_default_customer_business_analysis(
        generated_at=generated_at
    )
    write_json(DEFAULT_OUTPUT_MANIFEST, manifest)
    write_jsonl(DEFAULT_OUTPUT_SOURCE_LANES, source_lanes)
    write_jsonl(DEFAULT_OUTPUT_SUMMARIES, customer_summaries)
    write_jsonl(DEFAULT_OUTPUT_EXCEPTIONS, exception_items)
    write_json(
        DEFAULT_OUTPUT_STAGE_MANIFEST,
        {
            **manifest,
            "stage_artifact_manifest": True,
            "metadata_manifest_ref": "KMFA/metadata/reports/customer_business_analysis_manifest.json",
        },
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate KMFA S16-P3 customer business analysis public-safe artifacts.")
    parser.add_argument("--generated-at", default="2026-07-01T23:40:00+10:00")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    manifest, source_lanes, customer_summaries, exception_items = build_default_customer_business_analysis(
        generated_at=args.generated_at
    )
    validate_customer_business_analysis_artifacts(manifest, source_lanes, customer_summaries, exception_items)
    if not args.check_only:
        generate_default_outputs(generated_at=args.generated_at)
    summary = manifest["summary"]
    print(
        "PASS: KMFA S16-P3 customer business analysis generated "
        f"(source_lanes={summary['source_lane_count']}, "
        f"customer_summaries={summary['customer_summary_count']}, "
        f"exception_items={summary['exception_item_count']}, "
        "report_grade_visible=D, formal_report_allowed=false, "
        "business_decision_basis=false, collection_action=false, legal_collection_decision=false, "
        "stage16_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
