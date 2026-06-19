import unittest

from src.backtesting.engine import run_equal_weight_backtest
from src.config import ROOT
from src.data_io import read_csv


class BacktestingTest(unittest.TestCase):
    def test_backtest_produces_metrics_and_curve(self):
        rows = read_csv(ROOT / "data" / "sample" / "market_prices.csv")
        result = run_equal_weight_backtest(rows, ["DEMO_SEMI", "DEMO_AI"])
        self.assertNotEqual(result["metrics"]["cumulative_return"], 0)
        self.assertLessEqual(result["metrics"]["max_drawdown"], 0)
        self.assertGreater(len(result["equity_curve"]), 2)


if __name__ == "__main__":
    unittest.main()
