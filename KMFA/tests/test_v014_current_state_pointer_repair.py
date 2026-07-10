from __future__ import annotations

import unittest

from KMFA.tools.check_v014_current_state_pointer_repair import (
    EXPECTED_PHASE_ID,
    EXPECTED_VERSION,
    validate_recorded_current_state_pointer_repair,
)


class V014CurrentStatePointerRepairTest(unittest.TestCase):
    def test_recorded_pointer_repair_matches_owner_fill_application_gate(self) -> None:
        result = validate_recorded_current_state_pointer_repair()

        self.assertEqual(result["phase_id"], "V014_CURRENT_STATE_POINTER_REPAIR")
        self.assertEqual(result["canonical_phase_id"], EXPECTED_PHASE_ID)
        self.assertEqual(result["canonical_version"], EXPECTED_VERSION)
        self.assertEqual(result["go_no_go_decision"], "NO_GO")
        self.assertEqual(result["next_required_input"], "active_owner_or_authorized_delegate_fill_record")
        self.assertFalse(result["processed_value_materialization_replay_allowed"])
        self.assertFalse(result["raw_to_processed_value_comparison_allowed"])
        self.assertFalse(result["github_upload_allowed"])
        self.assertFalse(result["raw_inbox_access_performed_by_repair"])

    def test_recorded_repair_evidence_is_public_safe(self) -> None:
        saved = validate_recorded_current_state_pointer_repair()

        self.assertEqual(saved["canonical_phase_id"], EXPECTED_PHASE_ID)
        self.assertEqual(saved["canonical_version"], EXPECTED_VERSION)
        self.assertEqual(saved["repaired_public_state_file_count"], 5)
        self.assertTrue(saved["handoff_top_current"])
        self.assertTrue(saved["status_top_current"])
        self.assertTrue(saved["owner_status_top_current"])


if __name__ == "__main__":
    unittest.main()
