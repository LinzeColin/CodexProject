from __future__ import annotations

import importlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV022ReviewStage9(unittest.TestCase):
    def test_stage9_visualization_context_comes_from_real_canonical_sources(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v022_visualization_uiux")
        context = module.load_stage9_real_visualization_context(ROOT)

        self.assertEqual(context["schema"], "PFIV022Stage9RealVisualizationContextV1")
        self.assertEqual(context["real_data_source"], "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv")
        self.assertEqual(context["raw_file_count"], 4)
        self.assertEqual(context["normalized_transaction_count"], 8815)
        self.assertEqual(context["review_record_count"], 406)
        self.assertEqual(context["tag_count"], 56)
        self.assertEqual(context["advice_item_count"], 0)
        self.assertEqual(context["interconnection_count"], 0)
        self.assertIn("暂无真实 Interconnection 分组文件", context["interconnection_state_zh"])
        self.assertIn("暂无真实持仓快照", context["investment_data_status_zh"])
        self.assertEqual(str(context["gross_consumption_cny"]), "1727278.37")
        self.assertEqual(str(context["living_consumption_cny"]), "1545600.44")
        self.assertFalse(context["network_allowed"])

    def test_stage9_impact_preview_uses_real_context_not_legacy_count_argument(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v022_visualization_uiux")
        context = module.load_stage9_real_visualization_context(ROOT)
        preview = module.calculate_parameter_impact_preview(
            parameter_key="confidence.review_threshold",
            old_value=70,
            new_value=75,
            impact_counts=context["impact_counts"],
        )

        self.assertEqual(preview["affected_records"], 406)
        self.assertEqual(preview["affected_tags"], 56)
        self.assertEqual(preview["affected_advice_items"], 0)
        self.assertGreaterEqual(preview["affected_charts"], 4)
        self.assertIn("真实 MetaDatabase", preview["explanation_zh"])

    def test_stage9_target_tests_no_longer_use_legacy_count_argument_or_fake_financial_figures(self) -> None:
        text = (ROOT / "tests" / "test_v022_stage9_visualization_uiux.py").read_text(encoding="utf-8")
        for forbidden in (
            "sample" + "_counts",
            '"advice' + '_items": 12',
            '"charts": ' + "9",
            'self.assertEqual(preview["affected_advice' + '_items"], 12)',
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)

    def test_stage9_html_uses_real_metrics_or_real_empty_state(self) -> None:
        html_path = ROOT / "web" / "interconnection-map.html"
        html = html_path.read_text(encoding="utf-8")

        for forbidden in (
            *(f"CNY {amount}" for amount in ("18,420", "126,800", "21,800", "19,400")),
            "低置信 406 条；未匹配 interconnection 18 条",
            *(f"匹配率 {rate}%" for rate in ("94", "91", "89")),
            *(f"计算耗时 {ms}ms" for ms in ("42", "38", "44")),
            "当前" + "样本",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, html)

        for required in (
            "真实支付宝流水 8815 条",
            "消费总流出",
            "CNY 1,727,278.37",
            "生活消费",
            "CNY 1,545,600.44",
            "暂无真实持仓快照",
            "暂无真实 Interconnection 分组文件",
            "待复核记录",
            "406",
            "默认标签 56 个",
            "行动建议 0 条",
            "本轮未测量，不显示模拟耗时",
        ):
            with self.subTest(required=required):
                self.assertIn(required, html)

    def test_stage9_review_report_records_acceptance_stop_validation_and_real_data_boundary(self) -> None:
        report = ROOT / "docs" / "pfi_v022" / "reviews" / "STAGE9_REVIEW_20260628.md"
        self.assertTrue(report.exists(), "Stage 9 复审报告缺失")
        text = report.read_text(encoding="utf-8")

        for required in (
            "v0.2.2 Stage 9 复审并解决",
            "本轮只复审解决 Stage 9",
            "S9-P1-T1",
            "S9-P2-T2",
            "S9-P3-T4",
            "S9-P4-T3",
            "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv",
            "不得使用固定假金额、固定假匹配率或模拟耗时",
            "HTML 依赖外部 CDN 或网络时停止",
            "图表无法证明数据新鲜度时停止",
            "tests/test_v022_stage9_visualization_uiux.py",
            "tests/test_v022_review_stage9.py",
            "src/pfi_v02/stage_v022_visualization_uiux.py",
            "web/interconnection-map.html",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
