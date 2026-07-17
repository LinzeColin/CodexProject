from __future__ import annotations

import unittest

from KMFA.tools import v015_s07_stage_review_contract as contract


class V015S07StageReviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = contract.public_verification()

    def test_all_sixteen_checks_pass(self) -> None:
        self.assertEqual(self.result["accounting"], {"total": 16, "passed": 16, "failed": 0})
        self.assertEqual([row["check_id"] for row in self.result["checks"]], list(contract.CHECK_IDS))

    def test_golden_scope_and_regression_reconcile_exactly(self) -> None:
        self.assertEqual(self.result["p1_private_project_count"], 8)
        self.assertEqual(self.result["p1_private_accepted_field_count"], 92)
        self.assertTrue(self.result["private_zero_difference"])
        self.assertEqual(self.result["private_regression_pass_count"], 8)
        self.assertEqual(self.result["private_regression_fail_count"], 0)

    def test_open_items_remain_explicitly_unresolved(self) -> None:
        self.assertEqual(self.result["private_queue_item_count"], 147)
        self.assertEqual(self.result["open_unconfirmed_item_count"], 128)
        self.assertEqual(self.result["private_conflict_candidate_count"], 6)
        self.assertEqual(self.result["private_conflict_auto_selected_count"], 0)

    def test_report_remains_unavailable(self) -> None:
        self.assertEqual(self.result["current_report_display_label_zh"], "暂不可使用")
        self.assertFalse(self.result["current_formal_report_release_allowed"])

    def test_review_does_not_cross_private_or_release_boundaries(self) -> None:
        self.assertEqual(self.result["raw_root_access_count"], 0)
        self.assertFalse(self.result["raw_business_content_read"])
        self.assertFalse(self.result["github_upload_performed"])
        self.assertFalse(self.result["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
