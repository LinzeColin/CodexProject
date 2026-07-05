from __future__ import annotations

import json
import unittest

from KMFA.tools.check_v014_private_processed_value_source_map_gap_resolution import (
    validate_v014_private_processed_value_source_map_gap_resolution,
)
from KMFA.tools.v014_private_processed_value_source_map_gap_resolution import (
    PRIVATE_OWNER_WORKLIST_PATH,
    generate,
)


class V014PrivateProcessedValueSourceMapGapResolutionTest(unittest.TestCase):
    def test_gap_resolution_locks_unresolved_authorized_fill_gaps(self) -> None:
        manifest = generate(generated_at="2026-07-05T23:59:59+10:00")
        validated = validate_v014_private_processed_value_source_map_gap_resolution(
            require_private_owner_worklist=True
        )

        self.assertEqual(
            validated["phase_id"],
            "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_AUTHORIZED_FILL_GAP_RESOLUTION",
        )
        self.assertEqual(validated["status"], manifest["status"])
        summary = validated["gap_resolution_summary"]
        self.assertEqual(summary["previous_fill_request_item_count"], 149)
        self.assertEqual(summary["previous_authorized_filled_item_count"], 36)
        self.assertEqual(summary["unresolved_gap_item_count"], 113)
        self.assertEqual(summary["unresolved_unique_private_ref_count"], 101)
        self.assertEqual(summary["duplicate_unresolved_gap_item_count"], 12)
        self.assertFalse(summary["source_map_gap_resolution_complete"])
        self.assertTrue(summary["owner_authorized_fill_intake_required"])

    def test_public_gap_artifacts_are_aggregate_only(self) -> None:
        manifest = generate(generated_at="2026-07-05T23:59:59+10:00")
        validate_v014_private_processed_value_source_map_gap_resolution(
            require_private_owner_worklist=True
        )

        public_payload = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        forbidden_fragments = (
            '"private_processed_ref"',
            "private://",
            '"raw_value"',
            '"normalized_value"',
            '"processed_value"',
            "/Users/linzezhang/Downloads",
        )
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, public_payload)

    def test_private_owner_worklist_is_ignored_and_release_blocked(self) -> None:
        manifest = validate_v014_private_processed_value_source_map_gap_resolution(
            require_private_owner_worklist=True
        )
        worklist = json.loads(PRIVATE_OWNER_WORKLIST_PATH.read_text(encoding="utf-8"))

        self.assertEqual(worklist["owner_worklist_summary"]["owner_worklist_item_count"], 113)
        self.assertFalse(manifest["go_no_go"]["processed_value_materialization_replay_allowed"])
        self.assertFalse(manifest["go_no_go"]["raw_to_processed_value_comparison_allowed"])
        self.assertFalse(manifest["go_no_go"]["github_upload_allowed"])
        self.assertFalse(manifest["go_no_go"]["app_reinstall_allowed"])
        self.assertFalse(manifest["go_no_go"]["business_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
