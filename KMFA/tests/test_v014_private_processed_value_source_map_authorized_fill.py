from __future__ import annotations

import json
import unittest

from KMFA.tools.check_v014_private_processed_value_source_map_authorized_fill import (
    validate_v014_private_processed_value_source_map_authorized_fill,
)
from KMFA.tools.v014_private_processed_value_source_map_authorized_fill import (
    PRIVATE_SOURCE_MAP_PATH,
    generate,
)


class V014PrivateProcessedValueSourceMapAuthorizedFillTest(unittest.TestCase):
    def test_authorized_fill_writes_partial_private_source_map(self) -> None:
        manifest = generate(generated_at="2026-07-05T23:59:59+10:00")
        validated = validate_v014_private_processed_value_source_map_authorized_fill(
            require_private_authorized_fill=True
        )

        self.assertEqual(
            validated["phase_id"],
            "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_AUTHORIZED_FILL",
        )
        self.assertEqual(validated["status"], manifest["status"])
        summary = validated["authorized_fill_summary"]
        self.assertEqual(summary["fill_request_item_count"], 149)
        self.assertEqual(summary["unique_private_ref_count"], 137)
        self.assertEqual(summary["duplicate_private_ref_item_count"], 12)
        self.assertEqual(summary["authorized_filled_item_count"], 36)
        self.assertEqual(summary["authorized_unfilled_item_count"], 113)
        self.assertEqual(summary["authorized_filled_unique_ref_count"], 36)
        self.assertEqual(summary["authorized_unfilled_unique_ref_count"], 101)
        self.assertEqual(summary["source_map_records_written_count"], 36)
        self.assertEqual(summary["metadata_hash_sibling_source_file_count"], 1)
        self.assertFalse(summary["source_map_authorized_fill_complete"])
        self.assertFalse(
            validated["value_matching_readiness"]["raw_to_processed_value_comparison_performed"]
        )
        self.assertFalse(
            validated["value_matching_readiness"]["business_value_consistency_verified"]
        )
        self.assertEqual(validated["go_no_go"]["decision"], "NO_GO")

    def test_private_source_map_contains_fingerprints_not_values(self) -> None:
        generate(generated_at="2026-07-05T23:59:59+10:00")
        validate_v014_private_processed_value_source_map_authorized_fill(
            require_private_authorized_fill=True
        )

        payload = json.loads(PRIVATE_SOURCE_MAP_PATH.read_text(encoding="utf-8"))
        records = payload["processed_value_sources"]
        self.assertEqual(len(records), 36)
        for record in records:
            self.assertEqual(
                sorted(record),
                ["fill_status", "processed_value_fingerprint", "target_slot_id"],
            )
            self.assertTrue(record["target_slot_id"].startswith("PVSTG-"))
            self.assertTrue(record["processed_value_fingerprint"].startswith("sha256:"))
            self.assertEqual(record["fill_status"], "filled_from_existing_metadata_hash_sibling")

        forbidden_value_keys = {"raw_value", "normalized_value", "processed_value", "business_value", "value"}
        for record in records:
            self.assertTrue(forbidden_value_keys.isdisjoint(record))

    def test_release_upload_and_business_execution_remain_blocked(self) -> None:
        manifest = validate_v014_private_processed_value_source_map_authorized_fill(
            require_private_authorized_fill=True
        )

        for value in manifest["raw_readonly_boundary"].values():
            self.assertFalse(value)
        go_no_go = manifest["go_no_go"]
        self.assertFalse(go_no_go["processed_value_materialization_replay_performed"])
        self.assertFalse(go_no_go["lineage_full_check_complete"])
        self.assertFalse(go_no_go["formal_report_allowed"])
        self.assertFalse(go_no_go["github_upload_allowed"])
        self.assertFalse(go_no_go["app_reinstall_allowed"])
        self.assertFalse(go_no_go["business_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
