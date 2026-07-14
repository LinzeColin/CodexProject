import json
import unittest

from KMFA.tools.check_v014_s12_p3_manual_rerun_mechanism import (
    validate_v014_s12_p3_manual_rerun_mechanism,
)
from KMFA.tools.v014_s12_p3_manual_rerun_mechanism import REQUIRED_RERUN_CHAIN, generate


class V014S12P3ManualRerunMechanismTests(unittest.TestCase):
    def test_locks_manual_rerun_mechanism_without_review_upload_or_raw_access(self) -> None:
        manifest = generate()
        validated = validate_v014_s12_p3_manual_rerun_mechanism()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S12")
        self.assertEqual(validated["phase_id"], "S12-P3")
        self.assertEqual(validated["phase_scope"], "v014_s12_p3_manual_rerun_mechanism_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S12-P3-MANUAL-RERUN-MECHANISM-20260705")
        self.assertEqual(
            validated["completed_task_ids"],
            ["S12P1T01", "S12P1T02", "S12P1T03", "S12P2T01", "S12P2T02", "S12P2T03", "S12P3T01", "S12P3T02", "S12P3T03"],
        )
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S12-P3-MANUAL-RERUN-MECHANISM"])

        progress = validated["stage12_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 3)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_label"], "100.00%")
        self.assertTrue(progress["s12_p1_performed"])
        self.assertTrue(progress["s12_p2_performed"])
        self.assertTrue(progress["s12_p3_performed"])
        self.assertFalse(progress["stage12_review_performed"])

        summary = validated["manual_rerun_summary"]
        self.assertEqual(summary["source_preview_count"], 5)
        self.assertEqual(summary["eligible_event_count"], 2)
        self.assertEqual(summary["blocked_preview_count"], 3)
        self.assertEqual(summary["cache_invalidation_count"], 2)
        self.assertEqual(summary["rerun_step_count"], 8)
        self.assertEqual(summary["same_source_consistency_check_count"], 2)
        self.assertEqual(summary["rerun_chain_layer_count"], 4)
        self.assertEqual(summary["old_version_retained_count"], 8)
        self.assertEqual(summary["new_version_appended_count"], 8)
        self.assertEqual(summary["raw_layer_write_count"], 0)
        self.assertEqual(summary["formal_report_count"], 0)
        self.assertEqual(summary["business_decision_basis_count"], 0)

        self.assertEqual(tuple(validated["required_rerun_chain"]), REQUIRED_RERUN_CHAIN)
        self.assertEqual(tuple(validated["required_rerun_chain"]), ("field_mapping", "fact_layer", "derived_metric", "report_reference"))

        quality = validated["quality_gate"]
        self.assertTrue(quality["derived_cache_invalidation_allowed"])
        self.assertTrue(quality["derived_rerun_allowed"])
        self.assertTrue(quality["same_source_consistency_check_required"])
        self.assertFalse(quality["blocked_preview_rerun_allowed"])
        self.assertFalse(quality["old_version_overwrite_allowed"])
        self.assertFalse(quality["raw_layer_write_allowed"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])
        self.assertFalse(quality["stage12_review_allowed"])
        self.assertFalse(quality["github_upload_allowed"])

        records = validated["record_counts"]
        self.assertEqual(records["invalidations"], 2)
        self.assertEqual(records["rerun_steps"], 8)
        self.assertEqual(records["consistency_checks"], 2)

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["raw_inbox_read_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_listed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_stat_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_hashed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_phase"])

        upload = validated["github_upload"]
        self.assertFalse(upload["github_upload_performed"])
        self.assertFalse(upload["github_upload_ready_next_gate"])
        self.assertTrue(upload["github_upload_deferred_until_v014_stage1_18_complete"])

        payload = json.dumps(validated, ensure_ascii=False, sort_keys=True)
        for forbidden in (
            "private_ref://",
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
            ".zip",
            ".xlsx",
            ".xls",
            ".pdf",
            ".sqlite",
            ".db",
            "api_key",
            "private_key",
            "password",
            "/Users/linzezhang/Downloads",
            "KMFA_MetaData",
        ):
            self.assertNotIn(forbidden, payload)


if __name__ == "__main__":
    unittest.main()
