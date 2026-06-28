from __future__ import annotations

import importlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV022ReviewStage8(unittest.TestCase):
    def test_stage8_runtime_diff_inputs_come_from_canonical_real_sources(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v022_runtime_diff")
        loaded = module.load_stage8_runtime_diff_inputs_from_canonical_sources(ROOT)
        inputs = loaded["inputs"]
        summary = loaded["source_summary"]

        self.assertGreaterEqual(summary["raw_file_count"], 4)
        self.assertGreaterEqual(summary["normalized_transaction_count"], 8000)
        self.assertEqual(summary["raw_data_root"], "MetaDatabase/PFI/alipay_daily/raw")
        self.assertEqual(summary["normalized_transactions_path"], "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv")
        self.assertEqual(summary["interconnection_state_zh"], "暂无真实 Interconnection 分组文件，使用真实空态，不生成模拟分组。")
        self.assertIn("raw_data", inputs)
        self.assertIn("normalized_transactions", inputs)
        self.assertIn("ledger_events", inputs)
        self.assertIn("parameters", inputs)
        self.assertIn("categories", inputs)
        self.assertIn("tags", inputs)
        self.assertIn("fx_snapshot", inputs)

        snapshot = module.build_dependency_hash_snapshot(inputs, run_id="stage8-real-inputs")
        self.assertEqual(tuple(snapshot["dependency_hashes"].keys()), module.STAGE8_DEPENDENCY_HASH_KEYS)
        self.assertFalse(snapshot["network_allowed"])

    def test_stage8_target_tests_no_longer_use_constructed_financial_records(self) -> None:
        text = (ROOT / "tests" / "test_v022_stage8_runtime_diff.py").read_text(encoding="utf-8")
        for forbidden in (
            "source_record_id\": \"a-1",
            "transaction_id\": \"t-1",
            "ledger_event_id\": \"l-1",
            "interconnection_group_id\": \"g-1",
            "economic_event_id\": \"e-1",
            "large_spend_cny\": 2000",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)

    def test_stage8_review_report_records_acceptance_stop_validation_and_real_data_boundary(self) -> None:
        report = ROOT / "docs" / "pfi_v022" / "reviews" / "STAGE8_REVIEW_20260628.md"
        self.assertTrue(report.exists(), "Stage 8 复审报告缺失")
        text = report.read_text(encoding="utf-8")

        for required in (
            "v0.2.2 Stage 8 复审并解决",
            "本轮只复审解决 Stage 8",
            "S8-P1-T1",
            "S8-P1-T2",
            "S8-P1-T3",
            "S8-P2-T1",
            "S8-P2-T2",
            "S8-P2-T3",
            "S8-P2-T4",
            "S8-P3-T1",
            "S8-P3-T2",
            "S8-P3-T3",
            "MetaDatabase/PFI/alipay_daily/raw",
            "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv",
            "无 diff 仍触发 agent 时停止",
            "小 diff 导致全局重算时停止",
            "展示变化被误判为财务核心变化时停止",
            "tests/test_v022_stage8_runtime_diff.py",
            "tests/test_v022_review_stage8.py",
            "src/pfi_v02/stage_v022_runtime_diff.py",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
