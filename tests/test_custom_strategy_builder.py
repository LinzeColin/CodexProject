import tempfile
import unittest
from pathlib import Path

from quantlab.approvals import StrategyApprovalRegistry
from quantlab.data.models import BarDataRequest
from quantlab.data.providers import SampleDataProvider
from quantlab.strategies import (
    CustomNoCodeStrategy,
    create_strategy_template,
    evaluate_strategy_code_quality,
    get_custom_strategy_spec,
    load_custom_strategy_spec_history,
    load_custom_strategy_specs,
    next_strategy_version,
    run_strategy_smoke_test,
    save_custom_strategy_spec,
    save_custom_strategy_spec_revision,
    write_custom_strategy_code_for_spec,
)


def _custom_spec(strategy_id: str = "custom_no_code_reversion") -> dict:
    return {
        "strategy_id": strategy_id,
        "version": "0.1.0",
        "display_name": "自定义无代码均值回归",
        "display_name_en": "Custom No Code Reversion",
        "logic_key": "mean_reversion",
        "indicator_keys": ["rsi", "bollinger", "atr_risk"],
        "settings": {
            "rsi": {"window": 14, "entry": 35, "exit": 55},
            "bollinger": {"window": 20, "std_multiplier": 1.5, "exit_z": 0.0},
            "atr_risk": {"window": 14, "stop_multiplier": 2.5},
        },
        "category": "均值回归 Mean Reversion",
        "return_source": "行为偏差 Behavioral Bias；执行优势 Execution Advantage",
        "return_source_en": "Behavioral Bias; Execution Advantage",
        "thesis": "短期过度偏离后可能回归。",
        "thesis_en": "Short-term dislocation may revert.",
        "failure": "单边趋势和流动性断裂可能失效。",
        "failure_en": "One-way trends and liquidity breaks may invalidate it.",
        "parameter_notes": "RSI 和布林带组合入场，ATR 控制风险。",
        "parameter_notes_en": "RSI and Bollinger entries with ATR risk control.",
    }


class CustomStrategyBuilderTests(unittest.TestCase):
    def test_custom_strategy_spec_persists_and_loads(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "CustomStrategySpecs.json"
            save_custom_strategy_spec(_custom_spec(), path=path)

            specs = load_custom_strategy_specs(path)
            spec = get_custom_strategy_spec("custom_no_code_reversion", path=path)

            self.assertEqual(len(specs), 1)
            self.assertEqual(spec.strategy_id, "custom_no_code_reversion")
            self.assertEqual(spec.indicator_keys, ("rsi", "bollinger", "atr_risk"))
            self.assertEqual(spec.settings["rsi"]["entry"], 35.0)

    def test_custom_no_code_strategy_generates_long_only_signals(self):
        data = SampleDataProvider(seed=33).get_bars(
            BarDataRequest(symbol="AAPL", market="US", interval="1d", start="2020-01-01", end="2020-12-31")
        )
        strategy = CustomNoCodeStrategy(_custom_spec())

        result = strategy.generate_signals(data)

        self.assertFalse(result.signals.empty)
        self.assertIn("target_weight", result.signals.columns)
        self.assertIn("rsi", result.signals.columns)
        self.assertIn("z_score", result.signals.columns)
        self.assertGreaterEqual(result.signals["target_weight"].min(), 0.0)
        self.assertLessEqual(result.signals["target_weight"].max(), 1.0)
        self.assertEqual(result.metadata["strategy_id"], "custom_no_code_reversion")
        self.assertIn("custom_strategy_spec", result.metadata)

    def test_template_with_custom_spec_writes_executable_no_code_strategy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = StrategyApprovalRegistry(path=root / "StrategyApprovals.json")
            artifact = create_strategy_template(
                strategy_id="custom_no_code_reversion",
                display_name="自定义无代码均值回归",
                display_name_en="Custom No Code Reversion",
                category="均值回归 Mean Reversion",
                return_source="行为偏差 Behavioral Bias",
                thesis="短期过度偏离后可能回归。",
                failure="单边趋势和流动性断裂可能失效。",
                parameter_notes="RSI 和布林带组合入场，ATR 控制风险。",
                return_source_en="Behavioral Bias",
                thesis_en="Short-term dislocation may revert.",
                failure_en="One-way trends and liquidity breaks may invalidate it.",
                parameter_notes_en="RSI and Bollinger entries with ATR risk control.",
                custom_spec={"logic_key": "mean_reversion", "indicator_keys": ["rsi", "bollinger"], "settings": _custom_spec()["settings"]},
                custom_spec_path=root / "CustomStrategySpecs.json",
                strategy_dir=root / "strategies",
                profile_dir=root / "profiles",
                approval_registry=registry,
            )

            quality = evaluate_strategy_code_quality(artifact.strategy_file)
            smoke = run_strategy_smoke_test(artifact.strategy_file)
            spec = get_custom_strategy_spec("custom_no_code_reversion", path=root / "CustomStrategySpecs.json")

            self.assertEqual(quality.status, "CodeReadyForReview")
            self.assertEqual(quality.findings, ())
            self.assertEqual(smoke.status, "SmokePass")
            self.assertEqual(spec.logic_key, "mean_reversion")

    def test_custom_strategy_spec_revision_bumps_version_and_keeps_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec_path = root / "CustomStrategySpecs.json"
            history_path = root / "CustomStrategySpecHistory.json"
            save_custom_strategy_spec(_custom_spec(), path=spec_path)
            previous = get_custom_strategy_spec("custom_no_code_reversion", path=spec_path)
            updated = previous.to_dict()
            updated["version"] = next_strategy_version(previous.version)
            updated["settings"]["rsi"]["entry"] = 25.0

            save_custom_strategy_spec_revision(
                previous,
                updated,
                "Tighten RSI entry threshold.",
                "May reduce trades and change drawdown profile.",
                path=spec_path,
                history_path=history_path,
            )
            loaded = get_custom_strategy_spec("custom_no_code_reversion", path=spec_path)
            history = load_custom_strategy_spec_history(history_path)
            strategy_file = write_custom_strategy_code_for_spec(loaded, strategy_dir=root / "strategies")
            quality = evaluate_strategy_code_quality(strategy_file)
            smoke = run_strategy_smoke_test(strategy_file)

            self.assertEqual(loaded.version, "0.1.1")
            self.assertEqual(loaded.settings["rsi"]["entry"], 25.0)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["previous_version"], "0.1.0")
            self.assertEqual(history[0]["version"], "0.1.1")
            self.assertIn('version = "0.1.1"', strategy_file.read_text(encoding="utf-8"))
            self.assertEqual(quality.status, "CodeReadyForReview")
            self.assertEqual(smoke.status, "SmokePass")

    def test_custom_strategy_specs_fail_closed_on_corrupt_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "CustomStrategySpecs.json"
            path.write_text("{bad json", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_custom_strategy_specs(path)
            with self.assertRaises(ValueError):
                save_custom_strategy_spec(_custom_spec(), path=path)
            self.assertEqual(path.read_text(encoding="utf-8"), "{bad json")


if __name__ == "__main__":
    unittest.main()
