from __future__ import annotations

import unittest
from pathlib import Path

from pfi_os.application.homepage_summary import empty_homepage_summary
from pfi_v02.stage4_analysis_mvp import (
    STAGE4_CONSUMPTION_SOURCES,
    STAGE4_INVESTMENT_ATTRIBUTION_COMPONENTS,
    build_cashflow_forecast,
    build_consumption_anomalies,
    build_consumption_classification,
    build_consumption_summary,
    build_investment_behavior_review,
    build_qbvs_compatibility_contract,
    build_stage4_analysis_model,
    build_stage4_demo_spending_records,
)


class Stage4AnalysisMvpTest(unittest.TestCase):
    def setUp(self) -> None:
        self.model = build_stage4_analysis_model()

    def test_investment_summary_calculates_market_value_pnl_allocation_and_cash_without_consumption_mix(self) -> None:
        summary = self.model["investment_analysis"]["summary"]

        self.assertGreater(summary["total_market_value_aud"], 0)
        self.assertIn("total_unrealized_pnl_aud", summary)
        self.assertIn("cash_position_aud", summary)
        self.assertTrue(summary["evidence_refs"])
        self.assertIn("consumption", summary["excluded_event_types"])
        self.assertIn("transfer", summary["excluded_event_types"])
        self.assertIn("投资分析只读取投资持仓", summary["stop_condition_check"])
        self.assertAlmostEqual(
            sum(row["weight_pct"] for row in summary["asset_allocation_pct"]),
            100.0,
            delta=0.03,
        )

    def test_investment_attribution_separates_required_components_without_exact_claims(self) -> None:
        attribution = self.model["investment_analysis"]["attribution"]
        components = {row["component"]: row for row in attribution["components"]}

        self.assertEqual(tuple(components), STAGE4_INVESTMENT_ATTRIBUTION_COMPONENTS)
        self.assertEqual(attribution["precision_policy"], "insufficient_data_blocks_exact_conclusion")
        self.assertEqual(attribution["status"], "需要复核")
        for component in components.values():
            self.assertEqual(component["precision"], "estimate")
            self.assertTrue(component["evidence_refs"])

    def test_investment_risk_exposes_concentration_drawdown_currency_and_liquidity_evidence(self) -> None:
        risk = self.model["investment_analysis"]["risk"]

        self.assertIn("largest_instrument_id", risk["concentration"])
        self.assertTrue(risk["concentration"]["evidence_refs"])
        self.assertLess(risk["drawdown"]["max_drawdown_pct"], 0)
        self.assertTrue(risk["drawdown"]["evidence_refs"])
        self.assertGreaterEqual(len(risk["currency_exposure_pct"]), 2)
        self.assertGreater(risk["liquidity"]["slowest_position_days"], 0)
        self.assertTrue(risk["liquidity"]["evidence_refs"])

    def test_behavior_review_only_generates_behavior_tags_when_trade_data_exists(self) -> None:
        behavior = self.model["investment_analysis"]["behavior"]

        self.assertGreater(behavior["trade_count"], 0)
        self.assertIn("追涨", behavior["conclusions"])
        self.assertIn("杀跌", behavior["conclusions"])
        self.assertIn("频繁交易", behavior["conclusions"])

        empty = build_investment_behavior_review(())
        self.assertEqual(empty["trade_count"], 0)
        self.assertEqual(empty["conclusions"], ())
        self.assertIn("缺少交易数据", empty["data_requirement"])

    def test_qbvs_is_external_while_pfi_strategy_lab_features_remain(self) -> None:
        compat = build_qbvs_compatibility_contract()

        self.assertTrue(compat["runtime_moved_out_of_pfi"])
        self.assertFalse(compat["pfi_owns_qbvs"])
        self.assertEqual(compat["legacy_runtime_path"], "QBVS/qbvs")
        self.assertIn("独立系统：CodexProject/QBVS", compat["target_entry"])
        self.assertIn("投资管理 > PFI 策略实验室", compat["pfi_strategy_lab_entry"])
        self.assertIn("盘感训练", compat["preserved_pfi_features"])
        self.assertIn("大数据模拟器", compat["preserved_pfi_features"])

    def test_consumption_summary_excludes_transfers_and_investments_from_spending(self) -> None:
        records = build_stage4_demo_spending_records()
        summary = build_consumption_summary(records, self.model)

        self.assertGreater(summary["month_spend_aud"], 0)
        self.assertGreater(summary["excluded_transfer_aud"], 0)
        self.assertGreater(summary["excluded_investment_aud"], 0)
        self.assertNotIn("cn_broker", summary["source_ids"])
        self.assertEqual(tuple(summary["source_ids"]), STAGE4_CONSUMPTION_SOURCES)
        self.assertGreater(summary["fixed_spend_aud"], 0)
        self.assertGreater(summary["flexible_spend_aud"], 0)
        self.assertIn("转账、基金申购和投资买卖已排除", summary["stop_condition_check"])

    def test_consumption_classifier_covers_sources_and_sends_low_confidence_to_review(self) -> None:
        classification = build_consumption_classification(build_stage4_demo_spending_records())

        self.assertEqual(tuple(classification["covered_sources"]), STAGE4_CONSUMPTION_SOURCES)
        self.assertGreaterEqual(len(classification["rows"]), 8)
        self.assertGreaterEqual(len(classification["review_queue"]), 1)
        for item in classification["review_queue"]:
            self.assertLess(item["confidence"], 0.70)
            self.assertEqual(item["status"], "需要复核")
            self.assertEqual(item["choices"][0], "A 接受分类")

    def test_recurring_subscription_detection_supports_reviewable_subscription_candidates(self) -> None:
        recurring = self.model["consumption_analysis"]["recurring"]

        self.assertGreaterEqual(recurring["candidate_count"], 2)
        self.assertTrue(recurring["review_supported"])
        for item in recurring["candidates"]:
            self.assertEqual(item["status"], "有建议")
            self.assertTrue(item["evidence_ref"])
            self.assertIn("确认保留", item["review_action"])

    def test_anomaly_detection_returns_large_duplicate_night_weekend_and_impulsive_evidence(self) -> None:
        anomalies = build_consumption_anomalies(build_stage4_demo_spending_records())
        kinds = {item["kind"] for item in anomalies["anomalies"]}

        for expected in ("大额消费", "重复扣费", "夜间消费", "节假日/周末消费", "冲动型消费"):
            self.assertIn(expected, kinds)
        for item in anomalies["anomalies"]:
            self.assertEqual(item["status"], "需要复核")
            self.assertTrue(item["evidence_ref"])
        self.assertTrue(anomalies["evidence_required"])

    def test_cashflow_forecast_has_30_90_180_day_views_and_separates_life_cash_from_investment_cash(self) -> None:
        forecast = build_cashflow_forecast(build_stage4_demo_spending_records(), self.model)

        self.assertGreater(forecast["life_cash_aud"], 0)
        self.assertIn("investment_cash_aud", forecast)
        self.assertIn("生活现金和投资现金分开", forecast["cash_separation_policy"])
        self.assertEqual([row["days"] for row in forecast["horizons"]], [30, 90, 180])
        for row in forecast["horizons"]:
            self.assertGreaterEqual(row["available_to_invest_aud"], 0)
            self.assertTrue(row["evidence_refs"])

    def test_homepage_summary_exposes_stage4_dashboard_and_analysis_metric_cards(self) -> None:
        summary = empty_homepage_summary()

        self.assertEqual(summary["stage4_dashboard"]["schema"], "PFIV02Stage4AnalysisMVPV1")
        cards = {row["key"]: row for row in summary["metric_cards"]}
        for key in ("investment_market_value", "investment_pnl", "month_spend", "budget_remaining", "cashflow_pressure"):
            self.assertIn(key, cards)
        self.assertIn("第 4 阶段", summary["evidence_drawer"]["title"])

    def test_web_shell_exposes_stage4_analysis_without_adding_alpha_or_system_first_level_entries(self) -> None:
        root = Path(__file__).resolve().parents[1]
        html = (root / "web" / "index.html").read_text(encoding="utf-8")
        js = (root / "web" / "app" / "shell.js").read_text(encoding="utf-8")

        self.assertIn('data-primary-workspaces="15"', html)
        for label in ("投资总览", "收益归因", "风险分析", "行为复盘", "消费总览", "订阅检测", "异常消费", "现金流预测"):
            self.assertIn(label, js)
        self.assertIn("PFIV02Stage4AnalysisMVPV1", js)
        self.assertNotIn('data-workspace="alpha"', html.lower())
        self.assertNotIn('data-workspace="ralpha"', html.lower())
        self.assertNotIn('data-workspace="system"', html.lower())


if __name__ == "__main__":
    unittest.main()
