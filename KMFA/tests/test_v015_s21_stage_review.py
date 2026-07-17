from __future__ import annotations

import unittest

from KMFA.tools import v015_s21_stage_review_contract as contract


class Stage21ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = contract.end_to_end_fixture()

    def test_report_export_and_workflow_lineage_is_exact(self) -> None:
        by_version = {row["report_version_id"]: row for row in self.fixture["reports"]}
        for export in self.fixture["exports"]:
            report = by_version[export["report_version_id"]]
            self.assertEqual(export["source_binding_fingerprint"], report["source_binding_fingerprint"])
            self.assertEqual(export["formula_binding_fingerprint"], report["formula_binding_fingerprint"])
            self.assertEqual(export["cross_format_consistency"]["difference_integer"], 0)

    def test_published_case_has_five_auditable_events(self) -> None:
        case = self.fixture["north_case_v1"]
        self.assertEqual((case["state"], case["event_count"]), ("PUBLISHED_INTERNAL", 5))
        self.assertTrue(all(row.get("actor_user_id") and row.get("occurred_at") and row.get("comment_zh") for row in case["events"]))

    def test_revision_is_direct_explained_and_preserves_first_version(self) -> None:
        comparison = self.fixture["comparison"]
        self.assertTrue(comparison["direct_revision"] and comparison["publication_allowed"])
        self.assertGreaterEqual(comparison["source_difference_count"], 1)
        self.assertEqual(comparison["unexplained_difference_count"], 0)
        self.assertNotEqual(self.fixture["north_v1"]["report_version_id"], self.fixture["north_v2"]["report_version_id"])

    def test_workflow_cases_bind_selected_report_and_company(self) -> None:
        self.assertEqual(self.fixture["north_case_v2"]["report_version_id"], self.fixture["north_v2"]["report_version_id"])
        self.assertEqual(self.fixture["west_case"]["company_id"], "demo-west")
        self.assertTrue(all(row["public_share_link"] is None for row in self.fixture["cases"]))


if __name__ == "__main__":
    unittest.main()
