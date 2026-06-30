#!/usr/bin/env python3
"""Build KMFA S09-P3 public-safe scope reconciliation metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_MARGIN_MANIFEST = ROOT / "metadata" / "reports" / "project_margin_cash_margin_manifest.json"
DEFAULT_MARGIN_RECORDS = ROOT / "metadata" / "lineage" / "project_margin_cash_margin_records.jsonl"
DEFAULT_SCOPE_DIFFERENCE_SUMMARY = ROOT / "metadata" / "quality" / "scope_difference_summary.jsonl"
DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "project_scope_reconciliation_manifest.json"
DEFAULT_OUTPUT_RECONCILIATION_RECORDS = ROOT / "metadata" / "quality" / "scope_reconciliation_records.jsonl"
DEFAULT_OUTPUT_DOMAIN_CONTROLS = ROOT / "metadata" / "quality" / "scope_reconciliation_domain_controls.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S09_P3_scope_reconciliation" / "machine" / "s09_p3_manifest.json"
)

REQUIRED_RECONCILIATION_DOMAINS = (
    "contract_vs_project_revenue",
    "project_cost_vs_finance_expense",
    "bank_collection_vs_receivable_aging",
    "invoice_vs_contract_settlement_tax",
    "rd_expense_vs_project_personnel_evidence",
    "authority_pdf_excel_vs_system_recomputed",
)

REQUIRED_HUMAN_FIELDS = (
    "reason_candidate",
    "basis_evidence_refs",
    "impact_scope",
    "resolution_status",
    "responsible_owner_role",
    "reviewer",
    "created_at",
    "closed_at",
)

DIFFERENCE_TYPE_MAPPING = {
    "authority_vs_system_gross_profit": {
        "domain": "authority_pdf_excel_vs_system_recomputed",
        "source_a": "source_ref://KMFA/S05-P3/authority_q5_baseline",
        "source_b": "source_ref://KMFA/S09-P2/system_recomputed_margin",
        "field_name": "gross_profit",
        "reason_candidate": "authority baseline and system recomputation require owner-readable scope bridge",
        "impact_scope": "project_margin_formal_report_blocked_until_reconciled",
    },
    "authority_vs_system_gross_margin_rate": {
        "domain": "authority_pdf_excel_vs_system_recomputed",
        "source_a": "source_ref://KMFA/S05-P3/authority_q5_baseline",
        "source_b": "source_ref://KMFA/S09-P2/system_recomputed_margin_rate",
        "field_name": "gross_margin_rate",
        "reason_candidate": "authority display rate and system recomputed rate require denominator and scope review",
        "impact_scope": "project_margin_rate_formal_report_blocked_until_reconciled",
    },
    "cash_vs_accrual_gross_profit": {
        "domain": "bank_collection_vs_receivable_aging",
        "source_a": "source_ref://KMFA/S09-P2/cash_margin",
        "source_b": "source_ref://KMFA/S09-P2/accrual_margin",
        "field_name": "cash_gross_profit",
        "reason_candidate": "cash and accrual margin timing requires bank and receivable aging review",
        "impact_scope": "cash_margin_formal_report_blocked_until_reconciled",
    },
}

DOMAIN_CONTROL_SPECS = {
    "contract_vs_project_revenue": {
        "source_a": "source_ref://KMFA/S05-P3/authority_contract_amount",
        "source_b": "source_ref://KMFA/S09-P1/project_revenue",
        "field_name": "contract_amount_to_project_revenue",
        "reason_candidate": "contract amount and project revenue need scope mapping before report release",
    },
    "project_cost_vs_finance_expense": {
        "source_a": "source_ref://KMFA/S09-P1/project_cost_total",
        "source_b": "source_ref://KMFA/S07-P1/finance_expense_support",
        "field_name": "project_cost_to_finance_expense",
        "reason_candidate": "project cost and finance expense support need voucher or expense detail review",
    },
    "bank_collection_vs_receivable_aging": {
        "source_a": "source_ref://KMFA/S09-P1/collection_amount",
        "source_b": "source_ref://KMFA/S07-P2/receivable_aging_support",
        "field_name": "bank_collection_to_receivable_aging",
        "reason_candidate": "bank collection and receivable aging need timing and settlement review",
    },
    "invoice_vs_contract_settlement_tax": {
        "source_a": "source_ref://KMFA/S09-P1/invoice_amount",
        "source_b": "source_ref://KMFA/S07-P1/tax_invoice_support",
        "field_name": "invoice_to_contract_settlement_tax",
        "reason_candidate": "invoice amount, contract settlement and tax evidence need cross-check",
    },
    "rd_expense_vs_project_personnel_evidence": {
        "source_a": "source_ref://KMFA/S07-P1/rd_expense_support",
        "source_b": "source_ref://KMFA/S08-P2/project_personnel_evidence_entity",
        "field_name": "rd_expense_to_project_personnel_evidence",
        "reason_candidate": "research expense needs project, personnel and deliverable evidence review",
    },
    "authority_pdf_excel_vs_system_recomputed": {
        "source_a": "source_ref://KMFA/S05-P3/authority_pdf_excel_baseline",
        "source_b": "source_ref://KMFA/S09-P2/system_recomputed_margin",
        "field_name": "authority_to_system_margin",
        "reason_candidate": "authority PDF or Excel support and system recomputation need reconciliation bridge",
    },
}

FORBIDDEN_PUBLIC_KEYS = {
    "amount_a_cents",
    "amount_b_cents",
    "delta_cents",
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

FORBIDDEN_PUBLIC_SUFFIXES = (".zip", ".xls", ".xlsx", ".pdf", ".sqlite", ".db")
HASH_RE = re.compile(r"^sha256:[a-f0-9]{64}$")


class ProjectScopeReconciliationError(ValueError):
    """Raised when S09-P3 scope reconciliation artifacts are invalid."""


def require_text(value: Any, field_name: str) -> str:
    if value is None:
        raise ProjectScopeReconciliationError(f"{field_name} is required")
    text = str(value).strip()
    if not text:
        raise ProjectScopeReconciliationError(f"{field_name} is required")
    return text


def _sha256_for(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def _public_repo_safety() -> dict[str, bool]:
    return {
        "raw_business_values_committed": False,
        "normalized_business_values_committed": False,
        "field_plaintext_committed": False,
        "raw_file_committed": False,
        "private_tabular_files_committed": False,
    }


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ProjectScopeReconciliationError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ProjectScopeReconciliationError(f"{path} contains a non-object JSONL record")
            records.append(value)
    return records


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def read_json(path: Path) -> dict[str, Any]:
    return _read_json(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return _read_jsonl(path)


def _source_refs_for_record(summary_item: dict[str, Any], mapping: dict[str, str]) -> tuple[str, str]:
    source_a = require_text(mapping.get("source_a"), "source_a")
    source_b = require_text(mapping.get("source_b"), "source_b")
    if summary_item.get("authority_source_ref"):
        source_a = require_text(summary_item.get("authority_source_ref"), "authority_source_ref")
    if summary_item.get("system_source_ref"):
        source_b = require_text(summary_item.get("system_source_ref"), "system_source_ref")
    return source_a, source_b


def _build_reconciliation_records(
    scope_difference_summary: list[dict[str, Any]],
    *,
    generated_at: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, summary_item in enumerate(scope_difference_summary, start=1):
        difference_type = require_text(summary_item.get("difference_type"), "difference_type")
        mapping = DIFFERENCE_TYPE_MAPPING.get(difference_type)
        if mapping is None:
            raise ProjectScopeReconciliationError(f"unsupported S09-P2 difference_type: {difference_type}")
        difference_id = f"S09P3-REC-{index:03d}"
        source_a, source_b = _source_refs_for_record(summary_item, mapping)
        records.append(
            {
                "schema_version": "kmfa.scope_reconciliation_record.v1",
                "record_type": "scope_reconciliation_record",
                "project_id": "KMFA",
                "stage_phase": "S09-P3",
                "difference_id": difference_id,
                "source_difference_summary_id": require_text(summary_item.get("summary_id"), "summary_id"),
                "source_difference_summary_ref": (
                    "KMFA/metadata/quality/scope_difference_summary.jsonl#"
                    + require_text(summary_item.get("summary_id"), "summary_id")
                ),
                "margin_record_id": require_text(summary_item.get("margin_record_id"), "margin_record_id"),
                "reconciliation_domain": require_text(mapping.get("domain"), "reconciliation_domain"),
                "source_a": source_a,
                "source_b": source_b,
                "field_name": require_text(mapping.get("field_name"), "field_name"),
                "amount_a_cents_private_ref": f"private_ref://KMFA/S09-P3/{difference_id}/amount-a-cents",
                "amount_b_cents_private_ref": f"private_ref://KMFA/S09-P3/{difference_id}/amount-b-cents",
                "delta_cents_private_ref": f"private_ref://KMFA/S09-P3/{difference_id}/delta-cents",
                "amount_a_cents_hash": _sha256_for(f"S09-P3:{difference_id}:amount-a-cents"),
                "amount_b_cents_hash": _sha256_for(f"S09-P3:{difference_id}:amount-b-cents"),
                "delta_cents_hash": _sha256_for(f"S09-P3:{difference_id}:delta-cents"),
                "reason_candidate": require_text(mapping.get("reason_candidate"), "reason_candidate"),
                "basis_evidence_refs": [
                    "KMFA/metadata/quality/scope_difference_summary.jsonl",
                    "KMFA/metadata/lineage/project_margin_cash_margin_records.jsonl",
                    "KMFA/metadata/reports/project_margin_cash_margin_manifest.json",
                    "KMFA/metadata/quality/source_difference_queue.jsonl",
                    "KMFA/metadata/quality/entity_matching_review_queue.jsonl",
                ],
                "impact_scope": require_text(mapping.get("impact_scope"), "impact_scope"),
                "resolution_status": "pending_owner_or_authorized_review",
                "responsible_owner_role": "owner_or_authorized_delegate",
                "reviewer": "pending_owner_or_authorized_delegate",
                "created_at": generated_at,
                "closed_at": None,
                "confirmed_for_rerun": False,
                "derived_metric_rerun_allowed": False,
                "formal_report_rerun_allowed": False,
                "rerun_policy": "blocked_until_all_required_differences_confirmed",
                "human_readable_status": "pending_review_reason_basis_owner_status_recorded",
                "public_amount_values_committed": False,
                "raw_layer_write_allowed": False,
                "evidence_ref": "KMFA/stage_artifacts/S09_P3_scope_reconciliation/human/test_results.md",
                "public_repo_safety": _public_repo_safety(),
            }
        )
    return records


def _build_domain_controls(*, generated_at: str) -> list[dict[str, Any]]:
    controls: list[dict[str, Any]] = []
    for index, domain in enumerate(REQUIRED_RECONCILIATION_DOMAINS, start=1):
        spec = DOMAIN_CONTROL_SPECS[domain]
        control_id = f"S09P3-DOMAIN-{index:03d}"
        controls.append(
            {
                "schema_version": "kmfa.scope_reconciliation_domain_control.v1",
                "record_type": "scope_reconciliation_domain_control",
                "project_id": "KMFA",
                "stage_phase": "S09-P3",
                "domain_control_id": control_id,
                "reconciliation_domain": domain,
                "source_a": spec["source_a"],
                "source_b": spec["source_b"],
                "field_name": spec["field_name"],
                "reason_candidate": spec["reason_candidate"],
                "basis_evidence_refs": [
                    "KMFA/metadata/imports/finance_support_source_registry.json",
                    "KMFA/metadata/imports/wps_export_source_registry.json",
                    "KMFA/metadata/reports/project_cost_fact_layer_manifest.json",
                    "KMFA/metadata/reports/project_margin_cash_margin_manifest.json",
                    "KMFA/metadata/quality/scope_difference_summary.jsonl",
                ],
                "impact_scope": "stage9_review_and_formal_report_blocked_until_domain_reviewed",
                "resolution_status": "pending_owner_or_authorized_review",
                "control_status": "active_pending_difference_review",
                "responsible_owner_role": "owner_or_authorized_delegate",
                "reviewer": "pending_owner_or_authorized_delegate",
                "created_at": generated_at,
                "closed_at": None,
                "domain_confirmed_for_rerun": False,
                "derived_metric_rerun_allowed": False,
                "formal_report_rerun_allowed": False,
                "public_amount_values_committed": False,
                "raw_layer_write_allowed": False,
                "public_repo_safety": _public_repo_safety(),
            }
        )
    return controls


def build_default_project_scope_reconciliation_layer(
    *, generated_at: str
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    generated_at_value = require_text(generated_at, "generated_at")
    margin_manifest = _read_json(DEFAULT_MARGIN_MANIFEST)
    margin_records = _read_jsonl(DEFAULT_MARGIN_RECORDS)
    scope_difference_summary = _read_jsonl(DEFAULT_SCOPE_DIFFERENCE_SUMMARY)
    reconciliation_records = _build_reconciliation_records(scope_difference_summary, generated_at=generated_at_value)
    domain_controls = _build_domain_controls(generated_at=generated_at_value)

    manifest = {
        "schema_version": "kmfa.scope_reconciliation_manifest.v1",
        "record_type": "project_scope_reconciliation_manifest",
        "project_id": "KMFA",
        "stage_phase": "S09-P3",
        "generated_at": generated_at_value,
        "formula_version": "FORM-KMFA-SCOPE-RECONCILIATION-001",
        "mapping_version": "MAP-KMFA-S09P3-PUBLIC-SAFE-v1",
        "reconciliation_status": "public_safe_reconciliation_records_created_pending_owner_confirmation",
        "required_reconciliation_domains": list(REQUIRED_RECONCILIATION_DOMAINS),
        "required_human_fields": list(REQUIRED_HUMAN_FIELDS),
        "summary": {
            "upstream_margin_record_count": len(margin_records),
            "source_difference_summary_count": len(scope_difference_summary),
            "reconciliation_record_count": len(reconciliation_records),
            "domain_control_count": len(domain_controls),
            "confirmed_resolution_count": 0,
            "pending_resolution_count": len(reconciliation_records),
        },
        "upstream_refs": {
            "project_margin_cash_margin_manifest": "KMFA/metadata/reports/project_margin_cash_margin_manifest.json",
            "project_margin_cash_margin_records": "KMFA/metadata/lineage/project_margin_cash_margin_records.jsonl",
            "scope_difference_summary": "KMFA/metadata/quality/scope_difference_summary.jsonl",
            "source_difference_queue": "KMFA/metadata/quality/source_difference_queue.jsonl",
            "entity_matching_review_queue": "KMFA/metadata/quality/entity_matching_review_queue.jsonl",
        },
        "upstream_status": {
            "s09_p2_margin_record_count": margin_manifest.get("summary", {}).get("margin_record_count"),
            "s09_p2_difference_summary_count": margin_manifest.get("summary", {}).get("difference_summary_count"),
            "s09_p2_formal_report_allowed": margin_manifest.get("quality_gate", {}).get("formal_report_allowed"),
            "s09_p2_github_upload_allowed": margin_manifest.get("quality_gate", {}).get("github_upload_allowed"),
        },
        "rerun_policy": {
            "derived_metric_rerun_allowed": False,
            "formal_report_rerun_allowed": False,
            "requires_all_differences_confirmed": True,
            "requires_owner_or_authorized_review": True,
            "current_blocker": "pending_owner_or_authorized_difference_review",
        },
        "stage_scope": {
            "s09_p1_project_cost_fact_layer_scope_included": False,
            "s09_p2_margin_cash_margin_scope_included": False,
            "s09_p3_scope_difference_reconciliation_scope_included": True,
            "stage9_review_scope_included": False,
            "lineage_full_check_scope_included": False,
            "formal_report_scope_included": False,
            "ui_scope_included": False,
            "external_connector_scope_included": False,
        },
        "quality_gate": {
            "formal_report_allowed": False,
            "github_upload_allowed": False,
            "phase_completion_upload_allowed": False,
            "derived_metric_rerun_allowed": False,
            "formal_report_rerun_allowed": False,
            "stage9_review_allowed": False,
            "raw_layer_write_allowed": False,
            "automatic_external_action_allowed": False,
        },
        "artifact_refs": {
            "scope_reconciliation_manifest": "KMFA/metadata/reports/project_scope_reconciliation_manifest.json",
            "scope_reconciliation_records": "KMFA/metadata/quality/scope_reconciliation_records.jsonl",
            "scope_reconciliation_domain_controls": (
                "KMFA/metadata/quality/scope_reconciliation_domain_controls.jsonl"
            ),
            "stage_manifest": "KMFA/stage_artifacts/S09_P3_scope_reconciliation/machine/s09_p3_manifest.json",
            "completion_record": "KMFA/stage_artifacts/S09_P3_scope_reconciliation/human/s09_p3_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S09_P3_scope_reconciliation/human/test_results.md",
            "validator": "KMFA/tools/check_s09_p3_scope_reconciliation.py",
        },
        "public_repo_safety": _public_repo_safety(),
    }
    validate_project_scope_reconciliation_artifacts(manifest, reconciliation_records, domain_controls)
    return manifest, reconciliation_records, domain_controls


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


def _walk_forbidden_suffixes(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            hits.extend(_walk_forbidden_suffixes(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(_walk_forbidden_suffixes(child, f"{path}[{index}]"))
    elif isinstance(value, str) and value.lower().endswith(FORBIDDEN_PUBLIC_SUFFIXES):
        hits.append(path)
    return hits


def _require_false(container: dict[str, Any], path: str) -> None:
    for key, value in container.items():
        if value is not False:
            raise ProjectScopeReconciliationError(f"{path}.{key} must be false")


def _require_hash(value: Any, path: str) -> None:
    if not isinstance(value, str) or not HASH_RE.match(value):
        raise ProjectScopeReconciliationError(f"{path} must be sha256")


def _require_private_ref(value: Any, path: str) -> None:
    if not isinstance(value, str) or not value.startswith("private_ref://"):
        raise ProjectScopeReconciliationError(f"{path} must be private_ref")


def _validate_human_fields(record: dict[str, Any], path: str) -> None:
    for field_name in REQUIRED_HUMAN_FIELDS:
        if field_name not in record:
            raise ProjectScopeReconciliationError(f"{path}.{field_name} is required")
    if not record["reason_candidate"]:
        raise ProjectScopeReconciliationError(f"{path}.reason_candidate is required")
    if not isinstance(record["basis_evidence_refs"], list) or not record["basis_evidence_refs"]:
        raise ProjectScopeReconciliationError(f"{path}.basis_evidence_refs must be non-empty")
    if not record["impact_scope"]:
        raise ProjectScopeReconciliationError(f"{path}.impact_scope is required")
    if not record["responsible_owner_role"]:
        raise ProjectScopeReconciliationError(f"{path}.responsible_owner_role is required")
    if not record["reviewer"]:
        raise ProjectScopeReconciliationError(f"{path}.reviewer is required")
    if not record["created_at"]:
        raise ProjectScopeReconciliationError(f"{path}.created_at is required")


def validate_project_scope_reconciliation_artifacts(
    manifest: dict[str, Any],
    reconciliation_records: list[dict[str, Any]],
    domain_controls: list[dict[str, Any]],
) -> None:
    if manifest.get("schema_version") != "kmfa.scope_reconciliation_manifest.v1":
        raise ProjectScopeReconciliationError("invalid S09-P3 manifest schema_version")
    if manifest.get("stage_phase") != "S09-P3":
        raise ProjectScopeReconciliationError("S09-P3 manifest stage_phase mismatch")
    if tuple(manifest.get("required_reconciliation_domains", [])) != REQUIRED_RECONCILIATION_DOMAINS:
        raise ProjectScopeReconciliationError("S09-P3 required reconciliation domains mismatch")
    if tuple(manifest.get("required_human_fields", [])) != REQUIRED_HUMAN_FIELDS:
        raise ProjectScopeReconciliationError("S09-P3 required human fields mismatch")

    summary = manifest.get("summary", {})
    if summary.get("reconciliation_record_count") != len(reconciliation_records):
        raise ProjectScopeReconciliationError("S09-P3 reconciliation record count mismatch")
    if summary.get("domain_control_count") != len(domain_controls):
        raise ProjectScopeReconciliationError("S09-P3 domain control count mismatch")
    if summary.get("domain_control_count") != len(REQUIRED_RECONCILIATION_DOMAINS):
        raise ProjectScopeReconciliationError("S09-P3 must cover all required domains")
    if summary.get("confirmed_resolution_count") != 0:
        raise ProjectScopeReconciliationError("S09-P3 cannot pre-confirm unresolved differences")
    if summary.get("pending_resolution_count") != len(reconciliation_records):
        raise ProjectScopeReconciliationError("S09-P3 pending resolution count mismatch")

    stage_scope = manifest.get("stage_scope", {})
    if stage_scope.get("s09_p3_scope_difference_reconciliation_scope_included") is not True:
        raise ProjectScopeReconciliationError("S09-P3 scope must be included")
    for excluded_scope in (
        "s09_p1_project_cost_fact_layer_scope_included",
        "s09_p2_margin_cash_margin_scope_included",
        "stage9_review_scope_included",
        "lineage_full_check_scope_included",
        "formal_report_scope_included",
        "ui_scope_included",
        "external_connector_scope_included",
    ):
        if stage_scope.get(excluded_scope) is not False:
            raise ProjectScopeReconciliationError(f"S09-P3 must exclude {excluded_scope}")
    _require_false(manifest.get("quality_gate", {}), "manifest.quality_gate")
    _require_false(manifest.get("public_repo_safety", {}), "manifest.public_repo_safety")

    seen_domains = {control.get("reconciliation_domain") for control in domain_controls}
    if seen_domains != set(REQUIRED_RECONCILIATION_DOMAINS):
        raise ProjectScopeReconciliationError("S09-P3 domain controls do not cover all domains")

    for record in reconciliation_records:
        record_id = require_text(record.get("difference_id"), "difference_id")
        if record.get("schema_version") != "kmfa.scope_reconciliation_record.v1":
            raise ProjectScopeReconciliationError(f"{record_id} schema_version mismatch")
        if record.get("record_type") != "scope_reconciliation_record":
            raise ProjectScopeReconciliationError(f"{record_id} record_type mismatch")
        if record.get("stage_phase") != "S09-P3":
            raise ProjectScopeReconciliationError(f"{record_id} stage_phase mismatch")
        if record.get("reconciliation_domain") not in REQUIRED_RECONCILIATION_DOMAINS:
            raise ProjectScopeReconciliationError(f"{record_id} invalid reconciliation_domain")
        for required_text_field in ("source_a", "source_b", "field_name"):
            require_text(record.get(required_text_field), f"{record_id}.{required_text_field}")
        _require_private_ref(record.get("amount_a_cents_private_ref"), f"{record_id}.amount_a_cents_private_ref")
        _require_private_ref(record.get("amount_b_cents_private_ref"), f"{record_id}.amount_b_cents_private_ref")
        _require_private_ref(record.get("delta_cents_private_ref"), f"{record_id}.delta_cents_private_ref")
        _require_hash(record.get("amount_a_cents_hash"), f"{record_id}.amount_a_cents_hash")
        _require_hash(record.get("amount_b_cents_hash"), f"{record_id}.amount_b_cents_hash")
        _require_hash(record.get("delta_cents_hash"), f"{record_id}.delta_cents_hash")
        _validate_human_fields(record, record_id)
        if record.get("resolution_status") != "pending_owner_or_authorized_review":
            raise ProjectScopeReconciliationError(f"{record_id} must remain pending review")
        if record.get("closed_at") is not None:
            raise ProjectScopeReconciliationError(f"{record_id} closed_at must remain null")
        for false_key in (
            "confirmed_for_rerun",
            "derived_metric_rerun_allowed",
            "formal_report_rerun_allowed",
            "public_amount_values_committed",
            "raw_layer_write_allowed",
        ):
            if record.get(false_key) is not False:
                raise ProjectScopeReconciliationError(f"{record_id}.{false_key} must be false")
        _require_false(record.get("public_repo_safety", {}), f"{record_id}.public_repo_safety")

    for control in domain_controls:
        control_id = require_text(control.get("domain_control_id"), "domain_control_id")
        if control.get("schema_version") != "kmfa.scope_reconciliation_domain_control.v1":
            raise ProjectScopeReconciliationError(f"{control_id} schema_version mismatch")
        if control.get("record_type") != "scope_reconciliation_domain_control":
            raise ProjectScopeReconciliationError(f"{control_id} record_type mismatch")
        if control.get("stage_phase") != "S09-P3":
            raise ProjectScopeReconciliationError(f"{control_id} stage_phase mismatch")
        if control.get("control_status") != "active_pending_difference_review":
            raise ProjectScopeReconciliationError(f"{control_id} control_status mismatch")
        _validate_human_fields(control, control_id)
        for false_key in (
            "domain_confirmed_for_rerun",
            "derived_metric_rerun_allowed",
            "formal_report_rerun_allowed",
            "public_amount_values_committed",
            "raw_layer_write_allowed",
        ):
            if control.get(false_key) is not False:
                raise ProjectScopeReconciliationError(f"{control_id}.{false_key} must be false")
        _require_false(control.get("public_repo_safety", {}), f"{control_id}.public_repo_safety")

    forbidden_hits = _walk_forbidden_keys([manifest, reconciliation_records, domain_controls])
    if forbidden_hits:
        raise ProjectScopeReconciliationError("forbidden public keys found: " + ", ".join(forbidden_hits))
    suffix_hits = _walk_forbidden_suffixes([manifest, reconciliation_records, domain_controls])
    if suffix_hits:
        raise ProjectScopeReconciliationError("forbidden raw/sensitive suffix refs found: " + ", ".join(suffix_hits))


def write_default_artifacts(generated_at: str) -> dict[str, Any]:
    manifest, records, domain_controls = build_default_project_scope_reconciliation_layer(generated_at=generated_at)
    _write_json(DEFAULT_OUTPUT_MANIFEST, manifest)
    _write_jsonl(DEFAULT_OUTPUT_RECONCILIATION_RECORDS, records)
    _write_jsonl(DEFAULT_OUTPUT_DOMAIN_CONTROLS, domain_controls)
    stage_manifest = {
        "schema_version": "kmfa.s09_p3_manifest.v1",
        "record_type": "s09_p3_scope_reconciliation_manifest",
        "project_id": "KMFA",
        "stage_phase": "S09-P3",
        "generated_at": generated_at,
        "scope_reconciliation_manifest_ref": "KMFA/metadata/reports/project_scope_reconciliation_manifest.json",
        "scope_reconciliation_records_ref": "KMFA/metadata/quality/scope_reconciliation_records.jsonl",
        "scope_reconciliation_domain_controls_ref": (
            "KMFA/metadata/quality/scope_reconciliation_domain_controls.jsonl"
        ),
        "completion_record_ref": "KMFA/stage_artifacts/S09_P3_scope_reconciliation/human/s09_p3_completion_record.md",
        "test_results_ref": "KMFA/stage_artifacts/S09_P3_scope_reconciliation/human/test_results.md",
        "validator_ref": "KMFA/tools/check_s09_p3_scope_reconciliation.py",
        "reconciliation_record_count": manifest["summary"]["reconciliation_record_count"],
        "domain_control_count": manifest["summary"]["domain_control_count"],
        "confirmed_resolution_count": manifest["summary"]["confirmed_resolution_count"],
        "pending_resolution_count": manifest["summary"]["pending_resolution_count"],
        "derived_metric_rerun_allowed": False,
        "formal_report_allowed": False,
        "github_upload_allowed": False,
        "stage9_review_allowed": False,
        "raw_layer_write_allowed": False,
    }
    _write_json(DEFAULT_OUTPUT_STAGE_MANIFEST, stage_manifest)
    return stage_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S09-P3 public-safe scope reconciliation artifacts.")
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)

    manifest, records, domain_controls = build_default_project_scope_reconciliation_layer(
        generated_at=args.generated_at
    )
    if not args.check_only:
        stage_manifest = write_default_artifacts(args.generated_at)
    else:
        stage_manifest = {
            "reconciliation_record_count": manifest["summary"]["reconciliation_record_count"],
            "domain_control_count": manifest["summary"]["domain_control_count"],
            "confirmed_resolution_count": manifest["summary"]["confirmed_resolution_count"],
            "pending_resolution_count": manifest["summary"]["pending_resolution_count"],
        }
    print(
        "PASS: KMFA S09-P3 scope reconciliation artifacts "
        f"{'validated' if args.check_only else 'written'} "
        f"(reconciliation_records={stage_manifest['reconciliation_record_count']}, "
        f"domain_controls={stage_manifest['domain_control_count']}, "
        f"confirmed_resolutions={stage_manifest['confirmed_resolution_count']}, "
        f"pending_resolutions={stage_manifest['pending_resolution_count']}, "
        "derived_metric_rerun_allowed=false, formal_report_allowed=false, "
        "stage9_review_allowed=false, github_upload_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
