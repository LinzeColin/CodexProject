import unittest

import pandas as pd

from quantlab.risk import evaluate_decision_quality, evaluate_research_risk_gates


class DecisionQualityTests(unittest.TestCase):
    def test_complete_evidence_can_continue_research(self):
        metrics = {"total_return": 0.22, "max_drawdown": -0.08, "cost_total": 120, "ending_equity": 122000}
        metadata = {
            "strategy": {"strategy_id": "ma_crossover"},
            "backtest": {"initial_cash": 100000, "allow_short": False, "slippage_bps": 5, "market_impact_bps": 2},
        }
        trades = pd.DataFrame(
            [
                {"side": "BUY", "notional": 30000},
                {"side": "SELL", "notional": -12000},
            ]
        )
        positions = pd.DataFrame([{"position_value": 40000, "equity": 122000}])
        risk_gate = evaluate_research_risk_gates(
            metrics=metrics,
            stability={"stability_status": "Stable"},
            train_test={"validation_status": "Pass"},
            walk_forward={"validation_status": "Pass"},
            data_quality_status="Pass",
        )

        result = evaluate_decision_quality(
            metrics=metrics,
            metadata=metadata,
            trades=trades,
            positions=positions,
            risk_gate=risk_gate,
            data_quality_status="Pass",
            cross_validation_status="Pass",
            stability={"stability_status": "Stable"},
            train_test={"validation_status": "Pass"},
            walk_forward={"validation_status": "Pass"},
        )

        self.assertEqual(result.status, "ContinueResearch")
        self.assertGreaterEqual(result.score, 80)
        self.assertEqual(result.simulated_exposure["simulated_exposure_increase_count"], 1)
        self.assertEqual(result.simulated_exposure["simulated_exposure_reduction_count"], 1)

    def test_missing_cross_validation_requires_more_evidence(self):
        metrics = {"total_return": 0.22, "max_drawdown": -0.08, "cost_total": 120, "ending_equity": 122000}
        metadata = {
            "strategy": {"strategy_id": "ma_crossover"},
            "backtest": {"initial_cash": 100000, "allow_short": False, "slippage_bps": 5, "market_impact_bps": 2},
        }
        risk_gate = evaluate_research_risk_gates(
            metrics=metrics,
            stability={"stability_status": "Stable"},
            train_test={"validation_status": "Pass"},
            walk_forward={"validation_status": "Pass"},
            data_quality_status="Pass",
        )

        result = evaluate_decision_quality(
            metrics=metrics,
            metadata=metadata,
            risk_gate=risk_gate,
            data_quality_status="Pass",
            stability={"stability_status": "Stable"},
            train_test={"validation_status": "Pass"},
            walk_forward={"validation_status": "Pass"},
        )

        self.assertEqual(result.status, "NeedsMoreEvidence")
        self.assertIn("多源交叉校验", result.missing_evidence)


if __name__ == "__main__":
    unittest.main()
