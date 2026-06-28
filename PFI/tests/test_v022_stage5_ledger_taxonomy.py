from __future__ import annotations

import importlib
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV022Stage5LedgerTaxonomy(unittest.TestCase):
    def _stage5_module(self):
        try:
            return importlib.import_module("pfi_v02.stage_v022_ledger_taxonomy")
        except ModuleNotFoundError as exc:
            self.fail(f"Stage 5 ledger taxonomy module is missing: {exc}")

    def test_stage5_contract_locks_phase_task_acceptance_and_validation(self) -> None:
        governance = importlib.import_module("pfi_v02.stage_v022_database_governance")
        build_contract = getattr(governance, "build_v022_stage5_contract", None)
        self.assertIsNotNone(build_contract, "build_v022_stage5_contract() is required")

        contract = build_contract()

        self.assertEqual(contract["schema"], "PFIV022LedgerTaxonomyStage5ContractV1")
        self.assertEqual(contract["stage"], "Stage 5")
        self.assertEqual(
            tuple(contract["task_ids"]),
            (
                "S5-P1-T1",
                "S5-P1-T2",
                "S5-P2-T1",
                "S5-P2-T2",
                "S5-P2-T3",
                "S5-P3-T1",
                "S5-P3-T2",
                "S5-P3-T3",
                "S5-P3-T4",
            ),
        )
        for required in (
            "统一账本事件类型",
            "消费总流出金额",
            "生活消费金额",
            "12 大类",
            "总 L2 不超过 50",
            "PFI/tests/test_v022_stage5_ledger_taxonomy.py",
            "Stage 6 标签持久化不在本轮实现",
        ):
            self.assertIn(required, str(contract))

    def test_stage5_event_type_table_covers_real_money_flows_and_affects_flags(self) -> None:
        module = self._stage5_module()
        table = {item["event_type"]: item for item in module.build_stage5_ledger_event_type_table()}
        required_event_types = {
            "consumption",
            "investment_deposit",
            "fund_subscription",
            "bullion_purchase",
            "investment_buy",
            "investment_sell",
            "refund",
            "fee",
            "credit_card_repayment",
            "internal_transfer",
            "income",
            "valuation",
            "fx_conversion",
        }

        self.assertTrue(required_event_types.issubset(table))
        for event_type in required_event_types:
            with self.subTest(event_type=event_type):
                item = table[event_type]
                self.assertRegex(item["label_zh"], r"[\u4e00-\u9fff]")
                for field in (
                    "affects_total_consumption_outflow",
                    "affects_living_consumption",
                    "affects_investment",
                    "affects_net_worth",
                    "affects_cashflow",
                ):
                    self.assertIn(field, item)

        for event_type in ("investment_deposit", "fund_subscription", "bullion_purchase", "investment_buy", "fee"):
            with self.subTest(event_type=event_type):
                self.assertTrue(table[event_type]["affects_total_consumption_outflow"])
                self.assertFalse(table[event_type]["affects_living_consumption"])
        self.assertFalse(table["credit_card_repayment"]["affects_total_consumption_outflow"])
        self.assertFalse(table["valuation"]["affects_total_consumption_outflow"])
        self.assertTrue(table["valuation"]["affects_net_worth"])

    def test_double_consumption_templates_use_same_ledger_metrics_for_home_consumption_and_report(self) -> None:
        module = self._stage5_module()
        interconnection = importlib.import_module("pfi_v02.stage_v022_interconnection")
        record = interconnection.InterconnectionRecord
        records = (
            record("raw_food", "alipay_daily", "acct_alipay_daily", date(2026, 6, 1), "consumption", Decimal("100.00"), "outflow", "econ_food", "group_food"),
            record("raw_deposit", "cba_bank", "acct_cba_main", date(2026, 6, 2), "investment_deposit", Decimal("1000.00"), "outflow", "econ_deposit", "group_deposit"),
            record("raw_fund", "alipay_fund", "acct_alipay_daily", date(2026, 6, 3), "fund_subscription", Decimal("500.00"), "outflow", "econ_fund", "group_fund"),
            record("raw_gold", "abc_bullion", "acct_abc_bullion", date(2026, 6, 4), "bullion_purchase", Decimal("200.00"), "outflow", "econ_gold", "group_gold"),
            record("raw_buy", "moomoo_au", "acct_moomoo_au", date(2026, 6, 5), "investment_buy", Decimal("700.00"), "outflow", "econ_buy", "group_buy"),
            record("raw_fee", "moomoo_au", "acct_moomoo_au", date(2026, 6, 6), "fee", Decimal("30.00"), "outflow", "econ_fee", "group_fee"),
            record("raw_refund", "wechat_pay", "acct_wechat_pay", date(2026, 6, 7), "refund", Decimal("20.00"), "inflow", "econ_refund", "group_food", "econ_food"),
        )

        dashboard = module.build_stage5_double_consumption_dashboard(records)

        self.assertEqual(dashboard["schema"], "PFIV022Stage5DoubleConsumptionDashboardV1")
        self.assertEqual(dashboard["metrics"]["gross_consumption_cny"], Decimal("2510.00"))
        self.assertEqual(dashboard["metrics"]["living_consumption_cny"], Decimal("80.00"))
        for surface in ("homepage", "consumption_page", "report"):
            with self.subTest(surface=surface):
                payload = dashboard["surfaces"][surface]
                self.assertEqual(payload["gross_consumption_label_zh"], "消费总流出")
                self.assertEqual(payload["living_consumption_label_zh"], "生活消费")
                self.assertIn("投资入金", payload["difference_explanation_zh"])
                self.assertEqual(payload["gross_consumption_cny"], Decimal("2510.00"))
                self.assertEqual(payload["living_consumption_cny"], Decimal("80.00"))

    def test_consumption_taxonomy_respects_12_5_50_limits_and_future_merge_fields(self) -> None:
        module = self._stage5_module()
        taxonomy = module.build_stage5_consumption_taxonomy()
        validation = module.validate_stage5_taxonomy_constraints(taxonomy)

        self.assertEqual(validation["status"], "通过")
        self.assertLessEqual(validation["l1_count"], 12)
        self.assertLessEqual(validation["l2_total"], 50)
        self.assertTrue(validation["future_merge_ready"])
        self.assertEqual(validation["primary_category_per_transaction"], 1)
        seen_l1 = set()
        seen_l2 = set()
        for category in taxonomy:
            with self.subTest(category=category["l1_label_zh"]):
                self.assertNotIn(category["l1_key"], seen_l1)
                seen_l1.add(category["l1_key"])
                self.assertLessEqual(len(category["l2"]), 5)
                self.assertTrue(category.get("future_merge_to") or category.get("merge_candidate"))
                for item in category["l2"]:
                    self.assertRegex(item["label_zh"], r"[\u4e00-\u9fff]")
                    self.assertNotIn(item["l2_key"], seen_l2)
                    seen_l2.add(item["l2_key"])

    def test_stage5_human_docs_and_parameter_catalog_record_category_constraints(self) -> None:
        expected_docs = (
            ROOT / "docs" / "pfi_v022" / "STAGE5_LEDGER_TAXONOMY.md",
            ROOT / "docs" / "pfi_v022" / "ROADMAP_LOCK.md",
            ROOT / "模型参数文件.md",
            ROOT / "功能清单.md",
            ROOT / "开发记录.md",
        )
        for path in expected_docs:
            self.assertTrue(path.exists(), f"{path} must exist for Stage 5")
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("Stage 5 - 统一账本事件、消费双口径与分类体系", text)
                self.assertIn("S5-P1-T1", text)
                self.assertIn("消费总流出", text)
                self.assertIn("生活消费", text)
                self.assertIn("L1 ≤ 12", text)
                self.assertIn("L2 ≤ 50", text)

        governance = importlib.import_module("pfi_v02.stage_v022_database_governance")
        catalog = governance.load_v022_parameter_catalog(ROOT / "config" / "pfi_parameters.yaml")
        self.assertEqual(catalog["schema"], "PFIParametersV022Stage7")
        self.assertEqual(catalog["current_stage"], "Stage 7 - 模型公式、阈值与评分标准")
        self.assertEqual(catalog["stage5_task_ids"], list(governance.V022_STAGE5_TASK_IDS))
        categories = catalog["parameters"]["consumption_categories"]
        self.assertIn("default_taxonomy", categories)
        self.assertEqual(categories["max_l1_categories"]["value"], 12)
        self.assertEqual(categories["max_l2_per_l1"]["value"], 5)
        self.assertEqual(categories["max_l2_total"]["value"], 50)


if __name__ == "__main__":
    unittest.main()
