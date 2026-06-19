import unittest

from quantlab.analysis.strategy_diagnostics import build_strategy_diagnostics, cost_sensitivity_frame, round_trip_frame
from quantlab.backtest import BacktestConfig, BacktestEngine
from quantlab.data.models import BarDataRequest
from quantlab.data.providers import SampleDataProvider
from quantlab.strategies import MovingAverageCrossoverStrategy


class StrategyDiagnosticsTests(unittest.TestCase):
    def _result(self):
        data = SampleDataProvider(seed=31).get_bars(
            BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2020-01-01", end="2021-12-31")
        )
        return BacktestEngine(BacktestConfig(initial_cash=100_000, commission_rate=0.001, slippage_bps=5)).run(
            data,
            MovingAverageCrossoverStrategy(short_window=5, long_window=20),
        )

    def test_round_trip_frame_reconstructs_completed_trade_quality(self):
        result = self._result()

        round_trips = round_trip_frame(result.trades)

        self.assertFalse(round_trips.empty)
        self.assertIn("net_pnl", round_trips.columns)
        self.assertIn("holding_days", round_trips.columns)
        self.assertGreaterEqual(round_trips["holding_days"].min(), 0)

    def test_cost_sensitivity_uses_modeled_cost_multiplier(self):
        result = self._result()

        frame = cost_sensitivity_frame(result)

        self.assertEqual(list(frame["成本倍数 Cost Multiplier"]), ["1.0x", "2.0x", "3.0x"])
        self.assertGreaterEqual(frame.loc[1, "额外成本 Additional Cost"], frame.loc[0, "额外成本 Additional Cost"])
        self.assertIn("状态 Status", frame.columns)

    def test_build_strategy_diagnostics_returns_all_research_sections(self):
        diagnostics = build_strategy_diagnostics(self._result())

        self.assertFalse(diagnostics.trade_quality.empty)
        self.assertFalse(diagnostics.cost_sensitivity.empty)
        self.assertFalse(diagnostics.regime_breakdown.empty)
        self.assertFalse(diagnostics.failure_checks.empty)
        self.assertIn("高波动 High Volatility", set(diagnostics.regime_breakdown["市场环境 Market Regime"]))
        self.assertIn("检查项 Check", diagnostics.failure_checks.columns)


if __name__ == "__main__":
    unittest.main()
