from __future__ import annotations

import json
import struct
import unittest

from KMFA.tools import build_v015_s23_p1_end_to_end_business_flow as builder


class EndToEndBusinessFlowArtifactTests(unittest.TestCase):
    @staticmethod
    def value(path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_manifest_stays_inside_s23_p1(self) -> None:
        value = self.value(builder.MANIFEST_PATH)
        self.assertIn(value["phase_acceptance_status"], {"PENDING_FINAL_VALIDATION", "PASSED"})
        self.assertEqual((value["run_phase_id"], value["roadmap_phase_id"], value["phase_task_count"]), ("V015_S23_P1_END_TO_END_BUSINESS_FLOW", "S23-P1", 3))
        self.assertEqual((value["raw_root_access_count"], value["raw_write_count"], value["external_network_request_count"]), (0, 0, 0))
        self.assertTrue(value["s23_p1_started"])
        self.assertFalse(value["s23_p2_started"] or value["s23_p3_started"] or value["s23_stage_review_started"] or value["github_upload_performed"] or value["app_reinstall_performed"])

    def test_authoritative_trace_and_zero_difference(self) -> None:
        trace = self.value(builder.TRACE_PATH)
        consistency = self.value(builder.CONSISTENCY_PATH)
        self.assertEqual((trace["publication_version_count"], trace["backend_view_count"], trace["homepage_authoritative_binding_count"], trace["authoritative_project_count"], trace["project_difference_cents"]), (1, 4, 1, 4, 0))
        self.assertEqual((trace["report_version_count"], trace["report_export_count"], trace["workflow_case_count"], trace["workflow_step_count_per_case"], trace["revision_unexplained_difference_count"]), (2, 2, 2, 5, 0))
        self.assertEqual((consistency["formats"], consistency["numeric_value_count"], consistency["difference_integer"], consistency["xlsx_sheet_count"], consistency["xlsx_formula_error_count"], consistency["xlsx_visual_pass_count"]), (["HTML", "PDF", "CSV", "XLSX"], 26, 0, 3, 0, 3))

    def test_excel_deliverable_has_valid_signature(self) -> None:
        self.assertGreater(builder.DELIVERABLE_PATH.stat().st_size, 5_000)
        self.assertEqual(builder.DELIVERABLE_PATH.read_bytes()[:2], b"PK")
        self.assertEqual(self.value(builder.CONSISTENCY_PATH)["deliverable_sha256"], builder._sha256(builder.DELIVERABLE_PATH))

    def test_eight_screenshots_have_expected_dimensions(self) -> None:
        for index, path in enumerate(builder.SCREENSHOT_PATHS):
            data = path.read_bytes()[:24]
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            width, height = struct.unpack(">II", data[16:24])
            if index < 7:
                self.assertGreaterEqual(width, 1000)
                self.assertGreaterEqual(height, 700)
            else:
                self.assertEqual(width, 390)
                self.assertGreaterEqual(height, 800)

    def test_human_documents_are_plain_chinese(self) -> None:
        for path in (builder.COMPLETION_REPORT_PATH, builder.TEST_RESULTS_PATH, builder.USER_GUIDE_PATH, builder.RISKS_ROLLBACK_PATH):
            self.assertGreater(len(path.read_text(encoding="utf-8")), 150)
        self.assertIn("0 分", builder.COMPLETION_REPORT_PATH.read_text(encoding="utf-8"))
        self.assertIn("一分钱", builder.USER_GUIDE_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
