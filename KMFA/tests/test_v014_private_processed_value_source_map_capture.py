from __future__ import annotations

import unittest

from KMFA.tools.check_v014_private_processed_value_source_map_capture import (
    validate_v014_private_processed_value_source_map_capture,
)
from KMFA.tools.v014_private_processed_value_source_map_capture import generate


class V014PrivateProcessedValueSourceMapCaptureTest(unittest.TestCase):
    def test_path_only_refs_create_capture_request_without_fingerprints(self) -> None:
        manifest = generate(generated_at="2026-07-05T23:59:59+10:00")
        validated = validate_v014_private_processed_value_source_map_capture(
            require_private_capture=True
        )

        self.assertEqual(validated["phase_id"], "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_CAPTURE")
        self.assertEqual(validated["status"], manifest["status"])
        summary = validated["source_map_capture_summary"]
        self.assertEqual(summary["processed_target_slot_count"], 149)
        self.assertEqual(summary["path_only_private_ref_slot_count"], 149)
        self.assertEqual(summary["direct_processed_value_literal_count"], 0)
        self.assertEqual(summary["captured_processed_value_fingerprint_count"], 0)
        self.assertEqual(summary["usable_private_processed_value_source_map_record_count"], 0)
        self.assertEqual(summary["authorized_fill_required_slot_count"], 149)
        self.assertFalse(summary["source_map_capture_complete"])
        self.assertFalse(validated["value_matching_readiness"]["raw_to_processed_value_comparison_performed"])
        self.assertFalse(validated["value_matching_readiness"]["business_value_consistency_verified"])
        self.assertEqual(validated["go_no_go"]["decision"], "NO_GO")

    def test_raw_release_and_upload_boundaries_remain_blocked(self) -> None:
        manifest = validate_v014_private_processed_value_source_map_capture(
            require_private_capture=True
        )

        for value in manifest["raw_readonly_boundary"].values():
            self.assertFalse(value)
        go_no_go = manifest["go_no_go"]
        self.assertFalse(go_no_go["lineage_full_check_complete"])
        self.assertFalse(go_no_go["formal_report_allowed"])
        self.assertFalse(go_no_go["github_upload_allowed"])
        self.assertFalse(go_no_go["app_reinstall_allowed"])
        self.assertFalse(go_no_go["business_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
