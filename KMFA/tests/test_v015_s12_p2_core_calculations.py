from __future__ import annotations

import copy
import unittest

from KMFA.tools import v015_s12_p2_core_calculations as kernel


class S12P2CoreCalculationTests(unittest.TestCase):
    def test_public_verification_is_complete(self) -> None:
        result = kernel.public_verification()
        self.assertEqual(result["accounting"], {"total": 48, "passed": 48, "failed": 0})
        self.assertEqual(result["failed_checks"], [])

    def test_three_margin_views_are_exact(self) -> None:
        result = kernel.calculate_margin_views(kernel._margin_fixture())
        self.assertEqual(
            {name: row["gross_profit_cents"] for name, row in result["views"].items()},
            {"contract": 30000, "settlement": 20000, "management": 15000},
        )
        self.assertEqual(
            {name: row["gross_margin_bps"] for name, row in result["views"].items()},
            {"contract": 2500, "settlement": 2000, "management": 1667},
        )

    def test_margin_basis_is_explicit(self) -> None:
        payload = kernel._margin_fixture()
        payload["contract"]["revenue_basis"] = "UNKNOWN"
        with self.assertRaisesRegex(kernel.CoreCalculationError, "MARGIN_BASIS_MISMATCH"):
            kernel.calculate_margin_views(payload)

    def test_zero_revenue_has_no_determinate_rate(self) -> None:
        payload = kernel._margin_fixture()
        payload["contract"]["revenue_cents"] = 0
        payload["contract"]["cost_cents"] = 0
        result = kernel.calculate_margin_views(payload)
        self.assertIsNone(result["views"]["contract"]["gross_margin_bps"])
        self.assertEqual(result["views"]["contract"]["rate_status"], kernel.INSUFFICIENT_DATA)

    def test_golden_baseline_accepts_zero_difference(self) -> None:
        result = kernel.calculate_margin_views(kernel._margin_fixture())
        comparison = kernel.assert_margin_golden(
            result,
            {
                "contract": {"gross_profit_cents": 30000},
                "settlement": {"gross_profit_cents": 20000},
                "management": {"gross_profit_cents": 15000},
            },
        )
        self.assertTrue(comparison["zero_difference_pass"])
        self.assertEqual(set(comparison["differences_cents"].values()), {0})

    def test_golden_baseline_rejects_one_cent(self) -> None:
        result = kernel.calculate_margin_views(kernel._margin_fixture())
        with self.assertRaisesRegex(kernel.CoreCalculationError, "GOLDEN_CENT_DIFFERENCE"):
            kernel.assert_margin_golden(
                result,
                {
                    "contract": {"gross_profit_cents": 29999},
                    "settlement": {"gross_profit_cents": 20000},
                    "management": {"gross_profit_cents": 15000},
                },
            )

    def test_cash_uses_only_confirmed_collection(self) -> None:
        result = kernel.calculate_cash_metrics(kernel._cash_fixture())
        self.assertEqual(result["cash_gross_profit_cents"], 20000)
        self.assertEqual(result["uncollected_amount_counted_as_cash_cents"], 0)
        self.assertEqual(result["excluded_from_cash_income"]["invoiced_not_collected_cents"], 40000)
        self.assertEqual(result["excluded_from_cash_income"]["ordinary_receivable_cents"], 30000)

    def test_cash_capital_occupation_is_exact(self) -> None:
        result = kernel.calculate_cash_metrics(kernel._cash_fixture())
        self.assertEqual(result["net_capital_position_cents"], 10000)
        self.assertEqual(result["capital_occupied_cents"], 10000)
        self.assertEqual(result["net_cash_surplus_cents"], 0)

    def test_cash_surplus_is_separate_from_occupation(self) -> None:
        payload = kernel._cash_fixture()
        payload["confirmed_collection_cents"] = 100000
        result = kernel.calculate_cash_metrics(payload)
        self.assertEqual(result["capital_occupied_cents"], 0)
        self.assertEqual(result["net_cash_surplus_cents"], 20000)

    def test_unresolved_account_degrades_and_blocks_decision(self) -> None:
        result = kernel.calculate_cash_metrics(kernel._cash_fixture(unresolved=True))
        self.assertEqual(result["calculation_status"], kernel.DEGRADED)
        self.assertFalse(result["business_decision_allowed"])

    def test_unresolved_entity_degrades_and_blocks_decision(self) -> None:
        payload = kernel._cash_fixture()
        payload["entity_status"] = kernel.UNRESOLVED
        result = kernel.calculate_cash_metrics(payload)
        self.assertEqual(result["calculation_status"], kernel.DEGRADED)
        self.assertFalse(result["business_decision_allowed"])

    def test_default_risk_policy_triggers_all_rules(self) -> None:
        result = kernel.assess_cost_risk(kernel._risk_fixture(), kernel.DEFAULT_RISK_POLICY)
        self.assertEqual(result["conclusion"], kernel.DETERMINATE_ALERT)
        self.assertEqual(
            result["triggered_rule_codes"],
            ["COST_CATEGORY_INCOMPLETE", "UNALLOCATED_COST_EXCESS", "ABNORMAL_COST_CHANGE", "LOW_MANAGEMENT_MARGIN"],
        )

    def test_risk_metrics_are_exact_basis_points(self) -> None:
        result = kernel.assess_cost_risk(kernel._risk_fixture(), kernel.DEFAULT_RISK_POLICY)
        self.assertEqual(
            result["metrics"],
            {
                "cost_completeness_bps": 9000,
                "unallocated_cost_ratio_bps": 600,
                "abnormal_cost_change_bps": 3000,
                "management_margin_bps": 800,
            },
        )

    def test_adjustable_thresholds_change_conclusion(self) -> None:
        policy = {
            **kernel.DEFAULT_RISK_POLICY,
            "policy_version": "TEST-RELAXED-1",
            "low_margin_threshold_bps": 500,
            "abnormal_cost_change_threshold_bps": 4000,
            "max_unallocated_cost_ratio_bps": 700,
            "minimum_cost_completeness_bps": 8500,
        }
        result = kernel.assess_cost_risk(kernel._risk_fixture(), policy)
        self.assertEqual(result["conclusion"], kernel.DETERMINATE_CLEAR)
        self.assertEqual(result["triggered_rule_codes"], [])

    def test_missing_comparison_never_claims_determinate_result(self) -> None:
        payload = kernel._risk_fixture()
        payload["comparison_period_cost_cents"] = None
        result = kernel.assess_cost_risk(payload, kernel.DEFAULT_RISK_POLICY)
        self.assertEqual(result["conclusion"], kernel.INSUFFICIENT_DATA)
        self.assertFalse(result["deterministic_conclusion_allowed"])
        self.assertEqual(result["triggered_rule_codes"], [])

    def test_missing_management_margin_never_claims_determinate_result(self) -> None:
        payload = kernel._risk_fixture()
        payload["management_margin_bps"] = None
        result = kernel.assess_cost_risk(payload, kernel.DEFAULT_RISK_POLICY)
        self.assertEqual(result["conclusion"], kernel.INSUFFICIENT_DATA)
        self.assertEqual(result["missing_reason_codes"], ["MANAGEMENT_MARGIN_MISSING"])

    def test_float_and_boolean_money_are_rejected(self) -> None:
        float_payload = kernel._cash_fixture()
        float_payload["confirmed_collection_cents"] = 1.5
        with self.assertRaisesRegex(kernel.CoreCalculationError, "FLOAT_NOT_ALLOWED"):
            kernel.calculate_cash_metrics(float_payload)
        bool_payload = kernel._cash_fixture()
        bool_payload["confirmed_collection_cents"] = True
        with self.assertRaisesRegex(kernel.CoreCalculationError, "INTEGER_REQUIRED"):
            kernel.calculate_cash_metrics(bool_payload)

    def test_private_locator_is_rejected(self) -> None:
        payload = kernel._cash_fixture()
        payload["basis_version"] = "file:///private/source"
        with self.assertRaisesRegex(kernel.CoreCalculationError, "NON_PUBLIC_VALUE"):
            kernel.calculate_cash_metrics(payload)

    def test_input_and_returned_results_are_isolated(self) -> None:
        payload = kernel._margin_fixture()
        before = copy.deepcopy(payload)
        result = kernel.calculate_margin_views(payload)
        result["views"]["contract"]["gross_profit_cents"] = 0
        self.assertEqual(payload, before)
        self.assertEqual(kernel.calculate_margin_views(payload)["views"]["contract"]["gross_profit_cents"], 30000)

    def test_results_are_deterministic(self) -> None:
        self.assertEqual(
            kernel.calculate_margin_views(kernel._margin_fixture()),
            kernel.calculate_margin_views(kernel._margin_fixture()),
        )
        self.assertEqual(
            kernel.calculate_cash_metrics(kernel._cash_fixture()),
            kernel.calculate_cash_metrics(kernel._cash_fixture()),
        )
        self.assertEqual(
            kernel.assess_cost_risk(kernel._risk_fixture(), kernel.DEFAULT_RISK_POLICY),
            kernel.assess_cost_risk(kernel._risk_fixture(), kernel.DEFAULT_RISK_POLICY),
        )


if __name__ == "__main__":
    unittest.main()
