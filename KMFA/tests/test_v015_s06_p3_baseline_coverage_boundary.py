from __future__ import annotations

import json
import unittest

from KMFA.tools import v015_s06_p3_baseline_coverage_boundary as kernel


class S06P3BaselineCoverageBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        kernel.build_private_outputs()
        cls.fixture, cls.queue, cls.coverage = kernel.validate_private_outputs()
        cls.public = kernel.public_projection(cls.fixture, cls.queue, cls.coverage)

    def test_fixture_is_exact_immutable_golden_projection(self) -> None:
        self.assertEqual(self.fixture["fixture_version"], "S06P3-FIXTURE-0001")
        self.assertEqual(self.fixture["project_count"], 8)
        self.assertEqual(self.fixture["accepted_field_count"], 92)
        self.assertEqual(self.fixture["money_difference_cents"], 0)
        self.assertTrue(self.fixture["immutable"])
        self.assertFalse(self.fixture["overwrite_allowed"])
        self.assertEqual(len(self.fixture["fixture_digest"]), 64)

    def test_every_unconfirmed_item_has_impact_and_resolution_without_guessing(self) -> None:
        self.assertEqual(self.queue["item_count"], 147)
        self.assertEqual(
            self.queue["category_counts"],
            {"AMBIGUOUS": 46, "CONFLICT": 6, "MISSING": 82, "NOT_APPLICABLE": 13},
        )
        self.assertEqual(
            self.queue["status_counts"],
            {"OPEN": 128, "ROUTED_DERIVATION": 6, "ROUTED_EXCLUSION": 13},
        )
        self.assertEqual(self.queue["impact_present_count"], 147)
        self.assertEqual(self.queue["resolution_path_present_count"], 147)
        self.assertTrue(all(not row["guessing_used"] for row in self.queue["items"]))

    def test_sample_matrix_registers_only_real_gap(self) -> None:
        self.assertEqual(self.coverage["required_scenario_count"], 5)
        self.assertEqual(self.coverage["covered_scenario_count"], 4)
        self.assertEqual(self.coverage["missing_scenario_count"], 1)
        missing = [row for row in self.coverage["criteria"] if row["status"] == "MISSING"]
        self.assertEqual(missing, [{"scenario": "CROSS_PERIOD", "status": "MISSING", "evidence_count": 0}])
        self.assertEqual(self.coverage["future_sample_count"], 1)
        self.assertTrue(self.coverage["sample_expansion_required"])
        self.assertEqual(self.public["coverage_disposition_count"], 5)
        self.assertFalse(self.public["empirical_coverage_complete"])
        self.assertTrue(self.public["registered_gap_satisfies_stop_condition"])
        self.assertFalse(self.public["downstream_cross_period_claim_allowed"])
        self.assertFalse(self.public["tax_normalization_allowed"])
        self.assertFalse(self.public["open_items_may_be_treated_as_resolved"])

    def test_public_projection_is_aggregate_only(self) -> None:
        rendered = json.dumps(self.public, ensure_ascii=False)
        self.assertEqual(self.public["public_project_identity_count"], 0)
        self.assertEqual(self.public["public_money_value_count"], 0)
        self.assertEqual(self.public["public_source_locator_count"], 0)
        self.assertEqual(self.public["public_private_fixture_hash_count"], 0)
        for forbidden in ("project_summaries", "source_golden_record_hash", "fixture_digest", "source_locator"):
            self.assertNotIn(f'"{forbidden}"', rendered)


if __name__ == "__main__":
    unittest.main()
