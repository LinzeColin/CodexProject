from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_corrected_source_or_raw_scope_intake as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_corrected_source_or_raw_scope_intake import (
    validate,
)


class ProcessedValueSourceMapCompletionCorrectedSourceOrRawScopeIntakeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_raw_scope_is_registered_without_corrected_source_package(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertTrue(summary["previous_required_input_resolved_by_this_phase"])
        self.assertFalse(summary["corrected_source_package_supplied"])
        self.assertTrue(summary["owner_authorized_private_raw_comparison_scope_registered"])
        self.assertTrue(summary["raw_root_exists_private"])
        self.assertTrue(summary["raw_root_is_directory_private"])
        self.assertTrue(summary["private_raw_comparison_preflight_ready"])
        self.assertEqual(summary["scope_item_count"], 5)

    def test_scope_matrix_allows_only_root_precheck_this_phase(self) -> None:
        matrix = self.manifest["scope_matrix"]
        self.assertEqual(matrix["scope_item_count"], 5)
        by_code = {item["scope_code"]: item for item in matrix["scope_items"]}
        self.assertTrue(by_code["RAW_ROOT_EXISTENCE_PRECHECK"]["allowed_this_phase"])
        self.assertTrue(by_code["RAW_ROOT_EXISTENCE_PRECHECK"]["performed_this_phase"])
        self.assertFalse(by_code["RAW_FILE_LISTING"]["allowed_this_phase"])
        self.assertFalse(by_code["RAW_FILE_LISTING"]["performed_this_phase"])
        self.assertFalse(by_code["RAW_FILE_HASHING_OR_PARSE"]["allowed_this_phase"])
        self.assertFalse(by_code["RAW_FILE_HASHING_OR_PARSE"]["performed_this_phase"])
        self.assertFalse(by_code["RAW_TO_PROCESSED_COMPARISON"]["allowed_this_phase"])
        self.assertFalse(by_code["RAW_TO_PROCESSED_COMPARISON"]["performed_this_phase"])

    def test_delivery_and_execution_gates_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["delivery_allowed"])
        self.assertFalse(summary["formal_report_allowed"])
        self.assertFalse(summary["github_upload_allowed"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_allowed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_allowed"])
        self.assertFalse(summary["business_execution_performed"])
        self.assertFalse(summary["full_source_map_completion_reapplication_ready"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_ready"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["canonical_source_map_mutated"])
        self.assertEqual(summary["canonical_source_map_records_applied_count"], 0)

    def test_raw_boundary_excludes_file_access(self) -> None:
        boundary = self.manifest["summary"]["raw_boundary"]
        self.assertTrue(boundary["raw_data_root_readonly_policy_active"])
        self.assertTrue(boundary["raw_root_existence_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_file_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_hash_or_value_fingerprint_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_write_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_delete_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_move_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_rename_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_overwrite_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_copy_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_normalize_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_validator_accepts_private_scope(self) -> None:
        manifest = validate(require_private_scope=True)
        self.assertTrue(manifest["summary"]["private_raw_comparison_preflight_ready"])
        self.assertFalse(manifest["summary"]["delivery_allowed"])


if __name__ == "__main__":
    unittest.main()
