from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from pfi_os.application.read_models.investment import (
    ACCEPTANCE_ID,
    PHASE_ID,
    TASK_IDS,
    build_current_investment_read_model,
    build_investment_api_contract,
    build_phase42_contract,
    value_holding,
)
from pfi_os.domain.holdings import HoldingSnapshot
from pfi_os.domain.valuation import FxRateSnapshot, MarketPriceSnapshot


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
STAGE_ROOT = PFI_ROOT / "docs" / "pfi_v025" / "stage_4"
REPORT_ROOT = PFI_ROOT / "reports" / "pfi_v025" / "stage_4" / "phase_4_2"


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _holding(*, currency: str = "AUD") -> HoldingSnapshot:
    return HoldingSnapshot(
        snapshot_id="holding-contract-test",
        account_ref="opaque-account-contract-ref",
        instrument_ref="opaque-instrument-contract-ref",
        source_id="SRC-HOLDINGS",
        quantity=Decimal("2"),
        acquisition_cost_ex_fees=Decimal("16.00"),
        capitalized_fee_total=Decimal("1.00"),
        original_currency=currency,
        cost_basis_method="source_reported",
        transaction_link_status="linked",
        transaction_event_ids=("opaque-event-contract-ref",),
        quantity_as_of=datetime(2026, 7, 14, 5, 0, tzinfo=timezone.utc),
        source_record_count=1,
        source_content_hash="sha256:" + "a" * 64,
    )


def _price(*, currency: str = "AUD", hour: int = 6) -> MarketPriceSnapshot:
    return MarketPriceSnapshot(
        snapshot_id="price-contract-test",
        instrument_ref="opaque-instrument-contract-ref",
        source_id="SRC-MARKET-PRICES",
        price=Decimal("10.00"),
        currency=currency,
        price_as_of=datetime(2026, 7, 14, hour, 0, tzinfo=timezone.utc),
        source_content_hash="sha256:" + "b" * 64,
    )


def _fx(*, hour: int = 7) -> FxRateSnapshot:
    return FxRateSnapshot(
        snapshot_id="fx-contract-test",
        source_id="SRC-FX-SNAPSHOT",
        base_currency="AUD",
        quote_currency="CNY",
        direction="AUD_TO_CNY",
        rate=Decimal("5"),
        fx_effective_at=datetime(2026, 7, 14, hour, 0, tzinfo=timezone.utc),
        source_content_hash="sha256:" + "c" * 64,
    )


def test_phase_contract_is_exactly_phase_42_and_stops_before_phase_43() -> None:
    contract = build_phase42_contract()

    assert contract["version"] == "v0.2.5"
    assert contract["stage"] == 4
    assert contract["phase_id"] == PHASE_ID == "V025-S4-P4.2"
    assert contract["task_ids"] == list(TASK_IDS) == [
        "S4-P2-T1",
        "S4-P2-T2",
        "S4-P2-T3",
        "S4-P2-T4",
    ]
    assert contract["acceptance_id"] == ACCEPTANCE_ID == "ACC-PFI-V025-S4-P42-HOLDINGS-VALUATION"
    assert contract["current_phase_only"] is True
    assert contract["finder_used"] is False
    assert contract["financial_fixture_fallback_allowed"] is False
    assert contract["cost_basis_guess_allowed"] is False
    assert any(item.startswith("Phase 4.3") for item in contract["explicitly_not_done"])


