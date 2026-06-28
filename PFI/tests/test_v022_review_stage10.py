from __future__ import annotations

import importlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV022ReviewStage10(unittest.TestCase):
    def test_stage10_context_comes_from_real_metadatabase(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v022_report_advice_review")
        context = module.load_stage10_real_report_advice_context(ROOT)

        self.assertEqual(context["schema"], "PFIV022Stage10RealReportAdviceContextV1")
        self.assertEqual(context["real_data_source"], "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv")
        self.assertEqual(context["normalized_transaction_count"], 8815)
        self.assertEqual(context["review_record_count"], 406)
        self.assertEqual(str(context["review_amount_abs_cny"]), "3082013.96")
        self.assertEqual(context["large_spend_record_count"], 181)
        self.assertEqual(str(context["large_spend_amount_cny"]), "1213978.31")
        self.assertEqual(str(context["gross_consumption_cny"]), "1727278.37")
        self.assertEqual(str(context["living_consumption_cny"]), "1545600.44")
        self.assertIn("暂无真实持仓快照", context["investment_data_status_zh"])
        self.assertIn("暂无真实 Interconnection 分组文件", context["interconnection_state_zh"])
        self.assertFalse(context["network_allowed"])

    def test_stage10_recommendations_are_real_triggered_or_empty_state(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v022_report_advice_review")
        context = module.load_stage10_real_report_advice_context(ROOT)
        payload = module.build_stage10_contract_payload(project_root=ROOT, context=context)
        recommendations = payload["recommendations"]

        self.assertGreaterEqual(len(recommendations), 3)
        self.assertEqual(payload["action_review_definition"]["allowed_task_types"], module.STAGE10_ACTION_REVIEW_TASK_TYPES)
        self.assertEqual(tuple(item["task_type"] for item in recommendations), tuple(item["task_type"] for item in sorted(recommendations, key=lambda row: row["score"], reverse=True)))

        allowed = set(module.STAGE10_ACTION_REVIEW_TASK_TYPES)
        for item in recommendations:
            with self.subTest(task_type=item["task_type"]):
                self.assertIn(item["task_type"], allowed)
                self.assertEqual(item["evidence_source"], context["real_data_source"])
                self.assertTrue(item["related_transactions"])
                self.assertTrue(item["related_parameters"])
                self.assertTrue(item["related_formulas"])
                self.assertIn("expected_impact_amount_cny", item)
                self.assertIn("score_basis_zh", item)
                self.assertFalse(item["buy_sell_instruction"])
                self.assertTrue(item["requires_manual_review"])

        self.assertIn("投资行为复盘建议", payload["real_empty_states"])
        self.assertIn("订阅优化建议", payload["real_empty_states"])
        self.assertIn("暂无真实持仓快照", payload["real_empty_states"]["投资行为复盘建议"])
        self.assertIn("暂无真实订阅候选", payload["real_empty_states"]["订阅优化建议"])

    def test_stage10_no_constructed_transaction_ids_or_fake_recommendations(self) -> None:
        source = (ROOT / "src" / "pfi_v02" / "stage_v022_report_advice_review.py").read_text(encoding="utf-8")
        target_test = (ROOT / "tests" / "test_v022_stage10_report_advice_review.py").read_text(encoding="utf-8")
        combined = source + "\n" + target_test

        forbidden_patterns = (
            r"tx_[a-z]+_20\d{6}_\d+",
            r"trade_[a-z]+_20\d{6}_\d+",
            "tx_" + "subscription_",
            "复盘追涨买入后的" + "现金拖累",
            "确认重复订阅" + "是否仍需要",
            r"Stage10RecommendationInput\(55, 90, 80, 70, 95, 80, 65\)",
        )
        for pattern in forbidden_patterns:
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, combined))

    def test_stage10_review_report_records_real_data_boundary(self) -> None:
        report = ROOT / "docs" / "pfi_v022" / "reviews" / "STAGE10_REVIEW_20260628.md"
        self.assertTrue(report.exists(), "Stage 10 复审报告缺失")
        text = report.read_text(encoding="utf-8")

        for required in (
            "v0.2.2 Stage 10 复审并解决",
            "本轮只复审解决 Stage 10",
            "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv",
            "真实触发建议",
            "中文真实空态",
            "不得使用构造交易 ID",
            "tests/test_v022_review_stage10.py",
            "Stage 0-10 v0.2.2 相关回归",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
