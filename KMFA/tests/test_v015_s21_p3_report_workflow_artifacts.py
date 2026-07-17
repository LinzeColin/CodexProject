from __future__ import annotations

import json
import struct
import unittest

from KMFA.tools import build_v015_s21_p3_report_workflow as builder


class ReportWorkflowArtifactTests(unittest.TestCase):
    def value(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_manifest_is_pending_or_final_and_stays_inside_s21_p3(self) -> None:
        value = self.value(builder.MANIFEST_PATH)
        self.assertIn(value["phase_acceptance_status"], {"PENDING_FINAL_VALIDATION", "PASSED"})
        self.assertEqual((value["run_phase_id"], value["roadmap_phase_id"], value["workflow_action_count"]), ("V015_S21_P3_REPORT_WORKFLOW", "S21-P3", 5))
        self.assertEqual((value["internal_publication_count"], value["external_publication_count"], value["public_share_link_count"]), (1, 0, 0))
        self.assertFalse(value["s21_stage_review_started"])
        self.assertFalse(value["s22_p1_started"])
        self.assertFalse(value["github_upload_performed"])
        self.assertFalse(value["app_reinstall_performed"])

    def test_quality_workflow_comparison_and_center_contracts_are_complete(self) -> None:
        quality = self.value(builder.QUALITY_GATE_PATH)
        workflow = self.value(builder.WORKFLOW_PATH)
        comparison = self.value(builder.COMPARISON_PATH)
        center = self.value(builder.REPORT_CENTER_PATH)
        self.assertEqual((quality["status"], quality["check_count"], quality["failed_count"]), ("PASS", 15, 0))
        self.assertEqual((workflow["workflow_action_count"], workflow["event_count"], workflow["published_case_state"]), (5, 5, "PUBLISHED_INTERNAL"))
        self.assertTrue(workflow["all_events_bind_actor"] and workflow["all_events_bind_time"] and workflow["all_events_bind_comment"])
        self.assertGreaterEqual(comparison["difference_count"], 1)
        self.assertEqual(comparison["unexplained_difference_count"], 0)
        self.assertTrue(comparison["publication_allowed"])
        self.assertEqual((center["filter_count"], center["tax_download_format_count"], center["public_link_count"]), (6, 0, 0))

    def test_browser_visual_evidence_has_expected_dimensions(self) -> None:
        sizes = []
        for path in builder.SCREENSHOT_PATHS:
            data = path.read_bytes()[:24]
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            sizes.append(struct.unpack(">II", data[16:24]))
        self.assertTrue(all(width >= 1000 and height >= 700 for width, height in sizes[:5]))
        self.assertEqual(sizes[5][0], 390)
        self.assertGreaterEqual(sizes[5][1], 800)

    def test_public_checks_and_task_matrix_are_complete(self) -> None:
        checks = self.value(builder.PUBLIC_CHECKS_PATH)
        matrix = self.value(builder.TASK_MATRIX_PATH)
        browser = self.value(builder.BROWSER_PATH)
        self.assertEqual((checks["status"], checks["public_check_count"], checks["public_check_failed_count"]), ("PASS", 53, 0))
        self.assertEqual((matrix["phase_task_count"], len(matrix["tasks"])), (3, 3))
        self.assertTrue(all(row["status"] == "PASS" for row in matrix["tasks"]))
        self.assertEqual((browser["browser_flow_count"], browser["visual_evidence_count"], browser["external_network_request_count"]), (8, 6, 0))

    def test_human_documents_are_plain_chinese_and_present(self) -> None:
        for path in (
            builder.IMPLEMENTATION_REPORT_PATH, builder.USER_GUIDE_PATH,
            builder.TEST_RESULTS_PATH, builder.RISKS_ROLLBACK_PATH,
        ):
            text = path.read_text(encoding="utf-8")
            self.assertGreater(len(text), 120)
        self.assertIn("五步", builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8"))
        self.assertIn("没有公开链接", builder.USER_GUIDE_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
