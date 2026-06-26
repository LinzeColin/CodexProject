from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from econ_bleed_analyzer.alipay import Transaction
from econ_bleed_analyzer.classifier import classify_transaction, load_rules
from econ_bleed_analyzer.reports import _category_summary, _review_candidate_for, _review_status_summary, core_metrics
from econ_bleed_analyzer.review import load_review_decisions


RULES = load_rules(ROOT / "configs" / "classification_rules.json")


def large_tx() -> Transaction:
    return Transaction(
        transaction_time=datetime(2026, 5, 1, 12, 0, 0),
        transaction_type="转账红包",
        counterparty="待确认大额",
        account="/",
        description="转账",
        direction="支出",
        amount_cents=20_000_00,
        payment_method="余额宝",
        status="交易成功",
        order_id="review-1",
        merchant_order_id="",
        note="",
        source_file="sample.csv",
    )


def large_tx_with(**overrides) -> Transaction:
    data = large_tx().__dict__.copy()
    data.update(overrides)
    return Transaction(**data)


class ReviewDecisionTests(unittest.TestCase):
    def test_unconfirmed_large_expense_is_not_in_production_total(self):
        row = classify_transaction(large_tx(), RULES)
        self.assertTrue(row.needs_review)
        self.assertEqual(core_metrics([row])["total_expense"], 0)
        self.assertEqual(core_metrics([row])["pending_review"], 20_000_00)

    def test_manual_include_can_split_large_expense(self):
        row = classify_transaction(large_tx(), RULES)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "decisions.csv"
            path.write_text(
                "review_key,decision,main_category,sub_category,allocation_pct,risk_tags,note\n"
                "review-1,include,生活刚需,教育医疗,50,家庭教育,split test\n"
                "review-1,include,生活刚需,住房缴费,25,住房缴费,split test\n"
                "review-1,include,生活刚需,餐饮日用,25,餐饮日用,split test\n",
                encoding="utf-8",
            )
            decisions = load_review_decisions(path)
        metrics = core_metrics([row], decisions)
        self.assertEqual(metrics["total_expense"], 20_000_00)
        self.assertEqual(metrics["pending_review"], 0)
        sub_amounts = {
            item["sub_category"]: item["amount_cents"]
            for item in _category_summary([row], decisions)
            if item["level"] == "子类"
        }
        self.assertEqual(sub_amounts["教育医疗"], 10_000_00)
        self.assertEqual(sub_amounts["住房缴费"], 5_000_00)

    def test_confirmed_lolol_jiahansong_is_split_into_living_categories(self):
        row = classify_transaction(
            large_tx_with(
                counterparty="lolol(贾韩松)",
                description="家庭共同支出",
                order_id="lolol-1",
            ),
            RULES,
        )
        self.assertTrue(row.needs_review)
        metrics = core_metrics([row])
        self.assertEqual(metrics["total_expense"], 20_000_00)
        self.assertEqual(metrics["pending_review"], 0)
        sub_amounts = {
            item["sub_category"]: item["amount_cents"]
            for item in _category_summary([row])
            if item["level"] == "子类"
        }
        self.assertEqual(sub_amounts["教育医疗"], 10_000_00)
        self.assertEqual(sub_amounts["住房缴费"], 5_000_00)
        self.assertEqual(sub_amounts["餐饮日用"], 5_000_00)

    def test_confirmed_chun_zhangweiqian_goes_to_family_card(self):
        row = classify_transaction(
            large_tx_with(
                counterparty="蠢张伟倩",
                description="家庭转账",
                order_id="chun-1",
            ),
            RULES,
        )
        self.assertTrue(row.needs_review)
        metrics = core_metrics([row])
        self.assertEqual(metrics["total_expense"], 20_000_00)
        self.assertEqual(metrics["pending_review"], 0)
        sub_amounts = {
            item["sub_category"]: item["amount_cents"]
            for item in _category_summary([row])
            if item["level"] == "子类"
        }
        self.assertEqual(sub_amounts["亲情卡人情往来"], 20_000_00)

    def test_review_status_summary_splits_pending_confirmed_and_excluded(self):
        pending = classify_transaction(large_tx_with(order_id="pending-1", counterparty="待确认大额"), RULES)
        manual_include = classify_transaction(large_tx_with(order_id="include-1", counterparty="确认纳入"), RULES)
        manual_exclude = classify_transaction(large_tx_with(order_id="exclude-1", counterparty="确认排除"), RULES)
        builtin = classify_transaction(large_tx_with(order_id="lolol-2", counterparty="lolol贾韩松"), RULES)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "decisions.csv"
            path.write_text(
                "review_key,decision,main_category,sub_category,allocation_pct,risk_tags,note\n"
                "include-1,include,生活刚需,餐饮日用,100,餐饮日用,confirmed\n"
                "exclude-1,exclude,,,,,not expense\n",
                encoding="utf-8",
            )
            decisions = load_review_decisions(path)
        summary = {item["status"]: item for item in _review_status_summary([pending, manual_include, manual_exclude, builtin], decisions)}
        self.assertEqual(summary["pending_review"]["count"], 1)
        self.assertEqual(summary["manual_include"]["count"], 1)
        self.assertEqual(summary["manual_exclude"]["count"], 1)
        self.assertEqual(summary["auto_confirmed_rule"]["count"], 1)
        self.assertEqual(summary["pending_review"]["amount_pct"], "25.00%")

    def test_review_candidate_keeps_person_transfer_for_manual_review(self):
        row = classify_transaction(large_tx_with(order_id="person-1", counterparty="张三", description="转账"), RULES)
        candidate = _review_candidate_for(row)
        self.assertEqual(candidate["candidate_action"], "manual_review")
        self.assertEqual(candidate["candidate_confidence"], "low")

    def test_review_candidate_prefills_merchant_like_large_payment(self):
        row = classify_transaction(
            large_tx_with(order_id="merchant-1", counterparty="某某有限公司", description="服务费"),
            RULES,
        )
        candidate = _review_candidate_for(row)
        self.assertEqual(candidate["candidate_action"], "include_suggested")
        self.assertEqual(candidate["candidate_confidence"], "high")


if __name__ == "__main__":
    unittest.main()
