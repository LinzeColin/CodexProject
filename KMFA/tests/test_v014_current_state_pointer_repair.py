from __future__ import annotations

import json
import unittest

from KMFA.tools.check_v014_current_state_pointer_repair import (
    EVIDENCE_MANIFEST_PATH,
    EXPECTED_PHASE_ID,
    EXPECTED_VERSION,
    validate_current_state_pointer_repair,
    write_evidence,
)


class V014CurrentStatePointerRepairTest(unittest.TestCase):
    def test_current_state_pointers_match_latest_owner_fill_application_gate(self) -> None:
        result = validate_current_state_pointer_repair()

        self.assertEqual(result["phase_id"], "V014_CURRENT_STATE_POINTER_REPAIR")
        self.assertEqual(result["canonical_phase_id"], EXPECTED_PHASE_ID)
        self.assertEqual(result["canonical_version"], EXPECTED_VERSION)
        self.assertEqual(result["go_no_go_decision"], "NO_GO")
        self.assertEqual(result["next_required_input"], "active_owner_or_authorized_delegate_fill_record")
        self.assertFalse(result["processed_value_materialization_replay_allowed"])
        self.assertFalse(result["raw_to_processed_value_comparison_allowed"])
        self.assertFalse(result["github_upload_allowed"])
        self.assertFalse(result["raw_inbox_access_performed_by_repair"])

    def test_repair_writes_public_safe_evidence(self) -> None:
        evidence = write_evidence()
        saved = json.loads(EVIDENCE_MANIFEST_PATH.read_text(encoding="utf-8"))

        self.assertEqual(saved, evidence)
        self.assertEqual(saved["canonical_phase_id"], EXPECTED_PHASE_ID)
        self.assertEqual(saved["canonical_version"], EXPECTED_VERSION)
        self.assertEqual(saved["repaired_public_state_file_count"], 5)
        self.assertTrue(saved["handoff_top_current"])
        self.assertTrue(saved["status_top_current"])
        self.assertTrue(saved["owner_status_top_current"])


if __name__ == "__main__":
    unittest.main()
