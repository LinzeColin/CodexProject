import unittest

from quantlab.backtest import BacktestConfig, BacktestEngine
from quantlab.data.models import BarDataRequest
from quantlab.data.providers import SampleDataProvider
from quantlab.strategies import BollingerReversionStrategy, MovingAverageCrossoverStrategy


class BacktestTests(unittest.TestCase):
    def test_sample_backtest_runs(self):
        data = SampleDataProvider(seed=1).get_bars(
            BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2020-01-01", end="2021-12-31")
        )
        strategy = MovingAverageCrossoverStrategy(short_window=5, long_window=20)
        result = BacktestEngine(BacktestConfig(initial_cash=100_000)).run(data, strategy)
        self.assertFalse(result.equity_curve.empty)
        self.assertIn("sharpe", result.metrics)
        self.assertIn("max_drawdown", result.metrics)
        self.assertIn("buy_count", result.metrics)
        self.assertIn("sell_count", result.metrics)
        self.assertEqual(result.metrics["buy_count"], int((result.trades["side"] == "BUY").sum()))
        self.assertEqual(result.metrics["sell_count"], int((result.trades["side"] == "SELL").sum()))
        self.assertGreater(result.metrics["ending_equity"], 0)

    def test_market_impact_is_tracked_as_modeled_trading_friction(self):
        data = SampleDataProvider(seed=2).get_bars(
            BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2020-01-01", end="2021-12-31")
        )
        strategy = MovingAverageCrossoverStrategy(short_window=5, long_window=20)
        result = BacktestEngine(BacktestConfig(initial_cash=100_000, market_impact_bps=25.0)).run(data, strategy)
        self.assertIn("market_impact_bps", result.metadata["backtest"])
        self.assertEqual(result.metadata["backtest"]["market_impact_bps"], 25.0)
        self.assertFalse(result.trades.empty)
        self.assertIn("market_impact_cost", result.trades.columns)
        self.assertIn("execution_cost", result.trades.columns)
        self.assertGreater(result.trades["market_impact_cost"].sum(), 0)
        self.assertGreaterEqual(result.metrics["cost_total"], result.trades["cost"].sum())

    def test_bollinger_reversion_backtest_runs(self):
        data = SampleDataProvider(seed=3).get_bars(
            BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2020-01-01", end="2021-12-31")
        )
        strategy = BollingerReversionStrategy(window=20, num_std=1.5, exit_z=0.0)
        result = BacktestEngine(BacktestConfig(initial_cash=100_000)).run(data, strategy)

        self.assertFalse(result.signals.empty)
        self.assertIn("z_score", result.signals.columns)
        self.assertIn("total_return", result.metrics)
        self.assertGreater(result.metrics["ending_equity"], 0)

    def test_long_only_backtest_never_has_negative_position(self):
        data = SampleDataProvider(seed=4).get_bars(
            BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2020-01-01", end="2021-12-31")
        )
        strategy = MovingAverageCrossoverStrategy(short_window=5, long_window=20)
        result = BacktestEngine(BacktestConfig(initial_cash=100_000, allow_short=False)).run(data, strategy)

        self.assertGreaterEqual(result.positions["quantity"].min(), -1e-8)


if __name__ == "__main__":
    unittest.main()
