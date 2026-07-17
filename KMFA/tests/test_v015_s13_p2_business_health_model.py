import copy
import json
import unittest

from KMFA.tools import v015_s13_p2_business_health_model as health


class TestV015S13P2BusinessHealthModel(unittest.TestCase):
    def test_six_dimensions_and_weights_are_exact(self) -> None:
        rows = health.health_dimensions()
        summary = health.validate_health_dimensions(rows)
        self.assertEqual(tuple(row["dimension_id"] for row in rows), health.HEALTH_DIMENSION_IDS)
        self.assertEqual(summary["dimension_count"], 6)
        self.assertEqual(summary["weight_total_bps"], 10_000)
        self.assertEqual((summary["score_min_bps"], summary["score_max_bps"]), (0, 10_000))

    def test_normal_health_result_is_bounded_and_explainable(self) -> None:
        result = health.evaluate_health(health.synthetic_observations(factor_shift_bps=300))
        self.assertTrue(result["score_displayable"])
        self.assertIn(result["health_state"], ("HEALTHY", "WATCH", "AT_RISK"))
        self.assertGreaterEqual(result["overall_score_bps"], 0)
        self.assertLessEqual(result["overall_score_bps"], 10_000)
        self.assertEqual(result["weight_total_bps"], 10_000)
        self.assertTrue(result["explanation_complete"])
        self.assertTrue(result["data_freshness_visible"])

    def test_hard_gate_hides_score_even_when_factors_are_high(self) -> None:
        rows = health.synthetic_observations(factor_shift_bps=2000)
        rows[-1]["hard_gate_passed"] = False
        rows[-1]["hard_gate_reason_zh"] = "数据完整度硬门禁失败。"
        result = health.evaluate_health(rows)
        self.assertEqual(result["health_state"], "BLOCKED_BY_HARD_GATE")
        self.assertIsNone(result["overall_score_bps"])
        self.assertFalse(result["score_displayable"])
        self.assertTrue(result["hard_gate_override_applied"])
        self.assertFalse(result["scoring_replaced_hard_gate"])

    def test_stale_or_missing_data_hides_score(self) -> None:
        stale = health.synthetic_observations()
        stale[0]["freshness_age_days"] = 30
        stale_result = health.evaluate_health(stale)
        self.assertEqual(stale_result["health_state"], "INSUFFICIENT_DATA")
        self.assertIsNone(stale_result["overall_score_bps"])
        self.assertEqual(stale_result["stale_dimension_ids"], ["HEALTH-CASH-SAFETY"])
        missing_result = health.evaluate_health(health.synthetic_observations()[:-1])
        self.assertEqual(missing_result["missing_dimension_ids"], ["HEALTH-DATA-COMPLETENESS"])
        self.assertIsNone(missing_result["overall_score_bps"])

    def test_unexplained_or_assumption_factor_is_rejected(self) -> None:
        unexplained = health.synthetic_observations()
        unexplained[0]["factors"] = []
        with self.assertRaisesRegex(health.HealthModelError, "UNEXPLAINED_SCORE_REJECTED"):
            health.evaluate_health(unexplained)
        assumption = health.synthetic_observations()
        assumption[0]["factors"][0]["record_kind"] = "ASSUMPTION"
        with self.assertRaisesRegex(health.HealthModelError, "ASSUMPTION_IN_ACTUAL_SCORE"):
            health.evaluate_health(assumption)

    def test_score_change_explains_every_changed_dimension(self) -> None:
        current = health.synthetic_observations(factor_shift_bps=300)
        prior = health.synthetic_observations(factor_shift_bps=0)
        comparison = health.compare_health(current, prior)
        self.assertGreater(comparison["overall_score_change_bps"], 0)
        self.assertEqual(comparison["unexplained_change_count"], 0)
        self.assertTrue(comparison["explanation_complete"])
        self.assertTrue(all(row["factor_changes"] for row in comparison["dimension_changes"]))

    def test_three_scenarios_do_not_mutate_facts(self) -> None:
        facts = {
            "recognized_revenue_cents": 120_000,
            "recognized_cost_cents": 80_000,
            "confirmed_collection_cents": 90_000,
            "cash_balance_cents": 50_000,
            "outstanding_receivable_cents": 30_000,
        }
        before = copy.deepcopy(facts)
        result = health.run_sensitivity_analysis(facts, health.synthetic_scenarios())
        self.assertEqual(facts, before)
        self.assertEqual(tuple(result["scenario_types"]), health.SCENARIO_TYPES)
        self.assertEqual(result["scenario_count"], 3)
        self.assertEqual(result["fact_layer_write_count"], 0)
        self.assertFalse(result["assumption_written_to_fact_layer"])
        self.assertTrue(result["fact_and_assumption_separated"])

    def test_scenario_outputs_are_exact_integer_projections(self) -> None:
        facts = {
            "recognized_revenue_cents": 120_000,
            "recognized_cost_cents": 80_000,
            "confirmed_collection_cents": 90_000,
            "cash_balance_cents": 50_000,
            "outstanding_receivable_cents": 30_000,
        }
        result = health.run_sensitivity_analysis(facts, health.synthetic_scenarios())
        self.assertEqual(result["results"][0]["projection"]["cash_delta_cents"], -20_000)
        self.assertEqual(result["results"][1]["projection"]["recognized_cost_cents"], 88_000)
        self.assertEqual(result["results"][2]["projection"]["recognized_revenue_cents"], 102_000)
        self.assertTrue(all(row["projection"]["record_kind"] == "SCENARIO_PROJECTION" for row in result["results"]))

    def test_float_and_boolean_are_rejected(self) -> None:
        facts = {
            "recognized_revenue_cents": 120_000,
            "recognized_cost_cents": json.loads("1.0"),
            "confirmed_collection_cents": 90_000,
            "cash_balance_cents": 50_000,
            "outstanding_receivable_cents": 30_000,
        }
        with self.assertRaisesRegex(health.HealthModelError, "INTEGER_REQUIRED"):
            health.run_sensitivity_analysis(facts, health.synthetic_scenarios())
        rows = health.synthetic_observations()
        rows[0]["factors"][0]["effect_bps"] = True
        with self.assertRaisesRegex(health.HealthModelError, "INTEGER_REQUIRED"):
            health.evaluate_health(rows)

    def test_private_material_is_rejected(self) -> None:
        rows = health.health_dimensions()
        rows[0]["limitations_zh"] = "/Users/private/value"
        with self.assertRaisesRegex(health.HealthModelError, "PRIVATE_VALUE_REJECTED"):
            health.validate_health_dimensions(rows)

    def test_public_verification_is_exact_and_deterministic(self) -> None:
        first = health.public_verification()
        second = health.public_verification()
        self.assertEqual(first, second)
        self.assertEqual(first["accounting"], {"total": 88, "passed": 88, "failed": 0})
        self.assertEqual(first["failed_checks"], [])
        self.assertFalse(first["action_priority_computed"])
        self.assertFalse(first["business_execution_performed"])


if __name__ == "__main__":
    unittest.main()
