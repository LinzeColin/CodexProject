from __future__ import annotations

import importlib
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV022InterconnectionNoDoubleCount(unittest.TestCase):
    def _stage4_module(self):
        try:
            return importlib.import_module("pfi_v02.stage_v022_interconnection")
        except ModuleNotFoundError as exc:
            self.fail(f"Stage 4 interconnection module is missing: {exc}")

    def test_stage4_contract_locks_task_ids_acceptance_and_validation(self) -> None:
        governance = importlib.import_module("pfi_v02.stage_v022_database_governance")

        build_contract = getattr(governance, "build_v022_stage4_contract", None)
        self.assertIsNotNone(build_contract, "build_v022_stage4_contract() is required")
        contract = build_contract()

        self.assertEqual(contract["schema"], "PFIV022InterconnectionStage4ContractV1")
        self.assertEqual(
            tuple(contract["task_ids"]),
            ("S4-P1-T1", "S4-P1-T2", "S4-P1-T3", "S4-P2-T1", "S4-P2-T2", "S4-P2-T3"),
        )
        for required in (
            "economic_event_id",
            "interconnection_group_id",
            "同一真实事件只有一个 economic_event_id",
            "同一 interconnection_group 不会重复计入核心金额",
            "PFI/docs/pfi_v02/INTERCONNECTION_MATRIX.md",
            "test_v022_interconnection_no_double_count.py",
            "test_v022_consumption_investment_outflow.py",
        ):
            self.assertIn(required, str(contract))

    def test_same_economic_event_from_two_sources_counts_core_amount_once(self) -> None:
        module = self._stage4_module()
        record = module.InterconnectionRecord

        records = (
            record(
                source_record_id="raw_cba_001",
                source_id="cba_bank",
                account_id="acct_cba_main",
                event_date=date(2026, 6, 28),
                event_type="investment_deposit",
                amount_cny=Decimal("1000.00"),
                direction="outflow",
                economic_event_id="econ_invest_deposit_001",
                interconnection_group_id="group_cba_to_moomoo_001",
            ),
            record(
                source_record_id="raw_moomoo_001",
                source_id="moomoo_au",
                account_id="acct_moomoo_au",
                event_date=date(2026, 6, 28),
                event_type="investment_deposit",
                amount_cny=Decimal("1000.00"),
                direction="inflow",
                economic_event_id="econ_invest_deposit_001",
                interconnection_group_id="group_cba_to_moomoo_001",
            ),
        )

        metrics = module.aggregate_core_metrics(records)

        self.assertEqual(metrics["source_record_count"], 2)
        self.assertEqual(metrics["economic_event_count"], 1)
        self.assertEqual(metrics["interconnection_group_count"], 1)
        self.assertEqual(metrics["deduped_core_event_count"], 1)
        self.assertEqual(metrics["total_consumption_outflow_cny"], Decimal("1000.00"))
        self.assertEqual(metrics["living_consumption_cny"], Decimal("0.00"))
        self.assertEqual(metrics["investment_cash_cny"], Decimal("1000.00"))

    def test_credit_card_repayment_does_not_double_count_living_consumption(self) -> None:
        module = self._stage4_module()
        record = module.InterconnectionRecord

        records = (
            record(
                source_record_id="raw_alipay_food_001",
                source_id="alipay_daily",
                account_id="acct_credit_card",
                event_date=date(2026, 6, 20),
                event_type="consumption",
                amount_cny=Decimal("300.00"),
                direction="outflow",
                economic_event_id="econ_food_001",
                interconnection_group_id="group_credit_card_bill_001",
            ),
            record(
                source_record_id="raw_cba_repay_001",
                source_id="cba_bank",
                account_id="acct_cba_main",
                event_date=date(2026, 6, 28),
                event_type="credit_card_repayment",
                amount_cny=Decimal("300.00"),
                direction="outflow",
                economic_event_id="econ_credit_card_repay_001",
                interconnection_group_id="group_credit_card_bill_001",
            ),
        )

        metrics = module.aggregate_core_metrics(records)

        self.assertEqual(metrics["total_consumption_outflow_cny"], Decimal("300.00"))
        self.assertEqual(metrics["living_consumption_cny"], Decimal("300.00"))
        self.assertEqual(metrics["credit_card_repayment_cny"], Decimal("300.00"))
        self.assertEqual(metrics["economic_event_count"], 2)
        self.assertEqual(metrics["interconnection_group_count"], 1)

    def test_stage4_human_docs_record_cross_review_and_stop_conditions(self) -> None:
        expected_docs = (
            ROOT / "docs" / "pfi_v022" / "STAGE4_INTERCONNECTION.md",
            ROOT / "docs" / "pfi_v02" / "INTERCONNECTION_MATRIX.md",
            ROOT / "模型参数文件.md",
            ROOT / "功能清单.md",
            ROOT / "开发记录.md",
        )
        for path in expected_docs:
            self.assertTrue(path.exists(), f"{path} must exist for Stage 4")
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("Stage 4 - Economic Event 与 Interconnection 逻辑", text)
                self.assertIn("economic_event_id", text)
                self.assertIn("interconnection_group_id", text)
                self.assertIn("投资入金未进入消费总流出", text)
                self.assertIn("Agent 1", text)
                self.assertIn("Agent 2", text)


if __name__ == "__main__":
    unittest.main()
