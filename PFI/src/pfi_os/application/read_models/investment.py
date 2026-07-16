"""Fail-closed holdings and valuation read model for PFI v0.2.5 Phase 4.2.

The current adapter consumes only tracked aggregate source state. It never
loads private holding rows, infers positions from transactions, or promotes a
legacy FX reference to production truth.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from pfi_os.domain.holdings import HoldingSnapshot, require_aware_datetime
from pfi_os.domain.valuation import FxRateSnapshot, MarketPriceSnapshot


PHASE_ID = "V025-S4-P4.2"
TASK_IDS = ("S4-P2-T1", "S4-P2-T2", "S4-P2-T3", "S4-P2-T4")
ACCEPTANCE_ID = "ACC-PFI-V025-S4-P42-HOLDINGS-VALUATION"
COST_FORMULA_ID = "FORM-PFI-009"
VALUATION_FORMULA_ID = "FORM-PFI-010"
COST_FORMULA_VERSION = "pfi-v0.2.5-explicit-cost-basis-v1"
VALUATION_FORMULA_VERSION = "pfi-v0.2.5-point-in-time-valuation-v1"
COST_FORMULA_EXPRESSION = (
    "cost_basis_original = acquisition_cost_ex_fees + capitalized_fee_total; "
    "cost basis method must be explicit"
)
VALUATION_FORMULA_EXPRESSION = (
    "market_value_original = quantity * price; market_value_cny = market_value_original * fx_rate; "
    "cost_basis_cny = cost_basis_original * fx_rate; unrealized_pnl_cny = market_value_cny - cost_basis_cny"
)
PARAMETERS = {
    "allowed_cost_basis_methods": [
        "source_reported",
        "specific_identification",
        "fifo",
        "weighted_average",
    ],
    "unknown_cost_basis_calculation_allowed": False,
    "future_price_snapshot_allowed": False,
    "future_fx_snapshot_allowed": False,
    "holding_fixture_fallback_allowed": False,
    "cny_identity_fx_rate": "1",
    "valuation_rounding_mode": "none_exact_decimal",
}
REQUIRED_SOURCE_IDS = ("SRC-HOLDINGS", "SRC-MARKET-PRICES", "SRC-FX-SNAPSHOT")
SOURCE_MANIFEST_PATH = Path("PFI/reports/pfi_v025/stage_2/phase_2_1/source_manifest.json")
FX_STATUS_PATH = Path("PFI/reports/pfi_v025/stage_2/phase_2_2/fx_snapshot_status.json")


def _canonical_json(payload: object) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _hash(payload: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json(payload)).hexdigest()


COST_FORMULA_HASH = _hash({"formula_id": COST_FORMULA_ID, "expression": COST_FORMULA_EXPRESSION})
VALUATION_FORMULA_HASH = _hash(
    {"formula_id": VALUATION_FORMULA_ID, "expression": VALUATION_FORMULA_EXPRESSION}
)
PARAMETER_HASH = _hash(PARAMETERS)


def _rfc3339(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_phase42_contract() -> dict[str, object]:
    return {
        "version": "v0.2.5",
        "stage": 4,
        "phase": "4.2",
        "phase_id": PHASE_ID,
        "task_ids": list(TASK_IDS),
        "acceptance_id": ACCEPTANCE_ID,
        "acceptance_id_origin": "project_governance_assigned_not_taskpack",
        "current_phase_only": True,
        "read_only_real_sources": True,
        "financial_fixture_fallback_allowed": False,
        "transaction_holding_inference_allowed": False,
        "cost_basis_guess_allowed": False,
        "legacy_fx_promotion_allowed": False,
        "finder_used": False,
        "explicitly_not_done": [
            "Phase 4.3 five-surface metric-state integration and consistency",
            "Stage 4 whole-stage review and acceptance",
            "private source loading, production writes, GitHub push and canonical app install",
        ],
    }


def value_holding(
    holding: HoldingSnapshot,
    price_snapshot: MarketPriceSnapshot,
    *,
    fx_snapshot: FxRateSnapshot | None,
    valuation_as_of: datetime,
) -> dict[str, Any]:
    """Evaluate a complete contract input using exact Decimal arithmetic.

    The function is a deterministic capability contract. The tracked Phase 4.2
    evidence does not call it with financial rows and does not claim production
    valuation acceptance.
    """

    require_aware_datetime("valuation_as_of", valuation_as_of)
    if holding.instrument_ref != price_snapshot.instrument_ref:
        raise ValueError("price instrument_ref must match holding instrument_ref")
    if holding.original_currency != price_snapshot.currency:
        raise ValueError("price currency must match holding original_currency")
    if holding.quantity_as_of > valuation_as_of:
        raise ValueError("quantity_as_of must not be after valuation_as_of")
    if price_snapshot.price_as_of > valuation_as_of:
        raise ValueError("price_as_of must not be after valuation_as_of")

    if holding.original_currency == "CNY":
        if fx_snapshot is not None:
            raise ValueError("fx_snapshot must be omitted for CNY identity valuation")
        fx_rate = Decimal(PARAMETERS["cny_identity_fx_rate"])
        fx_snapshot_id: str | None = None
        fx_effective_at: str | None = None
        fx_source_hash: str | None = None
        source_ids = [holding.source_id, price_snapshot.source_id]
    else:
        if fx_snapshot is None:
            raise ValueError("fx_snapshot is required for non-CNY valuation")
        if fx_snapshot.base_currency != holding.original_currency:
            raise ValueError("fx base_currency must match holding original_currency")
        if fx_snapshot.fx_effective_at > valuation_as_of:
            raise ValueError("fx_effective_at must not be after valuation_as_of")
        fx_rate = fx_snapshot.rate
        fx_snapshot_id = fx_snapshot.snapshot_id
        fx_effective_at = _rfc3339(fx_snapshot.fx_effective_at)
        fx_source_hash = fx_snapshot.source_content_hash
        source_ids = [holding.source_id, price_snapshot.source_id, fx_snapshot.source_id]

    market_value_original = holding.quantity * price_snapshot.price
    cost_basis_original = holding.cost_basis_original
    market_value_cny = market_value_original * fx_rate
    cost_basis_cny = cost_basis_original * fx_rate
    unrealized_pnl_cny = market_value_cny - cost_basis_cny
    return {
        "schema": "PFIV025ValuationSnapshotV1",
        "status": "ready",
        "holding_snapshot_id": holding.snapshot_id,
        "price_snapshot_id": price_snapshot.snapshot_id,
        "fx_snapshot_id": fx_snapshot_id,
        "source_ids": source_ids,
        "original_currency": holding.original_currency,
        "quantity": str(holding.quantity),
        "price": str(price_snapshot.price),
        "market_value_original": str(market_value_original),
        "cost_basis_original": str(cost_basis_original),
        "fx_rate": str(fx_rate),
        "market_value_cny": str(market_value_cny),
        "cost_basis_cny": str(cost_basis_cny),
        "unrealized_pnl_cny": str(unrealized_pnl_cny),
        "cost_basis_method": holding.cost_basis_method,
        "quantity_as_of": _rfc3339(holding.quantity_as_of),
        "price_as_of": _rfc3339(price_snapshot.price_as_of),
        "fx_effective_at": fx_effective_at,
        "valuation_as_of": _rfc3339(valuation_as_of),
        "holding_source_hash": holding.source_content_hash,
        "price_source_hash": price_snapshot.source_content_hash,
        "fx_source_hash": fx_source_hash,
        "cost_formula_id": COST_FORMULA_ID,
        "cost_formula_hash": COST_FORMULA_HASH,
        "valuation_formula_id": VALUATION_FORMULA_ID,
        "valuation_formula_hash": VALUATION_FORMULA_HASH,
        "parameter_hash": PARAMETER_HASH,
        "calculation_state": "calculated_contract_test_only",
        "rounding_applied": False,
    }


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid JSON object: {path}")
    return payload


def _source_index(manifest: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    sources = manifest.get("sources")
    if not isinstance(sources, list):
        raise ValueError("source manifest sources must be a list")
    index = {
        str(item.get("source_id")): item
        for item in sources
        if isinstance(item, Mapping) and item.get("source_id")
    }
    missing = [source_id for source_id in REQUIRED_SOURCE_IDS if source_id not in index]
    if missing:
        raise ValueError(f"source manifest missing required sources: {', '.join(missing)}")
    return index


def _metric_status(source_states: Mapping[str, Mapping[str, Any]]) -> str:
    statuses = {str(source.get("status") or "not_loaded") for source in source_states.values()}
    precedence = (
        "permission_denied",
        "path_error",
        "parse_failed",
        "source_missing",
        "outdated_snapshot",
        "partial_coverage",
        "partial",
        "not_loaded",
    )
    for status in precedence:
        if status in statuses:
            return "partial_coverage" if status == "partial" else status
    # Aggregate metadata marked ready is not complete private valuation evidence.
    return "valuation_missing"


def _metric(
    metric_id: str,
    *,
    formula_id: str,
    formula_version: str,
    formula_hash: str,
    source_states: Mapping[str, Mapping[str, Any]],
    required_source_ids: tuple[str, ...],
    component_formula_ids: tuple[str, ...],
) -> dict[str, Any]:
    holding_source = source_states["SRC-HOLDINGS"]
    holding_coverage = (
        holding_source.get("coverage") if isinstance(holding_source.get("coverage"), Mapping) else {}
    )
    required_states = {source_id: source_states[source_id] for source_id in required_source_ids}
    status = _metric_status(required_states)
    reasons = [
        str(source.get("blocking_reason_zh"))
        for source in required_states.values()
        if source.get("blocking_reason_zh")
    ]
    return {
        "metric_id": metric_id,
        "value": None,
        "currency": "CNY",
        "status": status,
        "source_ids": list(required_source_ids),
        "record_count": (
            holding_source.get("record_count")
            if isinstance(holding_source.get("record_count"), int)
            else None
        ),
        "coverage_start": holding_coverage.get("start"),
        "coverage_end": holding_coverage.get("end"),
        "data_as_of": holding_source.get("as_of"),
        "valued_at": None,
        "price_as_of": None,
        "fx_effective_at": None,
        "valuation_as_of": None,
        "original_currency": None,
        "fx_snapshot_id": None,
        "formula_id": formula_id,
        "formula_version": formula_version,
        "formula_hash": formula_hash,
        "component_formula_ids": list(component_formula_ids),
        "parameter_hash": PARAMETER_HASH,
        "data_hash": None,
        "read_model_hash": "PENDING",
        "classification_confidence": None,
        "source_coverage": 0,
        "reconciliation_coverage": None,
        "valuation_coverage": 0,
        "model_validation": "blocked",
        "report_completeness": "blocked",
        "blocking_reason_zh": "；".join(dict.fromkeys(reasons))
        or "持仓、价格或 FX 完整证据未加载，不执行投资估值。",
        "calculation_state": "not_run",
    }


def build_current_investment_read_model(
    repo_root: Path,
    *,
    observed_at: str | None = None,
) -> dict[str, Any]:
    manifest = _load_json(repo_root / SOURCE_MANIFEST_PATH)
    source_states = _source_index(manifest)
    selected = {source_id: source_states[source_id] for source_id in REQUIRED_SOURCE_IDS}
    fx_status = _load_json(repo_root / FX_STATUS_PATH)
    if fx_status.get("source_id") != "SRC-FX-SNAPSHOT":
        raise ValueError("FX status source_id must be SRC-FX-SNAPSHOT")
    if fx_status.get("status") != selected["SRC-FX-SNAPSHOT"].get("status"):
        raise ValueError("source manifest and FX status disagree")
    if fx_status.get("legacy_reference", {}).get("loaded_as_production") is not False:
        raise ValueError("legacy FX reference must not be loaded as production")

    metrics = [
        _metric(
            "investment_market_value_cny",
            formula_id=VALUATION_FORMULA_ID,
            formula_version=VALUATION_FORMULA_VERSION,
            formula_hash=VALUATION_FORMULA_HASH,
            source_states=selected,
            required_source_ids=REQUIRED_SOURCE_IDS,
            component_formula_ids=(VALUATION_FORMULA_ID,),
        ),
        _metric(
            "investment_cost_basis_cny",
            formula_id=VALUATION_FORMULA_ID,
            formula_version=VALUATION_FORMULA_VERSION,
            formula_hash=VALUATION_FORMULA_HASH,
            source_states=selected,
            required_source_ids=("SRC-HOLDINGS", "SRC-FX-SNAPSHOT"),
            component_formula_ids=(COST_FORMULA_ID, VALUATION_FORMULA_ID),
        ),
        _metric(
            "investment_unrealized_pnl_cny",
            formula_id=VALUATION_FORMULA_ID,
            formula_version=VALUATION_FORMULA_VERSION,
            formula_hash=VALUATION_FORMULA_HASH,
            source_states=selected,
            required_source_ids=REQUIRED_SOURCE_IDS,
            component_formula_ids=(COST_FORMULA_ID, VALUATION_FORMULA_ID),
        ),
    ]
    dependency_states = [
        {
            "source_id": source_id,
            "status": selected[source_id].get("status"),
            "record_count": selected[source_id].get("record_count"),
            "coverage": selected[source_id].get("coverage"),
            "as_of": selected[source_id].get("as_of"),
            "content_hash": selected[source_id].get("content_hash"),
        }
        for source_id in REQUIRED_SOURCE_IDS
    ]
    semantic_payload = {
        "schema": "PFIV025InvestmentReadModelV1",
        "dependency_states": dependency_states,
        "fx_status": {
            "status": fx_status.get("status"),
            "snapshot_id": fx_status.get("snapshot_id"),
            "fx_effective_at": fx_status.get("fx_effective_at"),
            "source_hash": fx_status.get("source_hash"),
            "legacy_loaded_as_production": fx_status.get("legacy_reference", {}).get(
                "loaded_as_production"
            ),
        },
        "metrics": [
            {key: value for key, value in metric.items() if key != "read_model_hash"}
            for metric in metrics
        ],
        "cost_formula_hash": COST_FORMULA_HASH,
        "valuation_formula_hash": VALUATION_FORMULA_HASH,
        "parameter_hash": PARAMETER_HASH,
    }
    read_model_hash = _hash(semantic_payload)
    for metric in metrics:
        metric["read_model_hash"] = read_model_hash
    status = _metric_status(selected)
    return {
        "schema": "PFIV025InvestmentReadModelV1",
        "version": "v0.2.5",
        "stage": 4,
        "phase": "4.2",
        "acceptance_id": ACCEPTANCE_ID,
        "observed_at": observed_at or str(manifest.get("observed_at")),
        "status": status,
        "source_ids": list(REQUIRED_SOURCE_IDS),
        "dependency_statuses": {
            source_id: str(selected[source_id].get("status")) for source_id in REQUIRED_SOURCE_IDS
        },
        "dependency_states": dependency_states,
        "metrics": metrics,
        "read_model_hash": read_model_hash,
        "cost_formula_hash": COST_FORMULA_HASH,
        "valuation_formula_hash": VALUATION_FORMULA_HASH,
        "parameter_hash": PARAMETER_HASH,
        "transactions_available_is_not_holding_proof": True,
        "transaction_holding_inference_used": False,
        "cost_basis_guess_used": False,
        "legacy_fx_reference_used": False,
        "financial_fixture_fallback_used": False,
        "financial_values_emitted": 0,
        "contains_private_values": False,
    }


def build_investment_api_contract(read_model: Mapping[str, Any]) -> dict[str, Any]:
    read_model_hash = str(read_model["read_model_hash"])
    surface = {
        "read_model_hash": read_model_hash,
        "status": read_model["status"],
        "metric_ids": [str(metric["metric_id"]) for metric in read_model["metrics"]],
        "metric_count": len(read_model["metrics"]),
    }
    return {
        "schema": "PFIV025InvestmentAPIContractV1",
        "version": "v0.2.5",
        "stage": 4,
        "phase": "4.2",
        "status": read_model["status"],
        "surface_ids": ["investment"],
        "read_model_hash": read_model_hash,
        "surfaces": {"investment": surface},
        "phase_43_all_surface_consistency_done": False,
        "financial_values_emitted": read_model["financial_values_emitted"],
        "contains_private_values": False,
    }
