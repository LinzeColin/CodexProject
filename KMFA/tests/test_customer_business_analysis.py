import json
import unittest

from KMFA.tools.customer_business_analysis import (
    REQUIRED_ANALYSIS_DIMENSIONS,
    REQUIRED_EXCEPTION_TYPES,
    REQUIRED_SOURCE_LANES,
    CustomerBusinessAnalysisError,
    build_default_customer_business_analysis,
    validate_customer_business_analysis_artifacts,
)


class CustomerBusinessAnalysisTests(unittest.TestCase):
    def test_default_runtime_covers_s16_p3_required_scope(self) -> None:
        manifest, source_lanes, customer_summaries, exception_items = build_default_customer_business_analysis(
            generated_at="2026-07-01T23:40:00+10:00"
        )
        validate_customer_business_analysis_artifacts(
            manifest,
            source_lanes,
            customer_summaries,
            exception_items,
        )

        self.assertEqual(manifest["stage_phase"], "S16-P3")
        self.assertEqual(tuple(manifest["required_analysis_dimensions"]), REQUIRED_ANALYSIS_DIMENSIONS)
        self.assertEqual(tuple(manifest["required_source_lanes"]), REQUIRED_SOURCE_LANES)
        self.assertEqual(tuple(manifest["required_exception_types"]), REQUIRED_EXCEPTION_TYPES)
        self.assertEqual(manifest["summary"]["source_lane_count"], 5)
        self.assertEqual(manifest["summary"]["customer_summary_count"], 4)
        self.assertEqual(manifest["summary"]["exception_item_count"], 4)
        self.assertEqual(manifest["summary"]["report_grade_visible"], "D")
        self.assertEqual(manifest["quality_gate"]["pending_reconciliation_count"], 12)
        self.assertTrue(manifest["quality_gate"]["customer_operating_summary_allowed"])
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["business_decision_basis_allowed"])
        self.assertFalse(manifest["quality_gate"]["collection_action_allowed"])
        self.assertFalse(manifest["quality_gate"]["legal_collection_decision_allowed"])
        self.assertFalse(manifest["quality_gate"]["payment_execution_allowed"])
        self.assertFalse(manifest["quality_gate"]["bank_operation_allowed"])
        self.assertFalse(manifest["stage_scope"]["stage16_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["github_upload_scope_included"])

    def test_source_lanes_cover_customer_margin_collection_aging_and_lifecycle(self) -> None:
        manifest, source_lanes, customer_summaries, exception_items = build_default_customer_business_analysis(
            generated_at="2026-07-01T23:40:00+10:00"
        )
        validate_customer_business_analysis_artifacts(
            manifest,
            source_lanes,
            customer_summaries,
            exception_items,
        )

        lanes = {lane["lane_id"]: lane for lane in source_lanes}
        self.assertEqual(set(lanes), set(REQUIRED_SOURCE_LANES))
        for lane_id in REQUIRED_SOURCE_LANES:
            lane = lanes[lane_id]
            self.assertEqual(lane["record_type"], "customer_analysis_source_lane")
            self.assertTrue(lane["all_sources_readonly"])
            self.assertGreaterEqual(lane["source_count"], 1)
            self.assertFalse(lane["raw_business_values_allowed"])
            self.assertFalse(lane["public_amount_values_allowed"])
            self.assertFalse(lane["field_plaintext_allowed"])
            self.assertFalse(lane["collection_action_allowed"])
            self.assertFalse(lane["legal_collection_decision_allowed"])

    def test_customer_summaries_include_required_public_safe_dimensions(self) -> None:
        manifest, source_lanes, customer_summaries, exception_items = build_default_customer_business_analysis(
            generated_at="2026-07-01T23:40:00+10:00"
        )
        validate_customer_business_analysis_artifacts(
            manifest,
            source_lanes,
            customer_summaries,
            exception_items,
        )

        self.assertEqual(len(customer_summaries), 4)
        for record in customer_summaries:
            self.assertEqual(record["record_type"], "customer_operating_summary")
            self.assertEqual(set(record["dimension_signal_refs"]), set(REQUIRED_ANALYSIS_DIMENSIONS))
            self.assertTrue(record["manual_review_required"])
            self.assertEqual(record["summary_status"], "review_only_not_business_decision_basis")
            self.assertFalse(record["formal_report_allowed"])
            self.assertFalse(record["business_decision_basis_allowed"])
            self.assertFalse(record["contains_customer_name_plaintext"])
            self.assertFalse(record["contains_project_name_plaintext"])
            self.assertFalse(record["collection_action_allowed"])
            self.assertFalse(record["legal_collection_decision_allowed"])

    def test_exception_items_are_review_only_and_cover_required_risks(self) -> None:
        manifest, source_lanes, customer_summaries, exception_items = build_default_customer_business_analysis(
            generated_at="2026-07-01T23:40:00+10:00"
        )
        validate_customer_business_analysis_artifacts(
            manifest,
            source_lanes,
            customer_summaries,
            exception_items,
        )

        self.assertEqual({item["exception_type"] for item in exception_items}, set(REQUIRED_EXCEPTION_TYPES))
        for item in exception_items:
            self.assertEqual(item["record_type"], "customer_analysis_exception_item")
            self.assertTrue(item["manual_review_required"])
            self.assertEqual(item["candidate_status"], "review_only_pending_owner_or_authorized_confirmation")
            self.assertFalse(item["auto_contact_allowed"])
            self.assertFalse(item["auto_legal_decision_allowed"])
            self.assertFalse(item["collection_action_allowed"])
            self.assertFalse(item["legal_collection_decision_allowed"])
            self.assertFalse(item["business_decision_basis_allowed"])

    def test_public_payload_has_no_raw_private_files_values_or_credentials(self) -> None:
        manifest, source_lanes, customer_summaries, exception_items = build_default_customer_business_analysis(
            generated_at="2026-07-01T23:40:00+10:00"
        )
        payload = json.dumps(
            [manifest, source_lanes, customer_summaries, exception_items],
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

    def test_validator_rejects_collection_legal_or_review_upload_scope(self) -> None:
        manifest, source_lanes, customer_summaries, exception_items = build_default_customer_business_analysis(
            generated_at="2026-07-01T23:40:00+10:00"
        )

        broken_manifest = dict(manifest)
        broken_manifest["quality_gate"] = dict(manifest["quality_gate"])
        broken_manifest["quality_gate"]["collection_action_allowed"] = True
        with self.assertRaises(CustomerBusinessAnalysisError):
            validate_customer_business_analysis_artifacts(
                broken_manifest,
                source_lanes,
                customer_summaries,
                exception_items,
            )

        broken_manifest = dict(manifest)
        broken_manifest["quality_gate"] = dict(manifest["quality_gate"])
        broken_manifest["quality_gate"]["legal_collection_decision_allowed"] = True
        with self.assertRaises(CustomerBusinessAnalysisError):
            validate_customer_business_analysis_artifacts(
                broken_manifest,
                source_lanes,
                customer_summaries,
                exception_items,
            )

        broken_manifest = dict(manifest)
        broken_manifest["stage_scope"] = dict(manifest["stage_scope"])
        broken_manifest["stage_scope"]["stage16_review_scope_included"] = True
        with self.assertRaises(CustomerBusinessAnalysisError):
            validate_customer_business_analysis_artifacts(
                broken_manifest,
                source_lanes,
                customer_summaries,
                exception_items,
            )

        broken_manifest = dict(manifest)
        broken_manifest["stage_scope"] = dict(manifest["stage_scope"])
        broken_manifest["stage_scope"]["github_upload_scope_included"] = True
        with self.assertRaises(CustomerBusinessAnalysisError):
            validate_customer_business_analysis_artifacts(
                broken_manifest,
                source_lanes,
                customer_summaries,
                exception_items,
            )


if __name__ == "__main__":
    unittest.main()
