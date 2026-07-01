import json
import unittest

from KMFA.tools.project_status_lifecycle import (
    REQUIRED_EXCEPTION_TYPES,
    REQUIRED_HANDOFF_GUARDS,
    REQUIRED_LIFECYCLE_STATES,
    REQUIRED_SOURCE_LANES,
    ProjectStatusLifecycleError,
    build_default_project_status_lifecycle,
    validate_project_status_lifecycle_artifacts,
)


class ProjectStatusLifecycleTests(unittest.TestCase):
    def test_default_runtime_covers_s16_p2_required_scope(self) -> None:
        manifest, source_lanes, lifecycle_records, exception_items, handoff_guards = (
            build_default_project_status_lifecycle(generated_at="2026-07-01T23:30:00+10:00")
        )
        validate_project_status_lifecycle_artifacts(
            manifest,
            source_lanes,
            lifecycle_records,
            exception_items,
            handoff_guards,
        )

        self.assertEqual(manifest["stage_phase"], "S16-P2")
        self.assertEqual(tuple(manifest["required_source_lanes"]), REQUIRED_SOURCE_LANES)
        self.assertEqual(tuple(manifest["required_lifecycle_states"]), REQUIRED_LIFECYCLE_STATES)
        self.assertEqual(tuple(manifest["required_exception_types"]), REQUIRED_EXCEPTION_TYPES)
        self.assertEqual(tuple(manifest["required_handoff_guards"]), REQUIRED_HANDOFF_GUARDS)
        self.assertEqual(manifest["summary"]["source_lane_count"], 6)
        self.assertEqual(manifest["summary"]["lifecycle_record_count"], 4)
        self.assertEqual(manifest["summary"]["exception_item_count"], 3)
        self.assertEqual(manifest["summary"]["handoff_guard_count"], 3)
        self.assertEqual(manifest["summary"]["report_grade_visible"], "D")
        self.assertEqual(manifest["quality_gate"]["pending_reconciliation_count"], 12)
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["business_decision_basis_allowed"])
        self.assertFalse(manifest["quality_gate"]["site_construction_instruction_allowed"])
        self.assertFalse(manifest["quality_gate"]["safety_signature_allowed"])
        self.assertFalse(manifest["quality_gate"]["technical_acceptance_signature_allowed"])
        self.assertFalse(manifest["quality_gate"]["invoice_issuance_allowed"])
        self.assertFalse(manifest["quality_gate"]["collection_action_allowed"])
        self.assertFalse(manifest["stage_scope"]["s16_p1_scope_included"])
        self.assertTrue(manifest["stage_scope"]["s16_p2_project_status_scope_included"])
        self.assertFalse(manifest["stage_scope"]["s16_p3_scope_included"])
        self.assertFalse(manifest["stage_scope"]["stage16_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["github_upload_scope_included"])

    def test_source_lanes_cover_production_start_completion_settlement_invoice_collection(self) -> None:
        manifest, source_lanes, lifecycle_records, exception_items, handoff_guards = (
            build_default_project_status_lifecycle(generated_at="2026-07-01T23:30:00+10:00")
        )
        validate_project_status_lifecycle_artifacts(
            manifest,
            source_lanes,
            lifecycle_records,
            exception_items,
            handoff_guards,
        )

        lanes = {lane["lane_id"]: lane for lane in source_lanes}
        self.assertEqual(set(lanes), set(REQUIRED_SOURCE_LANES))
        for lane_id in REQUIRED_SOURCE_LANES:
            lane = lanes[lane_id]
            self.assertEqual(lane["record_type"], "project_status_source_lane")
            self.assertTrue(lane["all_sources_readonly"])
            self.assertGreaterEqual(lane["field_mapping_count"], 1)
            self.assertFalse(lane["raw_business_values_allowed"])
            self.assertFalse(lane["public_amount_values_allowed"])
            self.assertFalse(lane["field_plaintext_allowed"])
            self.assertFalse(lane["site_operation_allowed"])
            self.assertFalse(lane["signature_authority_allowed"])

    def test_lifecycle_records_include_required_public_safe_states(self) -> None:
        manifest, source_lanes, lifecycle_records, exception_items, handoff_guards = (
            build_default_project_status_lifecycle(generated_at="2026-07-01T23:30:00+10:00")
        )
        validate_project_status_lifecycle_artifacts(
            manifest,
            source_lanes,
            lifecycle_records,
            exception_items,
            handoff_guards,
        )

        states = [record["lifecycle_state"] for record in lifecycle_records]
        self.assertEqual(set(states), set(REQUIRED_LIFECYCLE_STATES))
        for record in lifecycle_records:
            self.assertEqual(record["record_type"], "project_lifecycle_record")
            self.assertTrue(record["manual_review_required"])
            self.assertFalse(record["raw_business_values_allowed"])
            self.assertFalse(record["contains_project_name_plaintext"])
            self.assertFalse(record["contains_customer_name_plaintext"])
            self.assertFalse(record["site_construction_instruction_allowed"])
            self.assertFalse(record["safety_signature_allowed"])
            self.assertFalse(record["technical_acceptance_signature_allowed"])
            self.assertFalse(record["business_decision_basis_allowed"])

    def test_exception_items_are_review_only_for_required_lifecycle_anomalies(self) -> None:
        manifest, source_lanes, lifecycle_records, exception_items, handoff_guards = (
            build_default_project_status_lifecycle(generated_at="2026-07-01T23:30:00+10:00")
        )
        validate_project_status_lifecycle_artifacts(
            manifest,
            source_lanes,
            lifecycle_records,
            exception_items,
            handoff_guards,
        )

        self.assertEqual({item["exception_type"] for item in exception_items}, set(REQUIRED_EXCEPTION_TYPES))
        for item in exception_items:
            self.assertEqual(item["record_type"], "project_lifecycle_exception_item")
            self.assertTrue(item["manual_review_required"])
            self.assertEqual(item["candidate_status"], "review_only_pending_owner_or_authorized_confirmation")
            self.assertFalse(item["auto_close_allowed"])
            self.assertFalse(item["invoice_issuance_allowed"])
            self.assertFalse(item["collection_action_allowed"])
            self.assertFalse(item["site_operation_allowed"])
            self.assertFalse(item["business_decision_basis_allowed"])

    def test_handoff_guards_block_site_safety_and_technical_signatures(self) -> None:
        manifest, source_lanes, lifecycle_records, exception_items, handoff_guards = (
            build_default_project_status_lifecycle(generated_at="2026-07-01T23:30:00+10:00")
        )
        validate_project_status_lifecycle_artifacts(
            manifest,
            source_lanes,
            lifecycle_records,
            exception_items,
            handoff_guards,
        )

        guard_ids = {guard["guard_id"] for guard in handoff_guards}
        self.assertEqual(guard_ids, set(REQUIRED_HANDOFF_GUARDS))
        for guard in handoff_guards:
            self.assertEqual(guard["record_type"], "project_lifecycle_handoff_guard")
            self.assertFalse(guard["delegated_to_system"])
            self.assertFalse(guard["signature_authority_allowed"])
            self.assertFalse(guard["operation_execution_allowed"])
            self.assertEqual(guard["required_actor"], "human_authorized_owner_or_site_role")

    def test_public_payload_has_no_raw_private_files_values_or_credentials(self) -> None:
        manifest, source_lanes, lifecycle_records, exception_items, handoff_guards = (
            build_default_project_status_lifecycle(generated_at="2026-07-01T23:30:00+10:00")
        )
        payload = json.dumps(
            [manifest, source_lanes, lifecycle_records, exception_items, handoff_guards],
            ensure_ascii=False,
            sort_keys=True,
        )

        for forbidden_text in (
            '"amount_cents":',
            '"amount_yuan":',
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
            "private://",
            "private_ref://",
            ".zip",
            ".xlsx",
            ".xls",
            ".pdf",
            ".sqlite",
            ".db",
            "bank_account_number",
            "account_number",
            "identity_document_number",
            '"project_name_plaintext":',
            '"customer_name_plaintext":',
            "password",
            "token",
            "api_key",
            "private_key",
        ):
            self.assertNotIn(forbidden_text, payload)

    def test_validator_rejects_execution_signature_or_later_phase_scope(self) -> None:
        manifest, source_lanes, lifecycle_records, exception_items, handoff_guards = (
            build_default_project_status_lifecycle(generated_at="2026-07-01T23:30:00+10:00")
        )

        broken_manifest = dict(manifest)
        broken_manifest["quality_gate"] = dict(manifest["quality_gate"])
        broken_manifest["quality_gate"]["safety_signature_allowed"] = True
        with self.assertRaises(ProjectStatusLifecycleError):
            validate_project_status_lifecycle_artifacts(
                broken_manifest,
                source_lanes,
                lifecycle_records,
                exception_items,
                handoff_guards,
            )

        broken_manifest = dict(manifest)
        broken_manifest["stage_scope"] = dict(manifest["stage_scope"])
        broken_manifest["stage_scope"]["s16_p3_scope_included"] = True
        with self.assertRaises(ProjectStatusLifecycleError):
            validate_project_status_lifecycle_artifacts(
                broken_manifest,
                source_lanes,
                lifecycle_records,
                exception_items,
                handoff_guards,
            )

        broken_manifest = dict(manifest)
        broken_manifest["stage_scope"] = dict(manifest["stage_scope"])
        broken_manifest["stage_scope"]["github_upload_scope_included"] = True
        with self.assertRaises(ProjectStatusLifecycleError):
            validate_project_status_lifecycle_artifacts(
                broken_manifest,
                source_lanes,
                lifecycle_records,
                exception_items,
                handoff_guards,
            )


if __name__ == "__main__":
    unittest.main()
