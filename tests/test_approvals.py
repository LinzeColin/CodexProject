import tempfile
import unittest

import pandas as pd

from quantlab.approvals import StrategyApprovalRegistry
from quantlab.backtest import BacktestConfig, BacktestEngine
from quantlab.data.models import BarDataRequest
from quantlab.data.providers import SampleDataProvider
from quantlab.strategies import AlipayStrategy, BollingerReversionStrategy
from quantlab.strategies.base import Strategy, StrategyResult, finalize_signal_frame


class CustomUnapprovedStrategy(Strategy):
    strategy_id = "custom_unapproved"
    version = "9.9.9"

    def generate_signals(self, data: pd.DataFrame) -> StrategyResult:
        return StrategyResult(signals=finalize_signal_frame(data, pd.Series(0.0, index=data.index)), metadata=self.metadata())


class ApprovalTests(unittest.TestCase):
    def test_custom_strategy_without_approval_is_blocked(self):
        data = SampleDataProvider(seed=12).get_bars(
            BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2020-01-01", end="2020-03-31")
        )
        with self.assertRaises(PermissionError):
            BacktestEngine(BacktestConfig(initial_cash=100_000)).run(data, CustomUnapprovedStrategy())

    def test_new_built_in_bollinger_strategy_is_approved(self):
        data = SampleDataProvider(seed=14).get_bars(
            BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2020-01-01", end="2020-06-30")
        )
        result = BacktestEngine(BacktestConfig(initial_cash=100_000)).run(data, BollingerReversionStrategy(window=20, num_std=1.5))

        self.assertGreater(result.metrics["ending_equity"], 0)

    def test_alipay_built_in_strategy_is_approved(self):
        data = SampleDataProvider(seed=15).get_bars(
            BarDataRequest(symbol="600519.SH", market="CN", interval="1d", start="2020-01-01", end="2020-06-30")
        )
        result = BacktestEngine(BacktestConfig(initial_cash=100_000)).run(data, AlipayStrategy(initial_cash=100_000))

        self.assertGreater(result.metrics["ending_equity"], 0)

    def test_registry_request_and_approve(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = StrategyApprovalRegistry(path=f"{tmp}/StrategyApprovals.json")
            pending = registry.request_approval("custom_strategy", "0.1.0", "Initial strategy review")
            self.assertEqual(pending.status, "Pending")
            approved = registry.approve("custom_strategy", "0.1.0")
            self.assertEqual(approved.status, "Approved")
            self.assertEqual(len(registry.records()), 1)

    def test_registry_approve_or_request_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = StrategyApprovalRegistry(path=f"{tmp}/StrategyApprovals.json")

            approved = registry.approve_or_request("custom_strategy", "0.1.0", "One-click approval", "Reviewed")
            approved_again = registry.approve_or_request("custom_strategy", "0.1.0", "One-click approval", "Reviewed")

            self.assertEqual(approved.status, "Approved")
            self.assertEqual(approved_again.status, "Approved")
            self.assertEqual(registry.latest_status("custom_strategy", "0.1.0"), "Approved")
            self.assertEqual(len(registry.records()), 1)

    def test_registry_fail_closes_on_corrupt_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/StrategyApprovals.json"
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("{bad json")
            registry = StrategyApprovalRegistry(path=path)

            with self.assertRaises(ValueError):
                registry.records()
            with self.assertRaises(ValueError):
                registry.request_approval("custom_strategy", "0.1.0", "Review")
            with open(path, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "{bad json")


if __name__ == "__main__":
    unittest.main()
