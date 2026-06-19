from __future__ import annotations

from quantlab.backtest import BacktestConfig
from quantlab.data.models import BarDataRequest
from quantlab.data.providers import SampleDataProvider
from quantlab.research import ExperimentRunner
from quantlab.strategies import MovingAverageCrossoverStrategy


def main() -> None:
    data = SampleDataProvider(seed=11).get_bars(
        BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2020-01-01", end="2024-12-31")
    )
    runner = ExperimentRunner(config=BacktestConfig(initial_cash=100_000, commission_rate=0.001, slippage_bps=5))
    summary, _ = runner.run_grid(
        data,
        MovingAverageCrossoverStrategy,
        {"short_window": [10, 20, 30], "long_window": [60, 90, 120]},
        experiment_name="sample_ma_scan",
    )
    print(summary.head(10).to_string(index=False))


if __name__ == "__main__":
    main()

