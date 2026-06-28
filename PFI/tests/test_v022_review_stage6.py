from __future__ import annotations

import importlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV022ReviewStage6(unittest.TestCase):
    def test_stage6_real_metadatabase_records_replace_constructed_financial_records(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v022_tags_views")
        records = module.load_stage6_alipay_records_from_metadatabase(
            ROOT.parent / "MetaDatabase" / "PFI" / "alipay_daily"
        )

        self.assertGreaterEqual(len(records), 7000)
        self.assertTrue(all(str(item["record_id"]).startswith("txn_alipay_") for item in records[:100]))
        self.assertTrue(all(item["real_data_source"].endswith("MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv") for item in records[:100]))
        event_types = {item["event_type"] for item in records}
        self.assertTrue({"ordinary_consumption", "investment_return", "investment_deposit", "investment_buy", "refund"}.issubset(event_types))

    def test_stage6_tests_no_longer_use_constructed_financial_transaction_ids(self) -> None:
        text = (ROOT / "tests" / "test_v022_stage6_tags_views.py").read_text(encoding="utf-8")
        for forbidden in ("txn_001", "txn_002", "txn_night_large", "txn_subscription", "txn_invest_deposit", "txn_wechat_001"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)

    def test_stage6_review_report_records_acceptance_stop_validation_and_real_data_boundary(self) -> None:
        report = ROOT / "docs" / "pfi_v022" / "reviews" / "STAGE6_REVIEW_20260628.md"
        self.assertTrue(report.exists(), "Stage 6 复审报告缺失")
        text = report.read_text(encoding="utf-8")

        for required in (
            "v0.2.2 Stage 6 复审并解决",
            "本轮只复审解决 Stage 6",
            "S6-P1-T1",
            "S6-P1-T2",
            "S6-P1-T3",
            "S6-P2-T1",
            "S6-P2-T2",
            "S6-P2-T3",
            "S6-P3-T1",
            "S6-P3-T2",
            "S6-P3-T3",
            "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv",
            "7247",
            "ordinary_consumption",
            "investment_return",
            "investment_deposit",
            "investment_buy",
            "refund",
            "标签不能持久化",
            "一笔记录只能有一个标签",
            "标签只能手动添加",
            "默认标签缺失关键分析维度",
            "自定义标签无法修改",
            "标签历史不可追踪",
            "标签无法筛选账本",
            "标签不参与报告",
            "自定义视图不能保存",
            "tests/test_v022_stage6_tags_views.py",
            "tests/test_v022_review_stage6.py",
            "src/pfi_v02/stage_v022_tags_views.py",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
