import json
import unittest

from KMFA.tools.home_navigation_runtime import (
    REQUIRED_NAVIGATION_LABELS,
    HomeNavigationRuntimeError,
    build_default_home_navigation_artifacts,
    validate_home_navigation_artifacts,
)


class HomeNavigationRuntimeTests(unittest.TestCase):
    def test_default_runtime_covers_s11_p1_required_modules(self) -> None:
        manifest, records, render_outputs = build_default_home_navigation_artifacts(
            generated_at="2026-07-01T09:00:00+10:00"
        )
        validate_home_navigation_artifacts(manifest, records, render_outputs)

        self.assertEqual(manifest["stage_phase"], "S11-P1")
        self.assertEqual(manifest["summary"]["navigation_module_count"], 8)
        self.assertEqual(manifest["summary"]["html_export_count"], 1)
        self.assertEqual([record["visible_label"] for record in records], list(REQUIRED_NAVIGATION_LABELS))
        self.assertTrue(manifest["stage_scope"]["s11_p1_home_navigation_scope_included"])
        self.assertFalse(manifest["stage_scope"]["s11_p2_source_matrix_scope_included"])
        self.assertFalse(manifest["stage_scope"]["s11_p3_project_cost_detail_scope_included"])
        self.assertFalse(manifest["stage_scope"]["stage11_review_scope_included"])
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["business_decision_basis_allowed"])
        self.assertFalse(manifest["quality_gate"]["github_upload_allowed"])

    def test_home_navigation_records_are_public_safe_and_business_facing(self) -> None:
        manifest, records, render_outputs = build_default_home_navigation_artifacts(
            generated_at="2026-07-01T09:00:00+10:00"
        )
        validate_home_navigation_artifacts(manifest, records, render_outputs)

        for record in records:
            self.assertEqual(record["record_type"], "home_navigation_module")
            self.assertTrue(record["visible_label"])
            self.assertIn("KMFA", record["system_name"])
            self.assertEqual(record["brand_mark"], "KM")
            self.assertLessEqual(record["warning_badge_count"], 1)
            self.assertFalse(record["contains_raw_business_values"])
            self.assertFalse(record["allows_raw_layer_write"])
            self.assertFalse(record["formal_report_allowed"])

    def test_rendered_home_html_inherits_required_ui_rules(self) -> None:
        manifest, records, render_outputs = build_default_home_navigation_artifacts(
            generated_at="2026-07-01T09:00:00+10:00"
        )
        validate_home_navigation_artifacts(manifest, records, render_outputs)
        html_text = render_outputs["html"]["kmfa_home_navigation"]

        self.assertTrue(html_text.startswith("<!doctype html>"))
        self.assertIn('lang="zh-CN"', html_text)
        self.assertIn("KMFA 经营分析系统", html_text)
        self.assertIn(">KM<", html_text)
        self.assertNotIn(">K<", html_text)
        for label in REQUIRED_NAVIGATION_LABELS:
            self.assertIn(label, html_text)
        for required_text in ("蓝色商务版", "不可作为正式经营报告", "报告等级 D"):
            self.assertIn(required_text, html_text)
        for forbidden_visible in ("source_ref://", "validator", "manifest", "metadata"):
            self.assertNotIn(forbidden_visible, html_text.lower())

    def test_public_payload_has_no_raw_values_or_private_files(self) -> None:
        manifest, records, render_outputs = build_default_home_navigation_artifacts(
            generated_at="2026-07-01T09:00:00+10:00"
        )
        payload = json.dumps([manifest, records, render_outputs], ensure_ascii=False, sort_keys=True)

        for forbidden_text in (
            '"amount_cents":',
            '"amount_yuan":',
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
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

    def test_validator_rejects_missing_required_module(self) -> None:
        manifest, records, render_outputs = build_default_home_navigation_artifacts(
            generated_at="2026-07-01T09:00:00+10:00"
        )
        broken_records = [record for record in records if record["visible_label"] != "报告中心"]

        with self.assertRaises(HomeNavigationRuntimeError):
            validate_home_navigation_artifacts(manifest, broken_records, render_outputs)


if __name__ == "__main__":
    unittest.main()
