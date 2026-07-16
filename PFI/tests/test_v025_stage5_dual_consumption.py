from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from pfi_os.application.metrics.financial_models import (
    ACCEPTANCE_ID,
    CASHFLOW_WINDOWS_DAYS,
    PHASE_ID,
    TASK_IDS,
    FinancialEvent,
    build_cashflow_windows,
    build_dual_metric_surface_contract,
    build_phase52_contract,
    build_taxonomy_tag_contract,
    calculate_dual_consumption,
    validate_primary_category_assignments,
)


def _event(
    source_record_id: str,
    event_date: date,
    event_type: str,
    amount: str,
    direction: str,
    economic_event_id: str,
    group_id: str,
    offset_event_id: str | None = None,
) -> FinancialEvent:
    return FinancialEvent(
        source_record_id=source_record_id,
        economic_event_id=economic_event_id,
        interconnection_group_id=group_id,
        event_date=event_date,
        event_type=event_type,
        amount_cny=Decimal(amount),
        direction=direction,
        offset_economic_event_id=offset_event_id,
    )


def _dual_metric_events() -> tuple[FinancialEvent, ...]:
    return (
        _event("raw_food_a", date(2026, 7, 1), "consumption", "120.00", "outflow", "econ_food", "group_food"),
        _event("raw_food_b", date(2026, 7, 1), "ordinary_consumption", "120.00", "outflow", "econ_food", "group_food"),
        _event("raw_deposit", date(2026, 7, 2), "investment_deposit", "1000.00", "outflow", "econ_deposit", "portfolio_cycle"),
        _event("raw_fund", date(2026, 7, 3), "fund_subscription", "500.00", "outflow", "econ_fund", "group_fund"),
        _event("raw_stock", date(2026, 7, 4), "investment_buy", "700.00", "outflow", "econ_stock", "portfolio_cycle"),
        _event("raw_bullion", date(2026, 7, 5), "bullion_purchase", "900.00", "outflow", "econ_bullion", "group_bullion"),
        _event("raw_fee", date(2026, 7, 5), "fee", "10.00", "outflow", "econ_fee", "group_fee"),
        _event("raw_refund", date(2026, 7, 6), "refund", "20.00", "inflow", "econ_refund", "group_food", "econ_food"),
        _event("raw_repayment", date(2026, 7, 7), "credit_card_repayment", "120.00", "outflow", "econ_repayment", "group_card"),
        _event("raw_internal", date(2026, 7, 7), "internal_transfer", "80.00", "internal", "econ_internal", "group_internal"),
    )


def test_phase52_contract_stops_before_phase53_and_real_validation() -> None:
    contract = build_phase52_contract()

    assert PHASE_ID == "V025-S5-P5.2"
    assert TASK_IDS == ("S5-P2-T1", "S5-P2-T2", "S5-P2-T3", "S5-P2-T4")
    assert ACCEPTANCE_ID == "ACC-PFI-V025-S5-P52-FINANCIAL-MODELS"
    assert contract["current_phase_only"] is True
    assert contract["phase_5_3_started"] is False
    assert contract["real_data_model_validation_completed"] is False
    assert contract["finder_used"] is False
    assert contract["push_performed"] is False
    assert contract["app_install_performed"] is False


def test_dual_consumption_deduplicates_sources_and_explains_two_investment_stages() -> None:
    metrics = calculate_dual_consumption(_dual_metric_events())

    assert metrics["source_record_count"] == 10
    assert metrics["deduped_economic_event_type_count"] == 9
    assert metrics["total_consumption_outflow_cny"] == Decimal("3210.00")
    assert metrics["living_consumption_cny"] == Decimal("100.00")
    assert metrics["investment_funding_outflow_cny"] == Decimal("1000.00")
    assert metrics["investment_allocation_amount_cny"] == Decimal("2100.00")
    assert metrics["financial_fee_outflow_cny"] == Decimal("10.00")
    assert metrics["refund_offset_cny"] == Decimal("20.00")
    assert metrics["component_reconciliation_difference_cny"] == Decimal("0.00")
    assert metrics["funding_and_allocation_group_count"] == 1
    assert metrics["investment_activity_is_net_worth_loss"] is False
    assert "不同活动阶段" in metrics["funding_allocation_explanation_zh"]

    surfaces = build_dual_metric_surface_contract(metrics)
    assert tuple(surfaces["surface_ids"]) == ("homepage", "consumption_page", "report")
    assert len(set(surfaces["surface_hashes"].values())) == 1
    for surface in surfaces["surfaces"].values():
        assert surface["消费总流出金额（用户定义活动口径）"] == "3210.00"
        assert surface["生活消费金额"] == "100.00"
        assert surface["投资资金流出金额"] == "1000.00"
        assert surface["投资域内配置金额"] == "2100.00"
        assert surface["不等于净资产损失"] is True


