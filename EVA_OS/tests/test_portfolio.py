import unittest

import pandas as pd

from quantlab.backtest import BacktestConfig, PortfolioBacktestEngine
from quantlab.data.models import BarDataRequest
from quantlab.data.providers import SampleDataProvider
from quantlab.strategies import MomentumRotationStrategy


class PortfolioBacktestTests(unittest.TestCase):
    def test_portfolio_rotation_runs(self):
        provider = SampleDataProvider(seed=3)
        data = pd.concat(
            [
                provider.get_bars(BarDataRequest(symbol=s, market="US", interval="1d", start="2020-01-01", end="2021-12-31"))
                for s in ["SPY", "QQQ", "TLT", "GLD"]
            ],
            ignore_index=True,
        )
        strategy = MomentumRotationStrategy(lookback=60, top_n=2)
        result = PortfolioBacktestEngine(BacktestConfig(initial_cash=100_000)).run(data, strategy)
        self.assertFalse(result.equity_curve.empty)
        self.assertFalse(result.positions.empty)
        self.assertIn("sharpe", result.metrics)
        self.assertGreater(result.metrics["ending_equity"], 0)


if __name__ == "__main__":
    unittest.main()

