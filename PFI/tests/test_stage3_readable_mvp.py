from __future__ import annotations

import unittest
from pathlib import Path

from pfi_v02.stage3_read_mvp import (
    SIMPLE_STATUS_LANGUAGE,
    STAGE3_REQUIRED_ACCOUNT_SOURCES,
    build_owner_review_checklist,
    build_stage3_demo_imports,
    build_stage3_read_model,
    build_sync_all_plan,
    simple_status_language,
    transfer_match_decision,
)
from pfi_v02.stage2_import import reconcile_cba_transfer


class Stage3ReadableMvpTest(unittest.TestCase):
    def setUp(self) -> None:
        self.model = build_stage3_read_model()

    def test_home_financial_status_runs_on_synthetic_local_data_without_real_accounts(self) -> None:
        cards = {card["key"]: card for card in self.model["home"]["financial_status_cards"]}

        for key in ("net_worth", "cash", "investment_assets", "monthly_spending", "data_health"):
            self.assertIn(key, cards)
            self.assertTrue(cards[key]["value"])
            self.assertTrue(cards[key]["detail"])

        self.assertIn(self.model["home"]["owner_status"], SIMPLE_STATUS_LANGUAGE)
        self.assertIn("synthetic_or_local_read_model_only", self.model["boundaries"])

    def test_account_map_covers_required_platforms_with_owner_status_language(self) -> None:
        rows = {row["source_id"]: row for row in self.model["account_map"]}

        self.assertEqual(set(STAGE3_REQUIRED_ACCOUNT_SOURCES), set(rows))
        for source_id, row in rows.items():
            self.assertTrue(row["display_name"], source_id)
            self.assertIn(row["status"], SIMPLE_STATUS_LANGUAGE, source_id)
            self.assertEqual(row["target_entry"], "账户与资产")
            self.assertIn("账户与资产/", row["detail_route"])

    def test_summary_snapshots_are_clickable_and_traceable(self) -> None:
        snapshots = {row["label"]: row for row in self.model["home"]["snapshots"]}

        for label in ("投资快照", "消费快照", "现金流快照"):
            self.assertIn(label, snapshots)
            self.assertTrue(snapshots[label]["detail_route"])
            self.assertTrue(snapshots[label]["evidence_refs"])

    def test_recommendations_have_evidence_action_status_effect_tradeoff_and_target_entry(self) -> None:
        recommendations = self.model["recommendations"]

        self.assertGreaterEqual(len(recommendations), 3)
        for item in recommendations:
            self.assertTrue(item["evidence_refs"], item["recommendation_id"])
            self.assertTrue(item["action"], item["recommendation_id"])
            self.assertIn(item["status"], SIMPLE_STATUS_LANGUAGE, item["recommendation_id"])
            self.assertTrue(item["expected_effect"], item["recommendation_id"])
            self.assertTrue(item["tradeoff"], item["recommendation_id"])
            self.assertIn(item["target_entry"], ("数据源与上传", "账本流水", "账户与资产", "报告与洞察"))

    def test_accounts_cover_investment_daily_cash_asset_and_liability_without_mixing_datasources(self) -> None:
        accounts = self.model["accounts"]
        categories = {account["category"] for account in accounts}

        for category in ("investment", "daily", "cash", "asset", "liability"):
            self.assertIn(category, categories)
        for account in accounts:
            self.assertNotEqual(account["source_id"], account["account_id"])
            self.assertTrue(account["evidence_ref"])

    def test_cross_currency_view_supports_aud_cny_usd_hkd_with_fixture_rates(self) -> None:
        fx = self.model["fx_view"]
        rows = {row["currency"]: row for row in fx["rows"]}

        self.assertEqual(fx["base_currency"], "AUD")
        self.assertEqual(tuple(rows), ("AUD", "CNY", "USD", "HKD"))
        for currency, row in rows.items():
            self.assertGreater(row["rate_to_aud"], 0.0, currency)
            self.assertEqual(row["rate_source"], "stage3_fixture_not_live_market_rate")

    def test_account_reconciliation_shows_platform_vs_ledger_balance_status(self) -> None:
        rows = self.model["reconciliation"]

        self.assertTrue(any(row["status"] == "正常" for row in rows))
        self.assertTrue(any(row["status"] == "需要复核" for row in rows))
        for row in rows:
            self.assertIn("platform_balance", row)
            self.assertIn("ledger_balance", row)
            self.assertIn(row["status"], SIMPLE_STATUS_LANGUAGE)

    def test_ledger_rows_trace_to_import_batch_raw_record_and_parser_version(self) -> None:
        rows = self.model["ledger"]

        self.assertGreaterEqual(len(rows), 5)
        for row in rows:
            trace = row["source_trace"]
            self.assertTrue(trace["batch_id"], row["transaction_id"])
            self.assertEqual(trace["raw_id"], row["source_trace"]["raw_id"])
            self.assertIn("private://imports/", trace["raw_payload_ref"])
            self.assertTrue(trace["parser_version"])
            self.assertIn("账本流水/", row["detail_route"])

    def test_low_confidence_rows_enter_owner_readable_abcd_review_queue(self) -> None:
        queue = self.model["review_queue"]

        self.assertGreaterEqual(len(queue), 1)
        choices = queue[0]["choices"]
        self.assertEqual(choices[0], "A 接受建议分类")
        self.assertEqual(choices[1], "B 标记为转账")
        self.assertEqual(choices[2], "C 标记为消费")
        self.assertEqual(choices[3], "D 保持待复核")
        self.assertEqual(queue[0]["status"], "需要复核")

    def test_transfer_matching_supports_confirm_reject_and_modify_without_consumption_double_count(self) -> None:
        imports = build_stage3_demo_imports()
        transfer = next(match for txn in imports[0].transactions if (match := reconcile_cba_transfer(txn)) is not None)

        confirmed = transfer_match_decision(transfer, "confirm")
        rejected = transfer_match_decision(transfer, "reject")
        modified = transfer_match_decision(transfer, "modify")

        self.assertFalse(confirmed["affects_consumption"])
        self.assertTrue(rejected["affects_consumption"])
        self.assertFalse(modified["affects_consumption"])
        self.assertEqual(modified["status"], "需要复核")

    def test_sync_all_plan_is_low_operation_preview_and_never_executes_external_actions(self) -> None:
        actions = build_sync_all_plan()

        self.assertEqual({item.source_id for item in actions}, set(STAGE3_REQUIRED_ACCOUNT_SOURCES))
        for item in actions:
            self.assertTrue(item.does_not_execute)
            self.assertIn(item.owner_status, SIMPLE_STATUS_LANGUAGE)
            self.assertIn("不登录、不下单、不支付", item.boundary)

    def test_simple_status_language_hides_technical_status_from_owner_copy(self) -> None:
        self.assertEqual(simple_status_language("completed"), "正常")
        self.assertEqual(simple_status_language("NEEDS_DATA"), "需要同步")
        self.assertEqual(simple_status_language("pending-review"), "需要复核")
        self.assertEqual(simple_status_language("failed"), "有异常")
        self.assertEqual(simple_status_language("watch"), "有建议")

    def test_owner_review_checklist_handles_empty_queue(self) -> None:
        self.assertEqual(build_owner_review_checklist(()), [])

    def test_web_shell_exposes_stage3_entries_and_data_health_card(self) -> None:
        root = Path(__file__).resolve().parents[1]
        html = (root / "web" / "index.html").read_text(encoding="utf-8")
        js = (root / "web" / "app" / "shell.js").read_text(encoding="utf-8")

        self.assertIn('data-primary-workspaces="10"', html)
        for label in ("首页总览", "账户与资产", "账本流水", "投资管理", "消费管理", "数据源与上传", "建议与复盘", "报告与洞察"):
            self.assertIn(label, html + js)
        self.assertIn("data_health", html + js)
        for action in ("同步全部", "处理待复核", "查看建议", "生成报告"):
            self.assertIn(action, js)


if __name__ == "__main__":
    unittest.main()
