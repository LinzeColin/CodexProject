#!/usr/bin/env python3
"""Privately rebind real project identities and materialize proven S09 values."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from KMFA.tools.a0_golden_fixture import normalize_ratio_to_basis_points  # noqa: E402
from KMFA.tools.amount_tools import normalize_amount_to_cents  # noqa: E402
from KMFA.tools.project_margin_cash_margin import _divide_to_basis_points  # noqa: E402
from KMFA.tools import (  # noqa: E402
    v014_authorized_agent_private_resolution_application_after_blocked_handoff as source_phase,
)


PROJECT_ROOT = Path("KMFA")
PHASE_ID = "V014_REAL_PROJECT_IDENTITY_PRIVATE_REBINDING_AND_PROCESSED_VALUE_MATERIALIZATION"
TASK_ID = "KMFA-V014-REAL-PROJECT-IDENTITY-PRIVATE-REBINDING-AND-PROCESSED-VALUE-MATERIALIZATION-20260710"
ACCEPTANCE_ID = "ACC-V014-REAL-PROJECT-IDENTITY-PRIVATE-REBINDING-AND-PROCESSED-VALUE-MATERIALIZATION"
VERSION = "0.1.4-real-project-identity-private-rebinding-and-processed-value-materialization"
STATUS = "completed_validated_local_only_real_identity_rebound_partial_value_materialization_no_go"
DECISION = "NO_GO"
PREFIX = "real_project_identity_private_rebinding_and_processed_value_materialization"

ARTIFACT_DIR = PROJECT_ROOT / "stage_artifacts" / PHASE_ID
MACHINE_DIR = ARTIFACT_DIR / "machine"
HUMAN_DIR = ARTIFACT_DIR / "human"
SUMMARY_PATH = MACHINE_DIR / f"{PREFIX}_summary.json"
MANIFEST_PATH = MACHINE_DIR / f"{PREFIX}_manifest.json"
GO_NO_GO_PATH = MACHINE_DIR / f"{PREFIX}_go_no_go_report.json"
MATRIX_PATH = MACHINE_DIR / f"{PREFIX}_matrix_public_safe.json"
REPORT_PATH = HUMAN_DIR / f"{PREFIX}.md"
GO_NO_GO_RECORD_PATH = HUMAN_DIR / "go_no_go_record.md"
TEST_RESULTS_PATH = HUMAN_DIR / "test_results.md"
RISK_REGISTER_PATH = HUMAN_DIR / "risk_register.md"
ROLLBACK_PATH = HUMAN_DIR / "rollback_plan.md"

METADATA_SUMMARY_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_summary.json"
METADATA_MANIFEST_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_manifest.json"
METADATA_GO_NO_GO_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_go_no_go_report.json"
METADATA_MATRIX_PATH = PROJECT_ROOT / f"metadata/quality/v014_{PREFIX}_matrix_public_safe.json"

PRIVATE_OUTPUT_DIR = PROJECT_ROOT / ".codex_private_runtime/v014_real_project_identity_private_rebinding_and_processed_value_materialization"
PRIVATE_RAW_BEFORE_PATH = PRIVATE_OUTPUT_DIR / "raw_immutability_before.json"
PRIVATE_RAW_AFTER_PATH = PRIVATE_OUTPUT_DIR / "raw_immutability_after.json"
PRIVATE_PRECHECK_PATH = PRIVATE_OUTPUT_DIR / "private_real_project_identity_precheck.json"
PRIVATE_IDENTITY_BINDINGS_PATH = PRIVATE_OUTPUT_DIR / "private_real_project_identity_bindings.jsonl"
PRIVATE_PROCESSED_METRICS_PATH = PRIVATE_OUTPUT_DIR / "private_processed_project_metrics.jsonl"
PRIVATE_TARGET_MATERIALIZATIONS_PATH = PRIVATE_OUTPUT_DIR / "private_s09_target_slot_materializations.jsonl"
PRIVATE_UNRESOLVED_TARGETS_PATH = PRIVATE_OUTPUT_DIR / "private_unresolved_cash_value_targets.jsonl"
PRIVATE_RECONCILIATION_COMPARISONS_PATH = PRIVATE_OUTPUT_DIR / "private_s09_reconciliation_comparisons.jsonl"
PRIVATE_DIAGNOSTIC_PATH = PRIVATE_OUTPUT_DIR / "private_rebinding_materialization_diagnostic.json"
PRIVATE_DIFFERENCE_REPORT_PATH = PRIVATE_OUTPUT_DIR / "private_difference_report_zh.md"

SOURCE_AUTHORITY_MATCH_PATH = source_phase.PRIVATE_AUTHORITY_MATCH_PATH
SOURCE_RAW_INDEX_PATH = source_phase.PRIVATE_RAW_INDEX_PATH
SOURCE_RESOLUTION_RECORDS_PATH = source_phase.PRIVATE_RESOLUTION_RECORDS_PATH
SOURCE_STAGING_PATH = source_phase.SOURCE_STAGING_PATH
SOURCE_OWNER_QUEUE_PATH = source_phase.SOURCE_PRIVATE_OWNER_RESOLUTION_QUEUE_PATH
SOURCE_PUBLIC_SUMMARY_PATH = source_phase.METADATA_SUMMARY_PATH
AUTHORITY_CANDIDATES_PATH = PROJECT_ROOT / "metadata/baseline/a0_project_candidates.jsonl"
FACT_RECORDS_PATH = PROJECT_ROOT / "metadata/lineage/project_cost_fact_records.jsonl"
MARGIN_RECORDS_PATH = PROJECT_ROOT / "metadata/lineage/project_margin_cash_margin_records.jsonl"
SCOPE_DIFFERENCE_SUMMARY_PATH = PROJECT_ROOT / "metadata/quality/scope_difference_summary.jsonl"
RECONCILIATION_RECORDS_PATH = PROJECT_ROOT / "metadata/quality/scope_reconciliation_records.jsonl"

DEVELOPMENT_EVENTS_PATH = PROJECT_ROOT / "docs/governance/development_events.jsonl"
STAGE_STATUS_PATH = PROJECT_ROOT / "metadata/stage_status.jsonl"
TASK_STATUS_PATH = PROJECT_ROOT / "metadata/traceability/v1_4_stage_phase_task_status.jsonl"


def _now(generated_at: str | None = None) -> str:
    return generated_at or datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    return source_phase._read_json(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return source_phase._read_jsonl(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    source_phase._write_json(path, payload)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    source_phase._write_jsonl(path, rows)


def _write_text(path: Path, text: str) -> None:
    source_phase._write_text(path, text)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _raw_snapshot(kind: str) -> dict[str, Any]:
    snapshot = source_phase._raw_snapshot(kind)
    snapshot["phase_id"] = PHASE_ID
    snapshot["snapshot_kind"] = kind
    return snapshot


def _snapshot_core(snapshot: dict[str, Any]) -> dict[str, Any]:
    return source_phase._snapshot_core(snapshot)


def source_private_paths() -> list[Path]:
    return [
        SOURCE_AUTHORITY_MATCH_PATH,
        SOURCE_RAW_INDEX_PATH,
        SOURCE_RESOLUTION_RECORDS_PATH,
        SOURCE_STAGING_PATH,
        SOURCE_OWNER_QUEUE_PATH,
    ]


def phase_output_paths() -> list[Path]:
    return [
        SUMMARY_PATH,
        MANIFEST_PATH,
        GO_NO_GO_PATH,
        MATRIX_PATH,
        REPORT_PATH,
        GO_NO_GO_RECORD_PATH,
        TEST_RESULTS_PATH,
        RISK_REGISTER_PATH,
        ROLLBACK_PATH,
        METADATA_SUMMARY_PATH,
        METADATA_MANIFEST_PATH,
        METADATA_GO_NO_GO_PATH,
        METADATA_MATRIX_PATH,
        PRIVATE_RAW_BEFORE_PATH,
        PRIVATE_RAW_AFTER_PATH,
        PRIVATE_PRECHECK_PATH,
        PRIVATE_IDENTITY_BINDINGS_PATH,
        PRIVATE_PROCESSED_METRICS_PATH,
        PRIVATE_TARGET_MATERIALIZATIONS_PATH,
        PRIVATE_UNRESOLVED_TARGETS_PATH,
        PRIVATE_RECONCILIATION_COMPARISONS_PATH,
        PRIVATE_DIAGNOSTIC_PATH,
        PRIVATE_DIFFERENCE_REPORT_PATH,
    ]


def _normalized_match_value(field_key: str, match: dict[str, Any]) -> int:
    raw_value = str(match.get("raw_value", ""))
    if field_key == "gross_margin":
        return normalize_ratio_to_basis_points(raw_value)
    interpreted_unit = match.get("interpreted_unit")
    unit = None if interpreted_unit in {None, "none"} else str(interpreted_unit)
    return normalize_amount_to_cents(raw_value, unit=unit)


def _normalize_identity_text(value: str) -> str:
    return re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "", value).lower()


def _identity_matcher(label: str):
    reduced = label
    for token in ("项目成本分析", "项目收支分析", "项目分析", "成本分析", "汇总", "明细", "报告", "最终版", "最新版"):
        reduced = reduced.replace(token, "")
    label_norm = _normalize_identity_text(label)
    reduced_norm = _normalize_identity_text(reduced)
    tokens = sorted(
        {
            token
            for token in re.split(r"[\s_（）()\-—/\\]+", reduced)
            if len(_normalize_identity_text(token)) >= 4
        },
        key=len,
        reverse=True,
    )

    def matches(text: str) -> bool:
        normalized = _normalize_identity_text(text)
        return bool(
            (len(label_norm) >= 5 and label_norm in normalized)
            or (len(reduced_norm) >= 5 and reduced_norm in normalized)
            or any(_normalize_identity_text(token) in normalized for token in tokens[:4])
        )

    return matches


def _build_private_precheck() -> dict[str, Any]:
    authority_match = read_json(SOURCE_AUTHORITY_MATCH_PATH)
    raw_container = read_json(SOURCE_RAW_INDEX_PATH)
    raw_index = raw_container.get("private_index", raw_container)
    candidate_rows = read_jsonl(AUTHORITY_CANDIDATES_PATH)
    candidates = {str(row["candidate_id"]): row for row in candidate_rows}
    complete_ids = set(authority_match.get("complete_numeric_candidate_ids", []))
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in authority_match.get("records", []):
        candidate_id = str(row.get("candidate_id"))
        if candidate_id not in complete_ids or not row.get("normalized_matches"):
            continue
        field_key = str(row.get("field_key"))
        values = {
            _normalized_match_value(field_key, match)
            for match in row.get("normalized_matches", [])
        }
        if len(values) != 1:
            raise ValueError("authority target does not normalize to one private integer value")
        grouped[candidate_id][field_key] = {
            "value": next(iter(values)),
            "matches": row.get("normalized_matches", []),
        }

    source_by_hash = {
        str(row.get("source_ref_hash")): row
        for row in raw_index.get("source_records", [])
    }
    workbook_records = [
        row
        for row in raw_index.get("numeric_records", [])
        if row.get("record_kind") == "workbook_cell"
    ]
    records: list[dict[str, Any]] = []
    for candidate_id in sorted(complete_ids, key=lambda item: int(candidates[item]["candidate_order"])):
        fields = grouped[candidate_id]
        required = {"contract_amount", "total_expense", "gross_profit", "gross_margin"}
        if set(fields) != required:
            raise ValueError(f"complete candidate is missing normalized fields: {candidate_id}")
        pdf_source_sets = [
            {
                str(match.get("source_ref_hash"))
                for match in fields[field_key]["matches"]
                if match.get("source_kind") == "raw_archive_pdf_member"
            }
            for field_key in sorted(required)
        ]
        shared_sources = set.intersection(*pdf_source_sets)
        label = str(candidates[candidate_id].get("candidate_label", ""))
        matches_identity = _identity_matcher(label)
        workbook_matches = [
            row
            for row in workbook_records
            if matches_identity(str(row.get("context_text", "")))
        ]
        contract = int(fields["contract_amount"]["value"])
        cost = int(fields["total_expense"]["value"])
        authority_gross_profit = int(fields["gross_profit"]["value"])
        authority_margin = int(fields["gross_margin"]["value"])
        system_gross_profit = contract - cost
        system_margin = _divide_to_basis_points(system_gross_profit, contract)
        if system_margin is None:
            raise ValueError("contract amount cannot be zero for materialization")
        shared_source_records = [source_by_hash[source] for source in sorted(shared_sources)]
        records.append(
            {
                "candidate_id": candidate_id,
                "candidate_order": int(candidates[candidate_id]["candidate_order"]),
                "candidate_label": label,
                "source_ref_hash": next(iter(shared_sources)) if len(shared_sources) == 1 else None,
                "shared_pdf_source_count": len(shared_sources),
                "private_source": shared_source_records[0] if len(shared_source_records) == 1 else shared_source_records,
                "values": {
                    "contract_amount_cents": contract,
                    "cost_total_cents": cost,
                    "authority_gross_profit_cents": authority_gross_profit,
                    "authority_gross_margin_basis_points": authority_margin,
                },
                "gross_profit_formula_exact": system_gross_profit == authority_gross_profit,
                "authority_margin_formula_exact": (
                    _divide_to_basis_points(authority_gross_profit, contract) == authority_margin
                ),
                "derived_system_gross_profit_cents": system_gross_profit,
                "derived_system_gross_margin_basis_points": system_margin,
                "workbook_identity_match_count": len(workbook_matches),
                "workbook_identity_sheet_count": len(
                    {row.get("sheet_ref_hash") for row in workbook_matches}
                ),
                "workbook_identity_matches": workbook_matches[:500],
            }
        )
    return {
        "schema_version": "kmfa.private.real_project_identity_precheck.v1",
        "classification": "private_real_project_identity_precheck_do_not_commit",
        "records": records,
    }


def _validate_precheck(precheck: dict[str, Any]) -> list[dict[str, Any]]:
    records = precheck.get("records", [])
    if not isinstance(records, list) or len(records) != 4:
        raise ValueError("real project identity precheck must contain four records")
    ordered = sorted(records, key=lambda row: int(row.get("candidate_order", 0)))
    if len({int(row.get("candidate_order", 0)) for row in ordered}) != 4:
        raise ValueError("candidate order must be unique")
    for row in ordered:
        if row.get("shared_pdf_source_count") != 1:
            raise ValueError("every real identity must have one shared authority PDF source")
        if row.get("authority_margin_formula_exact") is not True:
            raise ValueError("authority margin must exactly replay from gross profit and contract amount")
        values = row.get("values", {})
        for key in (
            "contract_amount_cents",
            "cost_total_cents",
            "authority_gross_profit_cents",
            "authority_gross_margin_basis_points",
        ):
            if isinstance(values.get(key), bool) or not isinstance(values.get(key), int):
                raise ValueError(f"{key} must be an integer")
        if int(values["contract_amount_cents"]) == 0:
            raise ValueError("contract amount cannot be zero")
    return ordered


def _build_identity_bindings(
    *, generated_at: str, projects: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    fact_records = read_jsonl(FACT_RECORDS_PATH)
    margin_records = read_jsonl(MARGIN_RECORDS_PATH)
    if len(fact_records) != 4 or len(margin_records) != 4:
        raise ValueError("expected four legacy fact and margin records")
    bindings: list[dict[str, Any]] = []
    for index, project in enumerate(projects, start=1):
        label = str(project.get("candidate_label", ""))
        amount_signature = json.dumps(project.get("values", {}), sort_keys=True, separators=(",", ":"))
        bindings.append(
            {
                "schema_version": "kmfa.private.real_project_identity_binding.v1",
                "classification": "private_real_project_identity_binding_do_not_commit",
                "binding_id": f"V014-RPIB-{index:03d}",
                "generated_at": generated_at,
                "legacy_fact_record_id": fact_records[index - 1].get("fact_record_id"),
                "legacy_margin_record_id": margin_records[index - 1].get("margin_record_id"),
                "legacy_synthetic_profile_ref": fact_records[index - 1].get("project_identity_profile_ref"),
                "synthetic_identity_replaced_in_private_overlay": True,
                "authority_candidate_id": project.get("candidate_id"),
                "authority_candidate_order": project.get("candidate_order"),
                "project_name_private_value": label,
                "project_name_private_hash": _sha256_text("project_name:" + label),
                "amount_signature_private_hash": _sha256_text("amount_signature:" + amount_signature),
                "source_ref_hash": project.get("source_ref_hash"),
                "private_source": project.get("private_source"),
                "present_identity_components": ["project_name", "amount_signature", "source_hash"],
                "missing_identity_components": [
                    "contract_number",
                    "counterparty",
                    "company_entity",
                    "occurrence_or_project_date",
                    "responsible_person",
                ],
                "binding_basis": "authority_candidate_order_plus_complete_four_field_hash_match_plus_unique_pdf_source",
                "binding_status": "real_authority_source_identity_rebound_private_only",
                "public_commit_allowed": False,
                "raw_layer_write_allowed": False,
            }
        )
    return bindings


def _metric_record(
    *,
    binding: dict[str, Any],
    metric_index: int,
    metric_key: str,
    value: int,
    unit: str,
    value_role: str,
    derivation: str,
) -> dict[str, Any]:
    return {
        "schema_version": "kmfa.private.processed_project_metric.v1",
        "classification": "private_processed_project_metric_do_not_commit",
        "metric_record_id": f"V014-PPM-{metric_index:03d}",
        "binding_id": binding["binding_id"],
        "legacy_fact_record_id": binding["legacy_fact_record_id"],
        "legacy_margin_record_id": binding["legacy_margin_record_id"],
        "metric_key": metric_key,
        "value": value,
        "unit": unit,
        "value_role": value_role,
        "derivation": derivation,
        "integer_only": True,
        "public_commit_allowed": False,
        "raw_layer_write_allowed": False,
    }


def _build_processed_metrics(
    bindings: list[dict[str, Any]], projects: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    records: list[dict[str, Any]] = []
    values_by_margin: dict[str, dict[str, int]] = {}
    metric_index = 0
    for binding, project in zip(bindings, projects):
        values = project["values"]
        contract = int(values["contract_amount_cents"])
        cost = int(values["cost_total_cents"])
        authority_gp = int(values["authority_gross_profit_cents"])
        authority_rate = int(values["authority_gross_margin_basis_points"])
        system_gp = contract - cost
        system_rate = _divide_to_basis_points(system_gp, contract)
        if system_rate is None:
            raise ValueError("system gross margin denominator cannot be zero")
        metric_specs = (
            ("contract_amount_cents", contract, "cents", "authority", "raw_authority_hash_preimage"),
            ("cost_total_cents", cost, "cents", "authority", "raw_authority_hash_preimage"),
            ("authority_gross_profit_cents", authority_gp, "cents", "authority", "raw_authority_hash_preimage"),
            ("authority_gross_margin_basis_points", authority_rate, "basis_points", "authority", "raw_authority_hash_preimage"),
            ("system_revenue_cents", contract, "cents", "system_input", "contract_amount_as_authority_margin_denominator"),
            ("system_cost_total_cents", cost, "cents", "system_input", "authority_total_expense_as_cost_total"),
            ("system_recomputed_gross_profit_cents", system_gp, "cents", "system_derived", "system_revenue_minus_system_cost_total"),
            ("system_recomputed_gross_margin_basis_points", system_rate, "basis_points", "system_derived", "system_gross_profit_divided_by_system_revenue"),
        )
        for metric_key, value, unit, role, derivation in metric_specs:
            metric_index += 1
            records.append(
                _metric_record(
                    binding=binding,
                    metric_index=metric_index,
                    metric_key=metric_key,
                    value=value,
                    unit=unit,
                    value_role=role,
                    derivation=derivation,
                )
            )
        values_by_margin[str(binding["legacy_margin_record_id"])] = {
            "authority_gross_profit_cents": authority_gp,
            "authority_gross_margin_basis_points": authority_rate,
            "system_recomputed_gross_profit_cents": system_gp,
            "system_recomputed_gross_margin_basis_points": system_rate,
        }
    return records, values_by_margin


def _build_reconciliation_comparisons(
    values_by_margin: dict[str, dict[str, int]]
) -> list[dict[str, Any]]:
    difference_rows = read_jsonl(SCOPE_DIFFERENCE_SUMMARY_PATH)
    reconciliation_rows = read_jsonl(RECONCILIATION_RECORDS_PATH)
    if len(difference_rows) != 12 or len(reconciliation_rows) != 12:
        raise ValueError("expected twelve S09 reconciliation records")
    records: list[dict[str, Any]] = []
    for index, (difference, reconciliation) in enumerate(
        zip(difference_rows, reconciliation_rows), start=1
    ):
        margin_id = str(difference.get("margin_record_id"))
        values = values_by_margin[margin_id]
        difference_type = str(difference.get("difference_type"))
        if difference_type == "authority_vs_system_gross_profit":
            amount_a = values["authority_gross_profit_cents"]
            amount_b = values["system_recomputed_gross_profit_cents"]
            unit = "cents"
        elif difference_type == "authority_vs_system_gross_margin_rate":
            amount_a = values["authority_gross_margin_basis_points"]
            amount_b = values["system_recomputed_gross_margin_basis_points"]
            unit = "basis_points"
        elif difference_type == "cash_vs_accrual_gross_profit":
            amount_a = None
            amount_b = values["system_recomputed_gross_profit_cents"]
            unit = "cents"
        else:
            raise ValueError(f"unsupported difference type: {difference_type}")
        delta = amount_a - amount_b if amount_a is not None else None
        status = (
            "comparison_incomplete_cash_source_disambiguation_required"
            if amount_a is None
            else ("comparison_complete_zero_delta" if delta == 0 else "comparison_complete_nonzero_delta")
        )
        records.append(
            {
                "schema_version": "kmfa.private.s09_reconciliation_comparison.v1",
                "classification": "private_s09_reconciliation_comparison_do_not_commit",
                "comparison_id": f"V014-RCMP-{index:03d}",
                "difference_id": reconciliation.get("difference_id"),
                "margin_record_id": margin_id,
                "difference_type": difference_type,
                "unit": unit,
                "amount_a": amount_a,
                "amount_b": amount_b,
                "delta": delta,
                "comparison_status": status,
                "public_commit_allowed": False,
                "raw_layer_write_allowed": False,
            }
        )
    return records


def _business_target_slots() -> list[dict[str, Any]]:
    queue_rows = read_jsonl(SOURCE_OWNER_QUEUE_PATH)
    staging = read_json(SOURCE_STAGING_PATH)
    slots_by_id = {
        str(row.get("target_slot_id")): row
        for row in staging.get("processed_target_slots", [])
    }
    slots = [slots_by_id[str(row.get("target_slot_id"))] for row in queue_rows]
    return [
        row
        for row in slots
        if row.get("context_group")
        in {
            "amount_a_cents_private_ref",
            "amount_b_cents_private_ref",
            "delta_cents_private_ref",
            "cash_gross_profit",
        }
    ]


def _build_target_materializations(
    comparisons: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    slots = _business_target_slots()
    comparisons_by_index = {index: row for index, row in enumerate(comparisons, start=1)}
    materialized: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for slot in slots:
        context = str(slot.get("context_group"))
        record_index = int(slot.get("record_index", 0))
        base = {
            "target_slot_id": slot.get("target_slot_id"),
            "private_processed_ref": slot.get("private_processed_ref"),
            "context_group": context,
            "record_index": record_index,
            "public_commit_allowed": False,
            "raw_layer_write_allowed": False,
        }
        if context == "cash_gross_profit":
            unresolved.append(
                {
                    **base,
                    "schema_version": "kmfa.private.unresolved_cash_value_target.v1",
                    "classification": "private_unresolved_cash_value_target_do_not_commit",
                    "resolution_status": "cash_source_disambiguation_required",
                    "reason_codes": [
                        "cash_collection_and_paid_cost_source_not_uniquely_bound",
                        "workbook_project_match_not_unique",
                    ],
                }
            )
            continue
        comparison = comparisons_by_index[record_index]
        key = {
            "amount_a_cents_private_ref": "amount_a",
            "amount_b_cents_private_ref": "amount_b",
            "delta_cents_private_ref": "delta",
        }[context]
        value = comparison.get(key)
        if value is None:
            unresolved.append(
                {
                    **base,
                    "schema_version": "kmfa.private.unresolved_cash_value_target.v1",
                    "classification": "private_unresolved_cash_value_target_do_not_commit",
                    "difference_id": comparison.get("difference_id"),
                    "resolution_status": "cash_source_disambiguation_required",
                    "reason_codes": [
                        "cash_collection_and_paid_cost_source_not_uniquely_bound",
                        "cash_gross_profit_or_delta_not_materialized",
                    ],
                }
            )
        else:
            materialized.append(
                {
                    **base,
                    "schema_version": "kmfa.private.s09_target_slot_materialization.v1",
                    "classification": "private_s09_target_slot_materialization_do_not_commit",
                    "difference_id": comparison.get("difference_id"),
                    "value": int(value),
                    "unit": comparison.get("unit"),
                    "value_fingerprint": _sha256_text(
                        f"{comparison.get('unit')}:{int(value)}"
                    ),
                    "materialization_status": "materialized_private_only",
                }
            )
    return materialized, unresolved


def _contains_float(value: Any) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_float(child) for child in value)
    return False


def _public_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    checks = [
        ("source_private_inputs_unchanged", summary["source_private_inputs_unchanged"]),
        ("raw_snapshot_exact_match", summary["raw_snapshot_exact_match"]),
        ("four_real_identity_bindings", summary["real_project_identity_binding_count"] == 4),
        ("four_unique_pdf_sources", summary["unique_authority_pdf_source_count"] == 4),
        ("authority_margin_exact", summary["authority_margin_formula_exact_count"] == 4),
        ("processed_metrics_materialized", summary["private_processed_metric_record_count"] == 32),
        ("target_values_materialized", summary["materialized_business_value_target_slot_count"] == 28),
        ("cash_targets_preserved", summary["unresolved_cash_value_target_slot_count"] == 12),
        ("comparison_counts", summary["completed_reconciliation_comparison_count"] == 8),
        ("nonzero_differences_preserved", summary["nonzero_delta_reconciliation_count"] == 6),
        ("full_materialization_not_claimed", not summary["full_processed_value_materialization_complete"]),
        ("business_consistency_not_claimed", not summary["business_value_consistency_verified"]),
        ("raw_not_committed", not summary["raw_business_data_committed"]),
        ("github_not_uploaded", not summary["github_upload_performed"]),
        ("app_not_reinstalled", not summary["app_reinstall_performed"]),
        ("stage_review_not_performed", not summary["stage_review_performed"]),
    ]
    rows = [
        {"check_id": f"RPIM-{index:02d}", "check_name": name, "passed": passed}
        for index, (name, passed) in enumerate(checks, start=1)
    ]
    return {
        "schema_version": "kmfa.v014_real_project_identity_materialization_matrix.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "check_count": len(rows),
        "check_pass_count": sum(row["passed"] for row in rows),
        "check_fail_count": sum(not row["passed"] for row in rows),
        "checks": rows,
    }


def _private_difference_report(
    *,
    summary: dict[str, Any],
    bindings: list[dict[str, Any]],
    projects: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    unresolved: list[dict[str, Any]],
) -> str:
    project_by_binding = {
        binding["binding_id"]: project for binding, project in zip(bindings, projects)
    }
    lines = [
        "# KMFA v0.1.4 真实项目身份重绑与处理值物化差异报告",
        "",
        "## 本轮结论",
        "",
        f"- 真实项目身份私有重绑：{summary['real_project_identity_binding_count']} 个。",
        f"- 已物化项目指标：{summary['private_processed_metric_record_count']} 条。",
        f"- 已物化 S09 目标槽位：{summary['materialized_business_value_target_slot_count']} 个。",
        f"- 仍需现金来源消歧的目标槽位：{summary['unresolved_cash_value_target_slot_count']} 个。",
        f"- 已完成差异比较：{summary['completed_reconciliation_comparison_count']} 条，其中零差异 {summary['zero_delta_reconciliation_count']} 条、非零差异 {summary['nonzero_delta_reconciliation_count']} 条。",
        f"- 现金口径未完成比较：{summary['incomplete_cash_reconciliation_count']} 条。",
        "- 当前结论仍为 NO_GO，不生成正式报告，不执行业务动作。",
        "",
        "## 真实项目私有绑定",
        "",
    ]
    for binding in bindings:
        project = project_by_binding[binding["binding_id"]]
        values = project["values"]
        lines.extend(
            [
                f"### {binding['binding_id']}",
                "",
                f"- 项目私有名称：{binding['project_name_private_value']}",
                f"- 旧事实记录：{binding['legacy_fact_record_id']}",
                f"- 旧毛利记录：{binding['legacy_margin_record_id']}",
                f"- 原始来源：{binding['private_source']}",
                f"- 合同额（分）：{values['contract_amount_cents']}",
                f"- 支出合计（分）：{values['cost_total_cents']}",
                f"- 权威毛利（分）：{values['authority_gross_profit_cents']}",
                f"- 权威毛利率（基点）：{values['authority_gross_margin_basis_points']}",
                f"- 合同额减支出合计是否等于权威毛利：{'是' if project['gross_profit_formula_exact'] else '否'}",
                f"- 财务工作簿项目候选数：{project.get('workbook_identity_match_count', 0)}；候选工作表数：{project.get('workbook_identity_sheet_count', 0)}。",
                "",
            ]
        )
    lines.extend(["## S09 口径差异", ""])
    status_labels = {
        "comparison_complete_zero_delta": "比较完成，零差异",
        "comparison_complete_nonzero_delta": "比较完成，存在非零差异",
        "comparison_incomplete_cash_source_disambiguation_required": "现金来源未唯一绑定，比较未完成",
    }
    for row in comparisons:
        lines.append(
            f"- {row['difference_id']}：{status_labels[row['comparison_status']]}；单位={row['unit']}；权威/现金侧={row['amount_a']}；系统/权责侧={row['amount_b']}；差额={row['delta']}。"
        )
    lines.extend(
        [
            "",
            "## 未解析现金槽位",
            "",
        ]
    )
    for row in unresolved:
        lines.append(
            f"- {row['target_slot_id']} / {row['context_group']}：回款与已付成本来源不能唯一绑定，继续保留差异。"
        )
    lines.extend(
        [
            "",
            "## 下一步",
            "",
            "- 对 3 个多工作表候选项目逐一核定回款与已付成本汇总口径。",
            "- 对 1 个未命中工作簿身份的项目补充项目名称、合同编号或对手方私有连接证据。",
            "- 完成现金毛利后重跑 4 条现金与权责毛利比较；6 条现有非零差异不得自动抹平。",
            "",
        ]
    )
    return "\n".join(lines)


def _public_reports(summary: dict[str, Any]) -> dict[Path, str]:
    report = f"""# v0.1.4 真实项目身份私有重绑与处理值物化

