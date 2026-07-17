import json
import unittest

from KMFA.tools import build_v015_s13_p1_indicator_registry as builder
from KMFA.tools import v015_s13_p1_indicator_registry as kernel


class TestV015S13P1IndicatorRegistryArtifacts(unittest.TestCase):
    def test_dependency_is_exactly_the_accepted_s12_review(self) -> None:
        value = builder.dependency()
        self.assertEqual(value["acceptance_status"], "PASSED")
        self.assertEqual(value["validation_receipt_count"], 24)
        self.assertTrue(value["s13_p1_entry_allowed"])
        self.assertFalse(value["s13_p1_started"])

    def test_expected_outputs_are_public_safe_and_deterministic(self) -> None:
        first = builder.expected_outputs()
        second = builder.expected_outputs()
        self.assertEqual(first, second)
        self.assertEqual(set(first), set(second))
        text = "\n".join(first.values())
        for forbidden in ("/" + "Users" + "/", "/Volumes/", "file://", "private://", "KMFA_MetaData"):
            self.assertNotIn(forbidden, text)

    def test_machine_contracts_match_kernel(self) -> None:
        outputs = builder.expected_outputs()
        indicator = json.loads(outputs[builder.INDICATOR_REGISTRY_PATH])
        parameters = json.loads(outputs[builder.PARAMETER_VERSIONS_PATH])
        functions = json.loads(outputs[builder.FUNCTION_CONTRACT_PATH])
        verification = json.loads(outputs[builder.VERIFICATION_PATH])
        self.assertEqual(indicator["indicators"], kernel.indicator_registry())
        self.assertEqual(parameters["parameters"], kernel.parameter_versions())
        self.assertEqual(functions["functions"], kernel.function_contracts())
        self.assertEqual(verification["accounting"], {"total": 78, "passed": 78, "failed": 0})

    def test_manifest_matches_the_receipt_state_and_closes_unopened_work(self) -> None:
        final, _, _ = builder.final_binding(builder.receipts())
        manifest = json.loads(builder.expected_outputs()[builder.MANIFEST_PATH])
        self.assertEqual(manifest["phase_acceptance_status"], "PASSED" if final else "PENDING_FINAL_VALIDATION")
        self.assertEqual(manifest["overall_accepted_phase_count"], 35 if final else 34)
        self.assertEqual(manifest["stage_execution_percentage"], 33)
        self.assertEqual(manifest["s13_p2_entry_allowed"], final)
        self.assertFalse(manifest["s13_p2_started"])
        self.assertFalse(manifest["s13_p3_entry_allowed"])
        self.assertFalse(manifest["health_score_computed"])
        self.assertFalse(manifest["action_priority_computed"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])

    def test_task_matrix_covers_exact_taskpack_tasks(self) -> None:
        final, _, _ = builder.final_binding(builder.receipts())
        matrix = json.loads(builder.expected_outputs()[builder.TASK_MATRIX_PATH])
        self.assertEqual([row["task_id"] for row in matrix["tasks"]], ["S13P1T01", "S13P1T02", "S13P1T03"])
        self.assertEqual(matrix["task_accepted_count"], 3 if final else 0)


if __name__ == "__main__":
    unittest.main()
