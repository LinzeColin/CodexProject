import unittest

from KMFA.tests._artifact_snapshot import ArtifactSnapshot
from KMFA.tools.check_v014_s14_p3_post_remediation_policy_evidence_plan import (
    validate_v014_s14_p3_post_remediation_policy_evidence_plan,
)
from KMFA.tools.v014_s14_p3_post_remediation_policy_evidence_plan import _phase_public_files, generate


class TestV014S14P3PostRemediationPolicyEvidencePlan(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact_snapshot = ArtifactSnapshot(_phase_public_files())
        try:
            cls.generated = generate(final_validation=False, write_governance=False)
            cls.validated = validate_v014_s14_p3_post_remediation_policy_evidence_plan(
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
            "V014_S14_P3_POST_REMEDIATION_POLICY_EVIDENCE_PLAN",
        )
        self.assertEqual(self.validated["roadmap_phase_id"], "S14-P3")
        self.assertTrue(self.validated["s14_p2_post_remediation_dependency_validated"])
        self.assertFalse(self.validated["historical_s14_p3_dynamic_state_is_authoritative"])

    def test_registers_five_public_safe_directories(self) -> None:
        summary = self.validated["summary"]
        self.assertEqual(summary["policy_program_count"], 5)
        self.assertEqual(summary["evidence_directory_definition_count"], 5)
        self.assertEqual(summary["required_evidence_category_total_count"], 23)
        self.assertEqual(summary["unique_public_source_ref_count"], 4)
        self.assertEqual(summary["program_source_association_count"], 12)
        self.assertEqual(summary["unique_structure_candidate_count"], 20)
        self.assertEqual(summary["program_structure_candidate_association_count"], 60)
        self.assertEqual(summary["authoritative_evidence_bound_program_count"], 0)
        self.assertEqual(summary["evidence_complete_program_count"], 0)

    def test_read_only_raw_probe_is_exact_and_private(self) -> None:
        summary = self.validated["summary"]
        self.assertEqual(summary["raw_source_file_count"], 5)
        self.assertEqual(summary["private_xlsx_container_count"], 48)
        self.assertEqual(summary["private_parseable_xlsx_count"], 25)
        self.assertEqual(summary["private_unparseable_xlsx_count"], 23)
        self.assertEqual(summary["private_parseable_sheet_count"], 4198)
        self.assertEqual(
            summary["private_policy_lexical_candidate_sheet_count_by_program"],
            {
                "small_tech_company": 0,
                "high_tech_enterprise": 1,
                "specialized_refined_innovative": 0,
                "little_giant": 0,
                "r_and_d_expense": 3830,
            },
        )
        self.assertEqual(summary["private_unique_policy_lexical_candidate_sheet_count"], 3830)
        self.assertEqual(summary["private_multi_program_candidate_sheet_count"], 1)
        self.assertEqual(summary["private_lexical_candidate_covered_program_count"], 2)
        self.assertEqual(summary["private_probe_roundtrip_mismatch_count"], 0)
        self.assertTrue(summary["raw_snapshot_exact_match"])
        self.assertTrue(summary["raw_cross_phase_snapshot_exact_match"])

    def test_outputs_only_gaps_and_risk_tips(self) -> None:
        summary = self.validated["summary"]
        self.assertEqual(summary["evidence_gap_count"], 5)
        self.assertEqual(summary["risk_tip_count"], 5)
        self.assertEqual(summary["formal_policy_qualification_conclusion_count"], 0)
        self.assertEqual(summary["policy_score_count"], 0)
        self.assertEqual(summary["policy_application_submission_count"], 0)
        self.assertEqual(summary["subsidy_application_count"], 0)
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
        self.assertFalse(self.validated["quality_gate"]["formal_policy_qualification_conclusion_allowed"])
        self.assertFalse(self.validated["quality_gate"]["formal_report_allowed"])

    def test_browser_flow_and_dependency_navigation(self) -> None:
        browser = self.validated["browser_review"]
        self.assertEqual(browser["baseline_pass_count"], 54)
        self.assertEqual(browser["baseline_warn_count"], 0)
        self.assertEqual(browser["baseline_fail_count"], 0)
        self.assertEqual(browser["current_page_count"], 1)
        self.assertEqual(browser["current_pass_count"], browser["current_control_row_count"])
        self.assertGreaterEqual(browser["current_pass_count"], 12)
        self.assertEqual(browser["viewport_check_count"], 2)
        self.assertEqual(browser["program_interaction_check_count"], 10)
        self.assertEqual(browser["dependency_link_http_check_count"], 4)
        self.assertEqual(browser["dependency_navigation_check_count"], 4)
        self.assertEqual(browser["console_error_count"], 0)
        self.assertEqual(browser["horizontal_overflow_count"], 0)

    def test_quarantines_legacy_static_signals(self) -> None:
        quarantine = self.validated["historical_quarantine"]
        self.assertTrue(quarantine["legacy_pending_twelve_quarantined"])
        self.assertTrue(quarantine["legacy_five_gap_statuses_quarantined"])
        self.assertTrue(quarantine["legacy_five_risk_statuses_quarantined"])
        self.assertEqual(quarantine["current_authoritative_evidence_bound_program_count"], 0)
        self.assertEqual(quarantine["current_formal_policy_qualification_conclusion_count"], 0)

    def test_stops_before_review_release_and_policy_actions(self) -> None:
        boundaries = self.validated["phase_boundaries"]
        self.assertTrue(boundaries["s14_p1_post_remediation_validated"])
        self.assertTrue(boundaries["s14_p2_post_remediation_validated"])
        self.assertTrue(boundaries["s14_p3_performed"])
        for key in (
            "stage14_review_performed",
            "formal_policy_qualification_conclusion_performed",
            "policy_application_submission_performed",
            "subsidy_application_performed",
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
