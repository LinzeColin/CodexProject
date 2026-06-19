from __future__ import annotations

from econ_bleed_analyzer.manual_review_audit import (
    build_manual_review_audit_rows,
    manual_review_audit_report_markdown,
    summarize_manual_review_audit,
)


def test_manual_review_audit_marks_large_pending_as_watch_blocker():
    rows = build_manual_review_audit_rows(
        review_rows=[
            {
                "review_key": "r1",
                "amount": "120000.00",
                "amount_cents": "12000000",
                "transaction_time": "2026-01-01",
                "counterparty": "大额对象",
                "description": "待确认",
                "main_category": "社交家庭",
                "sub_category": "红包转账",
                "risk_tags": "大额复核",
            }
        ],
        candidate_rows=[
            {
                "review_key": "r1",
                "candidate_action": "manual_review",
                "candidate_confidence": "low",
                "candidate_reason": "疑似个人转账",
            }
        ],
        status_rows=[],
        data_trust_rows=[{"review_key": "r1", "data_trust_status": "NEEDS_REVIEW", "status_reason": "large"}],
    )

    assert rows[0]["queue_status"] == "PENDING_REVIEW"
    assert rows[0]["priority"] == "P0"
    assert rows[0]["evidence_classification"] == "OBSERVATION"
    assert rows[0]["decision_grade"] == "Watch"
    assert rows[0]["ledger_effect"] == "blocked_until_manual_review"


def test_manual_review_audit_records_invalid_decision_as_reject():
    rows = build_manual_review_audit_rows(
        review_rows=[],
        candidate_rows=[],
        status_rows=[],
        data_trust_rows=[],
        invalid_decision_rows=[{"review_key": "bad1", "error": "invalid action"}],
    )

    assert rows[0]["queue_status"] == "INVALID_DECISION"
    assert rows[0]["priority"] == "P0"
    assert rows[0]["decision_grade"] == "Reject"
    assert rows[0]["evidence_classification"] == "FACT"


def test_manual_review_audit_report_contains_machine_readable_contract():
    rows = build_manual_review_audit_rows(
        review_rows=[],
        candidate_rows=[],
        status_rows=[{"status": "pending_review", "next_action": "none"}],
        data_trust_rows=[],
    )
    summary = summarize_manual_review_audit(rows)
    report = manual_review_audit_report_markdown(rows)

    assert summary[0]["queue_status"] == "EMPTY"
    assert "audit/manual_review_queue_audit.csv" in report
    assert "v_manual_review_queue_blockers" in report
