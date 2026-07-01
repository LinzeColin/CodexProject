import copy
import json
import unittest

from KMFA.tools.operations_sop import (
    REQUIRED_DRILL_TYPES,
    REQUIRED_KNOWLEDGE_ITEM_TYPES,
    REQUIRED_RUNBOOK_TYPES,
    OperationsSopError,
    build_default_operations_sop,
    validate_operations_sop_artifacts,
)


class OperationsSopTests(unittest.TestCase):
    def test_default_runtime_covers_s17_p3_required_scope(self) -> None:
        manifest, runbooks, knowledge_items, drill_logs = build_default_operations_sop(
            generated_at="2026-07-01T23:59:30+10:00"
        )
        validate_operations_sop_artifacts(manifest, runbooks, knowledge_items, drill_logs)

        self.assertEqual(manifest["stage_phase"], "S17-P3")
        self.assertEqual(tuple(manifest["required_runbook_types"]), REQUIRED_RUNBOOK_TYPES)
        self.assertEqual(tuple(manifest["required_knowledge_item_types"]), REQUIRED_KNOWLEDGE_ITEM_TYPES)
        self.assertEqual(tuple(manifest["required_drill_types"]), REQUIRED_DRILL_TYPES)
        self.assertEqual(manifest["summary"]["operation_runbook_count"], 4)
        self.assertEqual(manifest["summary"]["knowledge_item_count"], 2)
        self.assertEqual(manifest["summary"]["drill_log_count"], 2)
        self.assertTrue(manifest["quality_gate"]["operation_runbooks_complete"])
        self.assertTrue(manifest["quality_gate"]["finance_sop_indexed"])
        self.assertTrue(manifest["quality_gate"]["handoff_materials_indexed"])
        self.assertTrue(manifest["quality_gate"]["error_handling_drill_recorded"])
        self.assertTrue(manifest["quality_gate"]["backup_recovery_drill_recorded"])
        self.assertTrue(manifest["quality_gate"]["metadata_only"])
        self.assertTrue(manifest["quality_gate"]["manual_execution_only"])
        self.assertFalse(manifest["quality_gate"]["stage17_review_allowed"])
        self.assertFalse(manifest["quality_gate"]["github_upload_allowed"])

    def test_operation_runbooks_cover_import_review_publish_and_rollback(self) -> None:
        manifest, runbooks, knowledge_items, drill_logs = build_default_operations_sop(
            generated_at="2026-07-01T23:59:30+10:00"
        )
        validate_operations_sop_artifacts(manifest, runbooks, knowledge_items, drill_logs)

        runbooks_by_type = {row["runbook_type"]: row for row in runbooks}
        self.assertEqual(set(runbooks_by_type), set(REQUIRED_RUNBOOK_TYPES))
        for runbook_type, row in runbooks_by_type.items():
            self.assertEqual(row["record_type"], "operation_runbook")
            self.assertEqual(row["execution_mode"], "manual_sop_only")
            self.assertEqual(row["metadata_target"], "KMFA/metadata/operations/operations_runbooks.jsonl")
            self.assertTrue(row["append_only"])
            self.assertTrue(row["precheck_required"])
            self.assertTrue(row["rollback_step_ref"])
            self.assertFalse(row["raw_business_data_required"])
            self.assertFalse(row["live_connector_required"])
            self.assertFalse(row["business_execution_allowed"])
            self.assertIn(runbook_type, row["runbook_id"])

    def test_finance_sop_and_handoff_materials_are_public_safe_knowledge_index(self) -> None:
        manifest, runbooks, knowledge_items, drill_logs = build_default_operations_sop(
            generated_at="2026-07-01T23:59:30+10:00"
        )
        validate_operations_sop_artifacts(manifest, runbooks, knowledge_items, drill_logs)

        items_by_type = {row["item_type"]: row for row in knowledge_items}
        self.assertEqual(set(items_by_type), set(REQUIRED_KNOWLEDGE_ITEM_TYPES))
        for item_type, row in items_by_type.items():
            self.assertEqual(row["record_type"], "operations_knowledge_item")
            self.assertEqual(row["metadata_target"], "KMFA/metadata/operations/finance_sop_knowledge_index.jsonl")
            self.assertEqual(row["storage_mode"], "public_safe_index_only")
            self.assertTrue(row["append_only"])
            self.assertTrue(row["owner_role"])
            self.assertTrue(row["evidence_ref"])
            self.assertFalse(row["private_document_committed"])
            self.assertFalse(row["raw_business_data_committed"])
            self.assertFalse(row["credential_material_committed"])
            self.assertIn(item_type, row["knowledge_item_id"])

    def test_error_handling_and_backup_recovery_drills_are_recorded_without_live_execution(self) -> None:
        manifest, runbooks, knowledge_items, drill_logs = build_default_operations_sop(
            generated_at="2026-07-01T23:59:30+10:00"
        )
        validate_operations_sop_artifacts(manifest, runbooks, knowledge_items, drill_logs)

        drills_by_type = {row["drill_type"]: row for row in drill_logs}
        self.assertEqual(set(drills_by_type), set(REQUIRED_DRILL_TYPES))
        for drill_type, row in drills_by_type.items():
            self.assertEqual(row["record_type"], "operations_drill_log")
            self.assertEqual(row["metadata_target"], "KMFA/metadata/operations/error_backup_drill_log.jsonl")
            self.assertEqual(row["execution_mode"], "metadata_drill_only")
            self.assertEqual(row["result_status"], "simulated_passed")
            self.assertTrue(row["append_only"])
            self.assertTrue(row["recovery_evidence_ref"])
            self.assertFalse(row["production_restore_executed"])
            self.assertFalse(row["raw_business_data_required"])
            self.assertFalse(row["external_service_called"])
            self.assertIn(drill_type, row["drill_id"])

    def test_public_payload_has_no_raw_values_private_refs_reports_or_live_secrets(self) -> None:
        manifest, runbooks, knowledge_items, drill_logs = build_default_operations_sop(
            generated_at="2026-07-01T23:59:30+10:00"
        )
        payload = json.dumps([manifest, runbooks, knowledge_items, drill_logs], ensure_ascii=False, sort_keys=True)

        for forbidden_text in (
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
            "private://",
            "private_ref://",
            "bank_statement",
            "contract_full_text",
            "salary_detail",
            "tax_filing",
            "full_report_body_text",
            "complete_report_body_text",
            "report_attachment_path",
            "recipient_email",
            "smtp",
            "sk-",
            "-----BEGIN",
        ):
            self.assertNotIn(forbidden_text, payload)

    def test_validator_rejects_missing_items_raw_scope_escape_or_live_execution(self) -> None:
        manifest, runbooks, knowledge_items, drill_logs = build_default_operations_sop(
            generated_at="2026-07-01T23:59:30+10:00"
        )

        broken_runbooks = [row for row in runbooks if row["runbook_type"] != "rollback"]
        with self.assertRaises(OperationsSopError):
            validate_operations_sop_artifacts(manifest, broken_runbooks, knowledge_items, drill_logs)

        broken_knowledge = [row for row in knowledge_items if row["item_type"] != "finance_sop"]
        with self.assertRaises(OperationsSopError):
            validate_operations_sop_artifacts(manifest, runbooks, broken_knowledge, drill_logs)

        broken_drills = [row for row in drill_logs if row["drill_type"] != "backup_recovery"]
        with self.assertRaises(OperationsSopError):
            validate_operations_sop_artifacts(manifest, runbooks, knowledge_items, broken_drills)

        broken_manifest = copy.deepcopy(manifest)
        broken_manifest["quality_gate"]["github_upload_allowed"] = True
        with self.assertRaises(OperationsSopError):
            validate_operations_sop_artifacts(broken_manifest, runbooks, knowledge_items, drill_logs)

        broken_runbooks = copy.deepcopy(runbooks)
        broken_runbooks[0]["live_connector_required"] = True
        with self.assertRaises(OperationsSopError):
            validate_operations_sop_artifacts(manifest, broken_runbooks, knowledge_items, drill_logs)

        broken_drills = copy.deepcopy(drill_logs)
        broken_drills[0]["production_restore_executed"] = True
        with self.assertRaises(OperationsSopError):
            validate_operations_sop_artifacts(manifest, runbooks, knowledge_items, broken_drills)


if __name__ == "__main__":
    unittest.main()
