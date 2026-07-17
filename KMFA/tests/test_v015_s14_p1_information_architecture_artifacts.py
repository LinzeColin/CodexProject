import json
import unittest

from KMFA.tools import build_v015_s14_p1_information_architecture as builder
from KMFA.tools import v015_s14_p1_information_architecture as ia


class TestV015S14P1InformationArchitectureArtifacts(unittest.TestCase):
    def test_dependency_is_the_accepted_s13_stage_review(self) -> None:
        value = builder.dependency()
        self.assertEqual(value["acceptance_status"], "PASSED")
        self.assertEqual(value["validation_receipt_count"], 24)
        self.assertTrue(value["s14_p1_entry_allowed"])
        self.assertFalse(value["s14_p1_started"])

    def test_expected_outputs_are_deterministic_and_public_safe(self) -> None:
        first = builder.expected_outputs()
        second = builder.expected_outputs()
        self.assertEqual(first, second)
        public_text = "\n".join(first.values())
        for forbidden in ("/" + "Users" + "/", "/Volumes/", "file://", "private://", "KMFA_MetaData"):
            self.assertNotIn(forbidden, public_text)

    def test_machine_contracts_match_the_kernel(self) -> None:
        outputs = builder.expected_outputs()
        navigation = json.loads(outputs[builder.NAVIGATION_CONTRACT_PATH])
        hierarchy = json.loads(outputs[builder.PAGE_HIERARCHY_CONTRACT_PATH])
        disclosure = json.loads(outputs[builder.DISCLOSURE_CONTRACT_PATH])
        research = json.loads(outputs[builder.NAVIGATION_RESEARCH_PATH])
        self.assertEqual(navigation, ia.navigation_contract())
        self.assertEqual(hierarchy["summary"], ia.validate_page_hierarchy())
        self.assertEqual(disclosure, ia.progressive_disclosure_contract())
        self.assertEqual(research["card_sort_pass_count"], 21)
        self.assertEqual(research["tree_test_pass_count"], 10)

    def test_manifest_tracks_pending_or_final_state_and_stops_before_p2(self) -> None:
        final, _, _ = builder.final_binding(builder.receipts())
        manifest = json.loads(builder.expected_outputs()[builder.MANIFEST_PATH])
        self.assertEqual(manifest["phase_acceptance_status"], "PASSED" if final else "PENDING_FINAL_VALIDATION")
        self.assertEqual(manifest["overall_accepted_phase_count"], 38 if final else 37)
        self.assertEqual(manifest["stage_execution_percentage"], 33)
        self.assertEqual(manifest["primary_navigation_count"], 7)
        self.assertEqual(manifest["page_node_count"], 18)
        self.assertEqual(manifest["dead_end_count"], 0)
        self.assertEqual(manifest["default_visible_technical_term_count"], 0)
        self.assertEqual(manifest["s14_p2_entry_allowed"], final)
        self.assertFalse(manifest["s14_p2_started"])
        self.assertFalse(manifest["s14_p3_started"])
        self.assertFalse(manifest["s14_stage_review_started"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])

    def test_task_matrix_covers_exact_taskpack_tasks(self) -> None:
        final, _, _ = builder.final_binding(builder.receipts())
        matrix = json.loads(builder.expected_outputs()[builder.TASK_MATRIX_PATH])
        self.assertEqual([row["task_id"] for row in matrix["tasks"]], ["S14P1T01", "S14P1T02", "S14P1T03"])
        self.assertEqual(matrix["task_accepted_count"], 3 if final else 0)


if __name__ == "__main__":
    unittest.main()