def test_holding_and_valuation_schemas_are_draft_2020_12_decimal_string_contracts() -> None:
    holding_schema = _json(STAGE_ROOT / "holding_snapshot.schema.json")
    valuation_schema = _json(STAGE_ROOT / "valuation_snapshot.schema.json")
    Draft202012Validator.check_schema(holding_schema)
    Draft202012Validator.check_schema(valuation_schema)

    Draft202012Validator(holding_schema).validate(
        {
            "schema": "PFIV025HoldingSnapshotV1",
            "snapshot_id": "holding-contract-test",
            "account_ref": "opaque-account-contract-ref",
            "instrument_ref": "opaque-instrument-contract-ref",
            "source_id": "SRC-HOLDINGS",
            "quantity": "2",
            "acquisition_cost_ex_fees": "16.00",
            "capitalized_fee_total": "1.00",
            "original_currency": "AUD",
            "cost_basis_method": "source_reported",
            "transaction_link_status": "linked",
            "transaction_event_ids": ["opaque-event-contract-ref"],
            "quantity_as_of": "2026-07-14T05:00:00Z",
            "source_record_count": 1,
            "source_content_hash": "sha256:" + "a" * 64,
        }
    )
    assert holding_schema["properties"]["quantity"]["type"] == "string"
    assert valuation_schema["properties"]["market_value_cny"]["type"] == "string"


def test_holding_requires_decimal_explicit_cost_policy_and_traceable_linkage() -> None:
    holding = _holding()
    assert holding.cost_basis_original == Decimal("17.00")
    assert holding.transaction_event_ids == ("opaque-event-contract-ref",)

    with pytest.raises(TypeError, match="Decimal"):
        HoldingSnapshot(
            snapshot_id="holding-contract-test",
            account_ref="opaque-account-contract-ref",
            instrument_ref="opaque-instrument-contract-ref",
            source_id="SRC-HOLDINGS",
            quantity=2.0,  # type: ignore[arg-type]
            acquisition_cost_ex_fees=Decimal("16"),
            capitalized_fee_total=Decimal("1"),
            original_currency="AUD",
            cost_basis_method="source_reported",
            transaction_link_status="linked",
            transaction_event_ids=("opaque-event-contract-ref",),
            quantity_as_of=datetime(2026, 7, 14, tzinfo=timezone.utc),
            source_record_count=1,
            source_content_hash="sha256:" + "a" * 64,
        )
    with pytest.raises(ValueError, match="cost_basis_method"):
        replace(holding, cost_basis_method="guessed")
    with pytest.raises(ValueError, match="transaction_event_ids"):
        replace(holding, transaction_event_ids=())
    with pytest.raises(ValueError, match="duplicates"):
        replace(
            holding,
            transaction_event_ids=("opaque-event-contract-ref", "opaque-event-contract-ref"),
        )
    source_only = replace(
        holding,
        transaction_link_status="source_snapshot_only",
        transaction_event_ids=(),
    )
    assert source_only.transaction_event_ids == ()


def test_cross_currency_valuation_uses_exact_decimal_and_point_in_time_sources() -> None:
    result = value_holding(
        _holding(),
        _price(),
        fx_snapshot=_fx(),
        valuation_as_of=datetime(2026, 7, 14, 8, 0, tzinfo=timezone.utc),
    )

    assert result["status"] == "ready"
    assert result["market_value_original"] == "20.00"
    assert result["cost_basis_original"] == "17.00"
    assert result["market_value_cny"] == "100.00"
    assert result["cost_basis_cny"] == "85.00"
    assert result["unrealized_pnl_cny"] == "15.00"
    assert result["original_currency"] == "AUD"
    assert result["price_as_of"] == "2026-07-14T06:00:00Z"
    assert result["fx_effective_at"] == "2026-07-14T07:00:00Z"
    assert result["valuation_as_of"] == "2026-07-14T08:00:00Z"
    assert result["calculation_state"] == "calculated_contract_test_only"
    Draft202012Validator(_json(STAGE_ROOT / "valuation_snapshot.schema.json")).validate(result)


def test_cny_valuation_uses_identity_fx_and_does_not_invent_fx_snapshot() -> None:
    result = value_holding(
        _holding(currency="CNY"),
        _price(currency="CNY"),
        fx_snapshot=None,
        valuation_as_of=datetime(2026, 7, 14, 8, 0, tzinfo=timezone.utc),
    )

    assert result["market_value_cny"] == result["market_value_original"] == "20.00"
    assert result["fx_rate"] == "1"
    assert result["fx_snapshot_id"] is None
    assert result["fx_effective_at"] is None