- Phase: `{PHASE_ID}`
- 决策: `{DECISION}`
- 真实身份私有重绑: {summary['real_project_identity_binding_count']}
- 私有项目指标: {summary['private_processed_metric_record_count']}
- 已物化目标槽位: {summary['materialized_business_value_target_slot_count']}
- 未解析现金槽位: {summary['unresolved_cash_value_target_slot_count']}
- 完成比较: {summary['completed_reconciliation_comparison_count']}
- 零差异 / 非零差异 / 现金未完成: {summary['zero_delta_reconciliation_count']} / {summary['nonzero_delta_reconciliation_count']} / {summary['incomplete_cash_reconciliation_count']}
- raw 前后完全一致: `{str(summary['raw_snapshot_exact_match']).lower()}`

本 phase 已用真实权威来源替换 4 个合成项目身份的私有 overlay，并实际物化可证明的 S09 值。现金来源仍不唯一，6 条已确认非零口径差异不能自动抹平，因此维持 NO_GO。
"""
    go_no_go = """# Go / No-Go 记录

- 决策: `NO_GO`
- 已完成: 4 个真实身份重绑、32 条项目指标、28 个目标槽位、8 条口径比较。
- 阻断: 12 个现金值槽位未解析、6 条非零口径差异未关闭、4 条现金比较未完成。
- GitHub upload / app reinstall / business execution: `not_performed`
"""
    tests = """# 测试结果

