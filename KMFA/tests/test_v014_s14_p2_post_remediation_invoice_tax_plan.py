import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tests._artifact_snapshot import ArtifactSnapshot
from KMFA.tools.check_v014_s14_p2_post_remediation_invoice_tax_plan import (
    validate_v014_s14_p2_post_remediation_invoice_tax_plan,
)
from KMFA.tools.v014_s14_p2_post_remediation_invoice_tax_plan import (
    _phase_public_files,
    _upsert_jsonl,
    generate,
)


class TestPhaseLocalJsonlUpsert(unittest.TestCase):
    def test_preserves_upstream_phase_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            upstream = {"phase_id": "UPSTREAM", "value": 1}
            path.write_text(json.dumps(upstream) + "\n", encoding="utf-8")
            _upsert_jsonl(path, {"phase_id": "CURRENT", "value": 2})
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(rows, [upstream, {"phase_id": "CURRENT", "value": 2}])


class TestV014S14P2PostRemediationInvoiceTaxPlan(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact_snapshot = ArtifactSnapshot(_phase_public_files())
        try:
            cls.generated = generate(final_validation=False, write_governance=False)
            cls.validated = validate_v014_s14_p2_post_remediation_invoice_tax_plan(
                require_private_evidence=True,
                require_browser_evidence=True,
            )
        except BaseException:
            cls.artifact_snapshot.restore()
            raise

    @classmethod
    def tearDownClass(cls) -> None:
        cls.artifact_snapshot.restore()

    def test_identity_and_current_dependency(self) -> None:
        self.assertEqual(self.generated, self.validated)
        self.assertEqual(self.validated["project_id"], "KMFA")
        self.assertEqual(self.validated["stage_id"], "S14")
        self.assertEqual(
            self.validated["phase_id"],
            "V014_S14_P2_POST_REMEDIATION_INVOICE_TAX_PLAN",
        )
        self.assertEqual(self.validated["roadmap_phase_id"], "S14-P2")
        self.assertTrue(self.validated["s14_p1_post_remediation_dependency_validated"])
        self.assertFalse(self.validated["historical_s14_p2_dynamic_state_is_authoritative"])

    def test_connects_three_lanes_without_claiming_value_bindings(self) -> None:
        summary = self.validated["summary"]
        self.assertEqual(summary["source_lane_count"], 3)
        self.assertEqual(summary["structure_connected_lane_count"], 3)
        self.assertEqual(summary["unique_public_source_ref_count"], 4)
        self.assertEqual(summary["lane_source_binding_count"], 6)
        self.assertEqual(summary["unique_structure_candidate_count"], 20)
        self.assertEqual(summary["lane_structure_candidate_association_count"], 30)
        self.assertEqual(summary["private_parseable_direct_lane_count"], 2)
        self.assertEqual(summary["row_level_binding_proven_lane_count"], 0)
        self.assertEqual(summary["value_binding_proven_lane_count"], 0)

    def test_read_only_raw_probe_is_exact_and_private(self) -> None:
        summary = self.validated["summary"]
        self.assertEqual(summary["raw_source_file_count"], 5)
        self.assertEqual(summary["private_xlsx_container_count"], 48)
        self.assertEqual(summary["private_parseable_xlsx_count"], 25)
        self.assertEqual(summary["private_unparseable_xlsx_count"], 23)
        self.assertEqual(summary["private_parseable_sheet_count"], 4198)
        self.assertEqual(summary["private_invoice_candidate_sheet_count"], 538)
        self.assertEqual(summary["private_tax_candidate_sheet_count"], 104)
        self.assertEqual(summary["private_invoice_tax_overlap_sheet_count"], 30)
        self.assertEqual(summary["private_unique_invoice_tax_candidate_sheet_count"], 612)
        self.assertEqual(summary["private_probe_roundtrip_mismatch_count"], 0)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertTrue(summary["raw_cross_phase_snapshot_exact_match"])

    def test_defines_reviews_without_inventing_business_candidates(self) -> None:
        summary = self.validated["summary"]
        self.assertEqual(summary["issue_review_method_definition_count"], 3)
        self.assertEqual(summary["cash_summary_method_definition_count"], 3)
        self.assertEqual(summary["identified_pending_invoice_candidate_count"], 0)
        self.assertEqual(summary["identified_invoiced_not_collected_candidate_count"], 0)
        self.assertEqual(summary["identified_tax_rate_exception_candidate_count"], 0)
        self.assertEqual(summary["identified_issue_candidate_count"], 0)
        self.assertEqual(summary["materialized_cash_summary_count"], 0)
        self.assertEqual(summary["identified_business_item_count"], 0)
        self.assertEqual(summary["public_business_amount_count"], 0)

    def test_preserves_current_quality_and_non_additive_difference_state(self) -> None:
        summary = self.validated["summary"]
        self.assertEqual(summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(summary["incomplete_reconciliation_count"], 1)
        self.assertEqual(summary["current_data_quality_grade"], "Q4")
        self.assertEqual(summary["current_report_grade"], "D")
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertFalse(self.validated["quality_gate"]["tax_rate_exception_business_alert_allowed"])
        self.assertFalse(self.validated["quality_gate"]["formal_report_allowed"])

    def test_browser_flow_and_dependency_navigation(self) -> None:
        browser = self.validated["browser_review"]
        self.assertEqual(browser["baseline_pass_count"], 54)
        self.assertEqual(browser["baseline_warn_count"], 0)
        self.assertEqual(browser["baseline_fail_count"], 0)
        self.assertEqual(browser["current_page_count"], 1)
        self.assertEqual(browser["current_pass_count"], browser["current_control_row_count"])
        self.assertGreaterEqual(browser["current_pass_count"], 10)
        self.assertEqual(browser["viewport_check_count"], 2)
        self.assertEqual(browser["issue_method_interaction_check_count"], 6)
        self.assertEqual(browser["dependency_link_http_check_count"], 4)
        self.assertEqual(browser["dependency_navigation_check_count"], 4)
        self.assertEqual(browser["console_error_count"], 0)
        self.assertEqual(browser["horizontal_overflow_count"], 0)

    def test_quarantines_legacy_static_signals(self) -> None:
        quarantine = self.validated["historical_quarantine"]
        self.assertTrue(quarantine["legacy_pending_twelve_quarantined"])
        self.assertTrue(quarantine["legacy_three_issue_candidates_quarantined"])
        self.assertTrue(quarantine["legacy_three_cash_summaries_quarantined"])
        self.assertEqual(quarantine["current_identified_issue_candidate_count"], 0)
        self.assertEqual(quarantine["current_materialized_cash_summary_count"], 0)

    def test_stops_before_operations_and_later_scope(self) -> None:
        boundaries = self.validated["phase_boundaries"]
        self.assertTrue(boundaries["s14_p1_post_remediation_validated"])
        self.assertTrue(boundaries["s14_p2_performed"])
        for key in (
            "s14_p3_performed",
            "stage14_review_performed",
            "invoice_issuance_performed",
            "tax_filing_performed",
            "github_upload_performed",
            "app_reinstall_performed",
            "formal_report_release_performed",
            "difference_closure_performed",
            "persistent_business_write_performed",
            "business_execution_performed",
        ):
            self.assertFalse(boundaries[key], key)


if __name__ == "__main__":
    unittest.main()
