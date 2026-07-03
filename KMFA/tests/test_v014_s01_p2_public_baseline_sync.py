import unittest

from KMFA.tools.check_v014_s01_p2_public_baseline_sync import (
    validate_v014_s01_p2_public_baseline_sync,
)


class TestV014S01P2PublicBaselineSync(unittest.TestCase):
    def test_v14_s01_p2_syncs_public_baseline_without_raw_or_upload(self) -> None:
        result = validate_v014_s01_p2_public_baseline_sync()

        self.assertEqual(result["schema_version"], "kmfa.v014_s01_p2_public_baseline_sync.v1")
        self.assertEqual(result["version"], "0.1.4")
        self.assertEqual(result["stage_phase"], "S01-P2")
        self.assertEqual(result["status"], "completed_validated_local_only_no_go_upload_deferred")
        self.assertEqual(result["dependency"]["required_phase"], "S01-P1")
        self.assertTrue(result["phase_scope"]["current_phase_only"])
        self.assertFalse(result["phase_scope"]["business_code_modified"])
        self.assertFalse(result["phase_scope"]["product_runtime_modified"])
        self.assertFalse(result["phase_scope"]["s01_p3_started"])
        self.assertFalse(result["phase_scope"]["stage_review_performed"])
        self.assertFalse(result["phase_scope"]["github_upload_performed"])
        self.assertEqual(result["phase_scope"]["next_phase"], "S01-P3")
        self.assertFalse(result["phase_scope"]["next_phase_started"])

        baseline = result["baseline_sync"]
        self.assertEqual(baseline["copied_public_source_count"], 9)
        self.assertFalse(baseline["zip_internal_entry_names_committed"])
        self.assertFalse(baseline["raw_payload_extracted"])
        self.assertEqual(len(baseline["selected_public_sources"]), 9)

        gates = result["v14_gates"]
        self.assertEqual(gates["raw_data_root"], "/Users/linzezhang/Downloads/KMFA_MetaData")
        self.assertEqual(gates["raw_data_root_mode"], "read_only")
        self.assertEqual(gates["html_audit_pass"], 54)
        self.assertEqual(gates["html_audit_warn"], 0)
        self.assertEqual(gates["html_audit_fail"], 0)
        self.assertEqual(
            gates["quality_over_time_rule"],
            "quality_gate_passed_can_finish_early_quality_gate_failed_blocks_delivery",
        )

        boundary = result["raw_data_boundary"]
        self.assertFalse(boundary["raw_inbox_read_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_listed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_modified_by_this_phase"])
        self.assertFalse(boundary["raw_payload_extracted_from_delivery_zip"])
        self.assertFalse(boundary["raw_private_entry_names_committed"])
        self.assertFalse(boundary["raw_filenames_committed"])
        self.assertFalse(boundary["field_or_header_plaintext_committed"])
        self.assertFalse(boundary["business_values_committed"])

        self.assertFalse(result["release_state"]["delivery_allowed"])
        self.assertFalse(result["release_state"]["formal_report_allowed"])
        self.assertFalse(result["release_state"]["business_execution_allowed"])
        self.assertEqual(result["release_state"]["current_report_grade"], "D")


if __name__ == "__main__":
    unittest.main()