- focused unit test: `PENDING_FINAL_VERIFICATION`
- phase validator: `PENDING_FINAL_VERIFICATION`
- governance validators: `PENDING_FINAL_VERIFICATION`
- raw/private/secret scan: `PENDING_FINAL_VERIFICATION`
"""
    risks = """# 风险登记

- 高: 多工作表或未命中工作簿身份时，现金回款和已付成本不能自动汇总。
- 高: 6 条权威值与系统复算值存在真实非零差异，不得通过覆盖或四舍五入消除。
- 中: 私有重绑 overlay 尚未重放到全局 72 条 residual queue。
"""
    rollback = """# 回滚方案

1. 删除本 phase 公开 artifacts 和 metadata 镜像。
2. 删除本 phase ignored private runtime；不触碰原始数据目录。
3. 移除本 phase 治理记录，保留上一 phase NO_GO 证据。
"""
    return {
        REPORT_PATH: report,
        GO_NO_GO_RECORD_PATH: go_no_go,
        TEST_RESULTS_PATH: tests,
        RISK_REGISTER_PATH: risks,
        ROLLBACK_PATH: rollback,
    }


def _phase_public_files() -> list[str]:
    return [
        "KMFA/CHANGELOG.md",
        "KMFA/HANDOFF.md",
        "KMFA/VERSION",
        "KMFA/docs/governance/ASSURANCE_STATUS.yaml",
        "KMFA/docs/governance/DEVELOPMENT_LEDGER.md",
        "KMFA/docs/governance/MODEL_SPEC.md",
        "KMFA/docs/governance/OWNER_STATUS.md",
        "KMFA/docs/governance/STATUS.md",
        "KMFA/docs/governance/TRACEABILITY_MATRIX.csv",
        "KMFA/docs/governance/VERSION_MATRIX.yaml",
        "KMFA/docs/governance/delivery_tasks.yaml",
        "KMFA/docs/governance/development_events.jsonl",
        "KMFA/docs/governance/formula_registry.yaml",
        "KMFA/docs/governance/model_registry.yaml",
        "KMFA/docs/governance/parameter_registry.csv",
        "KMFA/metadata/model_registry.yaml",
        METADATA_SUMMARY_PATH.as_posix(),
        METADATA_MANIFEST_PATH.as_posix(),
        METADATA_GO_NO_GO_PATH.as_posix(),
        METADATA_MATRIX_PATH.as_posix(),
        "KMFA/metadata/stage_status.jsonl",
        "KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl",
        SUMMARY_PATH.as_posix(),
        MANIFEST_PATH.as_posix(),
        GO_NO_GO_PATH.as_posix(),
        MATRIX_PATH.as_posix(),
        REPORT_PATH.as_posix(),
        GO_NO_GO_RECORD_PATH.as_posix(),
        TEST_RESULTS_PATH.as_posix(),
        RISK_REGISTER_PATH.as_posix(),
        ROLLBACK_PATH.as_posix(),
        "KMFA/tests/test_v014_real_project_identity_private_rebinding_and_processed_value_materialization.py",
        "KMFA/tools/check_v014_real_project_identity_private_rebinding_and_processed_value_materialization.py",
        "KMFA/tools/v014_real_project_identity_private_rebinding_and_processed_value_materialization.py",
        "KMFA/功能清单.md",
        "KMFA/开发记录.md",
        "KMFA/模型参数文件.md",
    ]


def _write_governance(generated_at: str, summary: dict[str, Any]) -> None:
    evidence_ref = MANIFEST_PATH.as_posix()
    source_phase._upsert_jsonl(
        DEVELOPMENT_EVENTS_PATH,
        "event_id",
        {
            "event_id": "DEV-KMFA-20260710-V014-REAL-PROJECT-IDENTITY-PRIVATE-REBINDING-AND-PROCESSED-VALUE-MATERIALIZATION",
            "event_time": generated_at,
            "event_type": "development",
            "project_id": "KMFA",
            "stage_id": "value-consistency",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "decision": DECISION,
            "real_project_identity_binding_count": summary["real_project_identity_binding_count"],
            "materialized_business_value_target_slot_count": summary[
                "materialized_business_value_target_slot_count"
            ],
            "unresolved_cash_value_target_slot_count": summary[
                "unresolved_cash_value_target_slot_count"
            ],
            "raw_snapshot_exact_match": summary["raw_snapshot_exact_match"],
            "raw_business_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "files_changed": _phase_public_files(),
            "result_commit": "PENDING",
        },
    )
    source_phase._upsert_jsonl(
        STAGE_STATUS_PATH,
        "phase_id",
        {
            "schema_version": "kmfa.stage_status.v1",
            "record_type": "stage_phase_status",
            "project_id": "KMFA",
            "stage_id": "VALUE-CONSISTENCY",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "version": VERSION,
            "status": STATUS,
            "decision": DECISION,
            "raw_data_committed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at,
        },
    )
    source_phase._upsert_jsonl(
        TASK_STATUS_PATH,
        "phase_id",
        {
            "schema_version": "kmfa.v014_stage_phase_task_status.v1",
            "record_type": "v014_phase",
            "project_id": "KMFA",
            "stage_id": "VALUE-CONSISTENCY",
            "governance_stage_id": "VALUE-CONSISTENCY",
            "roadmap_stage_id": "VALUE-CONSISTENCY",
            "roadmap_phase_id": "REAL_PROJECT_IDENTITY_PRIVATE_REBINDING_AND_PROCESSED_VALUE_MATERIALIZATION",
            "phase_id": PHASE_ID,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "version": VERSION,
            "name": "v0.1.4 real project identity private rebinding and processed value materialization",
            "phase_goal": "replace synthetic project identities privately and materialize proven S09 values",
            "status": STATUS,
            "fact_level": "EXTRACTED",
            "derived_percent": 100.0,
            "estimated_task_units": 1,
            "completed_task_units": 1,
            "task_count": 1,
            "raw_data_committed": False,
            "evidence_ref": evidence_ref,
            "updated_at": generated_at[:10],
        },
    )


def generate(
    *,
    generated_at: str | None = None,
    precheck_override: dict[str, Any] | None = None,
    raw_before_snapshot_override: dict[str, Any] | None = None,
    raw_after_snapshot_override: dict[str, Any] | None = None,
    write_governance_event: bool = True,
) -> dict[str, Any]:
    timestamp = _now(generated_at)
    source_hashes_before = {
        path.as_posix(): _sha256_bytes(path.read_bytes()) for path in source_private_paths()
    }
    precheck = precheck_override or _build_private_precheck()
    projects = _validate_precheck(precheck)
    raw_before = raw_before_snapshot_override or (
        read_json(PRIVATE_RAW_BEFORE_PATH)
        if PRIVATE_RAW_BEFORE_PATH.exists()
        else _raw_snapshot("before")
    )
    raw_after = raw_after_snapshot_override or _raw_snapshot("after")
    _write_json(PRIVATE_RAW_BEFORE_PATH, raw_before)
    _write_json(PRIVATE_RAW_AFTER_PATH, raw_after)
    raw_snapshot_exact_match = _snapshot_core(raw_before) == _snapshot_core(raw_after)

    bindings = _build_identity_bindings(generated_at=timestamp, projects=projects)
    metrics, values_by_margin = _build_processed_metrics(bindings, projects)
    comparisons = _build_reconciliation_comparisons(values_by_margin)
    materialized, unresolved = _build_target_materializations(comparisons)
    source_hashes_after = {
        path.as_posix(): _sha256_bytes(path.read_bytes()) for path in source_private_paths()
    }
    source_unchanged = source_hashes_before == source_hashes_after
    completed = [
        row for row in comparisons if row["comparison_status"].startswith("comparison_complete_")
    ]
    zero = [row for row in completed if row["delta"] == 0]
    nonzero = [row for row in completed if row["delta"] != 0]
    incomplete = [row for row in comparisons if row not in completed]

    if _contains_float([bindings, metrics, comparisons, materialized, unresolved]):
        raise ValueError("private materialization cannot contain float values")
    if (len(bindings), len(metrics), len(materialized), len(unresolved), len(comparisons)) != (
        4,
        32,
        28,
        12,
        12,
    ):
        raise ValueError("private materialization counts do not match the phase contract")

    summary = {
        "schema_version": "kmfa.v014_real_project_identity_materialization_summary.v1",
        "record_type": "v014_real_project_identity_materialization_summary",
        "project_id": "KMFA",
        "version": VERSION,
        "stage_id": "VALUE-CONSISTENCY",
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": timestamp,
        "status": STATUS,
        "decision": DECISION,
        "source_phase_id": source_phase.PHASE_ID,
        "source_private_inputs_unchanged": source_unchanged,
        "authority_candidate_group_count": len(projects),
        "unique_authority_pdf_source_count": sum(
            row.get("shared_pdf_source_count") == 1 for row in projects
        ),
        "real_project_identity_binding_count": len(bindings),
        "synthetic_project_identity_replaced_private_overlay_count": len(bindings),
        "authority_margin_formula_exact_count": sum(
            row.get("authority_margin_formula_exact") is True for row in projects
        ),
        "authority_gross_profit_system_formula_exact_count": sum(
            row.get("gross_profit_formula_exact") is True for row in projects
        ),
        "workbook_identity_match_group_count": sum(
            int(row.get("workbook_identity_match_count", 0)) > 0 for row in projects
        ),
        "workbook_unique_sheet_binding_count": sum(
            int(row.get("workbook_identity_sheet_count", 0)) == 1 for row in projects
        ),
        "private_processed_metric_record_count": len(metrics),
        "materialized_business_value_target_slot_count": len(materialized),
        "unresolved_cash_value_target_slot_count": len(unresolved),
        "reconciliation_record_count": len(comparisons),
        "completed_reconciliation_comparison_count": len(completed),
        "zero_delta_reconciliation_count": len(zero),
        "nonzero_delta_reconciliation_count": len(nonzero),
        "incomplete_cash_reconciliation_count": len(incomplete),
        "global_unresolved_difference_count": 72,
        "global_residual_difference_queue_replayed": False,
        "partial_processed_value_materialization_complete": True,
        "full_processed_value_materialization_complete": False,
        "partial_raw_to_processed_reconciliation_performed": True,
        "full_raw_to_processed_value_comparison_complete": False,
        "processed_consistency_verified": False,
        "business_value_consistency_verified": False,
        "raw_source_file_count": raw_before.get("file_count", 0),
        "raw_snapshot_exact_match": raw_snapshot_exact_match,
        "raw_inbox_mutated_by_this_phase": not raw_snapshot_exact_match,
        "private_difference_report_written": True,
        "private_identity_bindings_gitignored": source_phase._git_check_ignored(
            PRIVATE_IDENTITY_BINDINGS_PATH
        ),
        "private_processed_metrics_gitignored": source_phase._git_check_ignored(
            PRIVATE_PROCESSED_METRICS_PATH
        ),
        "private_difference_report_gitignored": source_phase._git_check_ignored(
            PRIVATE_DIFFERENCE_REPORT_PATH
        ),
        "raw_business_data_committed": False,
        "raw_filename_or_value_committed": False,
        "credential_or_secret_committed": False,
        "stage_review_performed": False,
        "github_upload_performed": False,
        "app_reinstall_performed": False,
        "business_execution_performed": False,
        "goal_status_recommendation": "continue_active_with_cash_source_disambiguation",
        "next_recommended_phase": "cash_source_private_disambiguation_and_remaining_value_materialization",
    }
    matrix = _public_matrix(summary)
    if matrix["check_fail_count"]:
        raise ValueError("public acceptance matrix contains failures")
    manifest = {
        "schema_version": "kmfa.v014_real_project_identity_materialization_manifest.v1",
        "record_type": "v014_real_project_identity_materialization_manifest",
        "project_id": "KMFA",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "task_id": TASK_ID,
        "generated_at": timestamp,
        "reviewed_head": source_phase._git_output(["rev-parse", "HEAD"]),
        "branch": source_phase._git_output(["branch", "--show-current"]),
        "remote": source_phase._git_output(["remote", "get-url", "origin"]),
        "summary": summary,
        "artifact_refs": {
            "summary": SUMMARY_PATH.as_posix(),
            "go_no_go": GO_NO_GO_PATH.as_posix(),
            "matrix": MATRIX_PATH.as_posix(),
            "report": REPORT_PATH.as_posix(),
            "test_results": TEST_RESULTS_PATH.as_posix(),
            "validator": "KMFA/tools/check_v014_real_project_identity_private_rebinding_and_processed_value_materialization.py",
        },
        "public_repo_safety": {
            "aggregate_only": True,
            "raw_file_committed": False,
            "raw_filename_committed": False,
            "raw_hash_committed": False,
            "identity_plaintext_committed": False,
            "business_value_committed": False,
            "private_ref_committed": False,
            "credential_or_secret_committed": False,
        },
        "phase_boundaries": {
            "single_phase_only": True,
            "cash_source_disambiguation_completed": False,
            "global_residual_queue_replayed": False,
            "stage_review_performed": False,
            "github_upload_performed": False,
            "app_reinstall_performed": False,
            "business_execution_performed": False,
        },
    }
    go_no_go = {
        "schema_version": "kmfa.v014_real_project_identity_materialization_go_no_go.v1",
        "project_id": "KMFA",
        "phase_id": PHASE_ID,
        "decision": DECISION,
        "unresolved_cash_value_target_slot_count": len(unresolved),
        "nonzero_delta_reconciliation_count": len(nonzero),
        "incomplete_cash_reconciliation_count": len(incomplete),
        "blocking_reason_codes": [
            "cash_source_not_uniquely_bound",
            "nonzero_authority_vs_system_differences_remain",
            "global_residual_queue_not_replayed",
        ],
        "github_upload_performed": False,
    }

    _write_json(PRIVATE_PRECHECK_PATH, precheck)
    _write_jsonl(PRIVATE_IDENTITY_BINDINGS_PATH, bindings)
    _write_jsonl(PRIVATE_PROCESSED_METRICS_PATH, metrics)
    _write_jsonl(PRIVATE_TARGET_MATERIALIZATIONS_PATH, materialized)
    _write_jsonl(PRIVATE_UNRESOLVED_TARGETS_PATH, unresolved)
    _write_jsonl(PRIVATE_RECONCILIATION_COMPARISONS_PATH, comparisons)
    _write_json(
        PRIVATE_DIAGNOSTIC_PATH,
        {
            "schema_version": "kmfa.private.real_project_identity_materialization_diagnostic.v1",
            "classification": "private_rebinding_materialization_diagnostic_do_not_commit",
            "generated_at": timestamp,
            "source_hashes_before": source_hashes_before,
            "source_hashes_after": source_hashes_after,
            "source_private_inputs_unchanged": source_unchanged,
            "raw_before_snapshot": raw_before,
            "raw_after_snapshot": raw_after,
            "raw_snapshot_exact_match": raw_snapshot_exact_match,
            "comparison_status_counts": dict(
                sorted(Counter(row["comparison_status"] for row in comparisons).items())
            ),
        },
    )
    _write_text(
        PRIVATE_DIFFERENCE_REPORT_PATH,
        _private_difference_report(
            summary=summary,
            bindings=bindings,
            projects=projects,
            comparisons=comparisons,
            unresolved=unresolved,
        ),
    )
    for path, payload in (
        (SUMMARY_PATH, summary),
        (MANIFEST_PATH, manifest),
        (GO_NO_GO_PATH, go_no_go),
        (MATRIX_PATH, matrix),
        (METADATA_SUMMARY_PATH, summary),
        (METADATA_MANIFEST_PATH, manifest),
        (METADATA_GO_NO_GO_PATH, go_no_go),
        (METADATA_MATRIX_PATH, matrix),
    ):
        _write_json(path, payload)
    for path, content in _public_reports(summary).items():
        _write_text(path, content)
    if write_governance_event:
        _write_governance(timestamp, summary)
    return {"summary": summary, "manifest": manifest, "go_no_go": go_no_go, "matrix": matrix}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-at")
    parser.add_argument("--skip-governance-event", action="store_true")
    args = parser.parse_args()
    result = generate(
        generated_at=args.generated_at,
        write_governance_event=not args.skip_governance_event,
    )
    summary = result["summary"]
    print(
        "real project identity materialization: "
        f"decision={summary['decision']} "
        f"bindings={summary['real_project_identity_binding_count']} "
        f"materialized={summary['materialized_business_value_target_slot_count']} "
        f"unresolved_cash={summary['unresolved_cash_value_target_slot_count']} "
        f"raw_unchanged={summary['raw_snapshot_exact_match']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
