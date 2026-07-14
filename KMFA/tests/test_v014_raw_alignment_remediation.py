import unittest

from KMFA.tools.check_v014_raw_alignment_remediation import validate_v014_raw_alignment_remediation
from KMFA.tools.v014_raw_alignment_remediation import generate


class V014RawAlignmentRemediationTests(unittest.TestCase):
    def test_reports_raw_container_mismatch_without_publishing_private_data(self) -> None:
        manifest = generate(generated_at="2026-07-05T21:30:00+10:00")
        validated = validate_v014_raw_alignment_remediation(require_private_diagnostic=True)

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["schema_version"], "kmfa.v014_raw_alignment_remediation.v1")
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["phase_id"], "V014_RAW_ALIGNMENT_REMEDIATION")
        self.assertEqual(validated["task_id"], "KMFA-V014-RAW-ALIGNMENT-REMEDIATION-20260705")
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-RAW-ALIGNMENT-REMEDIATION"])
        self.assertEqual(validated["status"], "raw_alignment_remediation_reported_no_go_owner_source_identity_required")

        raw = validated["raw_source_identity_summary"]
        self.assertTrue(raw["raw_root_exists"])
        self.assertTrue(raw["raw_root_is_readable"])
        self.assertEqual(raw["raw_root_file_count"], 5)
        self.assertEqual(raw["raw_root_archive_count"], 3)
        self.assertEqual(raw["raw_root_spreadsheet_count"], 2)
        self.assertEqual(raw["selected_candidate_count"], 1)
        self.assertTrue(raw["selected_archive_openable"])
        self.assertEqual(raw["business_member_count"], 9)
        self.assertEqual(raw["business_document_member_count"], 8)
        self.assertEqual(raw["business_spreadsheet_member_count"], 1)
        self.assertGreaterEqual(raw["hidden_or_system_member_count"], 0)
        self.assertTrue(raw["business_shape_matches_expected_a0"])
        self.assertFalse(raw["package_hash_matches_registered"])
        self.assertFalse(raw["package_size_matches_registered"])
        self.assertTrue(raw["private_member_hashes_recorded"])
        self.assertFalse(raw["public_member_hash_backfill_allowed"])
        self.assertFalse(raw["raw_alignment_complete"])
        self.assertEqual(
            raw["remediation_status"],
            "container_mismatch_business_shape_match_private_only_owner_identity_decision_required",
        )

        boundary = validated["raw_boundary"]
        self.assertTrue(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertTrue(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertTrue(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertTrue(boundary["raw_inbox_hash_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])
        self.assertTrue(boundary["raw_root_stat_unchanged_after_scan"])
        self.assertTrue(boundary["selected_source_stat_unchanged_after_scan"])

        public_safety = validated["public_repo_safety"]
        self.assertTrue(public_safety["public_safe_aggregate_only"])
        self.assertFalse(public_safety["raw_filenames_committed"])
        self.assertFalse(public_safety["raw_hashes_committed"])
        self.assertFalse(public_safety["zip_member_names_committed"])
        self.assertFalse(public_safety["field_or_header_plaintext_committed"])
        self.assertFalse(public_safety["row_or_cell_values_committed"])
        self.assertFalse(public_safety["business_values_committed"])

        go_no_go = validated["go_no_go"]
        self.assertEqual(go_no_go["decision"], "NO_GO")
        self.assertIn("RAW_CONTAINER_HASH_SIZE_MISMATCH", go_no_go["blocker_ids"])
        self.assertIn("RAW_SOURCE_IDENTITY_OWNER_DECISION_REQUIRED", go_no_go["blocker_ids"])
        self.assertFalse(go_no_go["github_upload_allowed"])
        self.assertFalse(go_no_go["app_reinstall_allowed"])
        self.assertFalse(go_no_go["formal_report_allowed"])
        self.assertFalse(go_no_go["business_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
