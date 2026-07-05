from __future__ import annotations

import json
import unittest

from KMFA.tools.check_v014_private_processed_value_source_map_owner_authorized_fill_record_draft import (
    validate_v014_owner_authorized_fill_record_draft,
)
from KMFA.tools.v014_private_processed_value_source_map_owner_authorized_fill_record_draft import (
    PRIVATE_DRAFT_PATH,
    generate,
)


class V014OwnerAuthorizedFillRecordDraftTest(unittest.TestCase):
    def test_draft_preparation_keeps_owner_activation_required(self) -> None:
        manifest = generate(generated_at="2026-07-05T23:59:59+10:00")
        validated = validate_v014_owner_authorized_fill_record_draft(require_private_draft=True)

        self.assertEqual(validated["phase_id"], "V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_RECORD_DRAFT")
        self.assertEqual(validated["status"], manifest["status"])
        summary = validated["owner_authorized_fill_record_draft_summary"]
        self.assertEqual(summary["private_intake_request_item_count"], 113)
        self.assertEqual(summary["draft_fill_item_count"], 113)
        self.assertEqual(summary["draft_unique_target_slot_count"], 113)
        self.assertEqual(summary["draft_keep_pending_item_count"], 113)
        self.assertFalse(summary["draft_is_active_record"])
        self.assertFalse(summary["active_authorized_fill_record_created"])
        self.assertFalse(summary["fill_application_performed"])
        self.assertFalse(summary["source_map_gap_resolution_complete"])
        self.assertEqual(summary["next_required_input"], "owner_or_authorized_delegate_activation_of_draft_fill_record")

    def test_private_draft_contains_only_keep_pending_items(self) -> None:
        generate(generated_at="2026-07-05T23:59:59+10:00")
        validate_v014_owner_authorized_fill_record_draft(require_private_draft=True)
        draft = json.loads(PRIVATE_DRAFT_PATH.read_text(encoding="utf-8"))
        fill_items = draft["proposed_active_record_template"]["fill_items"]

        self.assertEqual(len(fill_items), 113)
        self.assertEqual(len({item["target_slot_id"] for item in fill_items}), 113)
        self.assertTrue(all(item["action_code"] == "keep_pending" for item in fill_items))
        self.assertFalse(draft["draft_is_active_record"])
        self.assertTrue(draft["activation_required"])

    def test_public_evidence_is_aggregate_only_and_release_blocked(self) -> None:
        manifest = generate(generated_at="2026-07-05T23:59:59+10:00")
        validate_v014_owner_authorized_fill_record_draft(require_private_draft=True)

        public_payload = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        forbidden_fragments = (
            '"private_processed_ref"',
            '"target_slot_id"',
            '"fill_items"',
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
        self.assertFalse(manifest["go_no_go"]["processed_value_materialization_replay_allowed"])
        self.assertFalse(manifest["go_no_go"]["raw_to_processed_value_comparison_allowed"])
        self.assertFalse(manifest["go_no_go"]["business_value_consistency_verified"])
        self.assertFalse(manifest["go_no_go"]["github_upload_allowed"])
        self.assertFalse(manifest["go_no_go"]["app_reinstall_allowed"])
        self.assertFalse(manifest["go_no_go"]["business_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
