import numpy as np
import pandas as pd

from quantlab.analysis import default_sentiment_universe, sentiment_from_bars, sentiment_score, sentiment_state, sentiment_summary


def _bars(close_values):
    index = pd.date_range("2026-01-01", periods=len(close_values), freq="B")
    close = np.array(close_values, dtype=float)
    return pd.DataFrame(
        {
            "datetime": index,
            "symbol": "TEST",
            "market": "US",
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 100000,
        }
    )


def test_sentiment_from_bars_returns_explainable_metrics():
    bars = _bars(np.linspace(100, 140, 80))

    result = sentiment_from_bars(bars, symbol="TEST", name="Test Asset", market="US")

    assert result.symbol == "TEST"
    assert result.sentiment_score > 50
    assert result.sentiment_state in {"偏热", "过热"}
    assert result.twenty_day_return > 0
    assert result.data_points == 80


def test_sentiment_score_and_state_boundaries_are_stable():
    cold = sentiment_score(
        one_day_return=-0.04,
        twenty_day_return=-0.12,
        price_vs_ma20=-0.08,
        rsi14=25,
        volatility20=0.35,
        max_drawdown60=-0.20,
    )
    hot = sentiment_score(
        one_day_return=0.03,
        twenty_day_return=0.16,
        price_vs_ma20=0.08,
        rsi14=78,
        volatility20=0.18,
        max_drawdown60=-0.02,
    )

    assert cold < hot
    assert sentiment_state(cold) in {"偏冷", "极度低迷"}
    assert sentiment_state(hot) in {"偏热", "过热"}


def test_default_universe_and_summary_cover_major_markets():
    cn = default_sentiment_universe("CN")
    rows = pd.DataFrame(
        [
            {"sentiment_score": 80, "sentiment_state": "过热", "latest_date": "2026-06-03"},
            {"sentiment_score": 40, "sentiment_state": "偏冷", "latest_date": "2026-06-03"},
        ]
    )

    summary = sentiment_summary(rows)

    assert any(item.symbol == "000001" for item in cn)
    assert summary["object_count"] == 2
    assert summary["hot_count"] == 1
    assert summary["cold_count"] == 1
