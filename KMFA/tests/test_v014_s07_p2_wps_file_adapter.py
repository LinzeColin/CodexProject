import unittest

from KMFA.tools.check_v014_s07_p2_wps_file_adapter import (
    validate_v014_s07_p2_wps_file_adapter,
)


class TestV014S07P2WpsFileAdapter(unittest.TestCase):
    def test_wps_file_adapter_is_public_safe_versioned_and_local_only(self) -> None:
        result = validate_v014_s07_p2_wps_file_adapter()

        self.assertEqual(result["stage_id"], "S07")
        self.assertEqual(result["phase_id"], "S07-P2")
        self.assertEqual(result["phase_scope"], "v014_s07_p2_wps_file_adapter_only")
        self.assertTrue(result["s06_stage_review_dependency_validated"])
        self.assertTrue(result["s07_p1_dependency_validated"])
        self.assertTrue(result["legacy_wps_adapter_validated"])
        self.assertEqual(result["source_export_type_count"], 4)
        self.assertEqual(result["source_registry_count"], 4)
        self.assertEqual(result["field_mapping_count"], 20)
        self.assertEqual(result["hash_only_field_mapping_count"], 20)
        self.assertEqual(result["field_report_count"], 4)
        self.assertEqual(result["conversion_guidance_count"], 4)
        self.assertEqual(result["mapping_rule_version_count"], 1)
        self.assertEqual(result["source_header_fingerprint_count"], 20)
        self.assertEqual(result["native_conversion_required_count"], 4)
        self.assertEqual(result["q4_human_confirmed_count"], 0)
        self.assertEqual(result["q5_calculation_baseline_allowed_count"], 0)
        self.assertEqual(result["formal_report_allowed_count"], 0)
        self.assertTrue(result["s07_p2_performed"])
        self.assertFalse(result["s07_p1_performed"])
        self.assertFalse(result["s07_p3_performed"])
        self.assertFalse(result["stage7_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["raw_inbox_read_performed"])
        self.assertFalse(result["raw_inbox_mutation_performed"])
        self.assertFalse(result["business_field_value_parsing_performed"])
        self.assertFalse(result["source_header_plaintext_committed"])
        self.assertFalse(result["field_plaintext_committed"])
        self.assertFalse(result["delivery_allowed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertEqual(result["current_data_quality_grade"], "Q4")
        self.assertEqual(result["current_report_grade"], "D")
        self.assertEqual(result["release_permission"], "blocked")
        self.assertEqual(result["next_recommended_phase"], "S07-P3")
        self.assertIn("Stage 1-18", result["next_phase_instruction"])


if __name__ == "__main__":
    unittest.main()
