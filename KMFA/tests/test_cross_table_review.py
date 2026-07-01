import json
import unittest

from KMFA.tools.cross_table_review import (
    REQUIRED_REVIEW_DIMENSIONS,
    CrossTableReviewError,
    build_default_cross_table_review_artifacts,
    validate_cross_table_review_artifacts,
)


class CrossTableReviewTests(unittest.TestCase):
    def test_default_runtime_covers_s13_p3_required_scope(self) -> None:
        manifest, review_checks, difference_queue, quality_report, html_outputs = (
            build_default_cross_table_review_artifacts(generated_at="2026-07-01T19:00:00+10:00")
        )
        validate_cross_table_review_artifacts(
            manifest, review_checks, difference_queue, quality_report, html_outputs
        )

        self.assertEqual(manifest["stage_phase"], "S13-P3")
        self.assertEqual(tuple(manifest["required_review_dimensions"]), REQUIRED_REVIEW_DIMENSIONS)
        self.assertEqual(manifest["summary"]["review_dimension_count"], 4)
        self.assertEqual(manifest["summary"]["difference_queue_count"], 4)
        self.assertEqual(manifest["summary"]["quality_report_count"], 1)
        self.assertEqual(manifest["summary"]["pending_reconciliation_count"], 12)
        self.assertEqual(manifest["summary"]["report_grade_visible"], "D")
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["business_decision_basis_allowed"])
        self.assertFalse(manifest["quality_gate"]["difference_auto_resolution_allowed"])
        self.assertFalse(manifest["quality_gate"]["stage13_review_allowed"])
        self.assertFalse(manifest["quality_gate"]["github_upload_allowed"])

    def test_review_checks_cover_project_customer_amount_and_time_consistency(self) -> None:
        manifest, review_checks, difference_queue, quality_report, html_outputs = (
            build_default_cross_table_review_artifacts(generated_at="2026-07-01T19:00:00+10:00")
        )
        validate_cross_table_review_artifacts(
            manifest, review_checks, difference_queue, quality_report, html_outputs
        )

        checks_by_dimension = {check["review_dimension"]: check for check in review_checks}
        self.assertEqual(set(checks_by_dimension), set(REQUIRED_REVIEW_DIMENSIONS))

        for dimension in REQUIRED_REVIEW_DIMENSIONS:
            check = checks_by_dimension[dimension]
            self.assertEqual(check["record_type"], "cross_table_review_check")
            self.assertEqual(check["review_result"], "difference_queue_required")
            self.assertTrue(check["s13_p1_evidence_refs"])
            self.assertTrue(check["s13_p2_evidence_refs"])
            self.assertTrue(check["s09_reconciliation_refs"])
            self.assertFalse(check["raw_business_values_allowed"])
            self.assertFalse(check["field_plaintext_allowed"])
            self.assertFalse(check["business_decision_basis_allowed"])

    def test_difference_queue_is_manual_review_only_and_public_safe(self) -> None:
        manifest, review_checks, difference_queue, quality_report, html_outputs = (
            build_default_cross_table_review_artifacts(generated_at="2026-07-01T19:00:00+10:00")
        )
        validate_cross_table_review_artifacts(
            manifest, review_checks, difference_queue, quality_report, html_outputs
        )

        self.assertEqual({item["review_dimension"] for item in difference_queue}, set(REQUIRED_REVIEW_DIMENSIONS))
        self.assertEqual([item["queue_rank"] for item in difference_queue], [1, 2, 3, 4])

        for item in difference_queue:
            self.assertEqual(item["record_type"], "cross_table_difference_queue_item")
            self.assertTrue(item["queue_item_id"].startswith("S13P3-DIFF-"))
            self.assertEqual(item["resolution_status"], "pending_owner_or_authorized_review")
            self.assertFalse(item["auto_resolution_allowed"])
            self.assertFalse(item["auto_source_selection_allowed"])
            self.assertFalse(item["amount_recalculation_allowed"])
            self.assertFalse(item["formal_report_allowed"])
            self.assertFalse(item["business_decision_basis_allowed"])
            self.assertFalse(item["raw_business_values_allowed"])

    def test_quality_report_blocks_formal_report_until_review_and_lineage_close(self) -> None:
        manifest, review_checks, difference_queue, quality_report, html_outputs = (
            build_default_cross_table_review_artifacts(generated_at="2026-07-01T19:00:00+10:00")
        )
        validate_cross_table_review_artifacts(
            manifest, review_checks, difference_queue, quality_report, html_outputs
        )

        self.assertEqual(quality_report["record_type"], "operating_report_quality_report")
        self.assertEqual(quality_report["report_grade_visible"], "D")
        self.assertEqual(quality_report["cross_table_review_status"], "completed_with_pending_differences")
        self.assertEqual(quality_report["difference_queue_count"], 4)
        self.assertEqual(quality_report["pending_reconciliation_count"], 12)
        self.assertFalse(quality_report["formal_report_allowed"])
        self.assertFalse(quality_report["complete_trusted_report_display_allowed"])
        self.assertFalse(quality_report["business_decision_basis_allowed"])
        self.assertFalse(quality_report["lineage_full_check_included"])
        self.assertFalse(quality_report["stage13_review_scope_included"])
        self.assertIn("项目", quality_report["visible_summary"])
        self.assertIn("客户", quality_report["visible_summary"])
        self.assertIn("金额", quality_report["visible_summary"])
        self.assertIn("时间", quality_report["visible_summary"])

    def test_rendered_html_is_public_safe_and_business_readable(self) -> None:
        manifest, review_checks, difference_queue, quality_report, html_outputs = (
            build_default_cross_table_review_artifacts(generated_at="2026-07-01T19:00:00+10:00")
        )
        validate_cross_table_review_artifacts(
            manifest, review_checks, difference_queue, quality_report, html_outputs
        )

        self.assertEqual(set(html_outputs), {"cross_table_quality_report"})
        html_text = html_outputs["cross_table_quality_report"]
        self.assertTrue(html_text.startswith("<!doctype html>"))
        self.assertIn('lang="zh-CN"', html_text)
        self.assertIn("跨表复核", html_text)
        self.assertIn("项目一致性", html_text)
        self.assertIn("客户一致性", html_text)
        self.assertIn("金额一致性", html_text)
        self.assertIn("时间一致性", html_text)
        self.assertIn("不可作为正式经营报告或经营决策依据", html_text)
        for forbidden_visible in ("source_ref://", "private://", "private_ref://", "validator", "manifest", "metadata"):
            self.assertNotIn(forbidden_visible, html_text.lower())
        for forbidden_suffix in (".zip", ".xlsx", ".xls", ".pdf", ".sqlite", ".db"):
            self.assertNotIn(forbidden_suffix, html_text.lower())

    def test_public_payload_has_no_raw_values_private_refs_or_credentials(self) -> None:
        manifest, review_checks, difference_queue, quality_report, html_outputs = (
            build_default_cross_table_review_artifacts(generated_at="2026-07-01T19:00:00+10:00")
        )
        payload = json.dumps(
            [manifest, review_checks, difference_queue, quality_report, html_outputs],
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
            "identity_document_number",
            "password",
            "token",
            "api_key",
            "private_key",
        ):
            self.assertNotIn(forbidden_text, payload)

    def test_validator_rejects_review_bypass_or_stage_review_scope(self) -> None:
        manifest, review_checks, difference_queue, quality_report, html_outputs = (
            build_default_cross_table_review_artifacts(generated_at="2026-07-01T19:00:00+10:00")
        )

        broken_manifest = dict(manifest)
        broken_manifest["quality_gate"] = dict(manifest["quality_gate"])
        broken_manifest["quality_gate"]["difference_auto_resolution_allowed"] = True
        with self.assertRaises(CrossTableReviewError):
            validate_cross_table_review_artifacts(
                broken_manifest, review_checks, difference_queue, quality_report, html_outputs
            )

        broken_report = dict(quality_report)
        broken_report["stage13_review_scope_included"] = True
        with self.assertRaises(CrossTableReviewError):
            validate_cross_table_review_artifacts(
                manifest, review_checks, difference_queue, broken_report, html_outputs
            )

        broken_queue = [dict(difference_queue[0]), *difference_queue[1:]]
        broken_queue[0]["auto_source_selection_allowed"] = True
        with self.assertRaises(CrossTableReviewError):
            validate_cross_table_review_artifacts(
                manifest, review_checks, broken_queue, quality_report, html_outputs
            )


if __name__ == "__main__":
    unittest.main()
