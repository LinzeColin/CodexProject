"""PFI v0.2.5 Stage 5.3 real-snapshot model validation.

This module replays the immutable Stage 3 transaction blob, adapts only the
published CNY ledger events into the Stage 5 financial-event contract, and
publishes redacted validation facts.  It never writes the source or database,
and it keeps models blocked when the required balance, holding, price, cost or
ground-truth inputs do not exist.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from pfi_os.application.metrics.financial_models import (
    CASHFLOW_WINDOWS_DAYS,
    FinancialEvent,
    build_cashflow_windows,
    build_dual_metric_surface_contract,
    calculate_dual_consumption,
)
from pfi_os.application.metrics.formula_governance import load_formula_registry
from pfi_os.application.stage3_reconciliation import (
    Phase33Run,
    run_phase33_real_reconciliation,
)
from pfi_v02.stage_v022_interconnection import event_policy


VERSION = "v0.2.5"
STAGE = 5
PHASE_ID = "V025-S5-P5.3"
TASK_IDS = ("S5-P3-T1", "S5-P3-T2", "S5-P3-T3", "S5-P3-T4")
CONTRACT_ID = "PFI-V025-STAGE5-PHASE53-MODEL-VALIDATION"
ACCEPTANCE_ID = "ACC-PFI-V025-S5-P53-MODEL-VALIDATION"
VALIDATION_VERSION = "pfi-v0.2.5-model-validation-v1"
MODEL_ID = "MOD-PFI-010"
MODEL_VERSION = "pfi-v0.2.5-financial-models-v1"

_REAL_TO_FINANCIAL_EVENT_TYPE = {
    "income": "income",
    "living_consumption": "consumption",
    "own_account_transfer": "internal_transfer",
    "credit_card_repayment": "credit_card_repayment",
    "refund": "refund",
    "investment_funding": "investment_deposit",
    "fund_subscription": "fund_subscription",
    "gold_subscription": "bullion_purchase",
    "investment_purchase": "investment_buy",
    "investment_sale": "investment_sell",
}
_DUAL_MONEY_KEYS = (
    "total_consumption_outflow_cny",
    "living_consumption_cny",
    "investment_funding_outflow_cny",
    "investment_allocation_amount_cny",
    "financial_fee_outflow_cny",
    "refund_offset_cny",
)
_BLOCKED_CORE_SOURCES = (
    "SRC-ACCOUNT-BALANCES",
    "SRC-LIABILITIES",
    "SRC-HOLDINGS",
    "SRC-MARKET-PRICES",
    "SRC-FX-SNAPSHOT",
)


@dataclass(frozen=True)
class Phase53ValidationRun:
    source_snapshot_attestation: dict[str, Any]
    invariant_results: dict[str, Any]
    metamorphic_results: dict[str, Any]
    sensitivity_results: dict[str, Any]
    model_validation_card: dict[str, Any]
    cross_surface_validation: dict[str, Any]


_STAGE5_COMPONENT_LABELS = {
    "total_consumption_outflow_cny": "消费总流出金额（用户定义活动口径）",
    "living_consumption_cny": "生活消费金额",
    "investment_funding_outflow_cny": "投资资金流出金额",
    "investment_allocation_amount_cny": "投资域内配置金额",
}


def build_phase53_contract() -> dict[str, Any]:
    return {
        "schema": "PFIV025Stage5Phase53ContractV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": "5.3",
        "phase_id": PHASE_ID,
        "contract_id": CONTRACT_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_source_roadmap",
        "task_ids": list(TASK_IDS),
        "risk_tier": "T3_FINANCIAL_MODEL_VALIDATION_PRIVACY",
        "current_phase_only": True,
        "real_data_read_only": True,
        "financial_fixture_fallback_allowed": False,
        "public_evidence_redacted": True,
        "database_changed": False,
        "stage_5_whole_stage_review_started": False,
        "stage_6_started": False,
        "finder_used": False,
        "network_performed": False,
        "push_performed": False,
        "app_install_performed": False,
    }


def run_phase53_real_model_validation(
    project_root: Path | str,
    *,
    observed_at: str,
    git_ref: str = "HEAD",
) -> Phase53ValidationRun:
    stage3 = run_phase33_real_reconciliation(
        project_root,
        observed_at=observed_at,
        git_ref=git_ref,
    )
    events = _adapt_real_ledger_events(stage3)
    if not events:
        raise ValueError("real published ledger is empty; fixture fallback is forbidden")
    source = _build_source_snapshot_attestation(stage3, events)
    dual_metrics = calculate_dual_consumption(events)
    as_of = max(event.event_date for event in events)
    cashflow = build_cashflow_windows(events, as_of=as_of)
    invariant = _build_invariant_results(events, dual_metrics, cashflow)
    metamorphic = _build_metamorphic_results(events, dual_metrics, cashflow, as_of=as_of)
    sensitivity = _build_sensitivity_results(events, cashflow, as_of=as_of)
    cross_surface = _build_cross_surface_validation(dual_metrics, source)
    card = _build_model_validation_card(
        source=source,
        invariant=invariant,
        metamorphic=metamorphic,
        sensitivity=sensitivity,
        cross_surface=cross_surface,
    )
    run = Phase53ValidationRun(
        source_snapshot_attestation=source,
        invariant_results=invariant,
        metamorphic_results=metamorphic,
        sensitivity_results=sensitivity,
        model_validation_card=card,
        cross_surface_validation=cross_surface,
    )
    _assert_public_payload_is_redacted(run)
    return run


def build_stage5_private_surface_payload(
    project_root: Path | str,
    *,
    observed_at: str | None = None,
    git_ref: str = "HEAD",
) -> dict[str, Any]:
    """Build the private local-runtime payload consumed by the formal UI.

    Unlike the tracked Phase 5.3 evidence, this payload intentionally contains
    aggregate financial values.  It is returned only to the local private
    runtime and must never be persisted in tracked reports, screenshots or
    browser traces.
    """

    root = Path(project_root).expanduser().resolve()
    repo_root = root.parent if root.name == "PFI" else root
    timestamp = observed_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    stage3 = run_phase33_real_reconciliation(
        repo_root,
        observed_at=timestamp,
        git_ref=git_ref,
    )
    events = _adapt_real_ledger_events(stage3)
    if not events:
        raise ValueError("real published ledger is empty; fixture fallback is forbidden")
    source = _build_source_snapshot_attestation(stage3, events)
    metrics = calculate_dual_consumption(events)
    if metrics["component_reconciliation_difference_cny"] != Decimal("0.00"):
        raise ValueError("private Stage 5 surface components do not reconcile")
    financial_fee = Decimal(metrics["financial_fee_outflow_cny"])
    if financial_fee != Decimal("0.00"):
        raise ValueError("four-component UI contract requires an explicit fee component before non-zero fees may publish")

    event_counts = _component_event_counts(events)
    count_by_metric = {
        "total_consumption_outflow_cny": int(metrics["deduped_economic_event_type_count"]),
        "living_consumption_cny": int(event_counts["living_consumption"]),
        "investment_funding_outflow_cny": int(event_counts["investment_funding"]),
        "investment_allocation_amount_cny": int(event_counts["investment_allocation"]),
    }
    components: list[dict[str, Any]] = []
    for metric_id, label_zh in _STAGE5_COMPONENT_LABELS.items():
        value = Decimal(metrics[metric_id])
        components.append(
            {
                "metric_id": metric_id,
                "label_zh": label_zh,
                "status": "ready",
                "value": format(value, ".2f"),
                "observed_zero_in_published_scope": value == 0,
                "currency": "CNY",
                "formula_id": "FORM-PFI-015",
                "formula_version": "pfi-v0.2.5-dual-consumption-v1",
                "source_id": source["source_id"],
                "record_count": count_by_metric[metric_id],
                "as_of": source["coverage_end"],
                "coverage_scope": "published_events_only",
                "excluded_review_record_count": source["review_queue_record_count"],
            }
        )

    shared_surface_payload = {
        "components": components,
        "currency": "CNY",
        "scope_explanation_zh": (
            "消费总流出是用户定义的广义活动口径；生活消费、投资资金进入投资域和投资域内配置分别展示。"
            "所有金额只覆盖已发布经济事件，待复核记录不计入；该口径不等于净资产损失。"
        ),
        "investment_activity_is_net_worth_loss": False,
        "model_validation_status": "partial_validated_with_blocked_components",
        "source_snapshot_hash": source["input_content_hash"],
    }
    surface_hash = _payload_hash(shared_surface_payload)
    surfaces = ("homepage", "consumption_page", "report")
    return {
        "schema": "PFIV025Stage5PrivateFinancialSurfaceV1",
        "version": VERSION,
        "stage": STAGE,
        "model_id": MODEL_ID,
        "model_version": MODEL_VERSION,
        "formula_id": "FORM-PFI-015",
        "status": "ready_with_partial_source_coverage_and_blocked_models",
        "components": components,
        "surface_ids": list(surfaces),
        "surface_payload_hashes": {surface: surface_hash for surface in surfaces},
        "same_payload_hash": True,
        "source": {
            "source_id": source["source_id"],
            "source_snapshot_hash": source["input_content_hash"],
            "input_record_count": source["input_record_count"],
            "published_record_count": source["published_record_count"],
            "review_queue_record_count": source["review_queue_record_count"],
            "silent_drop_count": source["silent_drop_count"],
            "coverage_start": source["coverage_start"],
            "coverage_end": source["coverage_end"],
        },
        "scope_explanation_zh": shared_surface_payload["scope_explanation_zh"],
        "investment_activity_is_net_worth_loss": False,
        "confidence_dimensions": {
            "classification_confidence": "blocked_missing_scores_and_labels",
            "source_coverage": "partial_published_scope_with_review_queue",
            "reconciliation_coverage": "partition_complete",
            "valuation_coverage": "blocked_missing_holdings_prices_fx",
            "model_validation": "partial_validated_with_blocked_components",
            "report_completeness": "actual_three_surface_binding",
        },
        "formula_validation": {
            "FORM-PFI-015": "validated_real_snapshot",
            "FORM-PFI-016": "blocked_missing_required_sources",
            "FORM-PFI-017": "blocked_missing_required_sources",
            "FORM-PFI-018": "blocked_insufficient_chain",
            "FORM-PFI-019": "validated_real_snapshot",
            "FORM-PFI-020": "validated_structure_only",
        },
        "financial_fixture_fallback_used": False,
        "actual_ui_render_binding_completed": True,
        "actual_report_render_binding_completed": True,
        "private_runtime_only": True,
        "persist_to_tracked_evidence_allowed": False,
    }


def _adapt_real_ledger_events(stage3: Phase33Run) -> tuple[FinancialEvent, ...]:
    adapted: list[FinancialEvent] = []
    for ledger in stage3.ledger_events:
        mapped_type = _REAL_TO_FINANCIAL_EVENT_TYPE.get(ledger.event_type)
        if mapped_type is None:
            raise ValueError(f"unregistered real event type: {ledger.event_type}")
        if not ledger.postings:
            raise ValueError("published ledger event requires at least one posting")
        currencies = {posting.currency for posting in ledger.postings}
        if currencies != {"CNY"}:
            raise ValueError("Phase 5.3 requires explicit CNY values; unresolved FX is blocked")
        amount = sum((Decimal(posting.amount) for posting in ledger.postings), Decimal("0"))
        if amount <= 0:
            raise ValueError("published ledger event amount must be positive")
        source_identity = _payload_hash(sorted(ledger.raw_record_ids))
        adapted.append(
            FinancialEvent(
                source_record_id="source_" + source_identity.removeprefix("sha256:")[:24],
                economic_event_id=ledger.economic_event_id,
                interconnection_group_id=ledger.interconnection_group_id,
                event_date=date.fromisoformat(ledger.occurred_at[:10]),
                event_type=mapped_type,
                amount_cny=amount,
                direction=event_policy(mapped_type).cashflow_direction,
                offset_economic_event_id=ledger.offset_economic_event_id,
            )
        )
    return tuple(
        sorted(
            adapted,
            key=lambda event: (
                event.event_date,
                event.economic_event_id,
                event.event_type,
                event.source_record_id,
            ),
        )
    )


def _build_source_snapshot_attestation(
    stage3: Phase33Run,
    events: tuple[FinancialEvent, ...],
) -> dict[str, Any]:
    identity = stage3.idempotency_result
    reconciliation = stage3.reconciliation_summary
    currencies = sorted({posting.currency for event in stage3.ledger_events for posting in event.postings})
    source_before = dict(identity["source_identity_before"])
    source_after = dict(identity["source_identity_after"])
    return {
        "schema": "PFIV025Stage5Phase53SourceSnapshotAttestationV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "status": "pass",
        "source_id": identity["source_id"],
        "path_alias": identity["path_alias"],
        "isolation_mode": identity["isolation_mode"],
        "resolved_commit": identity["resolved_commit"],
        "transactions_blob_oid": identity["transactions_blob_oid"],
        "input_content_hash": identity["input_content_hash"],
        "input_record_count": reconciliation["input_record_count"],
        "published_record_count": reconciliation["published_record_count"],
        "review_queue_record_count": reconciliation["review_queue_record_count"],
        "silent_drop_count": reconciliation["silent_drop_count"],
        "adapted_financial_event_count": len(events),
        "published_event_type_counts": dict(reconciliation["published_event_type_counts"]),
        "adapted_event_type_counts": dict(sorted(Counter(event.event_type for event in events).items())),
        "currencies": currencies,
        "coverage_start": min(event.event_date for event in events).isoformat(),
        "coverage_end": max(event.event_date for event in events).isoformat(),
        "source_identity_before": source_before,
        "source_identity_after": source_after,
        "source_mutation_performed": source_before != source_after,
        "financial_fixture_fallback_used": False,
        "raw_rows_emitted": 0,
        "financial_values_emitted": 0,
        "contains_private_values": False,
    }


def _build_invariant_results(
    events: tuple[FinancialEvent, ...],
    dual_metrics: Mapping[str, Any],
    cashflow: Mapping[str, Any],
) -> dict[str, Any]:
    unique_keys = {(event.economic_event_id, event.event_type) for event in events}
    duplicate_count = len(events) - len(unique_keys)
    window_counts = [int(cashflow["metrics"][window]["record_count"]) for window in CASHFLOW_WINDOWS_DAYS]
    dual_pass = (
        dual_metrics["component_reconciliation_difference_cny"] == Decimal("0.00")
        and duplicate_count == 0
        and dual_metrics["investment_activity_is_net_worth_loss"] is False
    )
    window_pass = window_counts == sorted(window_counts)
    if not dual_pass or not window_pass:
        raise ValueError("real snapshot invariant or cashflow-window invariant failed")
    return {
        "schema": "PFIV025Stage5Phase53InvariantResultsV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "status": "partial_pass_with_blocked_components",
        "dual_metric_reconciliation": {
            "status": "pass",
            "formula_id": "FORM-PFI-015",
            "difference_is_exact_zero": True,
            "duplicate_economic_event_count": duplicate_count,
            "source_record_count": dual_metrics["source_record_count"],
            "deduped_economic_event_type_count": dual_metrics["deduped_economic_event_type_count"],
            "component_event_counts": _component_event_counts(events),
            "financial_value_fingerprint": _dual_metric_fingerprint(dual_metrics),
            "investment_activity_is_net_worth_loss": False,
        },
        "cashflow_window_invariant": {
            "status": "pass",
            "formula_id": "FORM-PFI-019",
            "windows": list(CASHFLOW_WINDOWS_DAYS),
            "record_counts": window_counts,
            "window_record_counts_non_decreasing": window_pass,
            "internal_transfer_excluded_from_net_cashflow": True,
        },
        "core_balance_invariants": {
            "status": "blocked_missing_required_sources",
            "formula_id": "FORM-PFI-016",
            "missing_source_ids": list(_BLOCKED_CORE_SOURCES),
            "financial_values_emitted": 0,
        },
        "investment_return_xirr": {
            "status": "blocked_insufficient_chain",
            "formula_ids": ["FORM-PFI-017", "FORM-PFI-018"],
            "missing_inputs": [
                "explicit holdings and remaining cost basis",
                "point-in-time prices and required FX",
                "fee and tax lineage",
                "dated investment funding/return/terminal-value chain",
            ],
            "financial_values_emitted": 0,
        },
        "financial_values_emitted": 0,
        "contains_private_values": False,
    }


def _build_metamorphic_results(
    events: tuple[FinancialEvent, ...],
    dual_metrics: Mapping[str, Any],
    cashflow: Mapping[str, Any],
    *,
    as_of: date,
) -> dict[str, Any]:
    base_dual_fingerprint = _dual_metric_fingerprint(dual_metrics)
    reversed_fingerprint = _dual_metric_fingerprint(calculate_dual_consumption(reversed(events)))
    duplicate_input = events + (events[0],)
    duplicate_fingerprint = _dual_metric_fingerprint(calculate_dual_consumption(duplicate_input))

    factor = Decimal("2")
    scaled_events = tuple(replace(event, amount_cny=event.amount_cny * factor) for event in events)
    scaled_metrics = calculate_dual_consumption(scaled_events)
    scaling_pass = all(
        scaled_metrics[key] == dual_metrics[key] * factor for key in _DUAL_MONEY_KEYS
    ) and scaled_metrics["component_reconciliation_difference_cny"] == Decimal("0.00")

    shifted_events = tuple(replace(event, event_date=event.event_date + timedelta(days=1)) for event in events)
    shifted_cashflow = build_cashflow_windows(shifted_events, as_of=as_of + timedelta(days=1))
    date_translation_pass = _cashflow_fingerprint(cashflow) == _cashflow_fingerprint(shifted_cashflow)
    checks = {
        "input_permutation_invariance": "pass" if reversed_fingerprint == base_dual_fingerprint else "fail",
        "exact_duplicate_invariance": "pass" if duplicate_fingerprint == base_dual_fingerprint else "fail",
        "positive_scaling_invariance": "pass" if scaling_pass else "fail",
        "date_translation_window_invariance": "pass" if date_translation_pass else "fail",
    }
    if set(checks.values()) != {"pass"}:
        raise ValueError("real-snapshot metamorphic validation failed")
    return {
        "schema": "PFIV025Stage5Phase53MetamorphicResultsV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "status": "pass",
        **checks,
        "base_dual_metric_fingerprint": base_dual_fingerprint,
        "scaled_dual_metric_fingerprint": _dual_metric_fingerprint(scaled_metrics),
        "cashflow_window_fingerprint": _cashflow_fingerprint(cashflow),
        "source_snapshot_mutated": False,
        "financial_values_emitted": 0,
        "contains_private_values": False,
    }


def _build_sensitivity_results(
    events: tuple[FinancialEvent, ...],
    cashflow: Mapping[str, Any],
    *,
    as_of: date,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    previous_count = 0
    for window in CASHFLOW_WINDOWS_DAYS:
        metric = cashflow["metrics"][window]
        count = int(metric["record_count"])
        rows.append(
            {
                "window_days": window,
                "coverage_start": metric["coverage_start"],
                "coverage_end": metric["coverage_end"],
                "record_count": count,
                "incremental_record_count": count - previous_count,
                "status": metric["status"],
                "financial_value_fingerprint": _payload_hash(
                    {
                        key: _decimal_text(metric[key])
                        for key in (
                            "external_inflow_cny",
                            "external_outflow_cny",
                            "internal_transfer_cny",
                            "net_cashflow_cny",
                        )
                    }
                ),
            }
        )
        previous_count = count
    counts = [row["record_count"] for row in rows]
    if counts != sorted(counts):
        raise ValueError("cashflow window sensitivity record counts must be non-decreasing")

    before_source = min(event.event_date for event in events) - timedelta(days=1)
    empty = build_cashflow_windows(events, as_of=before_source)
    empty_rows = [empty["metrics"][window] for window in CASHFLOW_WINDOWS_DAYS]
    empty_safe = all(
        row["status"] == "filtered_empty"
        and row["external_inflow_cny"] is None
        and row["external_outflow_cny"] is None
        and row["internal_transfer_cny"] is None
        and row["net_cashflow_cny"] is None
        for row in empty_rows
    )
    if not empty_safe:
        raise ValueError("empty-window boundary emitted a false financial zero")
    return {
        "schema": "PFIV025Stage5Phase53SensitivityResultsV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "status": "partial_pass_with_blocked_parameters",
        "as_of": as_of.isoformat(),
        "cashflow_window_days": list(CASHFLOW_WINDOWS_DAYS),
        "cashflow_window_sensitivity": rows,
        "empty_window_boundary": {
            "status": "filtered_empty",
            "as_of": before_source.isoformat(),
            "financial_values_are_null": True,
        },
        "classification_threshold_sensitivity": {
            "status": "blocked_missing_scores",
            "configured_threshold": 70,
            "reason": "The immutable ledger has no per-record classification score vector or ground truth labels.",
        },
        "xirr_parameter_sensitivity": {
            "status": "blocked_insufficient_chain",
            "configured_day_count_basis": 365,
            "configured_tolerance": "0.0000000001",
            "configured_max_iterations": 256,
            "reason": "No complete dated funding/return/terminal-value chain exists in the accepted real snapshot.",
        },
        "historical_out_of_sample_sensitivity": {
            "status": "blocked_insufficient_ground_truth",
            "reason": "No pre-specified split, labels or complete valuation target exists; a retrospective split would overstate validity.",
        },
        "financial_values_emitted": 0,
        "contains_private_values": False,
    }


def _build_cross_surface_validation(
    dual_metrics: Mapping[str, Any],
    source: Mapping[str, Any],
) -> dict[str, Any]:
    surface_contract = build_dual_metric_surface_contract(dual_metrics)
    hashes = dict(surface_contract["surface_hashes"])
    same_hash = len(set(hashes.values())) == 1
    if not same_hash:
        raise ValueError("dual metrics diverge between consumer surfaces")
    return {
        "schema": "PFIV025Stage5Phase53CrossSurfaceValidationV1",
        "version": VERSION,
        "phase_id": PHASE_ID,
        "status": "contract_pass_render_binding_open",
        "surface_ids": list(surface_contract["surface_ids"]),
        "surface_payload_hashes": hashes,
        "same_payload_hash": True,
        "real_snapshot_bound": True,
        "source_snapshot_hash": source["input_content_hash"],
        "actual_ui_render_binding_completed": False,
        "actual_report_render_binding_completed": False,
        "open_requirement": (
            "The real-snapshot consumer payload is validated, but tracked Web/report renderers do not yet consume all four components."
        ),
        "financial_values_emitted": 0,
        "contains_private_values": False,
    }


def _build_model_validation_card(
    *,
    source: Mapping[str, Any],
    invariant: Mapping[str, Any],
    metamorphic: Mapping[str, Any],
    sensitivity: Mapping[str, Any],
    cross_surface: Mapping[str, Any],
) -> dict[str, Any]:
    registry = load_formula_registry()
    formula_by_id = {item["formula_id"]: item for item in registry["formulas"]}
    validation_status = {
        "FORM-PFI-015": "validated_real_snapshot",
        "FORM-PFI-016": "blocked_missing_required_sources",
        "FORM-PFI-017": "blocked_missing_required_sources",
        "FORM-PFI-018": "blocked_insufficient_chain",
        "FORM-PFI-019": "validated_real_snapshot",
        "FORM-PFI-020": "validated_structure_only",
    }
    limitations = {
        "FORM-PFI-015": "Published real events validate living consumption and investment allocation; unresolved transfer/refund pools prevent full funding/refund coverage.",
        "FORM-PFI-016": "Account balance, liability, holding, price and FX snapshots are not loaded.",
        "FORM-PFI-017": "Holdings, cost basis, point-in-time price, fee, tax and FX lineage are incomplete.",
        "FORM-PFI-018": "No complete dated funding/return/terminal-value chain is available for real XIRR.",
        "FORM-PFI-019": "Seven real lookback windows and empty-window false-zero boundaries pass; date precision remains daily.",
        "FORM-PFI-020": "Taxonomy structure passes, but classification accuracy lacks labels and out-of-sample ground truth.",
    }
    formula_validation = [
        {
            "formula_id": formula_id,
            "formula_version": formula_by_id[formula_id]["version"],
            "formula_hash": formula_by_id[formula_id]["formula_hash"],
            "status": validation_status[formula_id],
            "limitation": limitations[formula_id],
        }
        for formula_id in sorted(validation_status)
    ]
    return {
        "schema": "PFIV025Stage5Phase53ModelValidationCardV1",
        "version": VERSION,
        "stage": STAGE,
        "phase": "5.3",
        "phase_id": PHASE_ID,
        "validation_version": VALIDATION_VERSION,
        "model_id": MODEL_ID,
        "model_version": MODEL_VERSION,
        "status": "partial_validated_with_blocked_components",
        "input_snapshot": {
            "source_id": source["source_id"],
            "resolved_commit": source["resolved_commit"],
            "transactions_blob_oid": source["transactions_blob_oid"],
            "input_content_hash": source["input_content_hash"],
            "input_record_count": source["input_record_count"],
            "published_record_count": source["published_record_count"],
            "review_queue_record_count": source["review_queue_record_count"],
            "coverage_start": source["coverage_start"],
            "coverage_end": source["coverage_end"],
            "currencies": list(source["currencies"]),
        },
        "coverage_dimensions": {
            "classification_confidence": "unverified_missing_scores_and_labels",
            "source_coverage": "partial_6879_published_1936_review",
            "reconciliation_coverage": "partition_complete_with_review_queue",
            "valuation_coverage": "blocked_missing_holdings_prices_fx",
            "model_validation": "partial_validated_with_blocked_components",
            "report_completeness": "contract_only_actual_render_binding_open",
        },
        "formula_validation": formula_validation,
        "validation_tests": {
            "real_snapshot_invariants": invariant["status"],
            "metamorphic_tests": metamorphic["status"],
            "parameter_sensitivity": sensitivity["status"],
            "cross_surface_consumer_contract": cross_surface["status"],
        },
        "historical_out_of_sample_validation": {
            "status": "blocked_insufficient_ground_truth",
            "reason": "No complete target, labels and pre-specified split are available for a defensible historical or out-of-sample claim.",
        },
        "consumer_binding": {
            "surface_ids": list(cross_surface["surface_ids"]),
            "same_payload_contract_validated": True,
            "actual_ui_render_binding_completed": False,
            "actual_report_render_binding_completed": False,
            "status": "contract_only_render_binding_open",
        },
        "limitations": [
            "1,936 source rows remain fail-closed in review and are excluded from published metrics.",
            "The unresolved transfer pool prevents real validation of investment-funding activity.",
            "Unlinked refunds cannot offset living consumption until explicit lineage exists.",
            "Balance, liability, holding, price, fee, tax and FX sources required by core and investment formulas are not loaded.",
            "Source time precision is daily; intraday ordering is not claimed.",
            "Tracked Web/report renderers do not yet consume all four real-snapshot dual-metric components.",
        ],
        "counter_evidence": [
            "FORM-PFI-016..018 must remain blocked instead of inheriting the passing transaction-only evidence.",
            "Taxonomy constraints do not prove classification accuracy without labels.",
            "Consumer payload equality is not evidence of actual rendered UI/report parity.",
        ],
        "contains_private_values": False,
        "financial_values_emitted": 0,
        "production_accepted": False,
        "final_human_acceptance": False,
    }


def _component_event_counts(events: Iterable[FinancialEvent]) -> dict[str, int]:
    counter = Counter(event.event_type for event in events)
    return {
        "living_consumption": counter["consumption"],
        "investment_funding": counter["investment_deposit"],
        "investment_allocation": sum(
            counter[event_type] for event_type in ("fund_subscription", "bullion_purchase", "investment_buy")
        ),
        "financial_fee": counter["fee"],
        "linked_refund": counter["refund"],
    }


def _dual_metric_fingerprint(metrics: Mapping[str, Any]) -> str:
    return _payload_hash(
        {
            key: _decimal_text(metrics[key])
            for key in _DUAL_MONEY_KEYS + ("component_reconciliation_difference_cny",)
        }
    )


def _cashflow_fingerprint(payload: Mapping[str, Any]) -> str:
    return _payload_hash(
        {
            "windows": list(payload["windows"]),
            "metrics": {
                str(window): {
                    key: _decimal_text(payload["metrics"][window][key])
                    for key in (
                        "status",
                        "record_count",
                        "external_inflow_cny",
                        "external_outflow_cny",
                        "internal_transfer_cny",
                        "net_cashflow_cny",
                    )
                }
                for window in payload["windows"]
            },
        }
    )


def _decimal_text(value: object) -> object:
    return format(value, "f") if isinstance(value, Decimal) else value


def _payload_hash(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _assert_public_payload_is_redacted(run: Phase53ValidationRun) -> None:
    serialized = json.dumps(
        (
            run.source_snapshot_attestation,
            run.invariant_results,
            run.metamorphic_results,
            run.sensitivity_results,
            run.model_validation_card,
            run.cross_surface_validation,
        ),
        ensure_ascii=False,
        sort_keys=True,
    )
    forbidden = ("/Users/", "account_ref", "description", "raw_record_id", "normalized_transaction_id")
    if any(token in serialized for token in forbidden):
        raise ValueError("public model-validation payload contains private row material")
