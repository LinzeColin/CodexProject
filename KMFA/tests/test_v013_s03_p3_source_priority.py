import unittest

from KMFA.tools.check_v013_s03_p3_source_priority import (
    validate_v013_s03_p3_source_priority,
)


class TestV013S03P3SourcePriority(unittest.TestCase):
    def test_source_priority_locks_public_safe_difference_queue_boundary(self) -> None:
        result = validate_v013_s03_p3_source_priority()

        self.assertEqual(result["stage_id"], "S03")
        self.assertEqual(result["phase_id"], "S03-P3")
        self.assertEqual(result["phase_scope"], "v013_s03_p3_source_priority_only")
        self.assertTrue(result["s03_p2_dependency_validated"])
        self.assertTrue(result["source_priority_dependency_validated"])
        self.assertEqual(result["source_priority_order_count"], 9)
        self.assertEqual(
            result["source_priority_order"],
            [
                "raw_upload",
                "authorized_export",
                "raw_extracted_value",
                "staging_structured_row",
                "canonical_fact",
                "derived_metric",
                "report_reference",
                "frontend_display",
                "processed_data",
            ],
        )
        self.assertTrue(result["same_source_invalidation_event_validated"])
        self.assertEqual(
            result["same_source_inconsistency_actions"],
            ["invalidate_derived_cache", "request_rerun"],
        )
        self.assertTrue(result["cross_source_difference_queue_validated"])
        self.assertEqual(result["cross_source_resolution_policy"], "manual_review_required")
        self.assertFalse(result["auto_selection_allowed"])
        self.assertFalse(result["auto_correction_allowed"])
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertFalse(result["raw_layer_write_allowed"])
        self.assertFalse(result["raw_source_mutation_allowed"])
        self.assertFalse(result["raw_filename_publication_allowed"])
        self.assertFalse(result["raw_file_hash_publication_allowed"])
        self.assertFalse(result["business_field_parsing_performed"])
        self.assertFalse(result["raw_value_matching_performed"])
        self.assertFalse(result["stage3_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["delivery_allowed"])
        self.assertIn("Stage 3 review", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
