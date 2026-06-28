from __future__ import annotations

import importlib
import unittest
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
        inputs = module.load_stage7_alipay_formula_inputs_from_metadatabase(ROOT.parent / "MetaDatabase" / "PFI" / "alipay_daily")

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

        self.assertGreater(inputs["raw_record_count"], 8000)
        score = module.calculate_confidence_score(inputs["confidence_records"][0])
        self.assertGreaterEqual(score["score"], 70)
        self.assertFalse(score["requires_review"])

        review_score = module.calculate_confidence_score(
            {"impossible_state": True}
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
        inputs = module.load_stage7_alipay_formula_inputs_from_metadatabase(ROOT.parent / "MetaDatabase" / "PFI" / "alipay_daily")
        events = inputs["consumption_events"]
        metrics = module.calculate_consumption_model_metrics(events)
        policies = module.build_stage7_formula_catalog()["consumption_model"]["thresholds"]
        gross_included = {"consumption", "ordinary_consumption", "investment_deposit", "fund_subscription", "bullion_purchase", "investment_buy", "fee"}
        living_included = {"consumption", "ordinary_consumption"}
        expected_gross = sum(Decimal(str(item["amount_cny"])) for item in events if item["event_type"] in gross_included)
        expected_living = sum(Decimal(str(item["amount_cny"])) for item in events if item["event_type"] in living_included)
        refund_offset = sum(Decimal(str(item["amount_cny"])) for item in events if item["event_type"] == "refund")

        self.assertEqual(metrics["gross_consumption_cny"], (expected_gross - refund_offset).quantize(Decimal("0.01")))
        self.assertEqual(metrics["living_consumption_cny"], (expected_living - refund_offset).quantize(Decimal("0.01")))
        self.assertGreater(inputs["event_type_counts"]["fund_subscription"], 0)
        self.assertGreater(inputs["event_type_counts"]["bullion_purchase"], 0)
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
        inputs = module.load_stage7_alipay_formula_inputs_from_metadatabase(ROOT.parent / "MetaDatabase" / "PFI" / "alipay_daily")
        metrics = module.calculate_investment_model_metrics(
            holdings=inputs["investment_holdings"],
            realized_trades=inputs["realized_trades"],
            behavior_trades=inputs["behavior_trades"],
            average_market_value_cny=inputs["average_market_value_cny"],
            idle_cash_cny=inputs["idle_cash_cny"],
            benchmark_return_pct=Decimal("0"),
        )
        thresholds = module.build_stage7_formula_catalog()["investment_model"]["thresholds"]

        self.assertEqual(metrics["market_value_cny"], Decimal("0.00"))
        self.assertEqual(metrics["unrealized_pnl_cny"], Decimal("0.00"))
        self.assertEqual(metrics["realized_pnl_cny"], Decimal("0.00"))
        self.assertEqual(metrics["total_pnl_cny"], Decimal("0.00"))
        self.assertEqual(metrics["fee_drag_rate"], Decimal("0.0000"))
        self.assertEqual(metrics["tax_drag_rate"], Decimal("0.0000"))
        self.assertEqual(metrics["idle_cash_drag_cny"], Decimal("0.00"))
        self.assertIn("暂无真实持仓", metrics["data_status_zh"])
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
        inputs = module.load_stage7_alipay_formula_inputs_from_metadatabase(ROOT.parent / "MetaDatabase" / "PFI" / "alipay_daily")
        projection_inputs = inputs["cashflow_projection_inputs"]
        metrics = module.calculate_cashflow_projection(**projection_inputs)
        expected_future = (
            projection_inputs["current_life_cash_cny"]
            + projection_inputs["expected_income_cny"]
            + projection_inputs["expected_refund_cny"]
            - projection_inputs["fixed_expense_cny"]
            - projection_inputs["flexible_expense_cny"]
            - projection_inputs["debt_repayment_cny"]
            - projection_inputs["planned_investment_deposit_cny"]
            + projection_inputs["planned_investment_return_cny"]
        ).quantize(Decimal("0.01"))
        expected_reserve_floor = max(
            projection_inputs["user_min_reserve_cny"],
            projection_inputs["average_monthly_fixed_expense_cny"] * projection_inputs["reserve_months"],
        ).quantize(Decimal("0.01"))

        self.assertEqual(catalog["windows_days"], (7, 21, 30, 60, 90, 180, 360))
        self.assertEqual(metrics["future_cash_balance_cny"], expected_future)
        self.assertEqual(metrics["reserve_floor_cny"], expected_reserve_floor)
        self.assertGreater(projection_inputs["planned_investment_deposit_cny"], Decimal("0"))
        self.assertIn("计划投资入金", metrics["investment_squeeze_explanation_zh"])
        self.assertGreaterEqual(metrics["cashflow_pressure_score"], Decimal("0"))
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
        self.assertEqual(catalog["schema"], "PFIParametersV022Stage13")
        self.assertEqual(catalog["current_stage"], "Stage 13 - 后置触发型复核")
        self.assertEqual(catalog["stage7_task_ids"], list(governance.V022_STAGE7_TASK_IDS))
        self.assertEqual(catalog["parameters"]["confidence"]["review_threshold"]["value"], 70)
        self.assertEqual(catalog["parameters"]["cashflow"]["windows_days"]["value"], [7, 21, 30, 60, 90, 180, 360])


if __name__ == "__main__":
    unittest.main()
