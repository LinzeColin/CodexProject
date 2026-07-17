from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s23_p2_precision_stress_extreme as builder


class PrecisionStressExtremeArtifactTests(unittest.TestCase):
    @staticmethod
    def value(path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_manifest_stays_inside_s23_p2(self) -> None:
        value = self.value(builder.MANIFEST_PATH)
        self.assertIn(value["phase_acceptance_status"], {"PENDING_FINAL_VALIDATION", "PASSED"})
        self.assertEqual((value["run_phase_id"], value["roadmap_phase_id"], value["stage_execution_percentage"]), ("V015_S23_P2_PRECISION_STRESS_EXTREME", "S23-P2", 67))
        self.assertEqual((value["raw_root_access_count"], value["raw_write_count"], value["external_network_request_count"]), (0, 0, 0))
        self.assertTrue(value["s23_p2_started"])
        self.assertFalse(value["s23_p3_started"] or value["s23_stage_review_started"] or value["github_upload_performed"] or value["app_reinstall_performed"])

    def test_precision_performance_and_recovery_reports_are_real(self) -> None:
        precision = self.value(builder.PRECISION_REPORT_PATH)
        performance = self.value(builder.PERFORMANCE_REPORT_PATH)
        extreme = self.value(builder.EXTREME_REPORT_PATH)
        self.assertEqual((precision["case_count"], precision["difference_cents"], precision["float_money_accept_count"]), (20000, 0, 0))
        self.assertEqual((performance["synthetic_file_count"], performance["worksheet_count"], performance["concurrent_import_count"], performance["concurrent_report_count"], performance["data_error_count"]), (128, 64, 128, 128, 0))
        self.assertLessEqual(performance["total_elapsed_ms"], performance["total_elapsed_budget_ms"])
        self.assertEqual((extreme["attack_case_count"], extreme["rejected_attack_count"], extreme["successful_recovery_count"], extreme["data_pollution_count"]), (9, 9, 1, 0))

    def test_task_matrix_and_human_reports_are_complete(self) -> None:
        matrix = self.value(builder.TASK_MATRIX_PATH)
        self.assertEqual((matrix["phase_task_count"], len(matrix["tasks"])), (3, 3))
        self.assertTrue(all(row["status"] == "PASS" for row in matrix["tasks"]))
        for path in (builder.COMPLETION_REPORT_PATH, builder.PRECISION_REPORT_ZH_PATH, builder.PERFORMANCE_REPORT_ZH_PATH, builder.EXTREME_REPORT_ZH_PATH, builder.TEST_RESULTS_PATH, builder.RISKS_ROLLBACK_PATH):
            self.assertGreater(len(path.read_text(encoding="utf-8")), 100, path)


if __name__ == "__main__":
    unittest.main()
