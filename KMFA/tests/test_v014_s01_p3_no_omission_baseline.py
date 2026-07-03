import unittest

from KMFA.tools.check_v014_s01_p3_no_omission_baseline import (
    validate_v014_s01_p3_no_omission_baseline,
)


class TestV014S01P3NoOmissionBaseline(unittest.TestCase):
    def test_v14_no_omission_baseline_locks_traceability_without_release_scope(self) -> None:
        result = validate_v014_s01_p3_no_omission_baseline()

        self.assertEqual(result["schema_version"], "kmfa.v014_s01_p3_no_omission_baseline.v1")
        self.assertEqual(result["version"], "0.1.4")
        self.assertEqual(result["stage_phase"], "S01-P3")
        self.assertEqual(result["status"], "completed_validated_local_only_no_go_upload_deferred")
        self.assertEqual(result["legacy_requirements"], 20)
        self.assertEqual(result["legacy_p0"], 9)
        self.assertEqual(result["legacy_p1"], 8)
        self.assertEqual(result["v14_overlay_requirements"], 5)
        self.assertEqual(result["v14_overlay_p0"], 3)
        self.assertEqual(result["v14_overlay_p1"], 2)
        self.assertEqual(result["v14_stage_status_records"], 234)
        self.assertEqual(result["v14_stages"], 18)
        self.assertEqual(result["v14_phases"], 54)
        self.assertEqual(result["v14_tasks"], 162)

        scope = result["phase_scope"]
        self.assertTrue(scope["current_phase_only"])
        self.assertFalse(scope["stage_review_performed"])
        self.assertFalse(scope["github_upload_performed"])
        self.assertFalse(scope["s02_started"])
        self.assertEqual(scope["next_phase"], "S01_STAGE_REVIEW")
        self.assertFalse(scope["next_phase_started"])

        boundary = result["raw_data_boundary"]
        self.assertFalse(boundary["raw_inbox_read_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_listed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_modified_by_this_phase"])
        self.assertFalse(boundary["raw_payload_extracted_from_delivery_zip"])
        self.assertFalse(boundary["raw_filenames_committed"])
        self.assertFalse(boundary["raw_hashes_committed"])
        self.assertFalse(boundary["field_or_header_plaintext_committed"])
        self.assertFalse(boundary["business_values_committed"])

        release = result["release_state"]
        self.assertFalse(release["delivery_allowed"])
        self.assertFalse(release["formal_report_allowed"])
        self.assertFalse(release["business_decision_basis_allowed"])
        self.assertFalse(release["business_execution_allowed"])
        self.assertFalse(release["github_main_upload_allowed"])
        self.assertEqual(release["current_go_no_go"], "NO_GO")
        self.assertEqual(result["next_recommended_phase"], "S01_STAGE_REVIEW")


if __name__ == "__main__":
    unittest.main()
