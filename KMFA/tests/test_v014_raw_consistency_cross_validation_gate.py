import unittest

from KMFA.tools.check_v014_raw_consistency_cross_validation_gate import (
    validate_v014_raw_consistency_cross_validation_gate,
)
from KMFA.tools.v014_raw_consistency_cross_validation_gate import (
    ACCEPTANCE_ID,
    PHASE_ID,
    TASK_ID,
    generate,
)


class V014RawConsistencyCrossValidationGateTests(unittest.TestCase):
    def test_generate_preview_keeps_release_gates_blocked(self) -> None:
        manifest = generate(generated_at="2026-07-05T23:55:00+10:00", write=False)

        self.assertEqual(manifest["phase_id"], PHASE_ID)
        self.assertEqual(manifest["task_id"], TASK_ID)
        self.assertEqual(manifest["acceptance_ids"], [ACCEPTANCE_ID])

        raw = manifest["raw_consistency_summary"]
        self.assertTrue(raw["authoritative_raw_baseline_locked"])
        self.assertTrue(raw["source_container_consistency_verified"])
        self.assertTrue(raw["cross_run_private_hash_profile_matches_prior_diagnostic"])
        self.assertFalse(raw["business_value_consistency_verified"])
        self.assertFalse(raw["public_member_hash_backfill_allowed"])

        go_no_go = manifest["go_no_go"]
        self.assertEqual(go_no_go["decision"], "NO_GO")
        self.assertTrue(go_no_go["authoritative_raw_baseline_locked"])
        self.assertFalse(go_no_go["business_value_consistency_verified"])
        self.assertFalse(go_no_go["github_upload_allowed"])
        self.assertFalse(go_no_go["app_reinstall_allowed"])
        self.assertFalse(go_no_go["formal_report_allowed"])
        self.assertFalse(go_no_go["business_execution_allowed"])

    def test_validate_committed_gate_with_private_diagnostic(self) -> None:
        validated = validate_v014_raw_consistency_cross_validation_gate(require_private_diagnostic=True)

        self.assertEqual(validated["phase_id"], PHASE_ID)
        self.assertEqual(validated["go_no_go"]["decision"], "NO_GO")
        self.assertTrue(validated["raw_consistency_summary"]["authoritative_raw_baseline_locked"])
        self.assertFalse(validated["raw_consistency_summary"]["business_value_consistency_verified"])
        self.assertFalse(validated["github_upload_performed"])


if __name__ == "__main__":
    unittest.main()
