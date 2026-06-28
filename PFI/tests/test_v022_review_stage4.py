from __future__ import annotations

import importlib
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV022ReviewStage4(unittest.TestCase):
    def _stage4_module(self):
        try:
            return importlib.import_module("pfi_v02.stage_v022_interconnection")
        except ModuleNotFoundError as exc:
            self.fail(f"Stage 4 interconnection module is missing: {exc}")

    def test_same_interconnection_group_counts_once_even_when_source_economic_ids_disagree(self) -> None:
        module = self._stage4_module()
        record = module.InterconnectionRecord

        records = (
            record(
                source_record_id="bank_outflow_001",
                source_id="cba_bank",
                account_id="acct_cba_main",
                event_date=date(2026, 6, 28),
                event_type="investment_deposit",
                amount_cny=Decimal("1000.00"),
                direction="outflow",
                economic_event_id="econ_bank_side_001",
                interconnection_group_id="group_bank_to_moomoo_001",
            ),
            record(
                source_record_id="broker_inflow_001",
                source_id="moomoo_au",
                account_id="acct_moomoo_cash",
                event_date=date(2026, 6, 28),
                event_type="investment_deposit",
                amount_cny=Decimal("1000.00"),
                direction="inflow",
                economic_event_id="econ_broker_side_001",
                interconnection_group_id="group_bank_to_moomoo_001",
            ),
        )

        metrics = module.aggregate_core_metrics(records)

        self.assertEqual(metrics["source_record_count"], 2)
        self.assertEqual(metrics["economic_event_count"], 2)
        self.assertEqual(metrics["interconnection_group_count"], 1)
        self.assertEqual(metrics["deduped_core_event_count"], 1)
        self.assertEqual(metrics["total_consumption_outflow_cny"], Decimal("1000.00"))
        self.assertEqual(metrics["living_consumption_cny"], Decimal("0.00"))
        self.assertEqual(metrics["investment_cash_cny"], Decimal("1000.00"))

    def test_cashflow_dependency_graph_includes_stage4_cash_moving_events(self) -> None:
        module = self._stage4_module()
        graph = module.build_metric_dependency_graph()
        cashflow = set(graph["core_metrics"]["cashflow"])
        expected_cashflow_events = {
            "investment_deposit",
            "fund_subscription",
            "bullion_purchase",
            "investment_buy",
            "investment_sell",
            "income",
            "fee",
            "refund",
            "credit_card_repayment",
            "internal_transfer",
            "fx_conversion",
        }
        self.assertTrue(expected_cashflow_events.issubset(cashflow), cashflow)

    def test_parameter_catalog_matches_stage4_cashflow_dependency_graph(self) -> None:
        governance = importlib.import_module("pfi_v02.stage_v022_database_governance")
        catalog = governance.load_v022_parameter_catalog(ROOT / "config" / "pfi_parameters.yaml")
        cashflow = set(catalog["parameters"]["interconnection"]["metric_dependency_graph"]["cashflow"])
        expected_cashflow_events = {
            "investment_deposit",
            "fund_subscription",
            "bullion_purchase",
            "investment_buy",
            "investment_sell",
            "income",
            "fee",
            "refund",
            "credit_card_repayment",
            "internal_transfer",
            "fx_conversion",
        }
        self.assertTrue(expected_cashflow_events.issubset(cashflow), cashflow)

    def test_stage4_review_report_records_fixes_acceptance_stop_conditions_and_validation(self) -> None:
        report = ROOT / "docs" / "pfi_v022" / "reviews" / "STAGE4_REVIEW_20260628.md"
        self.assertTrue(report.exists(), "Stage 4 复审修复报告缺失")
        text = report.read_text(encoding="utf-8")

        for required in (
            "v0.2.2 Stage 4 复审并解决",
            "本轮只复审解决 Stage 4",
            "不复审 Stage 5-13",
            "复审结论：通过",
            "上线阻塞项：0",
            "S4-P1-T1",
            "S4-P1-T2",
            "S4-P1-T3",
            "S4-P2-T1",
            "S4-P2-T2",
            "S4-P2-T3",
            "修复 1：按 interconnection_group_id 防止重复核心计量",
            "修复 2：补齐现金流依赖图的投资与费用事件",
            "多条来源记录被当成多次经济影响时停止",
            "关联组缺失导致重复计算时停止",
            "同一事件在同一口径重复计算时停止",
            "核心资金流缺失时停止",
            "任一事件口径模糊时停止",
            "抵消逻辑不清时停止",
            "同一 interconnection_group 因重复来源记录导致核心金额重复计算",
            "tests/test_v022_review_stage4.py",
            "tests/test_v022_interconnection_no_double_count.py",
            "tests/test_v022_consumption_investment_outflow.py",
            "docs/pfi_v02/INTERCONNECTION_MATRIX.md",
            "src/pfi_v02/stage_v022_interconnection.py",
            "config/pfi_parameters.yaml",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
