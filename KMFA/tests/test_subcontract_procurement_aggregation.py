import json
import unittest

from KMFA.tools.subcontract_procurement_aggregation import (
    REQUIRED_OUTPUT_RECORD_TYPES,
    REQUIRED_SOURCE_LANES,
    SubcontractProcurementAggregationError,
    build_default_subcontract_procurement_aggregation,
    validate_subcontract_procurement_artifacts,
)


class SubcontractProcurementAggregationTests(unittest.TestCase):
    def test_default_runtime_covers_s16_p1_required_scope(self) -> None:
        manifest, source_lanes, project_matches, unallocated_pool, anomaly_candidates = (
            build_default_subcontract_procurement_aggregation(generated_at="2026-07-01T23:00:00+10:00")
        )
        validate_subcontract_procurement_artifacts(
            manifest,
            source_lanes,
            project_matches,
            unallocated_pool,
            anomaly_candidates,
        )

        self.assertEqual(manifest["stage_phase"], "S16-P1")
        self.assertEqual(tuple(manifest["required_source_lanes"]), REQUIRED_SOURCE_LANES)
        self.assertEqual(tuple(manifest["required_output_record_types"]), REQUIRED_OUTPUT_RECORD_TYPES)
        self.assertEqual(manifest["summary"]["source_lane_count"], 4)
        self.assertEqual(manifest["summary"]["project_match_count"], 5)
        self.assertEqual(manifest["summary"]["unallocated_cost_pool_count"], 2)
        self.assertEqual(manifest["summary"]["anomaly_candidate_count"], 4)
        self.assertEqual(manifest["summary"]["duplicate_payment_candidate_count"], 2)
        self.assertEqual(manifest["summary"]["cross_project_cost_candidate_count"], 2)
        self.assertEqual(manifest["summary"]["report_grade_visible"], "D")
        self.assertEqual(manifest["quality_gate"]["pending_reconciliation_count"], 12)
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["business_decision_basis_allowed"])
        self.assertFalse(manifest["quality_gate"]["payment_execution_allowed"])
        self.assertFalse(manifest["quality_gate"]["bank_operation_allowed"])
        self.assertFalse(manifest["stage_scope"]["s16_p2_scope_included"])
        self.assertFalse(manifest["stage_scope"]["s16_p3_scope_included"])
        self.assertFalse(manifest["stage_scope"]["stage16_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["github_upload_scope_included"])

    def test_source_lanes_are_readonly_public_safe_structural_lanes(self) -> None:
        manifest, source_lanes, project_matches, unallocated_pool, anomaly_candidates = (
            build_default_subcontract_procurement_aggregation(generated_at="2026-07-01T23:00:00+10:00")
        )
        validate_subcontract_procurement_artifacts(
            manifest,
            source_lanes,
            project_matches,
            unallocated_pool,
            anomaly_candidates,
        )

        lane_by_id = {lane["lane_id"]: lane for lane in source_lanes}
        self.assertEqual(set(lane_by_id), set(REQUIRED_SOURCE_LANES))
        self.assertEqual(lane_by_id["subcontract_cost_ledger"]["finance_categories"], ["expense"])
        self.assertEqual(lane_by_id["procurement_register"]["finance_categories"], ["expense", "journal"])
        self.assertEqual(lane_by_id["supplier_payment_register"]["finance_categories"], ["cash", "journal"])
        self.assertEqual(lane_by_id["project_identity_bridge"]["finance_categories"], ["project"])

        for lane in source_lanes:
            self.assertEqual(lane["record_type"], "subcontract_procurement_source_lane")
            self.assertGreaterEqual(lane["field_mapping_count"], 1)
            self.assertTrue(lane["all_sources_readonly"])
            self.assertFalse(lane["raw_business_values_allowed"])
            self.assertFalse(lane["public_amount_values_allowed"])
            self.assertFalse(lane["field_plaintext_allowed"])
            self.assertFalse(lane["payment_execution_allowed"])
            self.assertFalse(lane["bank_operation_allowed"])

    def test_project_matching_and_unallocated_pool_track_unmatched_items(self) -> None:
        manifest, source_lanes, project_matches, unallocated_pool, anomaly_candidates = (
            build_default_subcontract_procurement_aggregation(generated_at="2026-07-01T23:00:00+10:00")
        )
        validate_subcontract_procurement_artifacts(
            manifest,
            source_lanes,
            project_matches,
            unallocated_pool,
            anomaly_candidates,
        )

        statuses = {record["matching_status"] for record in project_matches}
        self.assertIn("matched_to_project", statuses)
        self.assertIn("unmatched_to_project", statuses)
        self.assertIn("cross_project_candidate", statuses)

        pool_refs = {item["match_record_ref"] for item in unallocated_pool}
        unmatched_refs = {
            record["match_record_id"]
            for record in project_matches
            if record["matching_status"] == "unmatched_to_project"
        }
        self.assertEqual(pool_refs, unmatched_refs)
        for item in unallocated_pool:
            self.assertEqual(item["record_type"], "subcontract_unallocated_cost_pool_item")
            self.assertEqual(item["assignment_status"], "pending_project_assignment_or_owner_review")
            self.assertTrue(item["manual_review_required"])
            self.assertFalse(item["amount_value_public_committed"])
            self.assertFalse(item["raw_layer_write_allowed"])
            self.assertFalse(item["payment_execution_allowed"])

    def test_duplicate_payment_and_cross_project_candidates_are_review_only(self) -> None:
        manifest, source_lanes, project_matches, unallocated_pool, anomaly_candidates = (
            build_default_subcontract_procurement_aggregation(generated_at="2026-07-01T23:00:00+10:00")
        )
        validate_subcontract_procurement_artifacts(
            manifest,
            source_lanes,
            project_matches,
            unallocated_pool,
            anomaly_candidates,
        )

        candidate_types = [candidate["candidate_type"] for candidate in anomaly_candidates]
        self.assertEqual(candidate_types.count("duplicate_payment_candidate"), 2)
        self.assertEqual(candidate_types.count("cross_project_cost_candidate"), 2)
        for candidate in anomaly_candidates:
            self.assertEqual(candidate["record_type"], "subcontract_anomaly_candidate")
            self.assertTrue(candidate["manual_review_required"])
            self.assertFalse(candidate["action_execution_allowed"])
            self.assertFalse(candidate["payment_execution_allowed"])
            self.assertFalse(candidate["bank_operation_allowed"])
            self.assertFalse(candidate["business_decision_basis_allowed"])
            self.assertFalse(candidate["contains_true_amounts"])
            self.assertFalse(candidate["contains_field_plaintext"])

    def test_public_payload_has_no_raw_values_private_refs_files_or_credentials(self) -> None:
        manifest, source_lanes, project_matches, unallocated_pool, anomaly_candidates = (
            build_default_subcontract_procurement_aggregation(generated_at="2026-07-01T23:00:00+10:00")
        )
        payload = json.dumps(
            [manifest, source_lanes, project_matches, unallocated_pool, anomaly_candidates],
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
            "private_csv",
            ".zip",
            ".xlsx",
            ".xls",
            ".pdf",
            ".sqlite",
            ".db",
            "bank_account_number",
            "account_number",
            "identity_document_number",
            "password",
            "token",
            "api_key",
            "private_key",
        ):
            self.assertNotIn(forbidden_text, payload)

    def test_validator_rejects_operation_or_later_phase_scope(self) -> None:
        manifest, source_lanes, project_matches, unallocated_pool, anomaly_candidates = (
            build_default_subcontract_procurement_aggregation(generated_at="2026-07-01T23:00:00+10:00")
        )

        broken_manifest = dict(manifest)
        broken_manifest["quality_gate"] = dict(manifest["quality_gate"])
        broken_manifest["quality_gate"]["payment_execution_allowed"] = True
        with self.assertRaises(SubcontractProcurementAggregationError):
            validate_subcontract_procurement_artifacts(
                broken_manifest,
                source_lanes,
                project_matches,
                unallocated_pool,
                anomaly_candidates,
            )

        broken_manifest = dict(manifest)
        broken_manifest["stage_scope"] = dict(manifest["stage_scope"])
        broken_manifest["stage_scope"]["s16_p2_scope_included"] = True
        with self.assertRaises(SubcontractProcurementAggregationError):
            validate_subcontract_procurement_artifacts(
                broken_manifest,
                source_lanes,
                project_matches,
                unallocated_pool,
                anomaly_candidates,
            )

        broken_manifest = dict(manifest)
        broken_manifest["stage_scope"] = dict(manifest["stage_scope"])
        broken_manifest["stage_scope"]["github_upload_scope_included"] = True
        with self.assertRaises(SubcontractProcurementAggregationError):
            validate_subcontract_procurement_artifacts(
                broken_manifest,
                source_lanes,
                project_matches,
                unallocated_pool,
                anomaly_candidates,
            )


if __name__ == "__main__":
    unittest.main()
