from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s23_p3_stability_usability as builder


class StabilityUsabilityArtifactTests(unittest.TestCase):
    @staticmethod
    def value(path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_manifest_stays_inside_s23_p3(self) -> None:
        value = self.value(builder.MANIFEST_PATH)
        self.assertIn(value["phase_acceptance_status"], {"PENDING_FINAL_VALIDATION", "PASSED"})
        self.assertEqual((value["run_phase_id"], value["roadmap_phase_id"], value["stage_execution_percentage"]), ("V015_S23_P3_STABILITY_USABILITY", "S23-P3", 100))
        self.assertEqual((value["raw_root_access_count"], value["raw_write_count"], value["external_network_request_count"]), (0, 0, 0))
        self.assertTrue(value["s23_p3_started"])
        self.assertFalse(value["s23_stage_review_started"] or value["s24_started"] or value["github_upload_performed"] or value["app_reinstall_performed"])

    def test_real_soak_browser_and_accessibility_reports_pass(self) -> None:
        soak, browser = self.value(builder.SOAK_REPORT_PATH), self.value(builder.BROWSER_ACCEPTANCE_PATH)
        accessibility = self.value(builder.ACCESSIBILITY_REPORT_PATH)
        self.assertEqual((soak["soak_cycle_count"], soak["restart_count"], soak["refresh_count"], soak["silent_error_count"]), (12, 3, 24, 0))
        self.assertEqual((browser["status"], browser["usability"]["completed_task_count"], browser["accessibility"]["fail_count"]), ("PASS", 3, 0))
        self.assertEqual((accessibility["check_count"], accessibility["pass_count"], accessibility["fail_count"]), (34, 34, 0))
        self.assertEqual(len(browser["screenshot_paths"]), 7)

    def test_task_matrix_and_human_reports_are_complete(self) -> None:
        matrix = self.value(builder.TASK_MATRIX_PATH)
        self.assertEqual((matrix["phase_task_count"], len(matrix["tasks"])), (3, 3))
        self.assertTrue(all(row["status"] == "PASS" for row in matrix["tasks"]))
        for path in (builder.COMPLETION_REPORT_PATH, builder.STABILITY_REPORT_ZH_PATH, builder.USABILITY_REPORT_ZH_PATH, builder.ACCESSIBILITY_REPORT_ZH_PATH, builder.TEST_RESULTS_PATH, builder.RISKS_ROLLBACK_PATH):
            self.assertGreater(len(path.read_text(encoding="utf-8")), 100, path)


if __name__ == "__main__":
    unittest.main()
