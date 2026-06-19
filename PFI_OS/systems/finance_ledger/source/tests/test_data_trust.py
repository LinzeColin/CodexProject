from __future__ import annotations

from datetime import datetime

from econ_bleed_analyzer.alipay import Transaction
from econ_bleed_analyzer.classifier import classify_transaction, load_rules
from econ_bleed_analyzer.data_trust import build_data_trust_transactions, summarize_data_trust
from econ_bleed_analyzer.review import ManualAllocation, ReviewDecisions


RULES = load_rules("configs/classification_rules.json")


def tx(**overrides) -> Transaction:
    data = {
        "transaction_time": datetime(2026, 6, 1, 12, 0, 0),
        "transaction_type": "餐饮美食",
        "counterparty": "商户",
        "account": "",
        "description": "午餐",
        "direction": "支出",
        "amount_cents": 3500,
        "payment_method": "余额",
        "status": "交易成功",
        "order_id": "order-1",
        "merchant_order_id": "",
        "note": "",
        "source_file": "sample.csv",
        "source_platform": "alipay",
    }
    data.update(overrides)
    return Transaction(**data)


def test_data_trust_marks_production_row_as_reconciled():
    row = classify_transaction(tx(), RULES)
    rows = build_data_trust_transactions([row], allocation_rows=[{"review_key": "order-1"}])
    assert rows[0]["data_trust_status"] == "RECONCILED"
    assert rows[0]["evidence_classification"] == "FACT"
    assert rows[0]["decision_grade"] == "Actionable"


def test_data_trust_blocks_large_unconfirmed_expense():
    row = classify_transaction(tx(amount_cents=1_500_000, order_id="large-1"), RULES)
    rows = build_data_trust_transactions([row], allocation_rows=[])
    assert rows[0]["data_trust_status"] == "NEEDS_REVIEW"
    assert rows[0]["review_required"] is True


def test_data_trust_records_user_confirmed_exclusion():
    row = classify_transaction(tx(amount_cents=1_500_000, order_id="review-1"), RULES)
    decisions = ReviewDecisions(excluded={"review-1"})
    rows = build_data_trust_transactions([row], review_decisions=decisions, allocation_rows=[])
    assert rows[0]["data_trust_status"] == "USER_CONFIRMED"
    assert rows[0]["ledger_effect"] == "excluded_by_user_review"
    assert rows[0]["decision_grade"] == "Reject"


def test_data_trust_user_confirmed_include_reconciles_when_allocated():
    row = classify_transaction(tx(amount_cents=1_500_000, order_id="review-2"), RULES)
    decisions = ReviewDecisions(
        included={
            "review-2": [
                ManualAllocation(
                    main_category="生活刚需",
                    sub_category="餐饮日用",
                    risk_tags=["基础支出"],
                    pct=100.0,
                )
            ]
        }
    )
    rows = build_data_trust_transactions([row], review_decisions=decisions, allocation_rows=[{"review_key": "review-2"}])
    assert rows[0]["data_trust_status"] == "RECONCILED"
    assert rows[0]["ledger_effect"] == "production_reconciled_after_user_review"


def test_data_trust_rejects_failed_or_closed_transactions():
    row = classify_transaction(tx(status="交易关闭", order_id="closed-1"), RULES)
    rows = build_data_trust_transactions([row], allocation_rows=[])
    assert rows[0]["data_trust_status"] == "REJECTED"
    summary = {item["data_trust_status"]: item for item in summarize_data_trust(rows)}
    assert summary["REJECTED"]["count_pct"] == "100.00%"
