from __future__ import annotations

import json
import unittest

from KMFA.tools.check_v014_private_processed_value_source_map_owner_authorized_fill_intake import (
    validate_v014_private_processed_value_source_map_owner_authorized_fill_intake,
)
from KMFA.tools.v014_private_processed_value_source_map_owner_authorized_fill_intake import (
    PRIVATE_INTAKE_REQUEST_PATH,
    generate,
)


class V014PrivateProcessedValueSourceMapOwnerAuthorizedFillIntakeTest(unittest.TestCase):
    def test_owner_authorized_fill_intake_locks_public_safe_contract(self) -> None:
        manifest = generate(generated_at="2026-07-05T23:59:59+10:00")
        validated = validate_v014_private_processed_value_source_map_owner_authorized_fill_intake(
            require_private_intake_request=True
        )

        self.assertEqual(
            validated["phase_id"],
            "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_INTAKE",
        )
        self.assertEqual(validated["status"], manifest["status"])
        summary = validated["owner_authorized_fill_intake_summary"]
        self.assertEqual(summary["source_unresolved_gap_item_count"], 113)
        self.assertEqual(summary["source_unresolved_unique_private_ref_count"], 101)
        self.assertEqual(summary["private_intake_request_item_count"], 113)
        self.assertEqual(summary["allowed_intake_action_count"], 3)
        self.assertTrue(summary["owner_authorized_fill_intake_ready"])
        self.assertFalse(summary["owner_authorized_fill_record_supplied"])
        self.assertFalse(summary["active_authorized_fill_record_created"])
        self.assertEqual(summary["new_authorized_fingerprint_count"], 0)

    def test_public_intake_artifacts_are_aggregate_only(self) -> None:
        manifest = generate(generated_at="2026-07-05T23:59:59+10:00")
        validate_v014_private_processed_value_source_map_owner_authorized_fill_intake(
            require_private_intake_request=True
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

    def test_private_intake_request_is_ignored_and_release_blocked(self) -> None:
        manifest = validate_v014_private_processed_value_source_map_owner_authorized_fill_intake(
            require_private_intake_request=True
        )
        private_request = json.loads(PRIVATE_INTAKE_REQUEST_PATH.read_text(encoding="utf-8"))

        self.assertEqual(private_request["intake_request_summary"]["intake_request_item_count"], 113)
        self.assertFalse(manifest["go_no_go"]["processed_value_materialization_replay_allowed"])
        self.assertFalse(manifest["go_no_go"]["raw_to_processed_value_comparison_allowed"])
        self.assertFalse(manifest["go_no_go"]["github_upload_allowed"])
        self.assertFalse(manifest["go_no_go"]["app_reinstall_allowed"])
        self.assertFalse(manifest["go_no_go"]["business_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
