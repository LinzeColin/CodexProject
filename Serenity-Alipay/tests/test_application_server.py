from app.core.application_server import (
    RefreshHolding,
    clear_manual_review_decisions,
    fetch_manual_review_decisions,
    save_manual_review_decision,
    summarize_refresh_changes,
)
from app.db import connect, init_db
from tests.helpers import temp_settings


def test_summarize_refresh_changes_uses_compact_rebalance_language():
    before = {"ETAX": RefreshHolding(code="ETAX", name="Example Tax Fund", weight=0.18)}
    after = {"ETAX": RefreshHolding(code="ETAX", name="Example Tax Fund", weight=0.15)}

    assert summarize_refresh_changes(before, after) == "减仓ETAX 3%到15%"


def test_summarize_refresh_changes_keeps_current_holding_when_unchanged():
    before = {"007300": RefreshHolding(code="007300", name="国联安中证半导体ETF联接A", weight=0.2093)}
    after = {"007300": RefreshHolding(code="007300", name="国联安中证半导体ETF联接A", weight=0.2093)}

    assert summarize_refresh_changes(before, after) == "保持当前持仓"


def test_manual_review_decision_persists_to_sqlite(tmp_path):
    settings = temp_settings(tmp_path)
    init_db(settings.db_path)
    with connect(settings.db_path) as conn:
        conn.execute(
            """
            INSERT INTO manual_review_queue (
                id, run_id, asset_id, reason, action_blocked, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                65,
                "sda_test_r7",
                None,
                "fee/redemption/subscription status missing or closed",
                "No-New-Order",
                "open",
                "2026-06-13T00:00:00Z",
            ),
        )

    result = save_manual_review_decision(
        settings,
        {
            "review_id": 65,
            "decision": "需要补证据",
            "note": "已核对支付宝费率页",
            "savedAt": "20260613 - 17:10 AEST",
        },
    )

    assert result["status"] == "pass"
    records = fetch_manual_review_decisions(settings)
    assert records["65"]["run_id"] == "sda_test_r7"
    assert records["65"]["decision"] == "需要补证据"
    assert records["65"]["note"] == "已核对支付宝费率页"
    assert records["65"]["savedAt"] == "20260613 - 17:10 AEST"
    assert records["65"]["source"] == "sqlite"

    save_manual_review_decision(
        settings,
        {
            "review_id": 65,
            "decision": "已人工处理",
            "note": "已在平台确认暂不新增",
            "savedAt": "20260613 - 17:20 AEST",
        },
    )
    records = fetch_manual_review_decisions(settings)
    assert records["65"]["decision"] == "已人工处理"
    assert records["65"]["note"] == "已在平台确认暂不新增"

    clear_result = clear_manual_review_decisions(settings)
    assert clear_result["deleted"] == 1
    assert fetch_manual_review_decisions(settings) == {}
