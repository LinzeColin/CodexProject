import unittest

from KMFA.tools.check_v013_s03_p2_source_check_matrix import (
    validate_v013_s03_p2_source_check_matrix,
)


class TestV013S03P2SourceCheckMatrix(unittest.TestCase):
    def test_source_check_matrix_locks_metadata_only_public_safe_boundary(self) -> None:
        result = validate_v013_s03_p2_source_check_matrix()

        self.assertEqual(result["stage_id"], "S03")
        self.assertEqual(result["phase_id"], "S03-P2")
        self.assertEqual(result["phase_scope"], "v013_s03_p2_source_check_matrix_only")
        self.assertTrue(result["s03_p1_dependency_validated"])
        self.assertTrue(result["source_check_matrix_dependency_validated"])
        self.assertEqual(result["required_dimension_count"], 6)
        self.assertEqual(
            result["required_dimensions"],
            [
                "source_system",
                "business_segment",
                "source_package_ref",
                "entity_ref",
                "account_ref",
                "frequency",
            ],
        )
        self.assertEqual(result["allowed_status_count"], 5)
        self.assertEqual(result["allowed_statuses"], ["已就绪", "部分/阻塞", "失败/不适用", "已过期", "人工复核"])
        self.assertTrue(result["metadata_status_event_validated"])
        self.assertTrue(result["status_change_append_only"])
        self.assertEqual(result["status_change_target_layer"], "metadata")
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertFalse(result["raw_layer_write_allowed"])
        self.assertFalse(result["raw_source_mutation_allowed"])
        self.assertFalse(result["raw_filename_publication_allowed"])
        self.assertFalse(result["raw_file_hash_publication_allowed"])
        self.assertFalse(result["business_field_parsing_performed"])
        self.assertFalse(result["raw_value_matching_performed"])
        self.assertFalse(result["source_priority_performed"])
        self.assertFalse(result["stage3_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["delivery_allowed"])
        self.assertIn("S03-P3", result["next_required_step"])


if __name__ == "__main__":
    unittest.main()
