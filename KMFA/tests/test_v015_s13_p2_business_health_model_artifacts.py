import json
import unittest

from KMFA.tools import build_v015_s13_p2_business_health_model as builder
from KMFA.tools import v015_s13_p2_business_health_model as health


class TestV015S13P2BusinessHealthModelArtifacts(unittest.TestCase):
    def test_dependency_is_exactly_the_accepted_s13_p1(self) -> None:
        value = builder.dependency()
        self.assertEqual(value["acceptance_status"], "PASSED")
        self.assertEqual(value["validation_receipt_count"], 20)
        self.assertTrue(value["s13_p2_entry_allowed"])
        self.assertFalse(value["s13_p2_started"])

    def test_expected_outputs_are_public_safe_and_deterministic(self) -> None:
        first = builder.expected_outputs()
        second = builder.expected_outputs()
        self.assertEqual(first, second)
        text = "\n".join(first.values())
        for forbidden in ("/" + "Users" + "/", "/Volumes/", "file://", "private://", "KMFA_MetaData"):
            self.assertNotIn(forbidden, text)

    def test_machine_contracts_match_kernel(self) -> None:
        outputs = builder.expected_outputs()
        dimensions = json.loads(outputs[builder.DIMENSION_REGISTRY_PATH])
        scoring = json.loads(outputs[builder.SCORING_CONTRACT_PATH])
        scenario = json.loads(outputs[builder.SCENARIO_CONTRACT_PATH])
        verification = json.loads(outputs[builder.VERIFICATION_PATH])
        self.assertEqual(dimensions["dimensions"], health.health_dimensions())
        self.assertEqual(scoring["health_states"], list(health.HEALTH_STATES))
        self.assertEqual(scenario["scenario_types"], list(health.SCENARIO_TYPES))
        self.assertEqual(verification["accounting"], {"total": 88, "passed": 88, "failed": 0})

    def test_manifest_matches_receipt_state_and_closes_unopened_work(self) -> None:
        final, _, _ = builder.final_binding(builder.receipts())
        manifest = json.loads(builder.expected_outputs()[builder.MANIFEST_PATH])
        self.assertEqual(manifest["phase_acceptance_status"], "PASSED" if final else "PENDING_FINAL_VALIDATION")
        self.assertEqual(manifest["overall_accepted_phase_count"], 36 if final else 35)
        self.assertEqual(manifest["stage_execution_percentage"], 67)
        self.assertTrue(manifest["health_model_implemented"])
        self.assertTrue(manifest["synthetic_health_score_computed"])
        self.assertFalse(manifest["real_business_health_score_computed"])
        self.assertEqual(manifest["s13_p3_entry_allowed"], final)
        self.assertFalse(manifest["s13_p3_started"])
        self.assertFalse(manifest["action_priority_computed"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])

    def test_task_matrix_covers_exact_taskpack_tasks(self) -> None:
        final, _, _ = builder.final_binding(builder.receipts())
        matrix = json.loads(builder.expected_outputs()[builder.TASK_MATRIX_PATH])
        self.assertEqual([row["task_id"] for row in matrix["tasks"]], ["S13P2T01", "S13P2T02", "S13P2T03"])
        self.assertEqual(matrix["task_accepted_count"], 3 if final else 0)


if __name__ == "__main__":
    unittest.main()
