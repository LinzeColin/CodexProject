#!/usr/bin/env python3
"""Build KMFA S15-P2 public-safe performance fact table and review list artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_S15P1_MANIFEST = ROOT / "metadata" / "reports" / "performance_fact_fields_manifest.json"
DEFAULT_S15P1_FIELD_BINDINGS = ROOT / "metadata" / "reports" / "performance_fact_field_bindings.jsonl"
DEFAULT_S15P1_MANUAL_REVIEW_FIELDS = ROOT / "metadata" / "reports" / "performance_fact_manual_review_fields.jsonl"
DEFAULT_PROJECT_COST_FACT_RECORDS = ROOT / "metadata" / "lineage" / "project_cost_fact_records.jsonl"
DEFAULT_MARGIN_RECORDS = ROOT / "metadata" / "lineage" / "project_margin_cash_margin_records.jsonl"
DEFAULT_COLLECTION_PRIORITY_ITEMS = ROOT / "metadata" / "reports" / "collection_receivable_aging_priority_items.jsonl"
DEFAULT_CROSS_TABLE_DIFFERENCE_QUEUE = ROOT / "metadata" / "reports" / "cross_table_difference_queue.jsonl"

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "performance_review_manifest.json"
DEFAULT_OUTPUT_FACT_TABLE = ROOT / "metadata" / "reports" / "performance_fact_table.jsonl"
DEFAULT_OUTPUT_REVIEW_ITEMS = ROOT / "metadata" / "reports" / "performance_review_items.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S15_P2_performance_review_list" / "machine" / "s15_p2_manifest.json"
)

REQUIRED_PERFORMANCE_REVIEW_FIELDS = (
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

FIELD_STATUS = {
    "invoice_amount": "public_safe_hash_bound_no_value_display",
    "gross_margin_rate": "public_safe_hash_bound_pending_report_grade_no_value_display",
    "settlement_speed": "manual_review_required_missing_authoritative_settlement_window",
    "collection_speed": "manual_review_required_missing_authoritative_collection_window",
    "audit_variance": "manual_review_required_pending_cross_table_differences",
    "customer_relationship_rate": "manual_review_required_missing_public_safe_authority_source",
}

SOURCE_TASKPACK_REFS = {
    "roadmap_s15_p2": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S15-P2",
    "taskpack_req": "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md:REQ-P1-011",
}

PERFORMANCE_REVIEW_VERSION = "REVIEW-KMFA-S15P2-PERFORMANCE-FACT-TABLE-PUBLIC-SAFE-001"
FORMULA_VERSION = "FORM-KMFA-S15P2-PERFORMANCE-REVIEW-LIST-001"
MAPPING_VERSION = "MAP-KMFA-S15P2-PUBLIC-SAFE-v1"

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
    "salary_amount",
    "wage_amount",
    "bonus_amount",
    "payroll_amount",
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


class PerformanceReviewListError(ValueError):
    """Raised when S15-P2 performance review artifacts are invalid."""


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PerformanceReviewListError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise PerformanceReviewListError(f"{path} contains a non-object JSONL record")
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
        "true_ratio_value_committed": False,
        "project_customer_plaintext_committed": False,
        "payroll_or_salary_data_committed": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s15_p1_scope_reopened": False,
        "s15_p2_review_list_scope_included": True,
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
        "performance_fact_table_output_allowed": True,
        "abnormal_project_review_list_allowed": True,
        "review_item_output_allowed": True,
        "manual_review_required_before_compensation_use": True,
        "salary_calculation_allowed": False,
        "wage_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "final_compensation_decision_allowed": False,
        "payment_execution_allowed": False,
        "business_decision_basis_allowed": False,
        "formal_report_allowed": False,
        "complete_trusted_report_display_allowed": False,
        "raw_layer_write_allowed": False,
        "public_numeric_value_display_allowed": False,
        "github_upload_allowed": False,
        "phase_completion_upload_allowed": False,
        "stage15_review_allowed": False,
        "s15_p3_allowed": False,
        "report_grade_visible": "D",
        "release_block_reason": "performance_review_list_only_pending_s15_p3_salary_boundary_stage_review_and_upload",
    }


def _require_upstream(
    *,
    s15p1_manifest: dict[str, Any],
    field_bindings: list[dict[str, Any]],
    manual_review_fields: list[dict[str, Any]],
    fact_records: list[dict[str, Any]],
    margin_records: list[dict[str, Any]],
    collection_priority_items: list[dict[str, Any]],
    cross_table_difference_queue: list[dict[str, Any]],
) -> None:
    if s15p1_manifest.get("stage_phase") != "S15-P1":
        raise PerformanceReviewListError("S15-P2 requires S15-P1 performance fact field manifest")
    if tuple(s15p1_manifest.get("required_performance_fact_fields", [])) != REQUIRED_PERFORMANCE_REVIEW_FIELDS:
        raise PerformanceReviewListError("S15-P1 required performance fields mismatch")
    if [row.get("field_key") for row in field_bindings] != list(REQUIRED_PERFORMANCE_REVIEW_FIELDS):
        raise PerformanceReviewListError("S15-P2 requires all S15-P1 field bindings")
    if [row.get("field_key") for row in manual_review_fields] != list(REQUIRED_MANUAL_REVIEW_FIELDS):
        raise PerformanceReviewListError("S15-P2 requires all S15-P1 manual review markers")
    if len(fact_records) < 4:
        raise PerformanceReviewListError("S15-P2 requires at least four public-safe project cost fact records")
    if len(margin_records) < 4:
        raise PerformanceReviewListError("S15-P2 requires at least four public-safe margin records")
    if len(collection_priority_items) < 4:
        raise PerformanceReviewListError("S15-P2 requires collection priority review items")
    if len(cross_table_difference_queue) < 4:
        raise PerformanceReviewListError("S15-P2 requires cross-table difference queue items")


def _manual_review_ref(field_key: str) -> str:
    return f"KMFA/metadata/reports/performance_fact_manual_review_fields.jsonl#{field_key}"


def _sanitize_source_refs(source_refs: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(source_refs, list):
        for ref in source_refs:
            if isinstance(ref, str) and "private://" not in ref and "private_ref://" not in ref:
                refs.append(ref)
    return refs


def _fact_row(
    *,
    index: int,
    fact_record: dict[str, Any],
    margin_record: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    fact_record_id = str(fact_record.get("fact_record_id"))
    margin_record_id = str(margin_record.get("margin_record_id"))
    invoice_hash = fact_record.get("metric_hash_refs", {}).get("invoice_amount")
    margin_hash = margin_record.get("authority_value_hash_refs", {}).get("gross_margin_rate")
    if not isinstance(invoice_hash, str) or not invoice_hash.startswith("sha256:"):
        raise PerformanceReviewListError(f"{fact_record_id} missing public-safe invoice hash")
    if not isinstance(margin_hash, str) or not margin_hash.startswith("sha256:"):
        raise PerformanceReviewListError(f"{margin_record_id} missing public-safe margin hash")

    fact_row_id = f"S15P2-FACT-{index:03d}"
    return {
        "schema_version": "kmfa.performance_fact_table_row.v1",
        "record_type": "performance_fact_table_row",
        "project_id": "KMFA",
        "stage_phase": "S15-P2",
        "performance_fact_row_id": fact_row_id,
        "generated_at": generated_at,
        "project_ref": str(fact_record.get("project_entity_ref")),
        "project_identity_profile_ref": str(fact_record.get("project_identity_profile_ref")),
        "project_cost_fact_ref": f"KMFA/metadata/lineage/project_cost_fact_records.jsonl#{fact_record_id}",
        "project_margin_ref": f"KMFA/metadata/lineage/project_margin_cash_margin_records.jsonl#{margin_record_id}",
        "fact_status_by_field": {field_key: FIELD_STATUS[field_key] for field_key in REQUIRED_PERFORMANCE_REVIEW_FIELDS},
        "fact_hash_refs_by_field": {
            "invoice_amount": invoice_hash,
            "gross_margin_rate": margin_hash,
        },
        "manual_review_refs_by_field": {
            field_key: _manual_review_ref(field_key) for field_key in REQUIRED_MANUAL_REVIEW_FIELDS
        },
        "review_item_refs": [
            f"KMFA/metadata/reports/performance_review_items.jsonl#S15P2-REV-{((index - 1) * 4) + item_index:03d}"
            for item_index in range(1, 5)
        ],
        "evidence_refs": [
            "KMFA/metadata/reports/performance_fact_fields_manifest.json",
            "KMFA/metadata/reports/performance_fact_field_bindings.jsonl",
            "KMFA/metadata/lineage/project_cost_fact_records.jsonl",
            "KMFA/metadata/lineage/project_margin_cash_margin_records.jsonl",
            "KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl",
            "KMFA/metadata/reports/cross_table_difference_queue.jsonl",
        ],
        "source_refs": _sanitize_source_refs(fact_record.get("source_refs")),
        "fact_table_value_policy": "public_safe_hash_refs_and_status_only_no_numeric_display",
        "review_status": "pending_owner_or_authorized_review_before_compensation_use",
        "report_grade_visible": "D",
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
        "final_compensation_decision_allowed": False,
    }


def _review_item(
    *,
    review_item_id: str,
    fact_row: dict[str, Any],
    field_key: str,
    manual_review_field: dict[str, Any],
    collection_item: dict[str, Any],
    difference_item: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.performance_review_item.v1",
        "record_type": "performance_review_item",
        "project_id": "KMFA",
        "stage_phase": "S15-P2",
        "review_item_id": review_item_id,
        "generated_at": generated_at,
        "performance_fact_row_ref": f"KMFA/metadata/reports/performance_fact_table.jsonl#{fact_row['performance_fact_row_id']}",
        "project_ref": fact_row["project_ref"],
        "field_key": field_key,
        "visible_field_label": FIELD_LABELS[field_key],
        "review_reason_code": str(manual_review_field.get("reason_code")),
        "abnormal_project_review_required": True,
        "abnormal_signal_ref": _sha256_for(f"S15-P2:{fact_row['performance_fact_row_id']}:{field_key}:review-signal"),
        "linked_collection_priority_ref": (
            "KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl#"
            f"{collection_item.get('priority_item_id')}"
        ),
        "linked_cross_table_difference_ref": (
            "KMFA/metadata/reports/cross_table_difference_queue.jsonl#"
            f"{difference_item.get('queue_item_id')}"
        ),
        "source_evidence_refs": [
            "KMFA/metadata/reports/performance_fact_manual_review_fields.jsonl",
            "KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl",
            "KMFA/metadata/reports/cross_table_difference_queue.jsonl",
        ],
        "review_owner_role": str(manual_review_field.get("responsible_role")),
        "review_mode": "owner_or_authorized_delegate_review_only",
        "required_review_action": str(manual_review_field.get("required_review_action")),
        "resolution_status": "pending_owner_or_authorized_review",
        "next_review_bucket": "next_internal_performance_review_cycle",
        "raw_business_values_allowed": False,
        "public_numeric_values_allowed": False,
        "field_plaintext_allowed": False,
        "auto_resolution_allowed": False,
        "auto_calculation_allowed": False,
        "auto_approval_allowed": False,
        "formal_report_allowed": False,
        "business_decision_basis_allowed": False,
        "salary_calculation_allowed": False,
        "wage_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "payment_execution_allowed": False,
        "final_compensation_decision_allowed": False,
    }


def build_default_performance_review_list_artifacts(
    *,
    generated_at: str = "2026-07-01T23:45:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    s15p1_manifest = read_json(DEFAULT_S15P1_MANIFEST)
    field_bindings = read_jsonl(DEFAULT_S15P1_FIELD_BINDINGS)
    manual_review_fields = read_jsonl(DEFAULT_S15P1_MANUAL_REVIEW_FIELDS)
    fact_records = read_jsonl(DEFAULT_PROJECT_COST_FACT_RECORDS)
    margin_records = read_jsonl(DEFAULT_MARGIN_RECORDS)
    collection_priority_items = read_jsonl(DEFAULT_COLLECTION_PRIORITY_ITEMS)
    cross_table_difference_queue = read_jsonl(DEFAULT_CROSS_TABLE_DIFFERENCE_QUEUE)

    _require_upstream(
        s15p1_manifest=s15p1_manifest,
        field_bindings=field_bindings,
        manual_review_fields=manual_review_fields,
        fact_records=fact_records,
        margin_records=margin_records,
        collection_priority_items=collection_priority_items,
        cross_table_difference_queue=cross_table_difference_queue,
    )

    fact_rows = [
        _fact_row(
            index=index,
            fact_record=fact_record,
            margin_record=margin_record,
            generated_at=generated_at,
        )
        for index, (fact_record, margin_record) in enumerate(zip(fact_records[:4], margin_records[:4]), start=1)
    ]

    manual_by_key = {str(row["field_key"]): row for row in manual_review_fields}
    review_items: list[dict[str, Any]] = []
    for row_index, fact_row in enumerate(fact_rows):
        collection_item = collection_priority_items[row_index % len(collection_priority_items)]
        difference_item = cross_table_difference_queue[row_index % len(cross_table_difference_queue)]
        for field_index, field_key in enumerate(REQUIRED_MANUAL_REVIEW_FIELDS, start=1):
            review_items.append(
                _review_item(
                    review_item_id=f"S15P2-REV-{(row_index * 4) + field_index:03d}",
                    fact_row=fact_row,
                    field_key=field_key,
                    manual_review_field=manual_by_key[field_key],
                    collection_item=collection_item,
                    difference_item=difference_item,
                    generated_at=generated_at,
                )
            )

    manifest = {
        "schema_version": "kmfa.performance_review_manifest.v1",
        "record_type": "performance_review_manifest",
        "project_id": "KMFA",
        "stage_phase": "S15-P2",
        "generated_at": generated_at,
        "performance_review_version": PERFORMANCE_REVIEW_VERSION,
        "formula_version": FORMULA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "runtime_status": "public_safe_performance_fact_table_and_review_items_created",
        "required_review_fields": list(REQUIRED_PERFORMANCE_REVIEW_FIELDS),
        "required_manual_review_fields": list(REQUIRED_MANUAL_REVIEW_FIELDS),
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "upstream_metadata_refs": {
            "s15p1_manifest": "KMFA/metadata/reports/performance_fact_fields_manifest.json",
            "s15p1_field_bindings": "KMFA/metadata/reports/performance_fact_field_bindings.jsonl",
            "s15p1_manual_review_fields": "KMFA/metadata/reports/performance_fact_manual_review_fields.jsonl",
            "project_cost_fact_records": "KMFA/metadata/lineage/project_cost_fact_records.jsonl",
            "project_margin_cash_margin_records": "KMFA/metadata/lineage/project_margin_cash_margin_records.jsonl",
            "collection_receivable_aging_priority_items": (
                "KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl"
            ),
            "cross_table_difference_queue": "KMFA/metadata/reports/cross_table_difference_queue.jsonl",
        },
        "quality_gate": _quality_gate(),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "artifact_refs": {
            "performance_review_manifest": "KMFA/metadata/reports/performance_review_manifest.json",
            "performance_fact_table": "KMFA/metadata/reports/performance_fact_table.jsonl",
            "performance_review_items": "KMFA/metadata/reports/performance_review_items.jsonl",
            "validator": "KMFA/tools/check_s15_p2_performance_review_list.py",
            "completion_record": (
                "KMFA/stage_artifacts/S15_P2_performance_review_list/human/s15_p2_completion_record.md"
            ),
            "test_results": "KMFA/stage_artifacts/S15_P2_performance_review_list/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S15_P2_performance_review_list/machine/s15_p2_manifest.json",
        },
        "summary": {
            "performance_fact_row_count": len(fact_rows),
            "abnormal_review_item_count": len(review_items),
            "manual_review_field_count": len(REQUIRED_MANUAL_REVIEW_FIELDS),
            "project_cost_fact_record_count": len(fact_records),
            "margin_record_count": len(margin_records),
            "collection_priority_item_count": len(collection_priority_items),
            "cross_table_difference_count": len(cross_table_difference_queue),
            "salary_calculation_count": 0,
            "wage_calculation_count": 0,
            "bonus_approval_count": 0,
            "payroll_export_count": 0,
            "final_compensation_decision_count": 0,
            "report_grade_visible": "D",
        },
        "limitations": [
            "S15-P2 只输出 public-safe 绩效事实表和异常项目复核事项。",
            "绩效事实表只包含 hash/ref/status，不显示真实金额、比例、日期、项目客户明文或人员信息。",
            "本 phase 不计算最终工资、不审批奖金、不导出薪资、不执行付款或外部接口。",
        ],
    }
    manifest["content_hash"] = _sha256_json(
        {
            "manifest": manifest,
            "fact_rows": fact_rows,
            "review_items": review_items,
        }
    )
    validate_performance_review_list_artifacts(manifest, fact_rows, review_items)
    return manifest, fact_rows, review_items


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


def _expect_map(container: dict[str, Any], expected: dict[str, Any], path: str) -> None:
    for key, expected_value in expected.items():
        if container.get(key) != expected_value:
            raise PerformanceReviewListError(f"{path}.{key} must be {expected_value}")


def validate_performance_review_list_artifacts(
    manifest: dict[str, Any],
    fact_rows: list[dict[str, Any]],
    review_items: list[dict[str, Any]],
) -> None:
    if manifest.get("schema_version") != "kmfa.performance_review_manifest.v1":
        raise PerformanceReviewListError("manifest schema_version mismatch")
    if manifest.get("stage_phase") != "S15-P2":
        raise PerformanceReviewListError("manifest stage_phase must be S15-P2")
    if tuple(manifest.get("required_review_fields", [])) != REQUIRED_PERFORMANCE_REVIEW_FIELDS:
        raise PerformanceReviewListError("required review fields mismatch")
    if tuple(manifest.get("required_manual_review_fields", [])) != REQUIRED_MANUAL_REVIEW_FIELDS:
        raise PerformanceReviewListError("required manual review fields mismatch")

    expected_summary = {
        "performance_fact_row_count": 4,
        "abnormal_review_item_count": 16,
        "manual_review_field_count": 4,
        "salary_calculation_count": 0,
        "wage_calculation_count": 0,
        "bonus_approval_count": 0,
        "payroll_export_count": 0,
        "final_compensation_decision_count": 0,
        "report_grade_visible": "D",
    }
    for key, expected in expected_summary.items():
        if manifest.get("summary", {}).get(key) != expected:
            raise PerformanceReviewListError(f"manifest summary {key} must be {expected}")
    for key in (
        "project_cost_fact_record_count",
        "margin_record_count",
        "collection_priority_item_count",
        "cross_table_difference_count",
    ):
        if int(manifest.get("summary", {}).get(key, 0)) < 4:
            raise PerformanceReviewListError(f"manifest summary {key} must be >= 4")

    _expect_map(manifest.get("stage_scope", {}), _stage_scope(), "manifest.stage_scope")
    _expect_map(manifest.get("quality_gate", {}), _quality_gate(), "manifest.quality_gate")
    _expect_map(manifest.get("public_repo_safety", {}), _public_repo_safety(), "manifest.public_repo_safety")

    if len(fact_rows) != 4:
        raise PerformanceReviewListError("fact row count must be 4")
    if [row.get("performance_fact_row_id") for row in fact_rows] != [
        "S15P2-FACT-001",
        "S15P2-FACT-002",
        "S15P2-FACT-003",
        "S15P2-FACT-004",
    ]:
        raise PerformanceReviewListError("fact row id order mismatch")
    for row in fact_rows:
        row_id = str(row.get("performance_fact_row_id"))
        if row.get("schema_version") != "kmfa.performance_fact_table_row.v1":
            raise PerformanceReviewListError(f"{row_id} schema mismatch")
        if row.get("record_type") != "performance_fact_table_row":
            raise PerformanceReviewListError(f"{row_id} record_type mismatch")
        if row.get("stage_phase") != "S15-P2":
            raise PerformanceReviewListError(f"{row_id} stage_phase mismatch")
        if not str(row.get("project_ref", "")).startswith("entity_ref://KMFA/S08-P2/project/"):
            raise PerformanceReviewListError(f"{row_id} project_ref must be a public entity ref")
        if set(row.get("fact_status_by_field", {})) != set(REQUIRED_PERFORMANCE_REVIEW_FIELDS):
            raise PerformanceReviewListError(f"{row_id} fact status fields mismatch")
        if set(row.get("fact_hash_refs_by_field", {})) != {"invoice_amount", "gross_margin_rate"}:
            raise PerformanceReviewListError(f"{row_id} fact hash fields mismatch")
        for hash_ref in row.get("fact_hash_refs_by_field", {}).values():
            if not isinstance(hash_ref, str) or not hash_ref.startswith("sha256:"):
                raise PerformanceReviewListError(f"{row_id} fact hash ref must be sha256")
        if set(row.get("manual_review_refs_by_field", {})) != set(REQUIRED_MANUAL_REVIEW_FIELDS):
            raise PerformanceReviewListError(f"{row_id} manual review refs mismatch")
        if len(row.get("review_item_refs", [])) != 4:
            raise PerformanceReviewListError(f"{row_id} must reference four review items")
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
            "final_compensation_decision_allowed",
        ):
            if row.get(false_key) is not False:
                raise PerformanceReviewListError(f"{row_id} {false_key} must be false")

    if len(review_items) != 16:
        raise PerformanceReviewListError("review item count must be 16")
    valid_fact_refs = {
        f"KMFA/metadata/reports/performance_fact_table.jsonl#{row['performance_fact_row_id']}" for row in fact_rows
    }
    for item in review_items:
        item_id = str(item.get("review_item_id"))
        if item.get("schema_version") != "kmfa.performance_review_item.v1":
            raise PerformanceReviewListError(f"{item_id} schema mismatch")
        if item.get("record_type") != "performance_review_item":
            raise PerformanceReviewListError(f"{item_id} record_type mismatch")
        if item.get("stage_phase") != "S15-P2":
            raise PerformanceReviewListError(f"{item_id} stage_phase mismatch")
        if item.get("performance_fact_row_ref") not in valid_fact_refs:
            raise PerformanceReviewListError(f"{item_id} fact row ref mismatch")
        if item.get("field_key") not in REQUIRED_MANUAL_REVIEW_FIELDS:
            raise PerformanceReviewListError(f"{item_id} field_key must require manual review")
        if item.get("abnormal_project_review_required") is not True:
            raise PerformanceReviewListError(f"{item_id} abnormal review flag must be true")
        if item.get("review_mode") != "owner_or_authorized_delegate_review_only":
            raise PerformanceReviewListError(f"{item_id} review mode mismatch")
        if item.get("resolution_status") != "pending_owner_or_authorized_review":
            raise PerformanceReviewListError(f"{item_id} resolution status mismatch")
        for false_key in (
            "raw_business_values_allowed",
            "public_numeric_values_allowed",
            "field_plaintext_allowed",
            "auto_resolution_allowed",
            "auto_calculation_allowed",
            "auto_approval_allowed",
            "formal_report_allowed",
            "business_decision_basis_allowed",
            "salary_calculation_allowed",
            "wage_calculation_allowed",
            "bonus_approval_allowed",
            "payroll_export_allowed",
            "payment_execution_allowed",
            "final_compensation_decision_allowed",
        ):
            if item.get(false_key) is not False:
                raise PerformanceReviewListError(f"{item_id} {false_key} must be false")

    by_fact: dict[str, set[str]] = {}
    for item in review_items:
        by_fact.setdefault(str(item["performance_fact_row_ref"]), set()).add(str(item["field_key"]))
    if set(by_fact) != valid_fact_refs:
        raise PerformanceReviewListError("review item fact coverage mismatch")
    for fact_ref, field_keys in by_fact.items():
        if field_keys != set(REQUIRED_MANUAL_REVIEW_FIELDS):
            raise PerformanceReviewListError(f"{fact_ref} review field coverage mismatch")

    public_payload = [manifest, fact_rows, review_items]
    forbidden_key_hits = _walk_forbidden_keys(public_payload)
    if forbidden_key_hits:
        raise PerformanceReviewListError("forbidden public keys found: " + ", ".join(forbidden_key_hits))
    forbidden_text_hits = _walk_forbidden_text(public_payload)
    if forbidden_text_hits:
        raise PerformanceReviewListError("forbidden public text found: " + ", ".join(forbidden_text_hits))


def write_default_performance_review_list_artifacts(
    *,
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    output_fact_table: Path = DEFAULT_OUTPUT_FACT_TABLE,
    output_review_items: Path = DEFAULT_OUTPUT_REVIEW_ITEMS,
    output_stage_manifest: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    generated_at: str = "2026-07-01T23:45:00+10:00",
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    manifest, fact_rows, review_items = build_default_performance_review_list_artifacts(generated_at=generated_at)
    write_json(output_manifest, manifest)
    write_jsonl(output_fact_table, fact_rows)
    write_jsonl(output_review_items, review_items)
    stage_manifest = {
        "schema_version": "kmfa.s15_p2_stage_manifest.v1",
        "record_type": "s15_p2_performance_review_list_stage_manifest",
        "project_id": "KMFA",
        "stage_phase": "S15-P2",
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
    return manifest, fact_rows, review_items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S15-P2 performance review list artifacts.")
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-fact-table", type=Path, default=DEFAULT_OUTPUT_FACT_TABLE)
    parser.add_argument("--output-review-items", type=Path, default=DEFAULT_OUTPUT_REVIEW_ITEMS)
    parser.add_argument("--output-stage-manifest", type=Path, default=DEFAULT_OUTPUT_STAGE_MANIFEST)
    parser.add_argument("--generated-at", default="2026-07-01T23:45:00+10:00")
    args = parser.parse_args(argv)

    manifest, fact_rows, review_items = write_default_performance_review_list_artifacts(
        output_manifest=args.output_manifest,
        output_fact_table=args.output_fact_table,
        output_review_items=args.output_review_items,
        output_stage_manifest=args.output_stage_manifest,
        generated_at=args.generated_at,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S15-P2 performance review list artifacts generated "
        f"(fact_rows={len(fact_rows)}, review_items={len(review_items)}, "
        f"manual_review_fields={summary['manual_review_field_count']}, "
        "performance_fact_table=true, abnormal_review_list=true, "
        "salary_calculation=false, bonus_approval=false, payroll_export=false, "
        "s15_p3_scope=false, stage15_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
