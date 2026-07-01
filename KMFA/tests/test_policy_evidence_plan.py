import json
import unittest

from KMFA.tools.policy_evidence_plan import (
    PolicyEvidencePlanError,
    REQUIRED_EVIDENCE_DIRECTORIES,
    REQUIRED_POLICY_PROGRAMS,
    build_default_policy_evidence_artifacts,
    validate_policy_evidence_artifacts,
)


class PolicyEvidencePlanTests(unittest.TestCase):
    def test_default_runtime_covers_s14_p3_required_scope(self) -> None:
        manifest, directories, gaps, risk_tips, html_outputs = build_default_policy_evidence_artifacts(
            generated_at="2026-07-01T23:30:00+10:00"
        )
        validate_policy_evidence_artifacts(manifest, directories, gaps, risk_tips, html_outputs)

        self.assertEqual(manifest["stage_phase"], "S14-P3")
        self.assertEqual(tuple(manifest["required_policy_programs"]), REQUIRED_POLICY_PROGRAMS)
        self.assertEqual(tuple(manifest["required_evidence_directories"]), REQUIRED_EVIDENCE_DIRECTORIES)
        self.assertEqual(manifest["summary"]["policy_program_count"], 5)
        self.assertEqual(manifest["summary"]["evidence_directory_count"], 5)
        self.assertEqual(manifest["summary"]["evidence_gap_count"], 5)
        self.assertEqual(manifest["summary"]["risk_tip_count"], 5)
        self.assertEqual(manifest["summary"]["pending_reconciliation_count"], 12)
        self.assertEqual(manifest["summary"]["report_grade_visible"], "D")
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["business_decision_basis_allowed"])
        self.assertFalse(manifest["quality_gate"]["policy_qualification_conclusion_allowed"])
        self.assertFalse(manifest["quality_gate"]["policy_application_submission_allowed"])
        self.assertFalse(manifest["quality_gate"]["tax_filing_allowed"])
        self.assertFalse(manifest["quality_gate"]["invoice_issuance_allowed"])
        self.assertFalse(manifest["stage_scope"]["stage14_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["github_upload_scope_included"])

    def test_evidence_directories_cover_required_policy_programs(self) -> None:
        manifest, directories, gaps, risk_tips, html_outputs = build_default_policy_evidence_artifacts(
            generated_at="2026-07-01T23:30:00+10:00"
        )
        validate_policy_evidence_artifacts(manifest, directories, gaps, risk_tips, html_outputs)

        self.assertEqual({item["policy_program"] for item in directories}, set(REQUIRED_POLICY_PROGRAMS))
        self.assertEqual({item["directory_id"] for item in directories}, set(REQUIRED_EVIDENCE_DIRECTORIES))
        for item in directories:
            self.assertEqual(item["record_type"], "policy_evidence_directory")
            self.assertEqual(item["stage_phase"], "S14-P3")
            self.assertGreaterEqual(len(item["required_evidence_categories"]), 3)
            self.assertTrue(item["directory_registered"])
            self.assertFalse(item["raw_business_values_allowed"])
            self.assertFalse(item["field_plaintext_allowed"])
            self.assertFalse(item["formal_policy_conclusion_allowed"])
            self.assertFalse(item["policy_application_submission_allowed"])

    def test_gaps_and_risk_tips_are_public_safe_and_non_conclusive(self) -> None:
        manifest, directories, gaps, risk_tips, html_outputs = build_default_policy_evidence_artifacts(
            generated_at="2026-07-01T23:30:00+10:00"
        )
        validate_policy_evidence_artifacts(manifest, directories, gaps, risk_tips, html_outputs)

        self.assertEqual({item["policy_program"] for item in gaps}, set(REQUIRED_POLICY_PROGRAMS))
        self.assertEqual({item["policy_program"] for item in risk_tips}, set(REQUIRED_POLICY_PROGRAMS))
        for item in gaps:
            self.assertEqual(item["record_type"], "policy_evidence_gap")
            self.assertEqual(item["stage_phase"], "S14-P3")
            self.assertIn(item["gap_status"], {"missing_or_unverified", "partial_manual_review_required"})
            self.assertFalse(item["eligibility_conclusion_allowed"])
            self.assertFalse(item["policy_score_allowed"])
            self.assertFalse(item["business_decision_basis_allowed"])

        for item in risk_tips:
            self.assertEqual(item["record_type"], "policy_risk_tip")
            self.assertEqual(item["stage_phase"], "S14-P3")
            self.assertIn(item["risk_level"], {"medium", "high"})
            self.assertFalse(item["formal_policy_conclusion_allowed"])
            self.assertFalse(item["policy_application_submission_allowed"])
            self.assertFalse(item["external_connector_action_allowed"])

    def test_rendered_html_is_business_readable_and_keeps_policy_conclusions_blocked(self) -> None:
        manifest, directories, gaps, risk_tips, html_outputs = build_default_policy_evidence_artifacts(
            generated_at="2026-07-01T23:30:00+10:00"
        )
        validate_policy_evidence_artifacts(manifest, directories, gaps, risk_tips, html_outputs)

        self.assertEqual(set(html_outputs), {"policy_evidence_overview"})
        html_text = html_outputs["policy_evidence_overview"]
        self.assertTrue(html_text.startswith("<!doctype html>"))
        self.assertIn('lang="zh-CN"', html_text)
        self.assertIn("KMFA 政策证据", html_text)
        for visible_text in ("科小", "高新", "专精特新", "小巨人", "研发费用"):
            self.assertIn(visible_text, html_text)
        self.assertIn("只输出证据缺口和风险提示", html_text)
        self.assertIn("不输出正式政策资格结论", html_text)
        self.assertIn("报告等级 D", html_text)
        for forbidden_visible in ("source_ref://", "private://", "private_ref://", "validator", "manifest", "metadata"):
            self.assertNotIn(forbidden_visible, html_text.lower())
        for forbidden_suffix in (".zip", ".xlsx", ".xls", ".pdf", ".sqlite", ".db"):
            self.assertNotIn(forbidden_suffix, html_text.lower())

    def test_public_payload_has_no_raw_values_private_refs_credentials_or_policy_scores(self) -> None:
        manifest, directories, gaps, risk_tips, html_outputs = build_default_policy_evidence_artifacts(
            generated_at="2026-07-01T23:30:00+10:00"
        )
        payload = json.dumps(
            [manifest, directories, gaps, risk_tips, html_outputs],
            ensure_ascii=False,
            sort_keys=True,
        )

        for forbidden_text in (
            '"amount_cents":',
            '"amount_yuan":',
            '"policy_score":',
            '"eligibility_result":',
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
            "invoice_number",
            "tax_declaration_number",
            "identity_document_number",
            "password",
            "token",
            "api_key",
            "private_key",
        ):
            self.assertNotIn(forbidden_text, payload)

    def test_validator_rejects_policy_conclusion_submission_or_stage_review_scope(self) -> None:
        manifest, directories, gaps, risk_tips, html_outputs = build_default_policy_evidence_artifacts(
            generated_at="2026-07-01T23:30:00+10:00"
        )

        broken_manifest = dict(manifest)
        broken_manifest["quality_gate"] = dict(manifest["quality_gate"])
        broken_manifest["quality_gate"]["policy_qualification_conclusion_allowed"] = True
        with self.assertRaises(PolicyEvidencePlanError):
            validate_policy_evidence_artifacts(broken_manifest, directories, gaps, risk_tips, html_outputs)

        broken_manifest = dict(manifest)
        broken_manifest["quality_gate"] = dict(manifest["quality_gate"])
        broken_manifest["quality_gate"]["policy_application_submission_allowed"] = True
        with self.assertRaises(PolicyEvidencePlanError):
            validate_policy_evidence_artifacts(broken_manifest, directories, gaps, risk_tips, html_outputs)

        broken_manifest = dict(manifest)
        broken_manifest["stage_scope"] = dict(manifest["stage_scope"])
        broken_manifest["stage_scope"]["stage14_review_scope_included"] = True
        with self.assertRaises(PolicyEvidencePlanError):
            validate_policy_evidence_artifacts(broken_manifest, directories, gaps, risk_tips, html_outputs)

        broken_gap = [dict(gaps[0]), *gaps[1:]]
        broken_gap[0]["eligibility_conclusion_allowed"] = True
        with self.assertRaises(PolicyEvidencePlanError):
            validate_policy_evidence_artifacts(manifest, directories, broken_gap, risk_tips, html_outputs)


if __name__ == "__main__":
    unittest.main()
