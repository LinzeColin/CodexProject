from __future__ import annotations

import unittest

from KMFA.tools import v015_s06_stage_review_contract as contract


class V015S06StageReviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = contract.public_verification()

    def test_all_twelve_checks_pass(self) -> None:
        self.assertEqual(self.result["accounting"], {"total": 12, "passed": 12, "failed": 0})
        self.assertEqual([row["check_id"] for row in self.result["checks"]], list(contract.CHECK_IDS))

    def test_golden_fixture_reconciles_exactly(self) -> None:
        self.assertEqual(self.result["golden_fixture_project_count"], 8)
        self.assertEqual(self.result["golden_fixture_accepted_field_count"], 92)
        self.assertEqual(self.result["golden_fixture_money_difference_cents"], 0)

    def test_open_items_remain_explicitly_unresolved(self) -> None:
        self.assertEqual(self.result["open_item_count"], 147)
        self.assertEqual(
            self.result["open_item_status_counts"],
            {"OPEN": 128, "ROUTED_DERIVATION": 6, "ROUTED_EXCLUSION": 13},
        )
        self.assertFalse(self.result["open_items_may_be_treated_as_resolved"])
        self.assertFalse(self.result["tax_normalization_allowed"])

    def test_scenario_acceptance_does_not_overclaim_empirical_coverage(self) -> None:
        self.assertEqual(self.result["required_scenario_count"], 5)
        self.assertEqual(self.result["observed_scenario_count"], 4)
        self.assertEqual(self.result["registered_future_sample_count"], 1)
        self.assertFalse(self.result["empirical_coverage_complete"])
        self.assertTrue(self.result["registered_gap_satisfies_stop_condition"])
        self.assertFalse(self.result["downstream_cross_period_claim_allowed"])

    def test_review_does_not_cross_private_or_release_boundaries(self) -> None:
        self.assertEqual(self.result["raw_root_access_count"], 0)
        self.assertFalse(self.result["raw_business_content_read"])
        self.assertFalse(self.result["github_upload_performed"])
        self.assertFalse(self.result["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