@pytest.mark.parametrize(
    ("price_hour", "fx_hour", "message"),
    [(9, 7, "price_as_of"), (6, 9, "fx_effective_at")],
)
def test_valuation_rejects_future_price_or_fx(
    price_hour: int, fx_hour: int, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        value_holding(
            _holding(),
            _price(hour=price_hour),
            fx_snapshot=_fx(hour=fx_hour),
            valuation_as_of=datetime(2026, 7, 14, 8, 0, tzinfo=timezone.utc),
        )


def test_current_real_investment_dependencies_are_not_loaded_and_values_remain_null() -> None:
    read_model = build_current_investment_read_model(REPO_ROOT)
    metrics = {item["metric_id"]: item for item in read_model["metrics"]}
    metric_validator = Draft202012Validator(_json(STAGE_ROOT / "metric_state.schema.json"))

    assert read_model["status"] == "not_loaded"
    assert read_model["dependency_statuses"] == {
        "SRC-HOLDINGS": "not_loaded",
        "SRC-MARKET-PRICES": "not_loaded",
        "SRC-FX-SNAPSHOT": "not_loaded",
    }
    assert read_model["transactions_available_is_not_holding_proof"] is True
    assert read_model["transaction_holding_inference_used"] is False
    assert read_model["legacy_fx_reference_used"] is False
    assert read_model["financial_fixture_fallback_used"] is False
    assert read_model["financial_values_emitted"] == 0
    assert set(metrics) == {
        "investment_market_value_cny",
        "investment_cost_basis_cny",
        "investment_unrealized_pnl_cny",
    }
    for metric in metrics.values():
        metric_validator.validate(metric)
        assert metric["status"] == "not_loaded"
        assert metric["value"] is None
        assert metric["price_as_of"] is None
        assert metric["fx_effective_at"] is None
        assert metric["valuation_as_of"] is None
        assert metric["read_model_hash"] == read_model["read_model_hash"]
    assert metrics["investment_cost_basis_cny"]["source_ids"] == [
        "SRC-HOLDINGS",
        "SRC-FX-SNAPSHOT",
    ]
    assert metrics["investment_cost_basis_cny"]["component_formula_ids"] == [
        "FORM-PFI-009",
        "FORM-PFI-010",
    ]


def test_investment_api_is_one_surface_only_until_phase_43() -> None:
    read_model = build_current_investment_read_model(REPO_ROOT)
    api = build_investment_api_contract(read_model)

    assert api["surface_ids"] == ["investment"]
    assert api["surfaces"]["investment"]["read_model_hash"] == read_model["read_model_hash"]
    assert api["phase_43_all_surface_consistency_done"] is False


def test_tracked_phase_42_reports_match_runtime_and_are_public_safe() -> None:
    evidence = _json(REPORT_ROOT / "evidence.json")
    read_model = build_current_investment_read_model(REPO_ROOT, observed_at=str(evidence["observed_at"]))

    assert _json(REPORT_ROOT / "investment_read_model.json") == read_model
    assert _json(REPORT_ROOT / "investment_api_contract.json") == build_investment_api_contract(read_model)
    no_fake = _json(REPORT_ROOT / "no_fake_valuation_result.json")
    assert no_fake["result"] == "pass"
    assert no_fake["non_ready_value_count"] == 0
    assert no_fake["financial_values_emitted"] == 0
    assert no_fake["cost_basis_guess_used"] is False
    assert no_fake["legacy_fx_reference_used"] is False
    assert evidence["status"] == "candidate_pass"
    assert evidence["requires_user_acceptance"] is True
    assert evidence["contains_private_values"] is False
