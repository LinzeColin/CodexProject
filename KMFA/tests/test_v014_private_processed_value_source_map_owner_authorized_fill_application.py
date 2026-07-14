from __future__ import annotations

import json
import unittest

from KMFA.tools.check_v014_private_processed_value_source_map_owner_authorized_fill_application import (
    validate_v014_private_processed_value_source_map_owner_authorized_fill_application,
)
from KMFA.tools.v014_private_processed_value_source_map_owner_authorized_fill_application import (
    PRIVATE_APPLICATION_DIAGNOSTIC_PATH,
    generate,
    materialize_active_record_from_draft,
)


class V014PrivateProcessedValueSourceMapOwnerAuthorizedFillApplicationTest(unittest.TestCase):
    def setUp(self) -> None:
        materialize_active_record_from_draft(generated_at="2026-07-06T00:00:00+10:00")

    def test_active_keep_pending_fill_record_locks_no_go_application(self) -> None:
        manifest = generate(generated_at="2026-07-05T23:59:59+10:00")
        validated = validate_v014_private_processed_value_source_map_owner_authorized_fill_application(
            require_private_application_diagnostic=True
        )

        self.assertEqual(
            validated["phase_id"],
            "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_APPLICATION",
        )
        self.assertEqual(validated["status"], manifest["status"])
        summary = validated["owner_authorized_fill_application_summary"]
        self.assertEqual(summary["source_unresolved_gap_item_count"], 113)
        self.assertEqual(summary["source_unresolved_unique_private_ref_count"], 101)
        self.assertEqual(summary["private_intake_request_item_count"], 113)
        self.assertEqual(summary["candidate_active_fill_record_path_count"], 2)
        self.assertEqual(summary["existing_active_fill_record_path_count"], 1)
        self.assertEqual(summary["active_fill_record_item_count"], 113)
        self.assertEqual(summary["active_fill_record_keep_pending_count"], 113)
        self.assertTrue(summary["owner_authorized_fill_record_supplied"])
        self.assertTrue(summary["active_authorized_fill_record_found"])
        self.assertTrue(summary["fill_application_performed"])
        self.assertEqual(summary["source_map_records_applied_count"], 0)
        self.assertEqual(summary["new_authorized_fingerprint_count"], 0)
        self.assertFalse(summary["source_map_gap_resolution_complete"])

    def test_public_application_artifacts_are_status_only(self) -> None:
        manifest = generate(generated_at="2026-07-05T23:59:59+10:00")
        validate_v014_private_processed_value_source_map_owner_authorized_fill_application(
            require_private_application_diagnostic=True
        )

        public_payload = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        forbidden_fragments = (
            '"private_processed_ref"',
            "private://",
            '"raw_value"',
            '"normalized_value"',
            '"processed_value"',
            "/Users/linzezhang/Downloads",
            "KMFA_MetaData",
            ".xlsx",
            ".zip",
            ".pdf",
        )
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, public_payload)

    def test_private_application_diagnostic_is_ignored_and_release_blocked(self) -> None:
        manifest = validate_v014_private_processed_value_source_map_owner_authorized_fill_application(
            require_private_application_diagnostic=True
        )
        private_diagnostic = json.loads(PRIVATE_APPLICATION_DIAGNOSTIC_PATH.read_text(encoding="utf-8"))

        self.assertEqual(private_diagnostic["application_diagnostic_summary"]["candidate_active_fill_record_path_count"], 2)
        self.assertTrue(private_diagnostic["application_diagnostic_summary"]["active_fill_record_found"])
        self.assertEqual(private_diagnostic["application_diagnostic_summary"]["active_fill_record_keep_pending_count"], 113)
        self.assertFalse(manifest["go_no_go"]["processed_value_materialization_replay_allowed"])
        self.assertFalse(manifest["go_no_go"]["raw_to_processed_value_comparison_allowed"])
        self.assertFalse(manifest["go_no_go"]["business_value_consistency_verified"])
        self.assertFalse(manifest["go_no_go"]["github_upload_allowed"])
        self.assertFalse(manifest["go_no_go"]["app_reinstall_allowed"])
        self.assertFalse(manifest["go_no_go"]["business_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
