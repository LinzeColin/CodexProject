from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s21_p1_report_model as builder


class ReportModelArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        builder.check_outputs()

    def value(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_manifest_is_bound_to_s21_p1_only(self) -> None:
        value = self.value(builder.MANIFEST_PATH)
        self.assertEqual(value["roadmap_phase_id"], "S21-P1")
        self.assertTrue(value["s21_p1_started"])
        self.assertFalse(value["s21_p2_started"])
        self.assertFalse(value["s21_p3_started"])

    def test_period_versions_are_immutable_and_bound(self) -> None:
        value = self.value(builder.PERIOD_VERSION_PATH)
        self.assertEqual((value["period_kind_count"], value["version_count"]), (5, 2))
        self.assertEqual((value["source_binding_count"], value["formula_binding_count"]), (6, 2))
        self.assertTrue(value["first_version_preserved"] and value["hash_chain_bound"])
        self.assertFalse(value["history_overwrite_allowed"])

    def test_audiences_and_limitations_are_human_readable(self) -> None:
        audience, trust = self.value(builder.AUDIENCE_PATH), self.value(builder.TRUST_PATH)
        self.assertEqual((audience["management_section_count"], audience["professional_section_count"]), (5, 1))
        self.assertEqual((audience["data_check_board_backend_content_count"], audience["technical_log_content_count"]), (0, 0))
        self.assertFalse(trust["incomplete_case"]["complete_report_claim_allowed"])
        self.assertEqual(trust["technical_grade_abbreviation_count"], 0)

    def test_public_checks_and_browser_evidence_are_complete(self) -> None:
        checks, browser = self.value(builder.PUBLIC_CHECKS_PATH), self.value(builder.BROWSER_PATH)
        self.assertEqual((checks["public_check_count"], checks["public_check_pass_count"], checks["public_check_failed_count"]), (55, 55, 0))
        self.assertEqual((browser["browser_flow_count"], browser["visual_evidence_count"]), (8, 5))
        self.assertTrue(all(path.is_file() and path.stat().st_size > 10_000 for path in builder.SCREENSHOT_PATHS))

    def test_business_report_and_release_actions_remain_closed(self) -> None:
        value = self.value(builder.MANIFEST_PATH)
        for key in ("html_report_generation_count", "pdf_report_generation_count", "spreadsheet_report_generation_count", "approval_or_publication_count", "raw_root_access_count", "raw_write_count"):
            self.assertEqual(value[key], 0)
        self.assertFalse(value["formal_business_report"] or value["github_upload_performed"] or value["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
