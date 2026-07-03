import importlib.util
import json
import unittest
from pathlib import Path


VALIDATOR_MODULE = "KMFA.tools.check_v014_s06_p2_difference_queue"


def validate_s06_p2() -> dict[str, object]:
    spec = importlib.util.find_spec(VALIDATOR_MODULE)
    if spec is None:
        raise AssertionError(f"{VALIDATOR_MODULE} must exist")
    from KMFA.tools.check_v014_s06_p2_difference_queue import validate_v014_s06_p2_difference_queue

    return validate_v014_s06_p2_difference_queue()


class V014S06P2DifferenceQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.result = validate_s06_p2()

    def test_pdf_excel_conflict_enters_manual_difference_queue(self) -> None:
        result = self.result

        self.assertEqual(result["phase_id"], "S06-P2")
        self.assertEqual(result["phase_scope"], "v014_s06_p2_difference_queue_only")
        self.assertTrue(result["s06_p1_dependency_validated"])
        self.assertEqual(result["queue_item_count"], 1)
        self.assertTrue(result["pdf_excel_conflict_detected"])
        self.assertEqual(result["source_types"], ["excel", "pdf"])
        self.assertEqual(result["difference_cents"], 1)
        self.assertEqual(result["queue_statuses"], ["queued_for_manual_review"])
        self.assertTrue(result["manual_review_required"])
        self.assertFalse(result["difference_closed"])

    def test_no_auto_correction_average_rounding_mask_or_auto_selection(self) -> None:
        result = self.result

        self.assertFalse(result["auto_correction_allowed"])
        self.assertFalse(result["averaging_allowed"])
        self.assertFalse(result["rounding_mask_allowed"])
        self.assertFalse(result["auto_selection_allowed"])
        self.assertIsNone(result["auto_selected_source_id"])
        self.assertIsNone(result["resolved_value_cents"])
        self.assertEqual(result["resolution_policy"], "manual_review_required")

    def test_unclosed_difference_blocks_report_grade_a(self) -> None:
        result = self.result

        self.assertFalse(result["report_grade_a_allowed"])
        self.assertEqual(result["maximum_report_grade"], "B")
        self.assertEqual(result["hard_block_reason"], "unresolved_critical_difference")
        self.assertEqual(len(result["blocking_queue_ids"]), 1)
        self.assertFalse(result["release_state"]["formal_report_allowed"])
        self.assertFalse(result["release_state"]["business_decision_basis_allowed"])

    def test_phase_boundaries_stay_public_safe_local_only_and_deferred(self) -> None:
        result = self.result

        self.assertFalse(result["raw_business_data_used"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_read_by_this_phase"])
        self.assertFalse(result["raw_data_boundary"]["raw_inbox_mutated_by_this_phase"])
        self.assertFalse(result["metadata_quality_written"])
        self.assertFalse(result["source_difference_queue_metadata_written"])
        self.assertFalse(result["s06_p3_started"])
        self.assertFalse(result["stage6_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertEqual(result["github_upload_status"], "not_uploaded_deferred_until_v014_stage1_18_complete")
        self.assertFalse(result["formal_report_performed"])
        self.assertFalse(result["business_execution_performed"])

    def test_recorded_queue_and_gate_match_recomputed_public_safe_outputs(self) -> None:
        result = self.result

        from KMFA.tools.cross_source_difference_queue import build_queue_from_fixture, evaluate_report_grade_gate

        fixture_path = Path(str(result["fixture_ref"]))
        queue_path = Path(str(result["queue_ref"]))
        gate_path = Path(str(result["gate_ref"]))
        recomputed_queue = build_queue_from_fixture(fixture_path)
        recomputed_gate = evaluate_report_grade_gate(recomputed_queue)
        recorded_queue = [json.loads(line) for line in queue_path.read_text(encoding="utf-8").splitlines() if line]
        recorded_gate = json.loads(gate_path.read_text(encoding="utf-8"))

        self.assertEqual(recorded_queue, recomputed_queue)
        self.assertEqual(recorded_gate, recomputed_gate)
        self.assertTrue(recorded_queue[0]["public_safe_fixture_only"])
        self.assertFalse(recorded_queue[0]["raw_business_data_used"])


if __name__ == "__main__":
    unittest.main()
