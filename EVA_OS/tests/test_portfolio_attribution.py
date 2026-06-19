import unittest

import pandas as pd

from quantlab.analysis import (
    portfolio_attribution,
    portfolio_concentration_metrics,
    portfolio_exposure_breakdown,
    portfolio_single_symbol_loss,
    portfolio_stress_scenarios,
)
from quantlab.backtest import BacktestConfig, PortfolioBacktestEngine
from quantlab.data.models import BarDataRequest
from quantlab.data.providers import SampleDataProvider
from quantlab.strategies import MomentumRotationStrategy


class PortfolioAttributionTests(unittest.TestCase):
    def test_portfolio_attribution_summarizes_symbol_exposure_and_costs(self):
        provider = SampleDataProvider(seed=15)
        data = pd.concat(
            [
                provider.get_bars(BarDataRequest(symbol=s, market="US", interval="1d", start="2020-01-01", end="2021-12-31"))
                for s in ["SPY", "QQQ", "TLT", "GLD"]
            ],
            ignore_index=True,
        )
        result = PortfolioBacktestEngine(BacktestConfig(initial_cash=100_000, market_impact_bps=5)).run(
            data,
            MomentumRotationStrategy(lookback=60, top_n=2),
        )
        attribution = portfolio_attribution(result)
        concentration = portfolio_concentration_metrics(result)

        self.assertFalse(attribution.empty)
        self.assertIn("avg_weight", attribution.columns)
        self.assertIn("execution_cost", attribution.columns)
        self.assertGreaterEqual(concentration["max_symbol_weight"], 0.0)
        self.assertGreaterEqual(concentration["top3_ending_weight"], concentration["max_symbol_weight"])
        self.assertEqual(concentration["symbol_count"], 4.0)
        self.assertIn("cash_weight", concentration)
        self.assertIn("gross_exposure", concentration)

        exposure = portfolio_exposure_breakdown(result)
        stress = portfolio_stress_scenarios(result)
        single_loss = portfolio_single_symbol_loss(result)

        self.assertFalse(exposure.empty)
        self.assertIn("市场", set(exposure["dimension"]))
        self.assertIn("货币", set(exposure["dimension"]))
        self.assertIn("主题", set(exposure["dimension"]))
        self.assertEqual(set(stress["shock"]), {-0.10, -0.20, -0.30, -0.50})
        self.assertIn("rebound_needed_to_recover", stress.columns)
        self.assertFalse(single_loss.empty)
        self.assertIn("account_loss_ratio", single_loss.columns)


if __name__ == "__main__":
    unittest.main()
