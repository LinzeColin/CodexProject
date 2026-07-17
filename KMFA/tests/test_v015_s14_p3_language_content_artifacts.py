import json
import unittest

from KMFA.tools import build_v015_s14_p3_language_content as builder
from KMFA.tools import v015_s14_p3_language_content as language


class TestV015S14P3LanguageContentArtifacts(unittest.TestCase):
    def test_dependency_is_the_accepted_s14_p2(self) -> None:
        value = builder.dependency()
        self.assertEqual(value["acceptance_status"], "PASSED")
        self.assertEqual(value["validation_receipt_count"], 20)
        self.assertTrue(value["s14_p3_entry_allowed"])
        self.assertFalse(value["s14_p3_started"])

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
            json.loads(outputs[builder.DICTIONARY_PATH]),
            language.interface_dictionary_contract(),
        )
        self.assertEqual(
            json.loads(outputs[builder.FORMAT_PATH]),
            language.format_contract(),
        )
        self.assertEqual(
            json.loads(outputs[builder.DENSITY_PATH]),
            language.content_density_contract(),
        )
        self.assertEqual(
            json.loads(outputs[builder.WALKTHROUGH_PATH]),
            language.cognitive_walkthrough_evidence(),
        )

    def test_manifest_tracks_pending_or_final_state_and_stops_before_review(self) -> None:
        final, _, _ = builder.final_binding(builder.receipts())
        manifest = json.loads(builder.expected_outputs()[builder.MANIFEST_PATH])
        self.assertEqual(
            manifest["phase_acceptance_status"],
            "PASSED" if final else "PENDING_FINAL_VALIDATION",
        )
        self.assertEqual(manifest["overall_accepted_phase_count"], 40 if final else 39)
        self.assertEqual(manifest["stage_execution_percentage"], 100)
        self.assertEqual(manifest["dictionary_entry_count"], 14)
        self.assertEqual(manifest["format_case_count"], 10)
        self.assertEqual(manifest["content_rule_screen_count"], 6)
        self.assertEqual(manifest["ten_second_failure_count"], 0)
        self.assertTrue(manifest["s14_p3_started"])
        self.assertEqual(manifest["s14_stage_review_entry_allowed"], final)
        self.assertFalse(manifest["s14_stage_review_started"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])

    def test_task_matrix_covers_exact_taskpack_tasks(self) -> None:
        final, _, _ = builder.final_binding(builder.receipts())
        matrix = json.loads(builder.expected_outputs()[builder.TASK_MATRIX_PATH])
        self.assertEqual(
            [row["task_id"] for row in matrix["tasks"]],
            ["S14P3T01", "S14P3T02", "S14P3T03"],
        )
        self.assertEqual(matrix["accepted_task_count"], 3 if final else 0)


if __name__ == "__main__":
    unittest.main()
