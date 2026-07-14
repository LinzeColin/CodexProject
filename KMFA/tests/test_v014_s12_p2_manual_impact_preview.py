import unittest

from KMFA.tools.check_v014_s12_p2_manual_impact_preview import (
    validate_v014_s12_p2_manual_impact_preview,
)
from KMFA.tools.v014_s12_p2_manual_impact_preview import generate


class V014S12P2ManualImpactPreviewTests(unittest.TestCase):
    def test_locks_manual_impact_preview_without_rerun_review_or_upload(self) -> None:
        manifest = generate()
        validated = validate_v014_s12_p2_manual_impact_preview()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S12")
        self.assertEqual(validated["phase_id"], "S12-P2")
        self.assertEqual(validated["phase_scope"], "v014_s12_p2_manual_impact_preview_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S12-P2-MANUAL-IMPACT-PREVIEW-20260705")
        self.assertEqual(validated["completed_task_ids"], ["S12P2T01", "S12P2T02", "S12P2T03"])
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S12-P2-MANUAL-IMPACT-PREVIEW"])

        progress = validated["stage12_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 2)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_label"], "66.67%")
        self.assertTrue(progress["s12_p1_performed"])
        self.assertTrue(progress["s12_p2_performed"])
        self.assertFalse(progress["s12_p3_performed"])
        self.assertFalse(progress["stage12_review_performed"])

        summary = validated["manual_impact_preview_summary"]
        self.assertEqual(summary["source_event_count"], 5)
        self.assertEqual(summary["impact_preview_count"], 5)
        self.assertEqual(summary["affected_project_count"], 8)
        self.assertEqual(summary["affected_metric_count"], 11)
        self.assertEqual(summary["affected_report_count"], 5)
        self.assertEqual(summary["high_risk_count"], 3)
        self.assertEqual(summary["second_confirmation_required_count"], 3)
        self.assertEqual(summary["blocked_publish_count"], 3)
        self.assertEqual(summary["publish_allowed_count"], 2)
        self.assertEqual(summary["derived_rerun_count"], 0)
        self.assertEqual(summary["formal_report_count"], 0)
        self.assertEqual(summary["business_decision_basis_count"], 0)

        baseline = validated["v14_html_uiux_baseline"]
        self.assertTrue(baseline["taskpack_html_requirement_read"])
        self.assertEqual(baseline["audit_file_count"], 6)
        self.assertEqual(baseline["audit_control_row_count"], 54)
        self.assertEqual(baseline["audit_pass_count"], 54)
        self.assertEqual(baseline["audit_warn_count"], 0)
        self.assertEqual(baseline["audit_fail_count"], 0)
        self.assertTrue(baseline["implementation_reflects_impact_preview"])
        self.assertTrue(baseline["implementation_reflects_second_confirmation_feedback"])
        self.assertTrue(baseline["implementation_reflects_no_raw_mutation"])

        quality = validated["quality_gate"]
        self.assertTrue(quality["impact_preview_generation_allowed"])
        self.assertTrue(quality["impact_preview_required_before_publish"])
        self.assertTrue(quality["high_risk_second_confirmation_required"])
        self.assertFalse(quality["unpassed_preview_publish_allowed"])
        self.assertFalse(quality["derived_rerun_allowed"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])
        self.assertFalse(quality["stage12_review_allowed"])
        self.assertFalse(quality["github_upload_allowed"])

        upload = validated["github_upload"]
        self.assertFalse(upload["github_upload_performed"])
        self.assertFalse(upload["github_upload_ready_next_gate"])
        self.assertTrue(upload["github_upload_deferred_until_v014_stage1_18_complete"])

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["raw_inbox_read_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_listed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_phase"])


if __name__ == "__main__":
    unittest.main()
