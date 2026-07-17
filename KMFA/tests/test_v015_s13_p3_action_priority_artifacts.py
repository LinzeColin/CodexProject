import json
import unittest

from KMFA.tools import build_v015_s13_p3_action_priority as builder
from KMFA.tools import v015_s13_p3_action_priority as action


class TestV015S13P3ActionPriorityArtifacts(unittest.TestCase):
    def test_dependency_is_exactly_the_accepted_s13_p2(self) -> None:
        value = builder.dependency()
        self.assertEqual(value["acceptance_status"], "PASSED")
        self.assertEqual(value["validation_receipt_count"], 20)
        self.assertTrue(value["s13_p3_entry_allowed"])
        self.assertFalse(value["s13_p3_started"])

    def test_expected_outputs_are_public_safe_and_deterministic(self) -> None:
        first = builder.expected_outputs()
        second = builder.expected_outputs()
        self.assertEqual(first, second)
        text = "\n".join(first.values())
        for forbidden in ("/" + "Users" + "/", "/Volumes/", "file://", "private://", "KMFA_MetaData"):
            self.assertNotIn(forbidden, text)

    def test_machine_contracts_match_kernel(self) -> None:
        outputs = builder.expected_outputs()
        ranking = json.loads(outputs[builder.RANKING_CONTRACT_PATH])
        focus = json.loads(outputs[builder.FOCUS_CONTRACT_PATH])
        review = json.loads(outputs[builder.REVIEW_CONTRACT_PATH])
        verification = json.loads(outputs[builder.VERIFICATION_PATH])
        self.assertEqual(ranking["factors"], action.ranking_contract())
        self.assertEqual(focus["domains"], list(action.ACTION_DOMAINS))
        self.assertEqual(review["outcome_states"], list(action.OUTCOME_STATES))
        self.assertEqual(verification["accounting"], {"total": 88, "passed": 88, "failed": 0})

    def test_manifest_matches_receipt_state_and_stops_before_review(self) -> None:
        final, _, _ = builder.final_binding(builder.receipts())
        manifest = json.loads(builder.expected_outputs()[builder.MANIFEST_PATH])
        self.assertEqual(manifest["phase_acceptance_status"], "PASSED" if final else "PENDING_FINAL_VALIDATION")
        self.assertEqual(manifest["overall_accepted_phase_count"], 37 if final else 36)
        self.assertEqual(manifest["stage_execution_percentage"], 100)
        self.assertTrue(manifest["action_priority_model_implemented"])
        self.assertTrue(manifest["synthetic_action_priority_computed"])
        self.assertFalse(manifest["real_business_action_priority_computed"])
        self.assertEqual(manifest["s13_stage_review_entry_allowed"], final)
        self.assertFalse(manifest["s13_stage_review_started"])
        self.assertEqual(manifest["automatic_execution_count"], 0)
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])

    def test_task_matrix_covers_exact_taskpack_tasks(self) -> None:
        final, _, _ = builder.final_binding(builder.receipts())
        matrix = json.loads(builder.expected_outputs()[builder.TASK_MATRIX_PATH])
        self.assertEqual([row["task_id"] for row in matrix["tasks"]], ["S13P3T01", "S13P3T02", "S13P3T03"])
        self.assertEqual(matrix["task_accepted_count"], 3 if final else 0)


if __name__ == "__main__":
    unittest.main()
