import json
import unittest

from KMFA.tools.check_v014_s17_p3_operations_sop import (
    validate_v014_s17_p3_operations_sop,
)
from KMFA.tools.v014_s17_p3_operations_sop import (
    REQUIRED_V014_DRILL_TYPES,
    REQUIRED_V014_KNOWLEDGE_ITEM_TYPES,
    REQUIRED_V014_RUNBOOK_TYPES,
    generate,
)


class V014S17P3OperationsSopTests(unittest.TestCase):
    def test_v014_s17_p3_locks_public_safe_operations_sop_only(self) -> None:
        manifest = generate(generated_at="2026-07-05T15:20:00+10:00")
        validated = validate_v014_s17_p3_operations_sop()

        self.assertEqual(manifest, validated)
        self.assertEqual(validated["schema_version"], "kmfa.v014_s17_p3_operations_sop.v1")
        self.assertEqual(validated["project_id"], "KMFA")
        self.assertEqual(validated["version"], "0.1.4")
        self.assertEqual(validated["stage_id"], "S17")
        self.assertEqual(validated["phase_id"], "S17-P3")
        self.assertEqual(validated["phase_scope"], "v014_s17_p3_operations_sop_only")
        self.assertEqual(validated["task_id"], "KMFA-V014-S17-P3-OPERATIONS-SOP-20260705")
        self.assertEqual(validated["acceptance_ids"], ["ACC-V014-S17-P3-OPERATIONS-SOP"])
        self.assertEqual(validated["completed_task_ids"], ["S17P3T01", "S17P3T02", "S17P3T03"])

        self.assertTrue(validated["s17_p2_dependency_validated"])
        self.assertTrue(validated["historical_s17_p3_public_safe_baseline_validated"])
        self.assertEqual(
            validated["historical_s17_p3_policy_version"],
            "KMFA-S17P3-OPERATIONS-SOP-PUBLIC-SAFE-001",
        )
        self.assertEqual(tuple(validated["required_runbook_types"]), REQUIRED_V014_RUNBOOK_TYPES)
        self.assertEqual(tuple(validated["required_knowledge_item_types"]), REQUIRED_V014_KNOWLEDGE_ITEM_TYPES)
        self.assertEqual(tuple(validated["required_drill_types"]), REQUIRED_V014_DRILL_TYPES)

        progress = validated["stage17_phase_progress"]
        self.assertEqual(progress["completed_phase_count"], 3)
        self.assertEqual(progress["total_phase_count"], 3)
        self.assertEqual(progress["derived_percent_bps"], 10000)
        self.assertEqual(progress["derived_percent_label"], "100.00%")
        self.assertTrue(progress["s17_p1_performed"])
        self.assertTrue(progress["s17_p2_performed"])
        self.assertTrue(progress["s17_p3_performed"])
        self.assertFalse(progress["stage17_review_performed"])

        summary = validated["operations_sop_summary"]
        self.assertEqual(summary["operation_runbook_count"], 4)
        self.assertEqual(summary["knowledge_item_count"], 2)
        self.assertEqual(summary["drill_log_count"], 2)
        self.assertEqual(summary["runbook_type_count"], 4)
        self.assertEqual(summary["knowledge_item_type_count"], 2)
        self.assertEqual(summary["drill_type_count"], 2)
        self.assertEqual(summary["production_restore_count"], 0)
        self.assertEqual(summary["external_service_call_count"], 0)
        self.assertEqual(summary["live_connector_call_count"], 0)
        self.assertEqual(summary["business_execution_count"], 0)
        self.assertEqual(summary["raw_inbox_access_count"], 0)
        self.assertEqual(summary["report_grade_visible"], "D")

        quality = validated["quality_gate"]
        for key in (
            "operation_runbooks_complete",
            "finance_sop_indexed",
            "handoff_materials_indexed",
            "error_handling_drill_recorded",
            "backup_recovery_drill_recorded",
            "metadata_only",
            "manual_execution_only",
        ):
            self.assertTrue(quality[key], key)
        for key in (
            "raw_payload_allowed",
            "private_document_allowed",
            "live_connector_allowed",
            "external_service_call_allowed",
            "production_restore_allowed",
            "formal_report_allowed",
            "full_report_email_allowed",
            "business_decision_basis_allowed",
            "business_execution_allowed",
            "stage17_review_allowed",
            "github_upload_allowed",
        ):
            self.assertFalse(quality[key], key)

        boundaries = validated["phase_boundaries"]
        self.assertTrue(boundaries["s17_p2_dependency_reused"])
        self.assertTrue(boundaries["legacy_s17_p3_public_safe_baseline_reused"])
        self.assertTrue(boundaries["s17_p3_operations_scope_included"])
        for key in (
            "stage17_review_scope_included",
            "github_upload_scope_included",
            "production_restore_scope_included",
            "external_connector_scope_included",
            "formal_report_runtime_scope_included",
            "business_execution_scope_included",
            "raw_inbox_access_scope_included",
        ):
            self.assertFalse(boundaries[key], key)

        payload = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
        for forbidden in (
            "original_filename",
            "source_header_text",
            "private_ref://",
            "actual_package_sha256",
            "report_attachment_path",
            "credential_payload",
            "production_restore_executed\": true",
            "external_service_called\": true",
        ):
            self.assertNotIn(forbidden, payload)

        self.assertFalse(validated["github_upload"]["github_upload_performed"])
        self.assertTrue(validated["github_upload"]["github_upload_deferred_until_v014_stage1_18_complete"])
        self.assertEqual(validated["next_phase"], "S17_STAGE_REVIEW")


if __name__ == "__main__":
    unittest.main()
