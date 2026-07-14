import json
import unittest

from KMFA.tools.check_v013_s06_p2_difference_queue_replay import (
    validate_v013_s06_p2_difference_queue_replay,
)
from KMFA.tools.cross_source_difference_queue import build_queue_from_fixture, evaluate_report_grade_gate
from KMFA.tools.v013_s06_p2_difference_queue_replay import FIXTURE_PATH, GATE_PATH, QUEUE_PATH


class V013S06P2DifferenceQueueReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validation_result = validate_v013_s06_p2_difference_queue_replay()

    def test_replay_validator_locks_difference_queue_and_report_grade_gate(self) -> None:
        result = self.validation_result

        self.assertEqual(result["phase_id"], "S06-P2")
        self.assertTrue(result["s06_p1_dependency_validated"])
        self.assertEqual(result["queue_item_count"], 1)
        self.assertTrue(result["pdf_excel_conflict_detected"])
        self.assertEqual(result["difference_cents"], 1)
        self.assertFalse(result["auto_correction_allowed"])
        self.assertFalse(result["averaging_allowed"])
        self.assertFalse(result["rounding_mask_allowed"])
        self.assertFalse(result["auto_selection_allowed"])
        self.assertFalse(result["report_grade_a_allowed"])
        self.assertEqual(result["maximum_report_grade"], "B")
        self.assertEqual(result["hard_block_reason"], "unresolved_critical_difference")

    def test_recomputed_queue_and_gate_match_public_safe_evidence(self) -> None:
        recomputed_queue = build_queue_from_fixture(FIXTURE_PATH)
        recorded_queue = [
            json.loads(line)
            for line in QUEUE_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        recorded_gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
        recomputed_gate = evaluate_report_grade_gate(recomputed_queue)

        self.assertEqual(recorded_queue, recomputed_queue)
        self.assertEqual(recorded_gate, recomputed_gate)
        self.assertEqual({ref["source_type"] for ref in recorded_queue[0]["source_refs"]}, {"pdf", "excel"})

    def test_phase_boundaries_remain_local_only_and_no_go(self) -> None:
        result = self.validation_result

        self.assertFalse(result["metadata_quality_written"])
        self.assertFalse(result["source_difference_queue_metadata_written"])
        self.assertFalse(result["stage6_review_performed"])
        self.assertFalse(result["s06_p3_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["business_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
