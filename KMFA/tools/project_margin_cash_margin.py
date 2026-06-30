#!/usr/bin/env python3
"""Build KMFA S09-P2 public-safe margin and cash margin metadata.

S09-P2 defines the integer-cent calculation contract for authoritative gross
profit, system recomputed gross profit, cash gross profit, and gross margin
rate. Public artifacts keep private refs, result hashes, formulas, status, and
difference summary records only; they do not commit business amount values or
perform S09-P3 reconciliation, Stage 9 review, formal report, UI, connector, or
GitHub upload work.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_FACT_LAYER_MANIFEST = ROOT / "metadata" / "reports" / "project_cost_fact_layer_manifest.json"
DEFAULT_FACT_RECORDS = ROOT / "metadata" / "lineage" / "project_cost_fact_records.jsonl"
DEFAULT_AUTHORITY_RECORDS = ROOT / "metadata" / "baseline" / "a0_authority_baseline_records.jsonl"
DEFAULT_OUTPUT_MANIFEST = ROOT / "metadata" / "reports" / "project_margin_cash_margin_manifest.json"
DEFAULT_OUTPUT_MARGIN_RECORDS = ROOT / "metadata" / "lineage" / "project_margin_cash_margin_records.jsonl"
DEFAULT_OUTPUT_DIFFERENCE_SUMMARY = ROOT / "metadata" / "quality" / "scope_difference_summary.jsonl"
DEFAULT_OUTPUT_STAGE_MANIFEST = (
    ROOT / "stage_artifacts" / "S09_P2_margin_cash_margin" / "machine" / "s09_p2_manifest.json"
)

REQUIRED_MARGIN_METRICS = (
    "authority_gross_profit",
    "system_recomputed_gross_profit",
    "cash_gross_profit",
    "gross_margin_rate",
)

AUTHORITY_REQUIRED_FIELDS = (
    "gross_profit",
    "gross_margin",
)

DIFFERENCE_TYPES = (
    "authority_vs_system_gross_profit",
    "authority_vs_system_gross_margin_rate",
    "cash_vs_accrual_gross_profit",
)

FORBIDDEN_PUBLIC_KEYS = {
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


class ProjectMarginCashMarginError(ValueError):
    """Raised when S09-P2 margin and cash margin artifacts are invalid."""


def require_text(value: Any, field_name: str) -> str:
    if value is None:
        raise ProjectMarginCashMarginError(f"{field_name} is required")
    text = str(value).strip()
    if not text:
        raise ProjectMarginCashMarginError(f"{field_name} is required")
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
        raise ProjectMarginCashMarginError(f"{path} must contain a JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ProjectMarginCashMarginError(f"{path} contains a non-object JSONL record")
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


def _divide_to_basis_points(numerator_cents: int, denominator_cents: int) -> int | None:
    if denominator_cents == 0:
        return None
    sign = -1 if numerator_cents < 0 else 1
    numerator_abs = abs(numerator_cents) * 10_000
    denominator_abs = abs(denominator_cents)
    return sign * ((numerator_abs + denominator_abs // 2) // denominator_abs)


def calculate_margin_metrics(
    *,
    revenue_cents: int,
    management_project_cost_cents: int,
    collection_amount_cents: int,
    cash_paid_cost_cents: int,
) -> dict[str, int | None]:
    """Calculate S09-P2 metrics with integer cents and basis points only."""

    for field_name, value in (
        ("revenue_cents", revenue_cents),
        ("management_project_cost_cents", management_project_cost_cents),
        ("collection_amount_cents", collection_amount_cents),
        ("cash_paid_cost_cents", cash_paid_cost_cents),
    ):
        if not isinstance(value, int):
            raise ProjectMarginCashMarginError(f"{field_name} must be integer cents")

    system_recomputed_gross_profit_cents = revenue_cents - management_project_cost_cents
    cash_gross_profit_cents = collection_amount_cents - cash_paid_cost_cents
    gross_margin_rate_basis_points = _divide_to_basis_points(system_recomputed_gross_profit_cents, revenue_cents)
    return {
        "system_recomputed_gross_profit_cents": system_recomputed_gross_profit_cents,
        "cash_gross_profit_cents": cash_gross_profit_cents,
        "gross_margin_rate_basis_points": gross_margin_rate_basis_points,
    }


def _authority_field_groups(authority_records: list[dict[str, Any]]) -> list[dict[str, dict[str, Any]]]:
    groups: dict[str, dict[str, dict[str, Any]]] = {}
    for record in authority_records:
        if record.get("lock_status") != "q5_locked_public_safe_hash_baseline":
            continue
        candidate_id = record.get("candidate_id")
        field_key = record.get("field_key")
        if not candidate_id or field_key not in {
            "contract_amount",
            "total_expense",
            "gross_profit",
            "gross_margin",
        }:
            continue
        groups.setdefault(str(candidate_id), {})[str(field_key)] = record

    complete_groups = [
        group
        for _, group in sorted(groups.items())
        if all(field_key in group for field_key in ("contract_amount", "total_expense", *AUTHORITY_REQUIRED_FIELDS))
    ]
    if not complete_groups:
        raise ProjectMarginCashMarginError("no complete S05-P3 authority field groups found")
    return complete_groups


def _authority_ref(group: dict[str, dict[str, Any]], field_key: str) -> str:
    value_lock = group[field_key].get("value_lock", {})
    return require_text(value_lock.get("normalized_value_private_ref"), f"authority {field_key} private ref").replace(
        "private://", "private_ref://", 1
    )


def _authority_hash(group: dict[str, dict[str, Any]], field_key: str) -> str:
    value_lock = group[field_key].get("value_lock", {})
    return require_text(value_lock.get("normalized_value_hash"), f"authority {field_key} hash")


def _hash_ref_map(record_id: str, namespace: str, keys: tuple[str, ...]) -> dict[str, str]:
    return {key: _sha256_for(f"S09-P2:{record_id}:{namespace}:{key}") for key in keys}


def _private_ref_map(record_id: str, namespace: str, keys: tuple[str, ...]) -> dict[str, str]:
    return {key: f"private_ref://KMFA/S09-P2/{record_id}/{namespace}/{key}" for key in keys}


def _build_margin_records(
    fact_records: list[dict[str, Any]],
    authority_groups: list[dict[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, fact_record in enumerate(fact_records, start=1):
        record_id = f"PCM-S09P2-{index:03d}"
        authority_group = authority_groups[(index - 1) % len(authority_groups)]
        system_keys = ("gross_profit", "gross_margin_rate")
        cash_keys = ("cash_gross_profit", "cash_paid_cost")
        records.append(
            {
                "schema_version": "kmfa.project_margin_cash_margin_record.v1",
                "record_type": "project_margin_cash_margin_record",
                "project_id": "KMFA",
                "stage_phase": "S09-P2",
                "margin_record_id": record_id,
                "project_cost_fact_record_id": require_text(fact_record.get("fact_record_id"), "fact_record_id"),
                "project_cost_fact_record_ref": (
                    "KMFA/metadata/lineage/project_cost_fact_records.jsonl#"
                    + require_text(fact_record.get("fact_record_id"), "fact_record_id")
                ),
                "project_identity_profile_ref": fact_record.get("project_identity_profile_ref"),
                "project_entity_ref": fact_record.get("project_entity_ref"),
                "margin_metric_slots": list(REQUIRED_MARGIN_METRICS),
                "formula_refs": {
                    "authority_gross_profit": "FORM-KMFA-MARGIN-CASH-MARGIN-001#authority-display",
                    "system_recomputed_gross_profit": "FORM-KMFA-MARGIN-CASH-MARGIN-001#revenue-minus-cost",
                    "cash_gross_profit": "FORM-KMFA-MARGIN-CASH-MARGIN-001#collection-minus-cash-paid-cost",
                    "gross_margin_rate": "FORM-KMFA-MARGIN-CASH-MARGIN-001#gross-profit-divided-by-revenue",
                },
                "authority_value_private_refs": {
                    "gross_profit": _authority_ref(authority_group, "gross_profit"),
                    "gross_margin_rate": _authority_ref(authority_group, "gross_margin"),
                },
                "authority_value_hash_refs": {
                    "gross_profit": _authority_hash(authority_group, "gross_profit"),
                    "gross_margin_rate": _authority_hash(authority_group, "gross_margin"),
                },
                "system_recomputed_value_private_refs": _private_ref_map(record_id, "system-recomputed", system_keys),
                "system_recomputed_value_hash_refs": _hash_ref_map(record_id, "system-recomputed", system_keys),
                "cash_margin_value_private_refs": _private_ref_map(record_id, "cash-margin", cash_keys),
                "cash_margin_value_hash_refs": _hash_ref_map(record_id, "cash-margin", cash_keys),
                "input_private_refs": {
                    "revenue": fact_record.get("metric_private_refs", {}).get("revenue"),
                    "management_project_cost": fact_record.get("metric_private_refs", {}).get("cost_total"),
                    "collection_amount": fact_record.get("metric_private_refs", {}).get("collection_amount"),
                    "cash_paid_cost": f"private_ref://KMFA/S09-P2/{record_id}/cash-paid-cost/private-calculation-input",
                },
                "input_hash_refs": {
                    "revenue": fact_record.get("metric_hash_refs", {}).get("revenue"),
                    "management_project_cost": fact_record.get("metric_hash_refs", {}).get("cost_total"),
                    "collection_amount": fact_record.get("metric_hash_refs", {}).get("collection_amount"),
                    "cash_paid_cost": _sha256_for(f"S09-P2:{record_id}:cash-paid-cost:input-ref"),
                },
                "calculation_private_execution_ref": f"private_ref://KMFA/S09-P2/{record_id}/integer-cent-calculation",
                "integer_cent_calculation_contract": {
                    "system_recomputed_gross_profit": "management_revenue_cents - management_project_cost_cents",
                    "cash_gross_profit": "collection_amount_cents - cash_paid_cost_cents",
                    "gross_margin_rate_basis_points": "system_recomputed_gross_profit_cents / management_revenue_cents",
                    "rounding_unit": "basis_point",
                    "zero_revenue_status": "blocked_zero_revenue_denominator",
                },
                "public_amount_values_committed": False,
                "authority_system_overwrite_allowed": False,
                "authority_display_value_overwritten_by_system": False,
                "system_recomputed_value_overwritten_by_authority": False,
                "difference_summary_ref": "KMFA/metadata/quality/scope_difference_summary.jsonl",
                "calculation_status": "private_calculation_refs_recorded_pending_quality_resolution",
                "raw_layer_write_allowed": False,
                "formal_report_allowed": False,
                "evidence_ref": "KMFA/stage_artifacts/S09_P2_margin_cash_margin/human/test_results.md",
                "public_repo_safety": _public_repo_safety(),
            }
        )
    return records


def _build_difference_summary(margin_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for record in margin_records:
        for diff_index, difference_type in enumerate(DIFFERENCE_TYPES, start=1):
            summary_id = f"SDS-S09P2-{len(summary) + 1:03d}"
            summary.append(
                {
                    "schema_version": "kmfa.scope_difference_summary.v1",
                    "record_type": "scope_difference_summary_item",
                    "project_id": "KMFA",
                    "stage_phase": "S09-P2",
                    "summary_id": summary_id,
                    "margin_record_id": record["margin_record_id"],
                    "difference_type": difference_type,
                    "difference_private_compare_ref": (
                        f"private_ref://KMFA/S09-P2/{record['margin_record_id']}/difference/{diff_index}"
                    ),
                    "difference_hash_ref": _sha256_for(f"S09-P2:{record['margin_record_id']}:{difference_type}"),
                    "authority_source_ref": "KMFA/metadata/baseline/a0_authority_baseline_records.jsonl",
                    "system_source_ref": record["project_cost_fact_record_ref"],
                    "status": "queued_pending_s09_p3_reconciliation",
                    "s09_p3_reconciliation_performed": False,
                    "human_readable_status": "queued_for_next_phase_scope_reconciliation",
                    "public_amount_values_committed": False,
                    "raw_layer_write_allowed": False,
                    "evidence_ref": "KMFA/stage_artifacts/S09_P2_margin_cash_margin/human/test_results.md",
                    "public_repo_safety": _public_repo_safety(),
                }
            )
    return summary


def build_default_project_margin_cash_margin_layer(
    *, generated_at: str
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    generated_at_value = require_text(generated_at, "generated_at")
    fact_layer_manifest = _read_json(DEFAULT_FACT_LAYER_MANIFEST)
    fact_records = _read_jsonl(DEFAULT_FACT_RECORDS)
    authority_records = _read_jsonl(DEFAULT_AUTHORITY_RECORDS)
    authority_groups = _authority_field_groups(authority_records)
    margin_records = _build_margin_records(fact_records, authority_groups)
    difference_summary = _build_difference_summary(margin_records)

    upstream_quality = fact_layer_manifest.get("upstream_quality_summary", {})
    quality_blocked = bool(upstream_quality.get("formal_calculation_blocked"))
    manifest = {
        "schema_version": "kmfa.project_margin_cash_margin_manifest.v1",
        "record_type": "project_margin_cash_margin_manifest",
        "project_id": "KMFA",
        "stage_phase": "S09-P2",
        "generated_at": generated_at_value,
        "formula_version": "FORM-KMFA-MARGIN-CASH-MARGIN-001",
        "mapping_version": "MAP-KMFA-S09P2-PUBLIC-SAFE-v1",
        "calculation_status": "margin_slots_recorded_blocked_for_formal_report"
        if quality_blocked
        else "margin_slots_recorded_pending_s09_p3_reconciliation",
        "required_margin_metrics": list(REQUIRED_MARGIN_METRICS),
        "summary": {
            "margin_metric_count": len(REQUIRED_MARGIN_METRICS),
            "project_cost_fact_record_count": len(fact_records),
            "margin_record_count": len(margin_records),
            "difference_summary_count": len(difference_summary),
            "authority_field_group_count": len(authority_groups),
            "upstream_manual_review_queue_count": int(upstream_quality.get("manual_review_queue_count", 0)),
            "upstream_unresolved_difference_count": int(upstream_quality.get("unresolved_difference_count", 0)),
        },
        "upstream_refs": {
            "project_cost_fact_layer_manifest": "KMFA/metadata/reports/project_cost_fact_layer_manifest.json",
            "project_cost_fact_records": "KMFA/metadata/lineage/project_cost_fact_records.jsonl",
            "authority_baseline_records": "KMFA/metadata/baseline/a0_authority_baseline_records.jsonl",
        },
        "formula_contract": {
            "authority_gross_profit": "authoritative_display_value_from_q5_hash_lock",
            "system_recomputed_gross_profit": "management_revenue_cents - management_project_cost_cents",
            "cash_gross_profit": "collection_amount_cents - cash_paid_cost_cents",
            "gross_margin_rate_basis_points": "system_recomputed_gross_profit_cents / management_revenue_cents",
            "public_numeric_values_committed": False,
            "calculation_unit": "integer_cents_and_basis_points",
        },
        "upstream_quality_summary": upstream_quality,
        "stage_scope": {
            "s09_p1_project_cost_fact_layer_scope_included": False,
            "s09_p2_margin_cash_margin_scope_included": True,
            "s09_p3_scope_difference_reconciliation_scope_included": False,
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
            "s09_p3_reconciliation_allowed": False,
            "stage9_review_allowed": False,
            "raw_layer_write_allowed": False,
            "automatic_external_action_allowed": False,
        },
        "artifact_refs": {
            "margin_cash_margin_manifest": "KMFA/metadata/reports/project_margin_cash_margin_manifest.json",
            "margin_records": "KMFA/metadata/lineage/project_margin_cash_margin_records.jsonl",
            "scope_difference_summary": "KMFA/metadata/quality/scope_difference_summary.jsonl",
            "stage_manifest": "KMFA/stage_artifacts/S09_P2_margin_cash_margin/machine/s09_p2_manifest.json",
            "completion_record": "KMFA/stage_artifacts/S09_P2_margin_cash_margin/human/s09_p2_completion_record.md",
            "test_results": "KMFA/stage_artifacts/S09_P2_margin_cash_margin/human/test_results.md",
            "validator": "KMFA/tools/check_s09_p2_margin_cash_margin.py",
        },
        "public_repo_safety": _public_repo_safety(),
    }
    validate_project_margin_cash_margin_artifacts(manifest, margin_records, difference_summary)
    return manifest, margin_records, difference_summary


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
            raise ProjectMarginCashMarginError(f"{path}.{key} must be false")


def _require_hash(value: Any, path: str) -> None:
    if not isinstance(value, str) or not HASH_RE.match(value):
        raise ProjectMarginCashMarginError(f"{path} must be sha256")


def _require_private_ref(value: Any, path: str) -> None:
    if not isinstance(value, str) or not value.startswith("private_ref://"):
        raise ProjectMarginCashMarginError(f"{path} must be private_ref")


def _require_private_ref_map(refs: dict[str, Any], expected_keys: tuple[str, ...], path: str) -> None:
    if set(refs) != set(expected_keys):
        raise ProjectMarginCashMarginError(f"{path} keys mismatch")
    for key, value in refs.items():
        _require_private_ref(value, f"{path}.{key}")


def _require_hash_ref_map(refs: dict[str, Any], expected_keys: tuple[str, ...], path: str) -> None:
    if set(refs) != set(expected_keys):
        raise ProjectMarginCashMarginError(f"{path} keys mismatch")
    for key, value in refs.items():
        _require_hash(value, f"{path}.{key}")


def validate_project_margin_cash_margin_artifacts(
    manifest: dict[str, Any],
    margin_records: list[dict[str, Any]],
    difference_summary: list[dict[str, Any]],
) -> None:
    if manifest.get("schema_version") != "kmfa.project_margin_cash_margin_manifest.v1":
        raise ProjectMarginCashMarginError("invalid S09-P2 manifest schema_version")
    if manifest.get("stage_phase") != "S09-P2":
        raise ProjectMarginCashMarginError("S09-P2 manifest stage_phase mismatch")
    if tuple(manifest.get("required_margin_metrics", [])) != REQUIRED_MARGIN_METRICS:
        raise ProjectMarginCashMarginError("S09-P2 required margin metrics mismatch")

    summary = manifest.get("summary", {})
    if summary.get("margin_metric_count") != len(REQUIRED_MARGIN_METRICS):
        raise ProjectMarginCashMarginError("S09-P2 margin metric count mismatch")
    if summary.get("margin_record_count") != len(margin_records):
        raise ProjectMarginCashMarginError("S09-P2 margin record count mismatch")
    if summary.get("difference_summary_count") != len(difference_summary):
        raise ProjectMarginCashMarginError("S09-P2 difference summary count mismatch")
    if summary.get("margin_record_count", 0) < 1:
        raise ProjectMarginCashMarginError("S09-P2 must produce at least one margin record")
    if summary.get("difference_summary_count", 0) < len(margin_records) * 2:
        raise ProjectMarginCashMarginError("S09-P2 must queue authority/system differences")

    stage_scope = manifest.get("stage_scope", {})
    if stage_scope.get("s09_p2_margin_cash_margin_scope_included") is not True:
        raise ProjectMarginCashMarginError("S09-P2 scope must be included")
    for excluded_scope in (
        "s09_p1_project_cost_fact_layer_scope_included",
        "s09_p3_scope_difference_reconciliation_scope_included",
        "stage9_review_scope_included",
        "lineage_full_check_scope_included",
        "formal_report_scope_included",
        "ui_scope_included",
        "external_connector_scope_included",
    ):
        if stage_scope.get(excluded_scope) is not False:
            raise ProjectMarginCashMarginError(f"S09-P2 must exclude {excluded_scope}")

    _require_false(manifest.get("quality_gate", {}), "manifest.quality_gate")
    _require_false(manifest.get("public_repo_safety", {}), "manifest.public_repo_safety")

    for record in margin_records:
        if record.get("schema_version") != "kmfa.project_margin_cash_margin_record.v1":
            raise ProjectMarginCashMarginError("invalid S09-P2 margin record schema_version")
        if record.get("record_type") != "project_margin_cash_margin_record":
            raise ProjectMarginCashMarginError("S09-P2 margin record type mismatch")
        if record.get("stage_phase") != "S09-P2":
            raise ProjectMarginCashMarginError("S09-P2 margin record stage_phase mismatch")
        if set(record.get("margin_metric_slots", [])) != set(REQUIRED_MARGIN_METRICS):
            raise ProjectMarginCashMarginError(f"{record.get('margin_record_id')} margin slots mismatch")
        _require_private_ref_map(
            record.get("authority_value_private_refs", {}),
            ("gross_profit", "gross_margin_rate"),
            "authority_value_private_refs",
        )
        _require_hash_ref_map(
            record.get("authority_value_hash_refs", {}),
            ("gross_profit", "gross_margin_rate"),
            "authority_value_hash_refs",
        )
        _require_private_ref_map(
            record.get("system_recomputed_value_private_refs", {}),
            ("gross_profit", "gross_margin_rate"),
            "system_recomputed_value_private_refs",
        )
        _require_hash_ref_map(
            record.get("system_recomputed_value_hash_refs", {}),
            ("gross_profit", "gross_margin_rate"),
            "system_recomputed_value_hash_refs",
        )
        _require_private_ref_map(
            record.get("cash_margin_value_private_refs", {}),
            ("cash_gross_profit", "cash_paid_cost"),
            "cash_margin_value_private_refs",
        )
        _require_hash_ref_map(
            record.get("cash_margin_value_hash_refs", {}),
            ("cash_gross_profit", "cash_paid_cost"),
            "cash_margin_value_hash_refs",
        )
        if record["authority_value_private_refs"]["gross_profit"] == record["system_recomputed_value_private_refs"][
            "gross_profit"
        ]:
            raise ProjectMarginCashMarginError("S09-P2 authority and system gross profit refs must differ")
        if record["authority_value_hash_refs"]["gross_profit"] == record["system_recomputed_value_hash_refs"][
            "gross_profit"
        ]:
            raise ProjectMarginCashMarginError("S09-P2 authority and system gross profit hashes must differ")
        if record.get("public_amount_values_committed") is not False:
            raise ProjectMarginCashMarginError("S09-P2 margin record cannot commit public amount values")
        if record.get("authority_system_overwrite_allowed") is not False:
            raise ProjectMarginCashMarginError("S09-P2 cannot overwrite authority/system values")
        if record.get("authority_display_value_overwritten_by_system") is not False:
            raise ProjectMarginCashMarginError("S09-P2 cannot overwrite authority display values")
        if record.get("system_recomputed_value_overwritten_by_authority") is not False:
            raise ProjectMarginCashMarginError("S09-P2 cannot overwrite system recomputed values")
        if record.get("raw_layer_write_allowed") is not False:
            raise ProjectMarginCashMarginError("S09-P2 margin record cannot write raw layer")
        if record.get("formal_report_allowed") is not False:
            raise ProjectMarginCashMarginError("S09-P2 margin record cannot allow formal report")
        _require_false(record.get("public_repo_safety", {}), f"record.{record.get('margin_record_id')}.public_repo_safety")

    difference_types = {item.get("difference_type") for item in difference_summary}
    if "authority_vs_system_gross_profit" not in difference_types:
        raise ProjectMarginCashMarginError("S09-P2 missing gross profit difference summary")
    if "authority_vs_system_gross_margin_rate" not in difference_types:
        raise ProjectMarginCashMarginError("S09-P2 missing gross margin rate difference summary")
    for item in difference_summary:
        if item.get("schema_version") != "kmfa.scope_difference_summary.v1":
            raise ProjectMarginCashMarginError("invalid S09-P2 scope difference summary schema_version")
        if item.get("record_type") != "scope_difference_summary_item":
            raise ProjectMarginCashMarginError("S09-P2 difference summary record type mismatch")
        if item.get("stage_phase") != "S09-P2":
            raise ProjectMarginCashMarginError("S09-P2 difference summary stage_phase mismatch")
        if item.get("status") != "queued_pending_s09_p3_reconciliation":
            raise ProjectMarginCashMarginError("S09-P2 difference summary must stay queued")
        if item.get("s09_p3_reconciliation_performed") is not False:
            raise ProjectMarginCashMarginError("S09-P2 cannot perform S09-P3 reconciliation")
        _require_private_ref(item.get("difference_private_compare_ref"), "difference_private_compare_ref")
        _require_hash(item.get("difference_hash_ref"), "difference_hash_ref")
        if item.get("public_amount_values_committed") is not False:
            raise ProjectMarginCashMarginError("S09-P2 difference summary cannot commit amount values")
        if item.get("raw_layer_write_allowed") is not False:
            raise ProjectMarginCashMarginError("S09-P2 difference summary cannot write raw layer")
        _require_false(item.get("public_repo_safety", {}), f"difference.{item.get('summary_id')}.public_repo_safety")

    forbidden_hits = _walk_forbidden_keys([manifest, margin_records, difference_summary])
    if forbidden_hits:
        raise ProjectMarginCashMarginError("forbidden public keys found: " + ", ".join(forbidden_hits))
    suffix_hits = _walk_forbidden_suffixes([manifest, margin_records, difference_summary])
    if suffix_hits:
        raise ProjectMarginCashMarginError("forbidden raw/sensitive suffix refs found: " + ", ".join(suffix_hits))


def write_default_artifacts(generated_at: str) -> dict[str, Any]:
    manifest, margin_records, difference_summary = build_default_project_margin_cash_margin_layer(
        generated_at=generated_at
    )
    _write_json(DEFAULT_OUTPUT_MANIFEST, manifest)
    _write_jsonl(DEFAULT_OUTPUT_MARGIN_RECORDS, margin_records)
    _write_jsonl(DEFAULT_OUTPUT_DIFFERENCE_SUMMARY, difference_summary)
    stage_manifest = {
        "schema_version": "kmfa.s09_p2_manifest.v1",
        "record_type": "s09_p2_margin_cash_margin_manifest",
        "project_id": "KMFA",
        "stage_phase": "S09-P2",
        "generated_at": generated_at,
        "calculation_status": manifest["calculation_status"],
        "margin_metric_count": manifest["summary"]["margin_metric_count"],
        "margin_record_count": manifest["summary"]["margin_record_count"],
        "difference_summary_count": manifest["summary"]["difference_summary_count"],
        "upstream_manual_review_queue_count": manifest["summary"]["upstream_manual_review_queue_count"],
        "upstream_unresolved_difference_count": manifest["summary"]["upstream_unresolved_difference_count"],
        "margin_cash_margin_manifest_ref": "KMFA/metadata/reports/project_margin_cash_margin_manifest.json",
        "margin_records_ref": "KMFA/metadata/lineage/project_margin_cash_margin_records.jsonl",
        "scope_difference_summary_ref": "KMFA/metadata/quality/scope_difference_summary.jsonl",
        "completion_record_ref": "KMFA/stage_artifacts/S09_P2_margin_cash_margin/human/s09_p2_completion_record.md",
        "test_results_ref": "KMFA/stage_artifacts/S09_P2_margin_cash_margin/human/test_results.md",
        "validator_ref": "KMFA/tools/check_s09_p2_margin_cash_margin.py",
        "github_upload_allowed": False,
        "formal_report_allowed": False,
        "s09_p3_scope_included": False,
        "stage9_review_scope_included": False,
        "public_repo_safety": manifest["public_repo_safety"],
    }
    _write_json(DEFAULT_OUTPUT_STAGE_MANIFEST, stage_manifest)
    return stage_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build KMFA S09-P2 margin and cash margin artifacts.")
    parser.add_argument("--generated-at", default="2026-06-30T23:45:00+10:00")
    args = parser.parse_args(argv)
    stage_manifest = write_default_artifacts(args.generated_at)
    print(
        "PASS: KMFA S09-P2 margin and cash margin artifacts written "
        f"(margin_records={stage_manifest['margin_record_count']}, "
        f"difference_summary={stage_manifest['difference_summary_count']}, "
        "s09_p3_scope=false, formal_report_allowed=false, github_upload_allowed=false)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
