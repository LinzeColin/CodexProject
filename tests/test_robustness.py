import unittest

from quantlab.analysis import bootstrap_equity_robustness, robustness_summary_rows
from quantlab.backtest import BacktestConfig, BacktestEngine
from quantlab.data.models import BarDataRequest
from quantlab.data.providers import SampleDataProvider
from quantlab.strategies import MovingAverageCrossoverStrategy


class RobustnessTests(unittest.TestCase):
    def test_bootstrap_equity_robustness_is_reproducible_and_summarized(self):
        data = SampleDataProvider(seed=17).get_bars(
            BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2020-01-01", end="2021-12-31")
        )
        result = BacktestEngine(BacktestConfig(initial_cash=100_000)).run(
            data, MovingAverageCrossoverStrategy(short_window=5, long_window=20)
        )

        first = bootstrap_equity_robustness(result.equity_curve, simulations=50, seed=7, target_return=0.05)
        second = bootstrap_equity_robustness(result.equity_curve, simulations=50, seed=7, target_return=0.05)
        rows = robustness_summary_rows(first)

        self.assertEqual(first.summary["simulations"], 10000)
        self.assertEqual(len(first.simulations), 10000)
        self.assertGreater(first.summary["horizon"], 0)
        self.assertEqual(first.simulations["total_return"].iloc[0], second.simulations["total_return"].iloc[0])
        self.assertIn("loss_probability", first.summary)
        self.assertIn("target_probability", first.summary)
        self.assertFalse(first.sample_paths.empty)
        self.assertFalse(first.path_interval.empty)
        self.assertIn("p05", first.path_interval.columns)
        self.assertIn("median", first.path_interval.columns)
        self.assertIn("p95", first.path_interval.columns)
        self.assertTrue(any(row["指标 Metric"].startswith("亏损概率") for row in rows))

    def test_bootstrap_default_simulation_count_is_10000(self):
        data = SampleDataProvider(seed=18).get_bars(
            BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2020-01-01", end="2020-03-31")
        )
        result = BacktestEngine(BacktestConfig(initial_cash=100_000)).run(
            data, MovingAverageCrossoverStrategy(short_window=5, long_window=20)
        )

        robustness = bootstrap_equity_robustness(result.equity_curve, seed=7)

        self.assertEqual(robustness.summary["simulations"], 10000)
        self.assertEqual(len(robustness.simulations), 10000)


if __name__ == "__main__":
    unittest.main()
