from __future__ import annotations

import unittest

from KMFA.tools import v015_s21_stage_review_contract as contract


class Stage21ReviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = contract.integrated_review()

    def test_all_cross_phase_bindings_pass(self) -> None:
        self.assertEqual(self.payload["integration_binding_count"], 44)
        self.assertEqual(self.payload["integration_binding_failed_count"], 0)
        self.assertTrue(self.payload["stage_acceptance_ready"])

    def test_fixture_covers_two_companies_and_three_versions(self) -> None:
        fixture = contract.end_to_end_fixture()
        self.assertEqual(len(fixture["reports"]), 3)
        self.assertEqual({row["company_id"] for row in fixture["reports"]}, {"demo-north", "demo-west"})
        self.assertEqual(len(fixture["exports"]), 3)

    def test_findings_are_real_and_closed(self) -> None:
        self.assertEqual(len(contract.REVIEW_FINDINGS), 3)
        self.assertTrue(all(row["status"] == "FIXED_VALIDATED" and not row["blocks_stage_acceptance"] for row in contract.REVIEW_FINDINGS))

    def test_review_does_not_advance_taskpack_counts_or_external_actions(self) -> None:
        self.assertEqual(self.payload["taskpack_phase_count_delta"], 0)
        self.assertEqual(self.payload["taskpack_task_count_delta"], 0)
        self.assertEqual((self.payload["raw_root_access_count"], self.payload["external_publication_count"], self.payload["github_upload_count"], self.payload["app_reinstall_count"]), (0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
