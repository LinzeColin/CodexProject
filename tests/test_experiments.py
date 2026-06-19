import tempfile
import unittest

from quantlab.backtest import BacktestConfig
from quantlab.config import REPORT_ROOT_DIR
from quantlab.data.models import BarDataRequest
from quantlab.data.providers import SampleDataProvider
from quantlab.research import ExperimentRunner, analyze_parameter_stability, grid_parameters, split_train_test_by_time, walk_forward_windows
from quantlab.strategies import MovingAverageCrossoverStrategy


class ExperimentTests(unittest.TestCase):
    def test_grid_parameters(self):
        params = grid_parameters({"a": [1, 2], "b": [3, 4]})
        self.assertEqual(len(params), 4)
        self.assertEqual(params[0], {"a": 1, "b": 3})

    def test_parameter_scan_runs_and_saves(self):
        data = SampleDataProvider(seed=4).get_bars(
            BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2020-01-01", end="2021-12-31")
        )
        with tempfile.TemporaryDirectory() as tmp:
            runner = ExperimentRunner(output_dir=tmp, config=BacktestConfig(initial_cash=100_000))
            summary, results = runner.run_grid(
                data,
                MovingAverageCrossoverStrategy,
                {"short_window": [5, 10], "long_window": [30, 60]},
                experiment_name="test_scan",
            )
            self.assertEqual(len(summary), 4)
            self.assertEqual(len(results), 4)
            self.assertIn("sharpe", summary.columns)
            self.assertTrue((runner.output_dir / "test_scan" / "stability.json").exists())

    def test_parameter_scan_accepts_strategy_factory(self):
        data = SampleDataProvider(seed=41).get_bars(
            BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2020-01-01", end="2021-12-31")
        )

        def factory(**params):
            return MovingAverageCrossoverStrategy(**params)

        factory.strategy_id = "factory_ma"
        with tempfile.TemporaryDirectory() as tmp:
            runner = ExperimentRunner(output_dir=tmp, config=BacktestConfig(initial_cash=100_000))
            summary, results = runner.run_grid(
                data,
                factory,
                {"short_window": [5, 10], "long_window": [30]},
                experiment_name="factory_scan",
            )

            self.assertEqual(len(summary), 2)
            self.assertEqual(len(results), 2)
            self.assertEqual(set(summary["strategy_id"]), {"ma_crossover"})

    def test_train_test_validation_runs_and_saves(self):
        data = SampleDataProvider(seed=5).get_bars(
            BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2020-01-01", end="2022-12-31")
        )
        with tempfile.TemporaryDirectory() as tmp:
            runner = ExperimentRunner(output_dir=tmp, config=BacktestConfig(initial_cash=100_000))
            report = runner.run_train_test_validation(
                data,
                MovingAverageCrossoverStrategy,
                {"short_window": [5, 10], "long_window": [30, 60]},
                experiment_name="test_train_test",
            )

            self.assertTrue((runner.output_dir / "test_train_test" / "train_test_validation.json").exists())
            self.assertTrue((runner.output_dir / "test_train_test" / "train_summary.csv").exists())
            self.assertTrue((runner.output_dir / "test_train_test" / "test_summary.csv").exists())
            self.assertGreater(report.train_rows, 0)
            self.assertGreater(report.test_rows, 0)
            self.assertIn(report.validation_status, {"Pass", "Watch", "Failed", "Review"})

    def test_walk_forward_validation_runs_and_saves(self):
        data = SampleDataProvider(seed=7).get_bars(
            BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2020-01-01", end="2023-12-31")
        )
        with tempfile.TemporaryDirectory() as tmp:
            runner = ExperimentRunner(output_dir=tmp, config=BacktestConfig(initial_cash=100_000))
            report = runner.run_walk_forward_validation(
                data,
                MovingAverageCrossoverStrategy,
                {"short_window": [5, 10], "long_window": [30, 60]},
                experiment_name="test_walk_forward",
                train_window=180,
                test_window=60,
            )

            self.assertTrue((runner.output_dir / "test_walk_forward" / "walk_forward_validation.json").exists())
            self.assertTrue((runner.output_dir / "test_walk_forward" / "walk_forward_windows.csv").exists())
            self.assertGreater(report.window_count, 0)
            self.assertEqual(report.window_count, len(report.windows))
            self.assertIn(report.validation_status, {"Pass", "Watch", "Failed", "Review", "InsufficientData"})

    def test_default_experiment_dir_uses_codex_report(self):
        runner = ExperimentRunner(config=BacktestConfig(initial_cash=100_000))
        self.assertEqual(runner.output_dir.parents[1], REPORT_ROOT_DIR)

    def test_parameter_stability_detects_broad_good_region(self):
        import pandas as pd

        summary = pd.DataFrame(
            {
                "run_id": [f"run{i}" for i in range(9)],
                "param_short_window": [5, 5, 5, 10, 10, 10, 15, 15, 15],
                "param_long_window": [30, 60, 90, 30, 60, 90, 30, 60, 90],
                "sharpe": [0.9, 1.1, 0.95, 1.2, 1.3, 1.15, 0.85, 1.05, 0.9],
            }
        ).sort_values(["sharpe"], ascending=False)

        stability = analyze_parameter_stability(summary)

        self.assertEqual(stability.stability_status, "Stable")
        self.assertGreater(stability.neighbor_count, 0)
        self.assertGreater(stability.parameter_coverage, 0)

    def test_split_train_test_by_time_keeps_ordered_periods(self):
        data = SampleDataProvider(seed=6).get_bars(
            BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2020-01-01", end="2020-12-31")
        )
        train, test, split_datetime = split_train_test_by_time(data, split_ratio=0.7)
        self.assertGreater(len(train), 0)
        self.assertGreater(len(test), 0)
        self.assertLess(train["datetime"].max(), split_datetime)
        self.assertGreaterEqual(test["datetime"].min(), split_datetime)

    def test_walk_forward_windows_have_non_overlapping_train_test_periods(self):
        data = SampleDataProvider(seed=8).get_bars(
            BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2020-01-01", end="2021-12-31")
        )
        windows = walk_forward_windows(data, train_window=120, test_window=40)
        self.assertGreater(len(windows), 0)
        train, test, bounds = windows[0]
        self.assertLess(train["datetime"].max(), test["datetime"].min())
        self.assertLess(bounds["train_end"], bounds["test_start"])


if __name__ == "__main__":
    unittest.main()
