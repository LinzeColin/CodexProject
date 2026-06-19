import numpy as np
import pandas as pd

from quantlab.analysis import market_feel_chart_frame, market_feel_from_bars, market_feel_indicator_rows, market_feel_training_case


def _bars(close_values, volume_values=None):
    index = pd.date_range("2026-01-01", periods=len(close_values), freq="B")
    close = np.array(close_values, dtype=float)
    volume = np.array(volume_values if volume_values is not None else [100000] * len(close), dtype=float)
    return pd.DataFrame(
        {
            "datetime": index,
            "symbol": "TEST",
            "market": "US",
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": volume,
        }
    )


def test_market_feel_from_bars_returns_explanation_analysis_and_conclusion():
    bars = _bars(np.linspace(100, 150, 120), volume_values=np.linspace(100000, 180000, 120))

    result = market_feel_from_bars(bars, symbol="TEST", name="Test Asset", market="US")

    assert result.symbol == "TEST"
    assert result.trend_state in {"多头结构", "短期改善"}
    assert result.market_feel_score > 50
    assert result.support20 > 0
    assert result.resistance20 > 0
    assert "讲解" in result.explanation
    assert "分析" in result.analysis
    assert "技术判断" in result.analysis
    assert "20日支撑" in result.analysis
    assert "研究结论" in result.training_conclusion
    assert "训练题" in result.practice_prompt
    assert result.data_points == 120


def test_market_feel_indicator_rows_and_chart_frame_cover_core_indicators():
    bars = _bars(np.r_[np.linspace(140, 100, 70), np.linspace(100, 112, 50)])
    result = market_feel_from_bars(bars, symbol="TEST", name="Test Asset", market="US")

    rows = market_feel_indicator_rows(result)
    chart = market_feel_chart_frame(bars)

    indicators = {row["指标"] for row in rows}
    assert {"RSI14", "MACD 柱", "相对 MA20", "ATR14/价格", "成交量比", "20日支撑", "20日压力"}.issubset(indicators)
    assert {"ma20", "ma60", "support20", "resistance20", "bb_upper", "bb_lower", "rsi14", "macd_hist"}.issubset(chart.columns)
    assert len(chart) == 120


def test_market_feel_training_case_hides_future_and_records_outcome():
    visible = np.linspace(100, 130, 100)
    hidden = np.array([131, 132, 133, 134, 136], dtype=float)
    bars = _bars(np.r_[visible, hidden])

    case = market_feel_training_case(bars, symbol="TEST", name="Test Asset", market="US", answer_horizon=5)
    row = case.to_row()

    assert case.result.latest_date == pd.Timestamp(bars["datetime"].iloc[-6]).date().isoformat()
    assert case.hidden_end_date == pd.Timestamp(bars["datetime"].iloc[-1]).date().isoformat()
    assert case.actual_direction == "上涨"
    assert case.actual_return > 0
    assert row["actual_return_interval"] in {"2.00%至5.00%", "5.00%以上"}
    assert "事前技术分析" in row["pre_result_analysis"]
    assert "不能倒推" in row["fairness_note"]


def test_market_feel_rejects_too_short_sample():
    bars = _bars(np.linspace(100, 110, 30))

    try:
        market_feel_from_bars(bars, symbol="SHORT")
    except ValueError as exc:
        assert "至少需要 60 个交易日" in str(exc)
    else:
        raise AssertionError("short market-feel sample should fail")
