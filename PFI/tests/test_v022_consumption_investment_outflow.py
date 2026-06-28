from __future__ import annotations

import importlib
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV022ConsumptionInvestmentOutflow(unittest.TestCase):
    def _stage4_module(self):
        try:
            return importlib.import_module("pfi_v02.stage_v022_interconnection")
        except ModuleNotFoundError as exc:
            self.fail(f"Stage 4 interconnection module is missing: {exc}")

    def test_event_type_policies_define_required_affects_flags(self) -> None:
        module = self._stage4_module()
        required_event_types = {
            "consumption",
            "ordinary_consumption",
            "investment_deposit",
            "fund_subscription",
            "bullion_purchase",
            "investment_buy",
            "investment_sell",
            "refund",
            "credit_card_repayment",
            "internal_transfer",
            "income",
            "fee",
            "fx_conversion",
        }

        matrix = {item["event_type"]: item for item in module.build_interconnection_matrix()}
        self.assertTrue(required_event_types.issubset(matrix))
        for event_type in required_event_types:
            with self.subTest(event_type=event_type):
                policy = module.event_policy(event_type)
                payload = policy.to_dict()
                for field in (
                    "affects_total_consumption_outflow",
                    "affects_living_consumption",
                    "affects_investment",
                    "affects_net_worth",
                    "affects_cashflow",
                    "homepage_display",
                    "consumption_display",
                    "investment_display",
                    "cashflow_display",
                    "report_display",
                    "offset_rule_zh",
                ):
                    self.assertIn(field, payload)

        self.assertTrue(module.event_policy("investment_deposit").affects_total_consumption_outflow)
        self.assertFalse(module.event_policy("investment_deposit").affects_living_consumption)
        self.assertTrue(module.event_policy("fund_subscription").affects_total_consumption_outflow)
        self.assertTrue(module.event_policy("investment_buy").affects_total_consumption_outflow)
        self.assertFalse(module.event_policy("credit_card_repayment").affects_living_consumption)

    def test_consumption_total_outflow_includes_investment_events_but_living_consumption_excludes_them(self) -> None:
        module = self._stage4_module()
        record = module.InterconnectionRecord
        records = (
            record("raw_food", "alipay_daily", "acct_alipay_daily", date(2026, 6, 1), "consumption", Decimal("120.00"), "outflow", "econ_food", "group_food"),
            record("raw_deposit", "cba_bank", "acct_cba_main", date(2026, 6, 2), "investment_deposit", Decimal("1000.00"), "outflow", "econ_deposit", "group_deposit"),
            record("raw_fund", "alipay_fund", "acct_alipay_daily", date(2026, 6, 3), "fund_subscription", Decimal("500.00"), "outflow", "econ_fund", "group_fund"),
            record("raw_stock", "moomoo_au", "acct_moomoo_au", date(2026, 6, 4), "investment_buy", Decimal("700.00"), "outflow", "econ_stock", "group_stock"),
            record("raw_bullion", "abc_bullion", "acct_abc_bullion", date(2026, 6, 5), "bullion_purchase", Decimal("900.00"), "outflow", "econ_gold", "group_gold"),
            record("raw_refund", "wechat_pay", "acct_wechat_pay", date(2026, 6, 6), "refund", Decimal("20.00"), "inflow", "econ_refund", "group_food", "econ_food"),
            record("raw_repay", "cba_bank", "acct_cba_main", date(2026, 6, 7), "credit_card_repayment", Decimal("120.00"), "outflow", "econ_repay", "group_credit_card"),
        )

        metrics = module.aggregate_core_metrics(records)

        self.assertEqual(metrics["total_consumption_outflow_cny"], Decimal("3200.00"))
        self.assertEqual(metrics["living_consumption_cny"], Decimal("100.00"))
        self.assertEqual(metrics["investment_cash_cny"], Decimal("1000.00"))
        self.assertEqual(metrics["fund_asset_flow_cny"], Decimal("500.00"))
        self.assertEqual(metrics["investment_holding_flow_cny"], Decimal("700.00"))
        self.assertEqual(metrics["bullion_asset_flow_cny"], Decimal("900.00"))
        self.assertEqual(metrics["refund_offset_cny"], Decimal("20.00"))
        self.assertEqual(metrics["credit_card_repayment_cny"], Decimal("120.00"))

    def test_interconnection_matrix_doc_is_chinese_readable_and_has_metric_dependency_graph(self) -> None:
        matrix_doc = ROOT / "docs" / "pfi_v02" / "INTERCONNECTION_MATRIX.md"
        self.assertTrue(matrix_doc.exists())
        text = matrix_doc.read_text(encoding="utf-8")

        for required in (
            "Stage 4 - Economic Event 与 Interconnection 逻辑",
            "Interconnection Matrix",
            "Metric Dependency Graph",
            "普通消费",
            "投资入金",
            "基金申购",
            "黄金申购",
            "投资买入",
            "投资卖出",
            "退款",
            "信用卡还款",
            "内部转账",
            "收入",
            "费用",
            "汇率兑换",
            "消费总流出",
            "生活消费",
            "净资产",
            "现金流",
            "退款抵消原消费",
            "信用卡还款不重复计入生活消费",
        ):
            self.assertIn(required, text)

    def test_parameter_catalog_records_stage4_event_flags_and_matrix_fields(self) -> None:
        governance = importlib.import_module("pfi_v02.stage_v022_database_governance")
        catalog = governance.load_v022_parameter_catalog(ROOT / "config" / "pfi_parameters.yaml")
        params = catalog["parameters"]

        self.assertEqual(catalog["schema"], "PFIParametersV022Stage11")
        self.assertEqual(catalog["current_stage"], "Stage 11 - 测试与验证")
        self.assertEqual(catalog["stage4_task_ids"], ["S4-P1-T1", "S4-P1-T2", "S4-P1-T3", "S4-P2-T1", "S4-P2-T2", "S4-P2-T3"])
        self.assertIn("event_type_policies", params["interconnection"])
        deposit = params["interconnection"]["event_type_policies"]["investment_deposit"]
        self.assertTrue(deposit["affects_total_consumption_outflow"])
        self.assertFalse(deposit["affects_living_consumption"])
        self.assertTrue(deposit["affects_investment"])
        self.assertIn("消费总流出", deposit["display_surfaces"]["consumption"])


if __name__ == "__main__":
    unittest.main()
