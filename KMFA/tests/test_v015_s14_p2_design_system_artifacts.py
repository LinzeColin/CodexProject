import json
import unittest

from KMFA.tools import build_v015_s14_p2_design_system as builder
from KMFA.tools import v015_s14_p2_design_system as design


class TestV015S14P2DesignSystemArtifacts(unittest.TestCase):
    def test_dependency_is_the_accepted_s14_p1(self) -> None:
        value = builder.dependency()
        self.assertEqual(value["acceptance_status"], "PASSED")
        self.assertEqual(value["validation_receipt_count"], 19)
        self.assertTrue(value["s14_p2_entry_allowed"])
        self.assertFalse(value["s14_p2_started"])

    def test_expected_outputs_are_deterministic_and_public_safe(self) -> None:
        first = builder.expected_outputs()
        second = builder.expected_outputs()
        self.assertEqual(first, second)
        public_text = "\n".join(first.values())
        for forbidden in ("/" + "Users" + "/", "/Volumes/", "file://", "private://", "KMFA_MetaData"):
            self.assertNotIn(forbidden, public_text)

    def test_machine_contracts_match_kernel(self) -> None:
        outputs = builder.expected_outputs()
        self.assertEqual(
            json.loads(outputs[builder.DESIGN_TOKEN_CONTRACT_PATH]),
            design.design_token_contract(),
        )
        self.assertEqual(
            json.loads(outputs[builder.COMPONENT_CONTRACT_PATH]),
            design.component_contract(),
        )
        self.assertEqual(
            json.loads(outputs[builder.MOTION_CONTRACT_PATH]),
            design.motion_contract(),
        )
        self.assertEqual(
            json.loads(outputs[builder.CONTRAST_EVIDENCE_PATH]),
            design.contrast_evidence(),
        )

    def test_manifest_tracks_pending_or_final_state_and_stops_before_p3(self) -> None:
        final, _, _ = builder.final_binding(builder.receipts())
        manifest = json.loads(builder.expected_outputs()[builder.MANIFEST_PATH])
        self.assertEqual(
            manifest["phase_acceptance_status"],
            "PASSED" if final else "PENDING_FINAL_VALIDATION",
        )
        self.assertEqual(manifest["overall_accepted_phase_count"], 39 if final else 38)
        self.assertEqual(manifest["stage_execution_percentage"], 67)
        self.assertEqual(manifest["theme_count"], 2)
        self.assertEqual(manifest["contrast_fail_count"], 0)
        self.assertEqual(manifest["component_count"], 11)
        self.assertEqual(manifest["full_state_coverage_count"], 11)
        self.assertEqual(manifest["no_feedback_component_count"], 0)
        self.assertEqual(manifest["color_only_state_count"], 0)
        self.assertEqual(manifest["maximum_motion_duration_ms"], 220)
        self.assertTrue(manifest["s14_p2_started"])
        self.assertEqual(manifest["s14_p3_entry_allowed"], final)
        self.assertFalse(manifest["s14_p3_started"])
        self.assertFalse(manifest["s14_stage_review_started"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])

    def test_task_matrix_covers_exact_taskpack_tasks(self) -> None:
        final, _, _ = builder.final_binding(builder.receipts())
        matrix = json.loads(builder.expected_outputs()[builder.TASK_MATRIX_PATH])
        self.assertEqual(
            [row["task_id"] for row in matrix["tasks"]],
            ["S14P2T01", "S14P2T02", "S14P2T03"],
        )
        self.assertEqual(matrix["task_accepted_count"], 3 if final else 0)


if __name__ == "__main__":
    unittest.main()
