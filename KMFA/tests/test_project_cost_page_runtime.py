import json
import unittest

from KMFA.tools.project_cost_page_runtime import (
    REQUIRED_PROJECT_PAGE_SECTIONS,
    REQUIRED_PROJECT_TABLE_COLUMNS,
    ProjectCostPageRuntimeError,
    build_default_project_cost_page_artifacts,
    validate_project_cost_page_artifacts,
)


class ProjectCostPageRuntimeTests(unittest.TestCase):
    def test_default_runtime_covers_s11_p3_project_cost_page(self) -> None:
        manifest, projects, render_outputs = build_default_project_cost_page_artifacts(
            generated_at="2026-07-01T11:00:00+10:00"
        )
        validate_project_cost_page_artifacts(manifest, projects, render_outputs)

        self.assertEqual(manifest["stage_phase"], "S11-P3")
        self.assertEqual(tuple(manifest["required_sections"]), REQUIRED_PROJECT_PAGE_SECTIONS)
        self.assertEqual(tuple(manifest["required_project_table_columns"]), REQUIRED_PROJECT_TABLE_COLUMNS)
        self.assertEqual(manifest["summary"]["project_row_count"], 4)
        self.assertEqual(manifest["summary"]["margin_record_count"], 4)
        self.assertEqual(manifest["summary"]["cost_category_count"], 9)
        self.assertEqual(manifest["summary"]["pending_reconciliation_count"], 12)
        self.assertTrue(manifest["quality_gate"]["report_preview_direct_view_allowed"])
        self.assertEqual(manifest["quality_gate"]["report_grade_visible"], "D")
        self.assertFalse(manifest["quality_gate"]["quality_grade_bypass_allowed"])
        self.assertFalse(manifest["quality_gate"]["formal_report_allowed"])
        self.assertFalse(manifest["quality_gate"]["business_decision_basis_allowed"])
        self.assertFalse(manifest["stage_scope"]["stage11_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["github_upload_scope_included"])

    def test_project_rows_cover_cost_margin_collection_difference_and_detail(self) -> None:
        manifest, projects, render_outputs = build_default_project_cost_page_artifacts(
            generated_at="2026-07-01T11:00:00+10:00"
        )
        validate_project_cost_page_artifacts(manifest, projects, render_outputs)

        for index, project in enumerate(projects, start=1):
            self.assertEqual(project["record_type"], "project_cost_page_project")
            self.assertEqual(project["stage_phase"], "S11-P3")
            self.assertEqual(project["project_order"], index)
            for required_field in (
                "project_display_ref",
                "fact_record_id",
                "margin_record_id",
                "gross_margin_status",
                "cost_structure_summary",
                "collection_status",
                "difference_status",
                "evidence_summary",
                "pending_actions",
                "report_preview_status",
                "next_step",
            ):
                self.assertTrue(project[required_field])
            self.assertFalse(project["contains_raw_business_values"])
            self.assertFalse(project["formal_report_allowed"])
            self.assertFalse(project["business_decision_basis_allowed"])
            self.assertFalse(project["raw_layer_write_allowed"])
            self.assertGreaterEqual(project["pending_action_count"], 1)

    def test_rendered_html_has_project_detail_evidence_and_blocked_report_preview(self) -> None:
        manifest, projects, render_outputs = build_default_project_cost_page_artifacts(
            generated_at="2026-07-01T11:00:00+10:00"
        )
        validate_project_cost_page_artifacts(manifest, projects, render_outputs)
        html_text = render_outputs["html"]["kmfa_project_cost_page"]

        self.assertTrue(html_text.startswith("<!doctype html>"))
        self.assertIn('lang="zh-CN"', html_text)
        self.assertIn("KMFA 项目成本页面", html_text)
        self.assertIn(">KM<", html_text)
        self.assertNotIn(">K<", html_text)
        for section in REQUIRED_PROJECT_PAGE_SECTIONS:
            self.assertIn(section, html_text)
        for column in REQUIRED_PROJECT_TABLE_COLUMNS:
            self.assertIn(column, html_text)
        for required_text in (
            "项目详情",
            "来源证据",
            "待处理事项",
            "报告预览",
            "报告等级 D",
            "不可绕过质量等级",
        ):
            self.assertIn(required_text, html_text)
        for forbidden_visible in ("source_ref://", "private_ref://", "validator", "manifest", "metadata"):
            self.assertNotIn(forbidden_visible, html_text.lower())
        for forbidden_suffix in (".zip", ".xlsx", ".xls", ".pdf", ".sqlite", ".db"):
            self.assertNotIn(forbidden_suffix, html_text.lower())

    def test_public_payload_has_no_raw_values_private_refs_or_credentials(self) -> None:
        manifest, projects, render_outputs = build_default_project_cost_page_artifacts(
            generated_at="2026-07-01T11:00:00+10:00"
        )
        payload = json.dumps([manifest, projects, render_outputs], ensure_ascii=False, sort_keys=True)

        for forbidden_text in (
            '"amount_cents":',
            '"amount_yuan":',
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
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

    def test_validator_rejects_quality_bypass_or_missing_required_section(self) -> None:
        manifest, projects, render_outputs = build_default_project_cost_page_artifacts(
            generated_at="2026-07-01T11:00:00+10:00"
        )

        broken_manifest = dict(manifest)
        broken_manifest["quality_gate"] = dict(manifest["quality_gate"])
        broken_manifest["quality_gate"]["quality_grade_bypass_allowed"] = True
        with self.assertRaises(ProjectCostPageRuntimeError):
            validate_project_cost_page_artifacts(broken_manifest, projects, render_outputs)

        broken_manifest = dict(manifest)
        broken_manifest["required_sections"] = [
            section for section in manifest["required_sections"] if section != "报告预览"
        ]
        with self.assertRaises(ProjectCostPageRuntimeError):
            validate_project_cost_page_artifacts(broken_manifest, projects, render_outputs)


if __name__ == "__main__":
    unittest.main()
