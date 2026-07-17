from __future__ import annotations

import copy
import unittest

from KMFA.tools import v015_s12_stage_review_contract as review


class V015S12StageReviewContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.result = review.build_integrated_review()

    def test_all_sixty_eight_cross_phase_checks_pass(self) -> None:
        verification = review.public_verification()
        self.assertEqual(verification["accounting"], {"total": 68, "passed": 68, "failed": 0})
        self.assertEqual(verification["failed_checks"], [])

    def test_supported_change_projects_to_fact_and_margin_layers(self) -> None:
        change = self.result["change_settlement_result"]
        facts = self.result["fact_projection"]
        contract_view = self.result["calculation_projection"]["margin_results"]["views"]["contract"]
        self.assertEqual(change["confirmed_change_amount_cents"], 20000)
        self.assertEqual(change["unconfirmed_change_amount_cents"], 15000)
        self.assertEqual(facts["supported_change_income_cents"], 20000)
        self.assertEqual(facts["unconfirmed_change_excluded_cents"], 15000)
        self.assertEqual(facts["unsupported_change_recognized_cents"], 0)
        self.assertEqual(contract_view["revenue_cents"], 120000)

    def test_cost_projection_conserves_and_excludes_unsafe_candidates(self) -> None:
        external = self.result["external_cost_result"]
        facts = self.result["fact_projection"]
        self.assertEqual(external["recognized_project_cost_cents"], 42000)
        self.assertEqual(facts["target_cost_input_cents"], 47000)
        self.assertEqual(facts["allocated_project_cost_cents"], 42000)
        self.assertEqual(facts["unallocated_project_cost_cents"], 5000)
        self.assertEqual(facts["cost_conservation_delta_cents"], 0)
        self.assertEqual(facts["duplicate_excluded_amount_cents"], 25000)
        self.assertEqual(facts["cross_project_excluded_amount_cents"], 7000)
        self.assertEqual(facts["excluded_candidate_leak_count"], 0)

    def test_p2_results_are_derived_from_p1_and_p3(self) -> None:
        calculation = self.result["calculation_projection"]
        margins = calculation["margin_results"]["views"]
        cash = calculation["cash_results"]
        risk = calculation["risk_results"]
        self.assertEqual(
            [margins[name]["gross_profit_cents"] for name in ("contract", "settlement", "management")],
            [73000, 73000, 68000],
        )
        self.assertEqual(cash["cash_gross_profit_cents"], 45000)
        self.assertEqual(cash["uncollected_amount_counted_as_cash_cents"], 0)
        self.assertEqual(risk["metrics"]["unallocated_cost_ratio_bps"], 1064)
        self.assertEqual(
            risk["triggered_rule_codes"],
            ["COST_CATEGORY_INCOMPLETE", "UNALLOCATED_COST_EXCESS"],
        )

    def test_both_explanation_layers_are_consistent(self) -> None:
        self.assertTrue(self.result["p3_explanation_consistency"]["consistency_pass"])
        self.assertEqual(self.result["p3_explanation_consistency"]["mismatch_count"], 0)
        self.assertTrue(self.result["review_explanation_consistency"]["consistency_pass"])
        self.assertEqual(self.result["review_explanation_consistency"]["mismatch_count"], 0)
        self.assertEqual(self.result["review_explanations"]["explanation_count"], 6)

    def test_tampered_cross_phase_result_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.result)
        tampered["calculation_projection"]["margin_results"]["views"]["management"]["gross_profit_cents"] += 1
        tampered["review_fingerprint"] = review._fingerprint({
            key: copy.deepcopy(value)
            for key, value in tampered.items()
            if key != "review_fingerprint"
        })
        with self.assertRaisesRegex(review.StageReviewError, "REVIEW_CROSS_PHASE_MISMATCH"):
            review.validate_integrated_review(tampered)

    def test_scope_drift_is_rejected(self) -> None:
        source = review.public_review_input()
        source["external_cost_chain"]["project_ref"] = "PROJECT-PUBLIC-002"
        with self.assertRaisesRegex(review.StageReviewError, "REVIEW_SCOPE_MISMATCH"):
            review.build_integrated_review(source)

    def test_review_is_deterministic_and_public_only(self) -> None:
        self.assertEqual(self.result, review.build_integrated_review())
        self.assertEqual(self.result["raw_root_access_count"], 0)
        self.assertEqual(self.result["live_source_read_count"], 0)
        self.assertFalse(self.result["real_business_calculation_performed"])
        self.assertFalse(self.result["github_upload_performed"])
        self.assertFalse(self.result["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
