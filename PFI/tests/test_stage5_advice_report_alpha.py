from __future__ import annotations

import unittest
from pathlib import Path

from pfi_os.application.homepage_summary import empty_homepage_summary
from pfi_v02.stage5_advice_report_alpha import (
    ALPHA_CONTEXT_SCHEMA,
    EXPORT_FORMATS,
    RECOMMENDATION_DECISIONS,
    apply_recommendation_decision,
    build_export_center,
    build_stage5_recommendations,
    build_stage5_delivery_model,
    rank_top_recommendations,
)
from pfi_v02.stage4_analysis_mvp import build_stage4_analysis_model


class Stage5AdviceReportAlphaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.model = build_stage5_delivery_model()

    def test_recommendation_model_has_required_fields_and_evidence(self) -> None:
        recommendations = self.model["recommendations"]

        self.assertGreaterEqual(len(recommendations), 8)
        for item in recommendations:
            self.assertTrue(item["domain"])
            self.assertTrue(item["evidence_refs"], item["recommendation_id"])
            self.assertTrue(item["expected_effect"])
            self.assertTrue(item["tradeoff_risk"])
            self.assertTrue(item["suggested_action"])
            self.assertIn(item["owner_decision"], RECOMMENDATION_DECISIONS)
            self.assertTrue(item["status"])

    def test_review_lifecycle_supports_accept_reject_snooze_review_and_effect_measurement(self) -> None:
        lifecycle = self.model["review_lifecycle"]
        first = self.model["recommendations"][0]

        self.assertTrue(lifecycle["decision_record_supported"])
        self.assertTrue(lifecycle["manual_review_required"])
        self.assertEqual(tuple(lifecycle["rows"][0]["supported_decisions"]), RECOMMENDATION_DECISIONS)

        recommendation_obj = rank_top_recommendations(build_stage5_recommendations(build_stage4_analysis_model()))[0]
        for decision in ("accept", "reject", "snooze", "review", "effect_measured"):
            result = apply_recommendation_decision(recommendation_obj, decision, measured_effect=1.0)
            self.assertEqual(result["decision_record"]["decision"], decision)
            self.assertTrue(result["decision_record"]["evidence_refs"])
            self.assertTrue(result["effect_measurement"]["enabled"])
        self.assertEqual(first["owner_decision"], "pending")

    def test_investment_recommendations_cover_required_controls_with_reasons(self) -> None:
        by_type = {item["recommendation_type"]: item for item in self.model["recommendations"] if item["domain"] == "investment"}

        for rec_type in ("concentration", "trading_frequency", "cash_position", "strategy_pause_or_launch"):
            self.assertIn(rec_type, by_type)
            self.assertTrue(by_type[rec_type]["evidence_refs"])
            self.assertTrue(by_type[rec_type]["tradeoff_risk"])
            self.assertIn(by_type[rec_type]["target_entry"], ("投资管理", "建议与复盘"))

    def test_consumption_recommendations_have_savings_targets(self) -> None:
        by_type = {item["recommendation_type"]: item for item in self.model["recommendations"] if item["domain"] == "consumption"}

        for rec_type in ("budget", "subscription", "anomaly", "cost_saving"):
            self.assertIn(rec_type, by_type)
            self.assertTrue(by_type[rec_type]["evidence_refs"])
            self.assertGreater(by_type[rec_type]["savings_target_aud"], 0.0)

    def test_top_n_ranking_keeps_homepage_quiet_without_removing_lifecycle(self) -> None:
        top = self.model["top_recommendations"]
        all_recs = self.model["recommendations"]
        expected_top_ids = [
            item.recommendation_id
            for item in rank_top_recommendations(build_stage5_recommendations(build_stage4_analysis_model()))
        ]

        self.assertLessEqual(len(top), 3)
        self.assertGreater(len(all_recs), len(top))
        self.assertEqual([item["recommendation_id"] for item in top], expected_top_ids)
        lifecycle_ids = {row["recommendation_id"] for row in self.model["review_lifecycle"]["rows"]}
        self.assertEqual({item["recommendation_id"] for item in all_recs}, lifecycle_ids)

    def test_monthly_report_contains_required_sections_and_evidence_chain(self) -> None:
        report = self.model["reports"]["monthly_report"]

        for section in ("净资产", "现金流", "消费", "投资", "建议复盘"):
            self.assertIn(section, report["required_sections"])
        self.assertTrue(report["has_evidence_chain"])
        self.assertTrue(report["evidence_refs"])

    def test_investment_report_separates_valuation_risk_attribution_position_and_behavior(self) -> None:
        report = self.model["reports"]["investment_report"]

        for section in ("收益", "风险", "归因", "持仓", "行为复盘"):
            self.assertIn(section, report["required_sections"])
        self.assertIn("return", report["sections"])
        self.assertIn("attribution", report["sections"])
        self.assertIn("behavior", report["sections"])

    def test_consumption_report_explains_category_budget_subscription_anomaly_and_savings(self) -> None:
        report = self.model["reports"]["consumption_report"]

        for section in ("分类", "预算", "订阅", "异常", "节省金额"):
            self.assertIn(section, report["required_sections"])
        self.assertGreater(report["sections"]["saving_target_aud"], 0)

    def test_data_quality_report_includes_sync_missing_reconciliation_and_parser_errors(self) -> None:
        report = self.model["reports"]["data_quality_report"]

        for section in ("同步状态", "缺失区间", "对账差异", "parser 错误"):
            self.assertIn(section, report["required_sections"])
        self.assertIn("sync_status", report["sections"])
        self.assertIn("missing_intervals", report["sections"])
        self.assertIn("reconciliation_differences", report["sections"])
        self.assertIn("parser_errors", report["sections"])

    def test_export_center_prefers_markdown_json_csv_and_is_reproducible(self) -> None:
        export_center = self.model["export_center"]
        rerun = build_export_center(self.model["reports"], generated_at=self.model["generated_at"])

        self.assertEqual(tuple(export_center["preferred_formats"]), EXPORT_FORMATS)
        self.assertEqual({item["format"] for item in export_center["exports"]}, set(EXPORT_FORMATS))
        self.assertTrue(all(item["reproducible"] for item in export_center["exports"]))
        self.assertEqual(export_center["reproducibility_key"], rerun["reproducibility_key"])

    def test_alpha_context_schema_and_export_fields_are_read_only(self) -> None:
        snapshot = self.model["alpha_context_export"]

        self.assertEqual(snapshot["schema"], ALPHA_CONTEXT_SCHEMA)
        self.assertTrue(snapshot["version"])
        self.assertTrue(snapshot["generated_at"])
        for key in ("net_worth_aud", "investable_cash_aud", "portfolio_allocation", "risk_budget", "cashflow_pressure", "behavior_tags", "data_freshness"):
            self.assertIn(key, snapshot)
        constraints = snapshot["constraints"]
        self.assertFalse(constraints["trading_password_available"])
        self.assertFalse(constraints["live_trade_submission_authorized"])
        self.assertFalse(constraints["broker_order_submission_authorized"])
        self.assertFalse(constraints["payment_submission_authorized"])

    def test_alpha_remains_independent_and_is_not_pfi_first_level_entry(self) -> None:
        independence = self.model["alpha_independence"]
        compatibility = self.model["compatibility"]

        self.assertFalse(independence["alpha_repo_modified"])
        self.assertFalse(independence["alpha_first_level_entry_added"])
        self.assertTrue(independence["pfi_exports_context_only"])
        self.assertFalse(compatibility["alpha_first_level_entry_added"])
        self.assertFalse(compatibility["ralpha_first_level_entry_added"])

    def test_homepage_summary_exposes_stage5_top_recommendations_and_context_export(self) -> None:
        summary = empty_homepage_summary()

        self.assertEqual(summary["stage5_dashboard"]["schema"], "PFIV02Stage5AdviceReportAlphaExportV1")
        self.assertGreaterEqual(len(summary["decision_rows"]), 3)
        self.assertIn("Stage 5", summary["evidence_drawer"]["title"])
        self.assertEqual(summary["stage5_dashboard"]["alpha_context_export"]["schema"], ALPHA_CONTEXT_SCHEMA)

    def test_web_shell_exposes_stage5_labels_without_alpha_first_level_entry(self) -> None:
        root = Path(__file__).resolve().parents[1]
        html = (root / "web" / "index.html").read_text(encoding="utf-8")
        js = (root / "web" / "app" / "shell.js").read_text(encoding="utf-8")

        self.assertIn('data-primary-workspaces="8"', html)
        for label in ("建议模型", "Review lifecycle", "投资建议", "消费建议", "月度报告", "投资报告", "消费报告", "数据质量报告", "PFI Context Export"):
            self.assertIn(label, js)
        self.assertNotIn('data-workspace="alpha"', html.lower())
        self.assertNotIn('data-workspace="ralpha"', html.lower())
        self.assertNotIn('data-workspace="system"', html.lower())


if __name__ == "__main__":
    unittest.main()
