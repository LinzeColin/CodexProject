import json
import unittest

from KMFA.tools.report_templates import (
    REQUIRED_BUSINESS_OVERVIEW_SECTION_TITLES,
    REQUIRED_PROJECT_COST_SECTION_TITLES,
    REQUIRED_TEMPLATE_IDS,
    ReportTemplateError,
    build_default_report_template_artifacts,
    validate_report_template_artifacts,
)


class ReportTemplateTests(unittest.TestCase):
    def test_default_templates_cover_s10_p1_required_reports(self) -> None:
        manifest, templates, sections = build_default_report_template_artifacts(
            generated_at="2026-06-30T23:59:45+10:00"
        )
        validate_report_template_artifacts(manifest, templates, sections)

        self.assertEqual(manifest["stage_phase"], "S10-P1")
        self.assertEqual(set(manifest["required_template_ids"]), set(REQUIRED_TEMPLATE_IDS))
        self.assertEqual(manifest["summary"]["template_count"], 2)
        self.assertEqual(manifest["summary"]["section_count"], 11)
        self.assertEqual(manifest["summary"]["project_cost_section_count"], 4)
        self.assertEqual(manifest["summary"]["business_overview_section_count"], 7)

        template_by_id = {template["template_id"]: template for template in templates}
        self.assertEqual(set(template_by_id), set(REQUIRED_TEMPLATE_IDS))
        self.assertIn("KMFA_项目成本专题报告预览_v0_6_blue_zero_delta.html", template_by_id["project_cost_special_report"]["html_acceptance_sample_ref"])
        self.assertIn("KMFA_经营分析报告预览_v3_blue.html", template_by_id["business_overview_report"]["html_acceptance_sample_ref"])

        for template in templates:
            self.assertFalse(template["formal_report_allowed"])
            self.assertFalse(template["trusted_grade_assignment_allowed"])
            self.assertFalse(template["s10_p2_scope_included"])
            self.assertFalse(template["s10_p3_scope_included"])
            self.assertFalse(template["ui_scope_included"])
            self.assertFalse(template["external_connector_included"])

    def test_sections_are_management_readable_and_match_required_titles(self) -> None:
        manifest, templates, sections = build_default_report_template_artifacts(
            generated_at="2026-06-30T23:59:45+10:00"
        )
        validate_report_template_artifacts(manifest, templates, sections)

        titles_by_template: dict[str, list[str]] = {}
        for section in sections:
            titles_by_template.setdefault(section["template_id"], []).append(section["visible_title"])
            self.assertEqual(section["record_type"], "report_template_section")
            self.assertTrue(section["management_summary_prompt"].strip())
            self.assertTrue(section["source_metadata_refs"])
            self.assertFalse(section["raw_business_values_allowed"])
            self.assertFalse(section["internal_technical_title_visible"])

        self.assertEqual(
            titles_by_template["project_cost_special_report"],
            list(REQUIRED_PROJECT_COST_SECTION_TITLES),
        )
        self.assertEqual(
            titles_by_template["business_overview_report"],
            list(REQUIRED_BUSINESS_OVERVIEW_SECTION_TITLES),
        )

    def test_public_payload_has_no_raw_values_or_private_business_files(self) -> None:
        manifest, templates, sections = build_default_report_template_artifacts(
            generated_at="2026-06-30T23:59:45+10:00"
        )
        payload = json.dumps([manifest, templates, sections], ensure_ascii=False, sort_keys=True)

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
            "bank_account_number",
            "identity_document_number",
        ):
            self.assertNotIn(forbidden_text, payload)
        self.assertIn("source_ref://", payload)

    def test_validator_rejects_internal_technical_visible_titles(self) -> None:
        manifest, templates, sections = build_default_report_template_artifacts(
            generated_at="2026-06-30T23:59:45+10:00"
        )
        broken_sections = [dict(sections[0]), *sections[1:]]
        broken_sections[0]["visible_title"] = "S10-P1 validator manifest"

        with self.assertRaises(ReportTemplateError):
            validate_report_template_artifacts(manifest, templates, broken_sections)


if __name__ == "__main__":
    unittest.main()
