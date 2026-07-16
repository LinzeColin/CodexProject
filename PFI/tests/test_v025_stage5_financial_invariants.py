from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from pfi_os.application.metrics.financial_models import (
    CashRollforward,
    CoreFinancialSnapshot,
    InvestmentReallocation,
    XirrCashFlow,
    build_financial_model_parameter_consistency_report,
    calculate_investment_metrics,
    calculate_net_worth,
    calculate_xirr,
    evaluate_core_invariants,
)


def test_net_worth_cash_and_reallocation_invariants_reconcile_exactly() -> None:
    snapshot = CoreFinancialSnapshot(
        cash_cny=Decimal("1000.00"),
        investment_market_value_cny=Decimal("500.00"),
        other_assets_cny=Decimal("200.00"),
        liabilities_cny=Decimal("300.00"),
        reported_net_worth_cny=Decimal("1400.00"),
    )
    cash = CashRollforward(
        opening_cash_cny=Decimal("1000.00"),
        external_inflows_cny=Decimal("500.00"),
        external_outflows_cny=Decimal("200.00"),
        adjustments_cny=Decimal("0.00"),
        closing_cash_cny=Decimal("1300.00"),
    )
    reallocation = InvestmentReallocation(
        life_cash_before_cny=Decimal("1000.00"),
        investment_assets_before_cny=Decimal("500.00"),
        life_cash_after_cny=Decimal("800.00"),
        investment_assets_after_cny=Decimal("700.00"),
        explicit_fee_cny=Decimal("0.00"),
    )

    assert calculate_net_worth(snapshot) == Decimal("1400.00")
    result = evaluate_core_invariants(snapshot, cash, reallocation)
    assert result["status"] == "pass"
    assert result["ledger_conserved"] is True
    assert result["net_worth_discrepancy_cny"] == Decimal("0.00")
    assert result["cash_rollforward_discrepancy_cny"] == Decimal("0.00")
    assert result["investment_reallocation_discrepancy_cny"] == Decimal("0.00")
    assert result["net_worth_cny"] == Decimal("1400.00")
    assert result["model_validation"] == "blocked_pending_phase_5_3_real_data"


def test_failed_invariant_is_fail_closed_and_emits_no_financial_value() -> None:
    snapshot = CoreFinancialSnapshot(
        cash_cny=Decimal("100.00"),
        investment_market_value_cny=Decimal("0.00"),
        other_assets_cny=Decimal("0.00"),
        liabilities_cny=Decimal("0.00"),
        reported_net_worth_cny=Decimal("99.00"),
    )
    cash = CashRollforward(
        opening_cash_cny=Decimal("100.00"),
        external_inflows_cny=Decimal("0.00"),
        external_outflows_cny=Decimal("0.00"),
        adjustments_cny=Decimal("0.00"),
        closing_cash_cny=Decimal("100.00"),
    )
    reallocation = InvestmentReallocation(
        life_cash_before_cny=Decimal("100.00"),
        investment_assets_before_cny=Decimal("0.00"),
        life_cash_after_cny=Decimal("100.00"),
        investment_assets_after_cny=Decimal("0.00"),
        explicit_fee_cny=Decimal("0.00"),
    )

    result = evaluate_core_invariants(snapshot, cash, reallocation)
    assert result["status"] == "failed_closed"
    assert result["ledger_conserved"] is False
    assert result["net_worth_cny"] is None
    assert result["blocking_reason_zh"]


def test_investment_return_cost_fee_fx_and_cash_drag_are_explicit() -> None:
    metrics = calculate_investment_metrics(
        market_value_cny=Decimal("2000.00"),
        remaining_cost_cny=Decimal("1500.00"),
        sell_proceeds_cny=Decimal("1000.00"),
        allocated_cost_cny=Decimal("800.00"),
        transaction_fees_cny=Decimal("20.00"),
        taxes_cny=Decimal("10.00"),
        dividends_cny=Decimal("50.00"),
        interest_cny=Decimal("0.00"),
        holding_costs_cny=Decimal("5.00"),
        gross_trade_value_cny=Decimal("2000.00"),
        original_currency_exposure=Decimal("1000.00"),
        current_fx_to_cny=Decimal("4.50"),
        reference_fx_to_cny=Decimal("4.80"),
        idle_cash_cny=Decimal("500.00"),
        benchmark_return_rate=Decimal("0.05"),
    )

    assert metrics["unrealized_pnl_cny"] == Decimal("500.00")
    assert metrics["realized_pnl_before_costs_cny"] == Decimal("200.00")
    assert metrics["realized_pnl_net_cny"] == Decimal("170.00")
    assert metrics["total_return_net_cny"] == Decimal("715.00")
    assert metrics["fee_drag_rate"] == Decimal("0.0125")
    assert metrics["tax_drag_rate"] == Decimal("0.0050")
    assert metrics["fx_effect_cny"] == Decimal("-300.00")
    assert metrics["fx_drag_cny"] == Decimal("300.00")
    assert metrics["idle_cash_drag_cny"] == Decimal("25.00")
    assert metrics["calculation_context"] == "contract_test_only"
    assert metrics["model_validation"] == "blocked_pending_phase_5_3_real_data"

    zero_denominator = calculate_investment_metrics(
        market_value_cny=Decimal("0"),
        remaining_cost_cny=Decimal("0"),
        sell_proceeds_cny=Decimal("0"),
        allocated_cost_cny=Decimal("0"),
        transaction_fees_cny=Decimal("0"),
        taxes_cny=Decimal("0"),
        dividends_cny=Decimal("0"),
        interest_cny=Decimal("0"),
        holding_costs_cny=Decimal("0"),
        gross_trade_value_cny=Decimal("0"),
        original_currency_exposure=Decimal("0"),
        current_fx_to_cny=Decimal("1"),
        reference_fx_to_cny=Decimal("1"),
        idle_cash_cny=Decimal("0"),
        benchmark_return_rate=Decimal("0"),
    )
    assert zero_denominator["fee_drag_rate"] is None
    assert zero_denominator["tax_drag_rate"] is None


def test_xirr_is_date_aware_and_rejects_non_unique_sign_patterns() -> None:
    result = calculate_xirr(
        (
            XirrCashFlow(date(2026, 1, 1), Decimal("-1000.00"), "investment_funding"),
            XirrCashFlow(date(2027, 1, 1), Decimal("1100.00"), "terminal_value"),
        )
    )
    assert abs(result["xirr"] - Decimal("0.10")) <= Decimal("0.00000001")
    assert result["day_count_basis"] == 365
    assert result["cashflow_count"] == 2
    assert result["residual_abs"] <= Decimal("0.00000001")
    assert result["model_validation"] == "blocked_pending_phase_5_3_real_data"

    with pytest.raises(ValueError, match="non-unique"):
        calculate_xirr(
            (
                XirrCashFlow(date(2026, 1, 1), Decimal("-100.00"), "investment_funding"),
                XirrCashFlow(date(2026, 6, 1), Decimal("230.00"), "investment_return"),
                XirrCashFlow(date(2027, 1, 1), Decimal("-132.00"), "investment_funding"),
            )
        )


def test_phase52_parameter_carriers_have_zero_conflict() -> None:
    report = build_financial_model_parameter_consistency_report()

    assert report["status"] == "pass"
    assert report["conflict_count"] == 0
    assert report["carriers"] == [
        "formula_registry_json",
        "pfi_parameters_yaml",
        "python_runtime",
        "ui_report_contract",
        "模型参数文件.md",
    ]
