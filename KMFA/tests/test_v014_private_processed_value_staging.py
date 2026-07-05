from __future__ import annotations

import unittest

from KMFA.tools.v014_private_processed_value_staging import generate
from KMFA.tools.check_v014_private_processed_value_staging import (
    validate_v014_private_processed_value_staging,
)


class V014PrivateProcessedValueStagingTest(unittest.TestCase):
    def test_private_processed_target_slots_are_staged_without_value_claim(self) -> None:
        manifest = generate(generated_at="2026-07-05T23:59:59+10:00")
        validated = validate_v014_private_processed_value_staging(require_private_staging=True)

        self.assertEqual(validated["phase_id"], "V014_PRIVATE_PROCESSED_VALUE_STAGING")
        self.assertEqual(validated["status"], manifest["status"])
        self.assertTrue(validated["processed_staging_summary"]["processed_target_slots_staged"])
        self.assertGreater(validated["processed_staging_summary"]["processed_target_slot_count"], 0)
        self.assertEqual(validated["processed_staging_summary"]["private_processed_value_fingerprint_count"], 0)
        self.assertFalse(validated["processed_staging_summary"]["processed_value_materialization_complete"])
        self.assertFalse(validated["value_matching_readiness"]["raw_to_processed_value_comparison_performed"])
        self.assertFalse(validated["value_matching_readiness"]["business_value_consistency_verified"])
        self.assertEqual(validated["go_no_go"]["decision"], "NO_GO")

    def test_release_upload_raw_and_business_actions_remain_blocked(self) -> None:
        manifest = validate_v014_private_processed_value_staging(require_private_staging=True)
        go_no_go = manifest["go_no_go"]
        raw_boundary = manifest["raw_readonly_boundary"]

        self.assertFalse(raw_boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_phase"])
        self.assertFalse(go_no_go["lineage_full_check_complete"])
        self.assertFalse(go_no_go["formal_report_allowed"])
        self.assertFalse(go_no_go["github_upload_allowed"])
        self.assertFalse(go_no_go["app_reinstall_allowed"])
        self.assertFalse(go_no_go["business_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