def test_dual_consumption_fails_closed_on_conflicting_duplicate_or_unlinked_refund() -> None:
    conflicting = (
        _event("raw_a", date(2026, 7, 1), "consumption", "100.00", "outflow", "econ_same", "group_same"),
        _event("raw_b", date(2026, 7, 1), "ordinary_consumption", "101.00", "outflow", "econ_same", "group_same"),
    )
    with pytest.raises(ValueError, match="conflicting duplicate"):
        calculate_dual_consumption(conflicting)

    unlinked_refund = (
        _event("raw_refund", date(2026, 7, 2), "refund", "10.00", "inflow", "econ_refund", "group_refund"),
    )
    with pytest.raises(ValueError, match="offset_economic_event_id"):
        calculate_dual_consumption(unlinked_refund)


def test_cashflow_has_exact_seven_windows_and_empty_windows_are_not_false_zero() -> None:
    events = (
        _event("income", date(2026, 7, 15), "income", "1000.00", "inflow", "econ_income", "group_income"),
        _event("food", date(2026, 7, 14), "consumption", "100.00", "outflow", "econ_food", "group_food"),
        _event("deposit", date(2026, 7, 10), "investment_deposit", "200.00", "outflow", "econ_deposit", "group_deposit"),
        _event("older", date(2026, 6, 20), "fee", "300.00", "outflow", "econ_older", "group_older"),
        _event("oldest", date(2026, 5, 1), "consumption", "400.00", "outflow", "econ_oldest", "group_oldest"),
        _event("internal", date(2026, 7, 15), "internal_transfer", "999.00", "internal", "econ_internal", "group_internal"),
    )
    result = build_cashflow_windows(events, as_of=date(2026, 7, 15))

    assert CASHFLOW_WINDOWS_DAYS == (7, 21, 30, 60, 90, 180, 360)
    assert tuple(result["windows"]) == CASHFLOW_WINDOWS_DAYS
    seven = result["metrics"][7]
    assert seven["status"] == "ready"
    assert seven["external_inflow_cny"] == Decimal("1000.00")
    assert seven["external_outflow_cny"] == Decimal("300.00")
    assert seven["net_cashflow_cny"] == Decimal("700.00")
    assert seven["internal_transfer_cny"] == Decimal("999.00")
    assert result["metrics"][30]["external_outflow_cny"] == Decimal("600.00")
    assert result["metrics"][90]["external_outflow_cny"] == Decimal("1000.00")

    empty = build_cashflow_windows((), as_of=date(2026, 7, 15))
    assert empty["metrics"][7]["status"] == "filtered_empty"
    assert empty["metrics"][7]["external_inflow_cny"] is None
    assert empty["metrics"][7]["external_outflow_cny"] is None
    assert empty["metrics"][7]["net_cashflow_cny"] is None


def test_taxonomy_and_tag_contract_preserves_v022_limits_and_one_primary_category() -> None:
    contract = build_taxonomy_tag_contract()

    assert contract["taxonomy_validation"]["status"] == "通过"
    assert contract["taxonomy_validation"]["l1_count"] <= 12
    assert contract["taxonomy_validation"]["max_l2_per_l1_actual"] <= 5
    assert contract["taxonomy_validation"]["l2_total"] <= 50
    assert contract["primary_category_per_transaction"] == 1
    assert contract["default_tag_count"] > 0
    assert contract["tag_types"] == ["default", "custom"]
    assert contract["tag_history_required"] is True
    assert contract["view_filter_modes"] == ["all", "any"]

    assert validate_primary_category_assignments(
        [
            {"source_record_id": "raw_1", "primary_category_id": "food_01", "tag_ids": ["tag_consumption_large"]},
            {"source_record_id": "raw_2", "primary_category_id": "transport_01", "tag_ids": []},
        ]
    )["status"] == "pass"
    with pytest.raises(ValueError, match="exactly one primary category"):
        validate_primary_category_assignments(
            [
                {"source_record_id": "raw_1", "primary_category_id": "food_01", "tag_ids": []},
                {"source_record_id": "raw_1", "primary_category_id": "shopping_01", "tag_ids": []},
            ]
        )
