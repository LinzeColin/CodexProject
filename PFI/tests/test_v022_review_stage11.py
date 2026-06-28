from __future__ import annotations

import importlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV022ReviewStage11(unittest.TestCase):
    def test_stage11_context_comes_from_real_metadatabase(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v022_test_validation")
        context = module.load_stage11_real_test_validation_context(ROOT)

        self.assertEqual(context["schema"], "PFIV022Stage11RealTestValidationContextV1")
        self.assertEqual(context["real_data_source"], "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv")
        self.assertEqual(context["normalized_transaction_count"], 8815)
        self.assertEqual(context["event_type_counts"]["ordinary_consumption"], 3831)
        self.assertEqual(context["event_type_counts"]["fund_subscription"], 21)
        self.assertEqual(context["event_type_counts"]["refund"], 250)
        self.assertEqual(context["event_type_counts"]["bullion_purchase"], 12)
        self.assertEqual(context["event_type_counts"]["internal_transfer"], 1260)
        self.assertEqual(str(context["gross_consumption_cny"]), "1727278.37")
        self.assertEqual(str(context["living_consumption_cny"]), "1545600.44")
        self.assertEqual(str(context["fund_subscription_cny"]), "4120.00")
        self.assertEqual(str(context["refund_offset_cny"]), "132707.90")
        self.assertIn("暂无真实 CBA -> Moomoo", context["cba_moomoo_empty_state_zh"])
        self.assertIn("暂无真实信用卡还款", context["credit_card_empty_state_zh"])
        self.assertFalse(context["network_allowed"])

    def test_stage11_financial_cases_use_real_events_or_empty_states(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v022_test_validation")
        context = module.load_stage11_real_test_validation_context(ROOT)
        cases = module.build_stage11_financial_logic_cases(context=context)
        by_id = {case["case_id"]: case for case in cases}

        deposit = by_id["cba_to_moomoo_investment_deposit"]
        self.assertEqual(deposit["evaluation_state"], "real_empty_state")
        self.assertIsNone(deposit["gross_consumption_delta_cny"])
        self.assertIn("暂无真实 CBA -> Moomoo", deposit["data_status_zh"])

        fund = by_id["alipay_fund_purchase"]
        self.assertEqual(fund["evaluation_state"], "verified_real_data")
        self.assertEqual(fund["real_record_count"], 21)
        self.assertEqual(str(fund["gross_consumption_delta_cny"]), "4120.00")
        self.assertEqual(str(fund["living_consumption_delta_cny"]), "0.00")
        self.assertIn("真实支付宝基金申购", fund["data_status_zh"])

        refund = by_id["refund_offsets_original_consumption"]
        self.assertEqual(refund["evaluation_state"], "verified_real_data")
        self.assertEqual(refund["real_record_count"], 250)
        self.assertEqual(str(refund["refund_offset_cny"]), "-132707.90")
        self.assertFalse(refund["refund_counted_as_income"])

        credit_card = by_id["credit_card_repayment_no_double_count"]
        self.assertEqual(credit_card["evaluation_state"], "real_empty_state")
        self.assertFalse(credit_card["double_counted"])
        self.assertIn("暂无真实信用卡还款", credit_card["data_status_zh"])

    def test_stage11_cross_surface_and_visualization_use_real_hashes(self) -> None:
        module = importlib.import_module("pfi_v02.stage_v022_test_validation")
        context = module.load_stage11_real_test_validation_context(ROOT)
        consistency = module.build_stage11_cross_surface_consistency(context=context)
        visualization = module.build_stage11_visualization_validation(context=context)

        consumption = consistency["consumption_total_outflow"]
        self.assertEqual(str(consumption["homepage_cny"]), "1727278.37")
        self.assertEqual(consumption["homepage_cny"], consumption["consumption_page_cny"])
        self.assertEqual(consumption["homepage_cny"], consumption["monthly_report_cny"])

        investment = consistency["investment_assets"]
        self.assertEqual(investment["evaluation_state"], "real_empty_state")
        self.assertIn("暂无真实持仓快照", investment["data_status_zh"])

        cashflow = consistency["cashflow_traceability"]
        self.assertTrue(cashflow["can_trace_to_ledger_events"])
        self.assertFalse(cashflow["can_trace_to_plan_events"])
        self.assertIn("暂无真实计划事件", cashflow["plan_event_empty_state_zh"])

        self.assertEqual(visualization["performance"]["record_count"], 8815)
        self.assertEqual(visualization["performance"]["data_source"], context["real_data_source"])
        self.assertNotIn("synthetic", visualization["performance"]["data_policy_zh"].lower())
        self.assertTrue(visualization["performance"]["not_obviously_stuck"])
        for chart in visualization["charts"]:
            self.assertTrue(chart["metric_id"])
            self.assertTrue(chart["formula_id"])
            self.assertTrue(chart["parameter_hash"])
            self.assertTrue(chart["data_hash"])
            self.assertEqual(chart["data_source"], context["real_data_source"])

    def test_stage11_source_and_docs_no_longer_use_simulated_performance_or_fake_amounts(self) -> None:
        paths = (
            "src/pfi_v02/stage_v022_test_validation.py",
            "tests/test_v022_stage11_test_validation.py",
            "docs/pfi_v022/STAGE11_TEST_VALIDATION.md",
            "docs/pfi_v022/ROADMAP_LOCK.md",
            "模型参数文件.md",
            "功能清单.md",
            "开发记录.md",
            "HANDOFF.md",
        )
        combined = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in paths)
        for forbidden in (
            "synthetic_total",
            "大量模拟记录",
            "record_count=12_000",
            "record_count: int = 10_000",
            "homepage_cny\": 8060",
            "homepage_cny\": 68740",
            "gross_consumption_delta_cny\": 5000",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, combined)

    def test_stage11_review_report_records_real_data_boundary(self) -> None:
        report = ROOT / "docs" / "pfi_v022" / "reviews" / "STAGE11_REVIEW_20260628.md"
        self.assertTrue(report.exists(), "Stage 11 复审报告缺失")
        text = report.read_text(encoding="utf-8")

        for required in (
            "v0.2.2 Stage 11 复审并解决",
            "本轮只复审解决 Stage 11",
            "MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv",
            "真实金融逻辑验证",
            "中文真实空态",
            "不得使用模拟记录",
            "tests/test_v022_review_stage11.py",
            "Stage 0-11 v0.2.2 相关回归",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
