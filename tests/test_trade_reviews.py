from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from quantlab.research import (
    create_trade_review_record,
    error_profile_frame,
    load_trade_reviews,
    review_dashboard_cards,
    save_trade_review_record,
    trade_review_frame,
)


def test_trade_review_records_are_persistent_and_summarized():
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "TradeReviewRecords.json"
        first = create_trade_review_record(
            {
                "symbol": "600519.SH",
                "market": "CN",
                "strategy_id": "ma_crossover",
                "research_status": "NeedsMoreEvidence",
                "decision_quality_score": 62,
                "action_type": "保持观察",
                "original_plan": "观察趋势是否延续。",
                "executed_as_planned": True,
                "final_pnl_amount": 1200,
                "final_pnl_ratio": 0.012,
                "return_attribution": "行为偏差",
                "error_type": "无明显错误",
            }
        )
        second = create_trade_review_record(
            {
                "symbol": "AAPL",
                "market": "US",
                "strategy_id": "rsi_reversion",
                "research_status": "WatchOnly",
                "decision_quality_score": 72,
                "action_type": "增加暴露",
                "discipline_violation": True,
                "final_pnl_amount": -800,
                "final_pnl_ratio": -0.008,
                "return_attribution": "未确认",
                "error_type": "纪律错误",
            }
        )

        save_trade_review_record(first, path)
        save_trade_review_record(second, path)

        records = load_trade_reviews(path)
        frame = trade_review_frame(path)
        cards = review_dashboard_cards(frame)
        error_profile = error_profile_frame(frame)

        assert len(records) == 2
        assert len(frame) == 2
        assert cards[0]["value"] == 2
        assert set(error_profile["error_type"]) == {"无明显错误", "纪律错误"}
        assert "discipline_violation_rate" in error_profile.columns


def test_trade_review_records_fail_close_on_corrupt_json():
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "TradeReviewRecords.json"
        path.write_text("{bad json", encoding="utf-8")
        record = create_trade_review_record({"symbol": "AAPL", "market": "US"})

        with pytest.raises(ValueError):
            load_trade_reviews(path)
        with pytest.raises(ValueError):
            save_trade_review_record(record, path)
        assert path.read_text(encoding="utf-8") == "{bad json"
