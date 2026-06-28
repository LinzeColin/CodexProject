from __future__ import annotations

import importlib
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV022Stage7FormulaScoring(unittest.TestCase):
    def _module(self):
        try:
            return importlib.import_module("pfi_v02.stage_v022_formula_scoring")
        except ModuleNotFoundError as exc:
            self.fail(f"Stage 7 formula/scoring module is missing: {exc}")

    def test_stage7_contract_locks_phase_task_acceptance_and_validation(self) -> None:
        governance = importlib.import_module("pfi_v02.stage_v022_database_governance")
        build_contract = getattr(governance, "build_v022_stage7_contract", None)
        self.assertIsNotNone(build_contract, "build_v022_stage7_contract() is required")

        contract = build_contract()

        self.assertEqual(contract["schema"], "PFIV022FormulaScoringStage7ContractV1")
        self.assertEqual(contract["stage"], "Stage 7")
        self.assertEqual(
            tuple(contract["task_ids"]),
            (
                "S7-P1-T1",
                "S7-P1-T2",
                "S7-P1-T3",
                "S7-P2-T1",
                "S7-P2-T2",
                "S7-P2-T3",
                "S7-P2-T4",
                "S7-P3-T1",
                "S7-P3-T2",
                "S7-P3-T3",
                "S7-P4-T1",
                "S7-P4-T2",
                "S7-P4-T3",
            ),
        )
        for required in (
            "字段完整度 30",
            "统一复核阈值 70",
            "消费总流出金额",
            "持仓数量 × 最新价格 × 汇率",
            "7 / 21 / 30 / 60 / 90 / 180 / 360",
            "Stage 8 Runtime Diff 不在本轮实现",
        ):
            self.assertIn(required, str(contract))

    def test_confidence_score_uses_exact_100_point_weights_and_single_review_threshold(self) -> None:
        module = self._module()
        model = module.build_confidence_scoring_model()

        weights = model["weights"]
        self.assertEqual(
            weights,
            {
                "field_completeness": 30,
                "amount_direction": 10,
                "rule_match": 20,
                "counterparty": 15,
                "interconnection": 15,
                "history_consistency": 10,
            },
        )
        self.assertEqual(sum(weights.values()), 100)
        self.assertEqual(model["review_threshold"], 70)
        self.assertEqual(model["threshold_policy"], "single_global_threshold")
        self.assertFalse(model["source_layered_thresholds_allowed"])

        score = module.calculate_confidence_score(
            {
                "field_completeness": "complete",
                "amount_direction": "clear",
                "rule_match": "exact",
                "counterparty": "exact",
                "interconnection": "not_required_or_exact",
                "history_consistency": "repeated_pattern",
                "deductions": {"blurry_description": 0, "duplicate_suspect": 0, "stale_fx_snapshot": 0},
            }
        )
        self.assertEqual(score["score"], 100)
        self.assertFalse(score["requires_review"])

        review_score = module.calculate_confidence_score(
            {
                "field_completeness": "missing_key_field",
                "amount_direction": "inferred",
                "rule_match": "weak_fallback",
                "counterparty": "keyword_only",
                "interconnection": "single_sided_should_match",
                "history_consistency": "new_but_reasonable",
                "deductions": {"blurry_description": 5},
            }
        )
        self.assertLess(review_score["score"], 70)
        self.assertTrue(review_score["requires_review"])

    def test_confidence_score_has_chinese_standards_for_every_component(self) -> None:
        module = self._module()
        standards = module.build_confidence_scoring_model()["standards"]

        for component in ("field_completeness", "amount_direction", "rule_match", "counterparty", "interconnection", "history_consistency"):
            with self.subTest(component=component):
                item = standards[component]
                self.assertEqual(tuple(item["bands"]), ("0分", "低分", "中分", "高分", "满分"))
                self.assertRegex(item["zero_zh"], r"[\u4e00-\u9fff]")
                self.assertRegex(item["low_zh"], r"[\u4e00-\u9fff]")
                self.assertRegex(item["medium_zh"], r"[\u4e00-\u9fff]")
                self.assertRegex(item["high_zh"], r"[\u4e00-\u9fff]")
                self.assertRegex(item["full_zh"], r"[\u4e00-\u9fff]")

    def test_consumption_formulas_thresholds_and_subscription_score_are_explainable(self) -> None:
        module = self._module()
        events = (
            {"event_type": "consumption", "amount_cny": Decimal("100.00"), "direction": "outflow"},
            {"event_type": "investment_deposit", "amount_cny": Decimal("1000.00"), "direction": "outflow"},
            {"event_type": "fund_subscription", "amount_cny": Decimal("500.00"), "direction": "outflow"},
            {"event_type": "bullion_purchase", "amount_cny": Decimal("200.00"), "direction": "outflow"},
            {"event_type": "investment_buy", "amount_cny": Decimal("700.00"), "direction": "outflow"},
            {"event_type": "fee", "amount_cny": Decimal("30.00"), "direction": "outflow"},
            {"event_type": "refund", "amount_cny": Decimal("20.00"), "direction": "inflow", "linked_original_event_type": "consumption"},
        )
        metrics = module.calculate_consumption_model_metrics(events)
        policies = module.build_stage7_formula_catalog()["consumption_model"]["thresholds"]

        self.assertEqual(metrics["gross_consumption_cny"], Decimal("2510.00"))
        self.assertEqual(metrics["living_consumption_cny"], Decimal("80.00"))
        self.assertEqual(policies["large_spend"]["cny_threshold"], Decimal("2000"))
        self.assertEqual(policies["large_spend"]["aud_original_threshold"], Decimal("500"))
        self.assertTrue(module.is_large_spend(amount_cny=Decimal("2000"), original_amount=Decimal("100"), original_currency="CNY"))
        self.assertTrue(module.is_large_spend(amount_cny=Decimal("1500"), original_amount=Decimal("500"), original_currency="AUD"))
        self.assertEqual(policies["night_window"], {"start": "22:00", "end": "06:00", "electronics_impulse_independent_rule": False})
        self.assertTrue(module.is_night_spend("23:30"))
        self.assertTrue(module.is_night_spend("05:59"))
        self.assertFalse(module.is_night_spend("12:00"))
        self.assertEqual(module.calculate_subscription_score(Decimal("1"), Decimal("1"), Decimal("1"), Decimal("1")), Decimal("100.00"))
        self.assertEqual(policies["subscription_score_threshold"], Decimal("75"))

    def test_investment_formulas_include_fx_fee_tax_behavior_and_xirr_policy(self) -> None:
        module = self._module()
        holdings = (
            {
                "symbol": "MOCK",
                "quantity": Decimal("10"),
                "latest_price": Decimal("12"),
                "price_currency": "AUD",
                "fx_to_cny": Decimal("4.6874"),
                "remaining_cost_cny": Decimal("450.00"),
            },
        )
        realized_trades = (
            {"sell_proceeds_cny": Decimal("1000"), "allocated_cost_cny": Decimal("800"), "fees_cny": Decimal("20"), "tax_cny": Decimal("10")},
        )
        behavior_trades = (
            {"trade_date": date(2026, 6, 1), "side": "buy", "amount_cny": Decimal("1000"), "pre_trade_return_pct": Decimal("0.04"), "holding_days": 2},
            {"trade_date": date(2026, 6, 3), "side": "sell", "amount_cny": Decimal("800"), "pre_trade_return_pct": Decimal("-0.06"), "holding_days": 2},
            {"trade_date": date(2026, 6, 5), "side": "buy", "amount_cny": Decimal("700"), "pre_trade_return_pct": Decimal("0.01"), "holding_days": 10},
            {"trade_date": date(2026, 6, 7), "side": "buy", "amount_cny": Decimal("600"), "pre_trade_return_pct": Decimal("0.01"), "holding_days": 10},
            {"trade_date": date(2026, 6, 9), "side": "buy", "amount_cny": Decimal("500"), "pre_trade_return_pct": Decimal("0.01"), "holding_days": 10},
            {"trade_date": date(2026, 6, 11), "side": "sell", "amount_cny": Decimal("400"), "pre_trade_return_pct": Decimal("-0.01"), "holding_days": 10},
            {"trade_date": date(2026, 6, 13), "side": "buy", "amount_cny": Decimal("300"), "pre_trade_return_pct": Decimal("0.01"), "holding_days": 10},
        )
        metrics = module.calculate_investment_model_metrics(
            holdings=holdings,
            realized_trades=realized_trades,
            behavior_trades=behavior_trades,
            average_market_value_cny=Decimal("5000.00"),
            idle_cash_cny=Decimal("1000.00"),
            benchmark_return_pct=Decimal("0.03"),
        )
        thresholds = module.build_stage7_formula_catalog()["investment_model"]["thresholds"]

        self.assertEqual(metrics["market_value_cny"], Decimal("562.49"))
        self.assertEqual(metrics["unrealized_pnl_cny"], Decimal("112.49"))
        self.assertEqual(metrics["realized_pnl_cny"], Decimal("170.00"))
        self.assertEqual(metrics["total_pnl_cny"], Decimal("282.49"))
        self.assertEqual(metrics["fee_drag_rate"], Decimal("0.0047"))
        self.assertEqual(metrics["tax_drag_rate"], Decimal("0.0588"))
        self.assertEqual(metrics["idle_cash_drag_cny"], Decimal("30.00"))
        self.assertTrue(metrics["behavior"]["chase_candidate"])
        self.assertTrue(metrics["behavior"]["panic_sell_candidate"])
        self.assertTrue(metrics["behavior"]["short_hold_candidate"])
        self.assertTrue(metrics["behavior"]["frequent_trading"])
        self.assertEqual(thresholds["chase_candidate"]["pre_buy_rise_pct"], Decimal("0.03"))
        self.assertEqual(thresholds["panic_sell_candidate"]["pre_sell_drop_pct"], Decimal("-0.05"))
        self.assertEqual(thresholds["short_hold_days"], 3)
        self.assertEqual(thresholds["frequent_trade_count_30d"], 6)
        self.assertEqual(thresholds["turnover_rate_pct"], Decimal("0.50"))
        self.assertEqual(thresholds["concentration_watch_pct"], Decimal("0.35"))
        self.assertEqual(thresholds["concentration_high_risk_pct"], Decimal("0.50"))
        self.assertIn("投资入金：负现金流", metrics["xirr_policy_zh"])

    def test_cashflow_windows_reserve_pressure_and_investment_squeeze_are_calculable(self) -> None:
        module = self._module()
        catalog = module.build_stage7_formula_catalog()["cashflow"]
        metrics = module.calculate_cashflow_projection(
            horizon_days=30,
            current_life_cash_cny=Decimal("10000"),
            expected_income_cny=Decimal("5000"),
            expected_refund_cny=Decimal("500"),
            fixed_expense_cny=Decimal("3000"),
            flexible_expense_cny=Decimal("1500"),
            debt_repayment_cny=Decimal("1000"),
            planned_investment_deposit_cny=Decimal("4000"),
            planned_investment_return_cny=Decimal("500"),
            user_min_reserve_cny=Decimal("6000"),
            average_monthly_fixed_expense_cny=Decimal("2500"),
            reserve_months=Decimal("3"),
            income_uncertainty=Decimal("0.20"),
            large_spend_pressure=Decimal("0.30"),
        )

        self.assertEqual(catalog["windows_days"], (7, 21, 30, 60, 90, 180, 360))
        self.assertEqual(metrics["future_cash_balance_cny"], Decimal("6500.00"))
        self.assertEqual(metrics["reserve_floor_cny"], Decimal("7500.00"))
        self.assertTrue(metrics["investment_deposit_squeezes_life_cash"])
        self.assertGreater(metrics["cashflow_pressure_score"], Decimal("0"))
        self.assertLessEqual(metrics["cashflow_pressure_score"], Decimal("100"))
        self.assertEqual(
            tuple(catalog["required_visualizations"]),
            ("现金流阶梯图", "现金流瀑布图", "储备金安全带", "未来大额流出时间轴", "消费-投资挤压图", "现金流窗口对比表"),
        )

    def test_stage7_docs_and_parameter_catalog_record_formula_scoring_governance(self) -> None:
        expected_docs = (
            ROOT / "docs" / "pfi_v022" / "STAGE7_FORMULA_SCORING.md",
            ROOT / "docs" / "pfi_v022" / "ROADMAP_LOCK.md",
            ROOT / "模型参数文件.md",
            ROOT / "功能清单.md",
            ROOT / "开发记录.md",
        )
        for path in expected_docs:
            self.assertTrue(path.exists(), f"{path} must exist for Stage 7")
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("Stage 7 - 模型公式、阈值与评分标准", text)
                self.assertIn("S7-P1-T1", text)
                self.assertIn("置信度评分", text)
                self.assertIn("消费总流出金额", text)
                self.assertIn("投资市值", text)
                self.assertIn("现金流压力分", text)

        governance = importlib.import_module("pfi_v02.stage_v022_database_governance")
        catalog = governance.load_v022_parameter_catalog(ROOT / "config" / "pfi_parameters.yaml")
        self.assertEqual(catalog["schema"], "PFIParametersV022Stage9")
        self.assertEqual(catalog["current_stage"], "Stage 9 - 可视化与 UI/UX")
        self.assertEqual(catalog["stage7_task_ids"], list(governance.V022_STAGE7_TASK_IDS))
        self.assertEqual(catalog["parameters"]["confidence"]["review_threshold"]["value"], 70)
        self.assertEqual(catalog["parameters"]["cashflow"]["windows_days"]["value"], [7, 21, 30, 60, 90, 180, 360])


if __name__ == "__main__":
    unittest.main()
