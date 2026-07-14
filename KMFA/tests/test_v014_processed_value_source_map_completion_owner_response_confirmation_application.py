from __future__ import annotations

import unittest

from KMFA.tools import v014_processed_value_source_map_completion_owner_response_confirmation_application as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_owner_response_confirmation_application import (
    validate,
)


class ProcessedValueSourceMapCompletionOwnerResponseConfirmationApplicationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    def test_user_sequence_is_recorded(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["primary_confirmation_code"], "KMFA_ORR_OPTION_REQUEST_MORE_DIAGNOSTICS_ALL")
        self.assertEqual(summary["follow_up_confirmation_code"], "KMFA_ORR_OPTION_REVIEW_GROUPS")
        self.assertTrue(summary["confirmation_record_written"])
        self.assertTrue(summary["confirmation_record_gitignored"])
        self.assertTrue(summary["supplemental_diagnostic_request_written"])
        self.assertEqual(summary["supplemental_diagnostic_request_row_count"], 113)
        self.assertTrue(summary["review_group_follow_up_ready"])
        self.assertEqual(summary["review_group_follow_up_row_count"], 113)

    def test_downstream_gates_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["active_owner_authorized_fill_record_ready"])
        self.assertFalse(summary["active_owner_authorized_fill_record_written"])
        self.assertFalse(summary["owner_response_template_modified"])
        self.assertFalse(summary["completion_template_overwritten"])
        self.assertFalse(summary["authorized_completion_record_supplied"])
        self.assertFalse(summary["source_map_completion_reapplication_ready"])
        self.assertFalse(summary["source_map_completion_reapplication_performed"])
        self.assertEqual(summary["source_map_records_applied_count"], 0)
        self.assertFalse(summary["raw_to_processed_value_comparison_performed"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_raw_boundary_is_closed_for_this_phase(self) -> None:
        boundary = self.manifest["summary"]["raw_boundary"]
        self.assertTrue(boundary["raw_data_root_readonly_policy_active"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_hash_or_value_fingerprint_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_write_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_delete_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_move_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_rename_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_overwrite_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_copy_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_normalize_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_validator_accepts_private_confirmation(self) -> None:
        manifest = validate(require_private_confirmation=True)
        self.assertEqual(manifest["summary"]["primary_confirmation_code"], "KMFA_ORR_OPTION_REQUEST_MORE_DIAGNOSTICS_ALL")
        self.assertTrue(manifest["summary"]["review_group_follow_up_ready"])


if __name__ == "__main__":
    unittest.main()
