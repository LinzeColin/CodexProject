import unittest

import pandas as pd

from quantlab.backtest import BacktestConfig, BacktestEngine
from quantlab.strategies import AlipayEnhancedStrategy, AlipayStrategy


def _bars(closes, datetimes=None):
    datetimes = datetimes or pd.date_range("2024-01-01", periods=len(closes), freq="D")
    return pd.DataFrame(
        {
            "datetime": pd.to_datetime(datetimes),
            "symbol": "600519.SH",
            "market": "CN",
            "open": closes,
            "high": closes,
            "low": closes,
            "close": closes,
            "volume": [1000] * len(closes),
        }
    )


class AlipayStrategyTests(unittest.TestCase):
    def test_down_day_buys_integer_amount_from_previous_close(self):
        data = _bars([100.0, 96.46])
        strategy = AlipayStrategy(buy_base_amount=100_000, initial_cash=100_000)

        signals = strategy.generate_signals(data).signals

        self.assertEqual(signals.loc[1, "action"], "BUY")
        self.assertEqual(signals.loc[1, "order_value"], 3540)
        self.assertAlmostEqual(signals.loc[1, "daily_return"], -0.0354)

    def test_intraday_signal_uses_first_row_at_or_after_1430(self):
        data = _bars(
            [100.0, 98.0, 96.0, 95.0],
            [
                "2024-01-01 15:00:00",
                "2024-01-02 14:29:00",
                "2024-01-02 14:30:00",
                "2024-01-02 14:31:00",
            ],
        )
        strategy = AlipayStrategy(buy_base_amount=100_000, initial_cash=100_000)

        signals = strategy.generate_signals(data).signals

        self.assertEqual(signals.loc[1, "action"], "HOLD")
        self.assertEqual(signals.loc[2, "action"], "BUY")
        self.assertEqual(signals.loc[2, "order_value"], 4000)
        self.assertEqual(signals.loc[3, "action"], "HOLD")

    def test_profitable_up_day_uses_highest_sell_threshold(self):
        data = _bars([100.0, 96.0, 121.0])
        strategy = AlipayStrategy(buy_base_amount=100_000, initial_cash=100_000)

        signals = strategy.generate_signals(data).signals

        self.assertEqual(signals.loc[1, "action"], "BUY")
        self.assertEqual(signals.loc[2, "action"], "SELL")
        self.assertEqual(signals.loc[2, "sell_fraction"], 1.0)
        self.assertGreaterEqual(signals.loc[2, "position_return"], 0.20)

    def test_insufficient_cash_skips_buy_signal(self):
        data = _bars([100.0, 90.0])
        strategy = AlipayStrategy(buy_base_amount=100_000, initial_cash=5_000)

        signals = strategy.generate_signals(data).signals

        self.assertEqual(signals.loc[1, "action"], "HOLD")
        self.assertEqual(signals.loc[1, "order_value"], 0.0)
        self.assertIn("insufficient", signals.loc[1, "reason"])

    def test_order_signal_backtest_runs_long_only(self):
        data = _bars([100.0, 96.0, 121.0, 118.0])
        strategy = AlipayStrategy(buy_base_amount=100_000, initial_cash=100_000)

        result = BacktestEngine(BacktestConfig(initial_cash=100_000, allow_short=False)).run(data, strategy)

        self.assertFalse(result.trades.empty)
        self.assertIn("order_value", result.trades.columns)
        self.assertIn("sell_fraction", result.trades.columns)
        self.assertGreaterEqual(result.positions["quantity"].min(), -1e-8)
        self.assertEqual(result.metadata["backtest"]["execution_model"], "order_value_and_sell_fraction_at_close_proxy")

    def test_enhanced_strategy_participates_in_strong_uptrend(self):
        closes = [100 + index * 1.5 for index in range(90)]
        data = _bars(closes)
        strategy = AlipayEnhancedStrategy(
            buy_base_amount=100_000,
            initial_cash=100_000,
            trend_buy_multiplier=1.0,
            rsi_overbought=90.0,
        )

        signals = strategy.generate_signals(data).signals

        self.assertIn("rsi", signals.columns)
        self.assertIn("macd_hist", signals.columns)
        self.assertTrue((signals["strong_trend"]).any())
        self.assertTrue((signals["action"] == "BUY").any())
        self.assertGreater(signals["target_weight"].max(), 0)

    def test_enhanced_strategy_delays_selling_in_strong_non_overbought_trend(self):
        strategy = AlipayEnhancedStrategy(trend_hold_buffer=0.05)

        self.assertEqual(
            strategy._sell_fraction(0.20, strong_trend=True, overbought=False, weak_trend=False),
            0.25,
        )
        self.assertEqual(
            strategy._sell_fraction(0.20, strong_trend=False, overbought=True, weak_trend=False),
            1.0,
        )

    def test_enhanced_order_signal_backtest_runs_long_only(self):
        closes = [100.0, 96.0, 98.0, 101.0, 105.0, 109.0, 112.0, 116.0, 121.0] * 12
        data = _bars(closes)
        strategy = AlipayEnhancedStrategy(buy_base_amount=100_000, initial_cash=100_000, rsi_overbought=90.0)

        result = BacktestEngine(BacktestConfig(initial_cash=100_000, allow_short=False)).run(data, strategy)

        self.assertFalse(result.trades.empty)
        self.assertIn("order_value", result.trades.columns)
        self.assertGreaterEqual(result.positions["quantity"].min(), -1e-8)
        self.assertEqual(result.metadata["strategy"]["strategy_id"], "alipay_enhanced")


if __name__ == "__main__":
    unittest.main()
