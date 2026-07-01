#!/usr/bin/env python3
"""Build KMFA S15-P3 public-safe performance-to-salary boundary artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_S15P2_MANIFEST = ROOT / "metadata" / "reports" / "performance_review_manifest.json"
DEFAULT_S15P2_FACT_TABLE = ROOT / "metadata" / "reports" / "performance_fact_table.jsonl"
DEFAULT_S15P2_REVIEW_ITEMS = ROOT / "metadata" / "reports" / "performance_review_items.jsonl"

DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "performance_salary_boundary_manifest.json"
DEFAULT_OUTPUT_INTERFACE_CONTRACT = ROOT / "metadata" / "reports" / "performance_fact_output_interface_contract.json"
DEFAULT_OUTPUT_READINESS_DRAFT = ROOT / "metadata" / "reports" / "salary_system_readiness_draft.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = ROOT / "stage_artifacts" / "S15_P3_salary_boundary" / "machine" / "s15_p3_manifest.json"

REQUIRED_FACT_INTERFACE_FIELDS = (
    "invoice_amount",
    "gross_margin_rate",
    "settlement_speed",
    "collection_speed",
    "audit_variance",
    "customer_relationship_rate",
)

SALARY_BOUNDARY_VERSION = "BOUNDARY-KMFA-S15P3-SALARY-FACT-INTERFACE-DRAFT-001"
FORMULA_VERSION = "FORM-KMFA-S15P3-SALARY-BOUNDARY-001"
MAPPING_VERSION = "MAP-KMFA-S15P3-SALARY-BOUNDARY-v1"

SOURCE_TASKPACK_REFS = {
    "roadmap_s15_p3": "KMFA/taskpack/v1_2/02_KMFA_Codex_Development_Roadmap_18_Stages_v1_2.md:S15-P3",
    "taskpack_non_goal": "KMFA/taskpack/v1_2/01_KMFA_Codex_TaskPack_v1_2_完整防遗漏_含HTML验收样板.md:不自动发工资或奖金",
}

FORBIDDEN_PUBLIC_KEYS = {
    "amount_cents",
    "amount_yuan",
    "raw_value",
    "normalized_value",
    "original_value",
    "plaintext_value",
    "source_header_text",
    "original_filename",
    "raw_file_bytes",
    "private_csv",
    "bank_account_number",
    "account_number",
    "identity_document_number",
    "project_name_plaintext",
    "customer_name_plaintext",
    "counterparty_plaintext",
    "company_entity_plaintext",
    "employee_name",
    "employee_id",
    "staff_name",
    "staff_id",
    "salary_amount",
    "wage_amount",
    "bonus_amount",
    "payroll_amount",
    "payment_account",
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
    "employee_name",
    "employee_id",
    "salary_amount",
    "wage_amount",
    "bonus_amount",
    "payroll_amount",
    "password",
    "token",
    "api_key",
    "private_key",
)


class PerformanceSalaryBoundaryError(ValueError):
    """Raised when S15-P3 salary boundary artifacts are invalid."""


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PerformanceSalaryBoundaryError(f"{path} must contain a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise PerformanceSalaryBoundaryError(f"{path} contains a non-object JSONL record")
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
        "employee_or_salary_data_committed": False,
        "bank_or_payment_account_committed": False,
    }


def _stage_scope() -> dict[str, bool]:
    return {
        "s15_p1_scope_reopened": False,
        "s15_p2_scope_reopened": False,
        "s15_p3_salary_boundary_scope_included": True,
        "stage15_review_scope_included": False,
        "github_upload_scope_included": False,
        "lineage_full_check_scope_included": False,
        "formal_report_runtime_scope_included": False,
        "external_connector_scope_included": False,
        "live_salary_system_scope_included": False,
        "salary_calculation_scope_included": False,
        "bonus_approval_scope_included": False,
        "payroll_export_scope_included": False,
        "payment_execution_scope_included": False,
    }


def _quality_gate() -> dict[str, Any]:
    return {
        "fact_output_interface_reserved": True,
        "future_salary_system_read_draft_allowed": True,
        "live_salary_system_integration_allowed": False,
        "api_endpoint_allowed": False,
        "connector_allowed": False,
        "file_export_allowed": False,
        "scheduled_sync_allowed": False,
        "external_system_write_allowed": False,
        "salary_calculation_allowed": False,
        "wage_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "final_compensation_decision_allowed": False,
        "automatic_compensation_decision_allowed": False,
        "final_approval_must_be_human": True,
        "payment_release_must_be_human": True,
        "payment_execution_allowed": False,
        "business_decision_basis_allowed": False,
        "formal_report_allowed": False,
        "raw_layer_write_allowed": False,
        "public_numeric_value_display_allowed": False,
        "phase_completion_upload_allowed": False,
        "stage15_review_allowed": False,
        "github_upload_allowed": False,
        "report_grade_visible": "D",
        "release_block_reason": "salary_boundary_contract_only_pending_stage15_review_and_human_approval",
    }


def _require_upstream(
    *,
    s15p2_manifest: dict[str, Any],
    fact_rows: list[dict[str, Any]],
    review_items: list[dict[str, Any]],
) -> None:
    if s15p2_manifest.get("stage_phase") != "S15-P2":
        raise PerformanceSalaryBoundaryError("S15-P3 requires S15-P2 performance review manifest")
    if tuple(s15p2_manifest.get("required_review_fields", [])) != REQUIRED_FACT_INTERFACE_FIELDS:
        raise PerformanceSalaryBoundaryError("S15-P2 required review fields mismatch")
    if len(fact_rows) != 4:
        raise PerformanceSalaryBoundaryError("S15-P3 requires four S15-P2 performance fact rows")
    if len(review_items) != 16:
        raise PerformanceSalaryBoundaryError("S15-P3 requires sixteen S15-P2 review items")
    for row in fact_rows:
        if row.get("stage_phase") != "S15-P2":
            raise PerformanceSalaryBoundaryError("S15-P3 input fact rows must be S15-P2")
        if set(row.get("fact_status_by_field", {})) != set(REQUIRED_FACT_INTERFACE_FIELDS):
            raise PerformanceSalaryBoundaryError("S15-P2 fact row field coverage mismatch")
    if s15p2_manifest.get("quality_gate", {}).get("final_compensation_decision_allowed") is not False:
        raise PerformanceSalaryBoundaryError("S15-P2 must not allow final compensation decision")


def _review_items_by_fact(review_items: list[dict[str, Any]]) -> dict[str, list[str]]:
    by_fact: dict[str, list[str]] = {}
    for item in review_items:
        fact_ref = str(item.get("performance_fact_row_ref"))
        by_fact.setdefault(fact_ref, []).append(str(item.get("review_item_id")))
    return by_fact


def _build_interface_contract(generated_at: str) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.performance_fact_output_interface_contract.v1",
        "record_type": "performance_fact_output_interface_contract",
        "project_id": "KMFA",
        "stage_phase": "S15-P3",
        "generated_at": generated_at,
        "salary_boundary_version": SALARY_BOUNDARY_VERSION,
        "formula_version": FORMULA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "interface_status": "reserved_contract_only",
        "source_manifest_ref": "KMFA/metadata/reports/performance_review_manifest.json",
        "source_artifact_ref": "KMFA/metadata/reports/performance_fact_table.jsonl",
        "source_review_item_ref": "KMFA/metadata/reports/performance_review_items.jsonl",
        "fact_interface_fields": list(REQUIRED_FACT_INTERFACE_FIELDS),
        "allowed_payload_fields": [
            "performance_fact_row_ref",
            "project_ref",
            "available_fact_fields",
            "field_status_refs",
            "fact_hash_ref_fields",
            "review_item_refs",
            "evidence_refs",
            "boundary_flags",
        ],
        "value_policy": "hash_ref_status_and_evidence_only_no_numeric_payload",
        "read_model_status": "draft_schema_for_future_system_only",
        "api_endpoint_created": False,
        "file_export_created": False,
        "connector_enabled": False,
        "live_read_enabled": False,
        "scheduled_sync_enabled": False,
        "external_write_enabled": False,
        "raw_layer_write_allowed": False,
        "public_numeric_values_allowed": False,
        "automatic_compensation_decision_allowed": False,
        "final_approval_must_be_human": True,
        "payment_release_must_be_human": True,
    }


def _readiness_row(
    *,
    index: int,
    fact_row: dict[str, Any],
    review_item_ids: list[str],
    generated_at: str,
) -> dict[str, Any]:
    row_id = f"S15P3-READ-{index:03d}"
    fact_row_id = str(fact_row["performance_fact_row_id"])
    return {
        "schema_version": "kmfa.future_salary_system_readiness_draft.v1",
        "record_type": "future_salary_system_readiness_draft",
        "project_id": "KMFA",
        "stage_phase": "S15-P3",
        "readiness_row_id": row_id,
        "generated_at": generated_at,
        "performance_fact_row_ref": f"KMFA/metadata/reports/performance_fact_table.jsonl#{fact_row_id}",
        "project_ref": str(fact_row["project_ref"]),
        "interface_contract_ref": "KMFA/metadata/reports/performance_fact_output_interface_contract.json",
        "source_review_item_refs": [
            f"KMFA/metadata/reports/performance_review_items.jsonl#{item_id}" for item_id in sorted(review_item_ids)
        ],
        "available_fact_fields": list(REQUIRED_FACT_INTERFACE_FIELDS),
        "field_status_refs": dict(fact_row.get("fact_status_by_field", {})),
        "fact_hash_ref_fields": sorted(fact_row.get("fact_hash_refs_by_field", {}).keys()),
        "review_item_count": len(review_item_ids),
        "future_read_status": "draft_only_blocked_until_manual_review_and_human_approval",
        "value_policy": "no_numeric_salary_or_bonus_payload",
        "boundary_decision_policy": "facts_may_be_read_later_decisions_must_be_manual",
        "manual_approval_role": "owner_or_authorized_compensation_approver",
        "final_approval_must_be_human": True,
        "payment_release_must_be_human": True,
        "raw_business_values_allowed": False,
        "public_numeric_values_allowed": False,
        "field_plaintext_allowed": False,
        "api_endpoint_created": False,
        "connector_enabled": False,
        "live_read_enabled": False,
        "salary_calculation_allowed": False,
        "wage_calculation_allowed": False,
        "bonus_approval_allowed": False,
        "payroll_export_allowed": False,
        "automatic_compensation_decision_allowed": False,
        "automatic_payment_allowed": False,
        "payment_execution_allowed": False,
        "final_compensation_decision_allowed": False,
    }


def build_default_performance_salary_boundary_artifacts(
    *,
    generated_at: str = "2026-07-01T23:55:00+10:00",
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    s15p2_manifest = read_json(DEFAULT_S15P2_MANIFEST)
    fact_rows = read_jsonl(DEFAULT_S15P2_FACT_TABLE)
    review_items = read_jsonl(DEFAULT_S15P2_REVIEW_ITEMS)
    _require_upstream(s15p2_manifest=s15p2_manifest, fact_rows=fact_rows, review_items=review_items)

    interface_contract = _build_interface_contract(generated_at)
    review_by_fact = _review_items_by_fact(review_items)
    readiness_rows = []
    for index, fact_row in enumerate(fact_rows, start=1):
        fact_ref = f"KMFA/metadata/reports/performance_fact_table.jsonl#{fact_row['performance_fact_row_id']}"
        review_ids = review_by_fact.get(fact_ref, [])
        if len(review_ids) != 4:
            raise PerformanceSalaryBoundaryError(f"{fact_ref} must have four S15-P2 review items")
        readiness_rows.append(
            _readiness_row(index=index, fact_row=fact_row, review_item_ids=review_ids, generated_at=generated_at)
        )

    manifest = {
        "schema_version": "kmfa.performance_salary_boundary_manifest.v1",
        "record_type": "performance_salary_boundary_manifest",
        "project_id": "KMFA",
        "stage_phase": "S15-P3",
        "generated_at": generated_at,
        "salary_boundary_version": SALARY_BOUNDARY_VERSION,
        "formula_version": FORMULA_VERSION,
        "mapping_version": MAPPING_VERSION,
        "runtime_status": "reserved_fact_output_interface_and_future_readiness_draft_created",
        "source_taskpack_refs": SOURCE_TASKPACK_REFS,
        "upstream_metadata_refs": {
            "s15p2_manifest": "KMFA/metadata/reports/performance_review_manifest.json",
            "s15p2_fact_table": "KMFA/metadata/reports/performance_fact_table.jsonl",
            "s15p2_review_items": "KMFA/metadata/reports/performance_review_items.jsonl",
        },
        "artifact_refs": {
            "salary_boundary_manifest": "KMFA/metadata/reports/performance_salary_boundary_manifest.json",
            "fact_output_interface_contract": "KMFA/metadata/reports/performance_fact_output_interface_contract.json",
            "future_salary_system_readiness_draft": "KMFA/metadata/reports/salary_system_readiness_draft.jsonl",
            "validator": "KMFA/tools/check_s15_p3_salary_boundary.py",
            "completion_record": "KMFA/stage_artifacts/S15_P3_salary_boundary/human/s15_p3_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S15_P3_salary_boundary/human/test_results.md",
            "stage_manifest": "KMFA/stage_artifacts/S15_P3_salary_boundary/machine/s15_p3_manifest.json",
        },
        "quality_gate": _quality_gate(),
        "stage_scope": _stage_scope(),
        "public_repo_safety": _public_repo_safety(),
        "summary": {
            "fact_interface_contract_count": 1,
            "future_salary_system_readiness_row_count": len(readiness_rows),
            "human_approval_boundary_count": len(readiness_rows),
            "pending_review_item_count": len(review_items),
            "salary_calculation_count": 0,
            "wage_calculation_count": 0,
            "bonus_approval_count": 0,
            "payroll_export_count": 0,
            "final_compensation_decision_count": 0,
            "payment_release_count": 0,
            "report_grade_visible": "D",
        },
        "limitations": [
            "S15-P3 只预留 public-safe 绩效事实输出接口契约。",
            "未来读取草案只包含 refs、hash/status 字段和边界 flags，不包含薪酬金额或人员明细。",
            "最终审批、发放和任何薪酬结论必须由人工处理。",
        ],
    }
    manifest["content_hash"] = _sha256_json(
        {
            "manifest": manifest,
            "interface_contract": interface_contract,
            "readiness_rows": readiness_rows,
        }
    )
    validate_performance_salary_boundary_artifacts(manifest, interface_contract, readiness_rows)
    return manifest, interface_contract, readiness_rows


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
        for suffix in FORBIDDEN_PUBLIC_SUFFIXES:
            if text.endswith(suffix):
                hits.append(f"{path}:{suffix}")
    return hits


def _expect_map(container: dict[str, Any], expected: dict[str, Any], path: str) -> None:
    for key, expected_value in expected.items():
        if container.get(key) != expected_value:
            raise PerformanceSalaryBoundaryError(f"{path}.{key} must be {expected_value}")


def validate_performance_salary_boundary_artifacts(
    manifest: dict[str, Any],
    interface_contract: dict[str, Any],
    readiness_rows: list[dict[str, Any]],
) -> None:
    if manifest.get("schema_version") != "kmfa.performance_salary_boundary_manifest.v1":
        raise PerformanceSalaryBoundaryError("manifest schema_version mismatch")
    if manifest.get("stage_phase") != "S15-P3":
        raise PerformanceSalaryBoundaryError("manifest stage_phase must be S15-P3")
    _expect_map(manifest.get("quality_gate", {}), _quality_gate(), "manifest.quality_gate")
    _expect_map(manifest.get("stage_scope", {}), _stage_scope(), "manifest.stage_scope")
    _expect_map(manifest.get("public_repo_safety", {}), _public_repo_safety(), "manifest.public_repo_safety")

    expected_summary = {
        "fact_interface_contract_count": 1,
        "future_salary_system_readiness_row_count": 4,
        "human_approval_boundary_count": 4,
        "pending_review_item_count": 16,
        "salary_calculation_count": 0,
        "wage_calculation_count": 0,
        "bonus_approval_count": 0,
        "payroll_export_count": 0,
        "final_compensation_decision_count": 0,
        "payment_release_count": 0,
        "report_grade_visible": "D",
    }
    for key, expected in expected_summary.items():
        if manifest.get("summary", {}).get(key) != expected:
            raise PerformanceSalaryBoundaryError(f"manifest summary {key} must be {expected}")

    if interface_contract.get("schema_version") != "kmfa.performance_fact_output_interface_contract.v1":
        raise PerformanceSalaryBoundaryError("interface contract schema mismatch")
    if interface_contract.get("record_type") != "performance_fact_output_interface_contract":
        raise PerformanceSalaryBoundaryError("interface contract record_type mismatch")
    if interface_contract.get("stage_phase") != "S15-P3":
        raise PerformanceSalaryBoundaryError("interface contract stage mismatch")
    if tuple(interface_contract.get("fact_interface_fields", [])) != REQUIRED_FACT_INTERFACE_FIELDS:
        raise PerformanceSalaryBoundaryError("interface fact fields mismatch")
    if interface_contract.get("interface_status") != "reserved_contract_only":
        raise PerformanceSalaryBoundaryError("interface must be contract-only")
    for false_key in (
        "api_endpoint_created",
        "file_export_created",
        "connector_enabled",
        "live_read_enabled",
        "scheduled_sync_enabled",
        "external_write_enabled",
        "raw_layer_write_allowed",
        "public_numeric_values_allowed",
        "automatic_compensation_decision_allowed",
    ):
        if interface_contract.get(false_key) is not False:
            raise PerformanceSalaryBoundaryError(f"interface {false_key} must be false")
    for true_key in ("final_approval_must_be_human", "payment_release_must_be_human"):
        if interface_contract.get(true_key) is not True:
            raise PerformanceSalaryBoundaryError(f"interface {true_key} must be true")

    if len(readiness_rows) != 4:
        raise PerformanceSalaryBoundaryError("readiness draft row count must be 4")
    expected_ids = [f"S15P3-READ-{index:03d}" for index in range(1, 5)]
    if [row.get("readiness_row_id") for row in readiness_rows] != expected_ids:
        raise PerformanceSalaryBoundaryError("readiness row ids mismatch")
    for row in readiness_rows:
        row_id = str(row.get("readiness_row_id"))
        if row.get("schema_version") != "kmfa.future_salary_system_readiness_draft.v1":
            raise PerformanceSalaryBoundaryError(f"{row_id} schema mismatch")
        if row.get("record_type") != "future_salary_system_readiness_draft":
            raise PerformanceSalaryBoundaryError(f"{row_id} record type mismatch")
        if row.get("stage_phase") != "S15-P3":
            raise PerformanceSalaryBoundaryError(f"{row_id} stage mismatch")
        if not str(row.get("performance_fact_row_ref", "")).startswith(
            "KMFA/metadata/reports/performance_fact_table.jsonl#S15P2-FACT-"
        ):
            raise PerformanceSalaryBoundaryError(f"{row_id} fact row ref mismatch")
        if not str(row.get("project_ref", "")).startswith("entity_ref://KMFA/S08-P2/project/"):
            raise PerformanceSalaryBoundaryError(f"{row_id} project ref mismatch")
        if set(row.get("available_fact_fields", [])) != set(REQUIRED_FACT_INTERFACE_FIELDS):
            raise PerformanceSalaryBoundaryError(f"{row_id} available fields mismatch")
        if len(row.get("source_review_item_refs", [])) != 4:
            raise PerformanceSalaryBoundaryError(f"{row_id} must reference four review items")
        if row.get("future_read_status") != "draft_only_blocked_until_manual_review_and_human_approval":
            raise PerformanceSalaryBoundaryError(f"{row_id} future read status mismatch")
        for true_key in ("final_approval_must_be_human", "payment_release_must_be_human"):
            if row.get(true_key) is not True:
                raise PerformanceSalaryBoundaryError(f"{row_id} {true_key} must be true")
        for false_key in (
            "raw_business_values_allowed",
            "public_numeric_values_allowed",
            "field_plaintext_allowed",
            "api_endpoint_created",
            "connector_enabled",
            "live_read_enabled",
            "salary_calculation_allowed",
            "wage_calculation_allowed",
            "bonus_approval_allowed",
            "payroll_export_allowed",
            "automatic_compensation_decision_allowed",
            "automatic_payment_allowed",
            "payment_execution_allowed",
            "final_compensation_decision_allowed",
        ):
            if row.get(false_key) is not False:
                raise PerformanceSalaryBoundaryError(f"{row_id} {false_key} must be false")

    public_payload = [manifest, interface_contract, readiness_rows]
    forbidden_key_hits = _walk_forbidden_keys(public_payload)
    if forbidden_key_hits:
        raise PerformanceSalaryBoundaryError("forbidden public keys found: " + ", ".join(forbidden_key_hits))
    forbidden_text_hits = _walk_forbidden_text(public_payload)
    if forbidden_text_hits:
        raise PerformanceSalaryBoundaryError("forbidden public text found: " + ", ".join(forbidden_text_hits))


def write_default_performance_salary_boundary_artifacts(
    *,
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    output_interface_contract: Path = DEFAULT_OUTPUT_INTERFACE_CONTRACT,
    output_readiness_draft: Path = DEFAULT_OUTPUT_READINESS_DRAFT,
    output_stage_manifest: Path = DEFAULT_OUTPUT_STAGE_MANIFEST,
    generated_at: str = "2026-07-01T23:55:00+10:00",
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    manifest, interface_contract, readiness_rows = build_default_performance_salary_boundary_artifacts(
        generated_at=generated_at
    )
    write_json(output_manifest, manifest)
    write_json(output_interface_contract, interface_contract)
    write_jsonl(output_readiness_draft, readiness_rows)
    stage_manifest = {
        "schema_version": "kmfa.s15_p3_stage_manifest.v1",
        "record_type": "s15_p3_salary_boundary_stage_manifest",
        "project_id": "KMFA",
        "stage_phase": "S15-P3",
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
    return manifest, interface_contract, readiness_rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S15-P3 performance salary boundary artifacts.")
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-interface-contract", type=Path, default=DEFAULT_OUTPUT_INTERFACE_CONTRACT)
    parser.add_argument("--output-readiness-draft", type=Path, default=DEFAULT_OUTPUT_READINESS_DRAFT)
    parser.add_argument("--output-stage-manifest", type=Path, default=DEFAULT_OUTPUT_STAGE_MANIFEST)
    parser.add_argument("--generated-at", default="2026-07-01T23:55:00+10:00")
    args = parser.parse_args(argv)

    manifest, interface_contract, readiness_rows = write_default_performance_salary_boundary_artifacts(
        output_manifest=args.output_manifest,
        output_interface_contract=args.output_interface_contract,
        output_readiness_draft=args.output_readiness_draft,
        output_stage_manifest=args.output_stage_manifest,
        generated_at=args.generated_at,
    )
    summary = manifest["summary"]
    print(
        "PASS: KMFA S15-P3 salary boundary artifacts generated "
        f"(interface_contracts={summary['fact_interface_contract_count']}, "
        f"readiness_rows={len(readiness_rows)}, "
        "future_read_draft=true, live_integration=false, "
        "salary_calculation=false, bonus_approval=false, payroll_export=false, "
        "human_approval_required=true, payment_release_human=true, "
        "stage15_review=false, github_upload=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
