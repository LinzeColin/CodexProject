import unittest

from quantlab.risk import evaluate_research_risk_gates


class RiskGateTests(unittest.TestCase):
    def test_clean_research_candidate_can_continue(self):
        result = evaluate_research_risk_gates(
            metrics={"total_return": 0.2, "max_drawdown": -0.08, "cost_total": 100, "ending_equity": 120000},
            stability={"stability_status": "Stable"},
            train_test={"validation_status": "Pass"},
            walk_forward={"validation_status": "Pass"},
            data_quality_status="Pass",
        )
        self.assertEqual(result.status, "ContinueResearch")
        self.assertEqual(result.score, 0)

    def test_walk_forward_failure_deactivates_candidate(self):
        result = evaluate_research_risk_gates(
            metrics={"total_return": 0.2, "max_drawdown": -0.08, "cost_total": 100, "ending_equity": 120000},
            stability={"stability_status": "Stable"},
            train_test={"validation_status": "Pass"},
            walk_forward={"validation_status": "Failed"},
            data_quality_status="Pass",
        )
        self.assertEqual(result.status, "DoNotUse")
        self.assertTrue(any("Walk-forward" in reason for reason in result.reasons))

    def test_large_drawdown_and_bad_data_deactivates_candidate(self):
        result = evaluate_research_risk_gates(
            metrics={"total_return": -0.1, "max_drawdown": -0.35, "cost_total": 100, "ending_equity": 90000},
            stability={"stability_status": "Fragile"},
            train_test={"validation_status": "Watch"},
            walk_forward={"validation_status": "Watch"},
            data_quality_status="Review",
        )
        self.assertEqual(result.status, "DoNotUse")
        self.assertGreaterEqual(result.score, 6)

    def test_missing_critical_evidence_requires_more_evidence(self):
        result = evaluate_research_risk_gates(
            metrics={"total_return": 0.2, "max_drawdown": -0.08, "cost_total": 100, "ending_equity": 120000},
        )

        self.assertEqual(result.status, "NeedsMoreEvidence")
        self.assertIn("数据质量检查", result.missing_evidence)


if __name__ == "__main__":
    unittest.main()
