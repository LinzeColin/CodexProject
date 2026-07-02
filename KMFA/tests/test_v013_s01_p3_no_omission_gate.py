import unittest

from KMFA.tools.check_v013_s01_p3_no_omission_gate import validate_s01_p3_no_omission_gate


class TestV013S01P3NoOmissionGate(unittest.TestCase):
    def test_no_omission_gate_replays_traceability_without_release_scope(self) -> None:
        result = validate_s01_p3_no_omission_gate()

        self.assertEqual(result["stage_phase"], "S01-P3")
        self.assertEqual(result["phase_scope"], "no_omission_gate_replay_only")
        self.assertEqual(result["no_omission"]["requirements"], 20)
        self.assertEqual(result["no_omission"]["p0"], 9)
        self.assertEqual(result["no_omission"]["p1"], 8)
        self.assertEqual(result["no_omission"]["stage_status_records"], 549)
        self.assertGreaterEqual(result["no_omission"]["task_records"], 162)
        self.assertFalse(result["stage_review_scope_included"])
        self.assertFalse(result["github_upload_this_phase"])
        self.assertFalse(result["delivery_allowed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["business_execution_allowed"])
        self.assertEqual(result["next_required_step"], "Stage 1 review; do not upload GitHub until review findings are fixed.")


if __name__ == "__main__":
    unittest.main()
