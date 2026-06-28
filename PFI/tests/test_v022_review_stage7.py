from __future__ import annotations

import importlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV022ReviewStage7(unittest.TestCase):
    def test_stage7_formula_inputs_come_from_real_metadatabase_alipay_records(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v022_formula_scoring")
        inputs = module.load_stage7_alipay_formula_inputs_from_metadatabase(
            ROOT.parent / "MetaDatabase" / "PFI" / "alipay_daily"
        )

        self.assertGreaterEqual(inputs["raw_record_count"], 8000)
        self.assertEqual(
            inputs["real_data_source"],
            "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv",
        )
        self.assertGreater(inputs["event_type_counts"]["ordinary_consumption"], 3000)
        self.assertGreater(inputs["event_type_counts"]["investment_return"], 3000)
        self.assertGreater(inputs["event_type_counts"]["fund_subscription"], 0)
        self.assertGreater(inputs["event_type_counts"]["bullion_purchase"], 0)
        self.assertEqual(inputs["investment_holdings"], [])
        self.assertIn("暂无真实持仓", inputs["investment_data_status_zh"])

    def test_stage7_target_tests_no_longer_use_constructed_financial_facts(self) -> None:
        text = (ROOT / "tests" / "test_v022_stage7_formula_scoring.py").read_text(encoding="utf-8")
        for forbidden in (
            '"symbol": "MOCK"',
            "date(2026, 6, 1)",
            '"event_type": "consumption", "amount_cny": Decimal("100.00")',
            '"sell_proceeds_cny": Decimal("1000")',
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)

    def test_stage7_review_report_records_acceptance_stop_validation_and_real_data_boundary(self) -> None:
        report = ROOT / "docs" / "pfi_v022" / "reviews" / "STAGE7_REVIEW_20260628.md"
        self.assertTrue(report.exists(), "Stage 7 复审报告缺失")
        text = report.read_text(encoding="utf-8")

        for required in (
            "v0.2.2 Stage 7 复审并解决",
            "本轮只复审解决 Stage 7",
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
            "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv",
            "置信度权重不等于 100",
            "评分项缺少中文评分标准",
            "出现 source 分层复核阈值",
            "投资入金挤压生活现金无法解释",
            "tests/test_v022_stage7_formula_scoring.py",
            "tests/test_v022_review_stage7.py",
            "src/pfi_v02/stage_v022_formula_scoring.py",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
