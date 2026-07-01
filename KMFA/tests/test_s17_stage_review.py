import unittest

from KMFA.tools.check_s17_stage_review import (
    DEFAULT_REVIEW_MANIFEST,
    validate_stage_review,
)


class S17StageReviewTests(unittest.TestCase):
    def test_stage17_review_manifest_matches_phase_evidence(self) -> None:
        counts = validate_stage_review(DEFAULT_REVIEW_MANIFEST)

        self.assertEqual(counts["role_count"], 4)
        self.assertEqual(counts["sensitive_policy_category_count"], 15)
        self.assertEqual(counts["audit_action_type_count"], 5)
        self.assertEqual(counts["notification_rule_count"], 3)
        self.assertEqual(counts["notification_event_count"], 3)
        self.assertEqual(counts["notification_dispatch_log_count"], 3)
        self.assertEqual(counts["operation_runbook_count"], 4)
        self.assertEqual(counts["knowledge_item_count"], 2)
        self.assertEqual(counts["drill_log_count"], 2)
        self.assertEqual(counts["full_report_email_count"], 0)
        self.assertEqual(counts["live_connector_count"], 0)
        self.assertEqual(counts["production_restore_count"], 0)
        self.assertEqual(counts["business_execution_count"], 0)
        self.assertEqual(counts["lineage_full_check_count"], 0)
        self.assertEqual(counts["github_upload_count"], 0)
        self.assertEqual(counts["full_kmfa_unit_tests"], 246)


if __name__ == "__main__":
    unittest.main()
