import unittest

from KMFA.tools.check_v014_s12_p1_manual_resolution_events import (
    validate_v014_s12_p1_manual_resolution_events,
)
from KMFA.tools.v014_s12_p1_manual_resolution_events import generate


class V014S12P1ManualResolutionEventsTests(unittest.TestCase):
    def test_locks_manual_resolution_events_without_preview_rerun_or_upload(self) -> None:
        manifest = generate()
        validated = validate_v014_s12_p1_manual_resolution_events()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S12")
        self.assertEqual(validated["phase_id"], "S12-P1")
        self.assertEqual(validated["phase_scope"], "v014_s12_p1_manual_resolution_events_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S12-P1-MANUAL-RESOLUTION-EVENTS-20260704")
        self.assertEqual(validated["completed_task_ids"], ["S12P1T01", "S12P1T02", "S12P1T03"])
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S12-P1-MANUAL-RESOLUTION-EVENTS"])

        progress = validated["stage12_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 1)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_label"], "33.33%")
        self.assertTrue(progress["s12_p1_performed"])
        self.assertFalse(progress["s12_p2_performed"])
        self.assertFalse(progress["s12_p3_performed"])
        self.assertFalse(progress["stage12_review_performed"])

        summary = validated["manual_resolution_summary"]
        self.assertEqual(summary["manual_event_count"], 5)
        self.assertEqual(summary["manual_action_kind_count"], 4)
        self.assertEqual(summary["event_type_count"], 4)
        self.assertEqual(summary["approved_event_count"], 1)
        self.assertEqual(summary["reverse_event_count"], 1)
        self.assertEqual(summary["html_export_count"], 1)
        self.assertTrue(summary["field_mapping_event_present"])
        self.assertTrue(summary["project_matching_event_present"])
        self.assertTrue(summary["difference_handling_event_present"])
        self.assertTrue(summary["note_event_present"])
        self.assertTrue(summary["approved_event_reversal_chain_present"])
        self.assertEqual(summary["formal_report_count"], 0)
        self.assertEqual(summary["business_decision_basis_count"], 0)

        baseline = validated["v14_html_uiux_baseline"]
        self.assertTrue(baseline["taskpack_html_requirement_read"])
        self.assertTrue(baseline["human_flow_entry_exists"])
        self.assertTrue(baseline["human_flow_audit_script_exists"])
        self.assertTrue(baseline["human_flow_audit_report_exists"])
        self.assertEqual(baseline["audit_file_count"], 6)
        self.assertEqual(baseline["audit_control_row_count"], 54)
        self.assertEqual(baseline["audit_pass_count"], 54)
        self.assertEqual(baseline["audit_warn_count"], 0)
        self.assertEqual(baseline["audit_fail_count"], 0)
        self.assertTrue(baseline["implementation_reflects_manual_resolution_workbench"])
        self.assertTrue(baseline["implementation_reflects_visible_feedback"])
        self.assertTrue(baseline["implementation_reflects_no_raw_mutation"])

        upload = validated["github_upload"]
        self.assertFalse(upload["github_upload_performed"])
        self.assertFalse(upload["github_upload_ready_next_gate"])
        self.assertTrue(upload["github_upload_deferred_until_v014_stage1_18_complete"])

        raw_boundary = validated["raw_data_boundary"]
        self.assertFalse(raw_boundary["raw_inbox_read_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_listed_by_this_phase"])
        self.assertFalse(raw_boundary["raw_inbox_mutated_by_this_phase"])

        quality = validated["quality_gate"]
        self.assertFalse(quality["impact_preview_publish_allowed"])
        self.assertFalse(quality["derived_rerun_allowed"])
        self.assertFalse(quality["formal_report_allowed"])
        self.assertFalse(quality["business_decision_basis_allowed"])
        self.assertFalse(quality["business_execution_allowed"])
        self.assertFalse(quality["stage12_review_allowed"])
        self.assertFalse(quality["github_upload_allowed"])


if __name__ == "__main__":
    unittest.main()
