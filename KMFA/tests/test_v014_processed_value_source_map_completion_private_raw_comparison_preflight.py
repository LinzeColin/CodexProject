from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_private_raw_comparison_preflight as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_private_raw_comparison_preflight import (
    validate,
)


class ProcessedValueSourceMapCompletionPrivateRawComparisonPreflightTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_private_raw_inventory_is_ready(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertTrue(summary["raw_inventory_ready"])
        self.assertTrue(summary["raw_manifest_private_written"])
        self.assertGreater(summary["raw_manifest_record_count"], 0)
        self.assertGreaterEqual(summary["raw_manifest_directory_count"], 0)
        self.assertGreater(summary["raw_total_size_bytes"], 0)
        self.assertTrue(summary["raw_type_bucket_counts"])
        self.assertTrue(summary["raw_root_exists_private"])
        self.assertTrue(summary["raw_root_is_directory_private"])
        self.assertTrue(summary["raw_root_stable_after_inventory"])
        self.assertTrue(summary["private_raw_value_matching_dry_run_ready"])

    def test_raw_access_is_limited_to_preflight_inventory(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["raw_value_matching_allowed_by_this_phase"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["raw_field_or_header_read_performed_by_this_phase"])
        self.assertFalse(summary["raw_value_extraction_performed_by_this_phase"])
        boundary = summary["raw_boundary"]
        self.assertTrue(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertTrue(boundary["raw_inbox_file_stat_performed_by_this_phase"])
        self.assertTrue(boundary["raw_inbox_hash_or_value_fingerprint_performed_by_this_phase"])
        self.assertTrue(boundary["raw_inbox_file_content_hash_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_field_or_header_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_write_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_delete_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_move_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_rename_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_copy_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

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

    def test_validator_accepts_private_manifest(self) -> None:
        manifest = validate(require_private_manifest=True)
        self.assertTrue(manifest["summary"]["raw_inventory_ready"])
        self.assertGreater(manifest["summary"]["raw_manifest_record_count"], 0)
        self.assertFalse(manifest["summary"]["delivery_allowed"])


if __name__ == "__main__":
    unittest.main()
