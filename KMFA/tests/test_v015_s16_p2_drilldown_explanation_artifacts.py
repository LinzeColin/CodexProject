from __future__ import annotations

import json
import struct
import unittest

from KMFA.tools import build_v015_s16_p2_drilldown_explanation as builder


class DrilldownArtifactTests(unittest.TestCase):
    def value(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_builder_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_manifest_stays_pending_until_receipt_bound_validation(self) -> None:
        value = self.value(builder.MANIFEST_PATH)
        if builder.receipts():
            self.assertEqual(value["phase_acceptance_status"], "PASSED")
            self.assertEqual(value["phase_task_accepted_count"], 3)
            self.assertTrue(value["s16_p3_entry_allowed"])
        else:
            self.assertEqual(value["phase_acceptance_status"], "PENDING_FINAL_VALIDATION")
            self.assertEqual(value["phase_task_accepted_count"], 0)
            self.assertFalse(value["s16_p3_entry_allowed"])
        self.assertTrue(value["s16_p2_started"])
        self.assertFalse(value["s16_p3_started"])
        self.assertFalse(value["s16_stage_review_entry_allowed"])
        self.assertFalse(value["s17_entry_allowed"])
        self.assertEqual(value["stage_execution_percentage"], 67)

    def test_drilldown_explanation_and_comparison_contracts_are_complete(self) -> None:
        drilldown = self.value(builder.DRILLDOWN_CONTRACT_PATH)
        explanation = self.value(builder.EXPLANATION_CONTRACT_PATH)
        comparison = self.value(builder.COMPARISON_CONTRACT_PATH)
        self.assertEqual(drilldown["metric_count"], 5)
        self.assertEqual(drilldown["drilldown_route_count"], 5)
        self.assertEqual(drilldown["preserved_filter_count"], 4)
        self.assertEqual(drilldown["primary_exact_count"], 5)
        self.assertEqual(drilldown["secondary_exact_count"], 5)
        self.assertEqual(explanation["short_explanation_count"], 5)
        self.assertEqual(explanation["complete_lineage_count"], 5)
        self.assertEqual(explanation["technical_log_count"], 0)
        self.assertFalse(explanation["missing_lineage_detail_allowed"])
        self.assertEqual(comparison["comparison_kind_count"], 3)
        self.assertEqual(comparison["exact_comparison_allowed_count"], 3)
        self.assertTrue(comparison["basis_mismatch_blocked"])
        self.assertTrue(comparison["coverage_mismatch_blocked"])

    def test_html_snapshot_is_human_readable_accessible_and_restrained(self) -> None:
        text = builder.HTML_PATH.read_text(encoding="utf-8")
        for token in (
            "返回经营首页",
            "当前数字",
            "这个数字怎么来的",
            "组成明细",
            "期间比较",
            "查看专业依据",
            "KMFA_DRILLDOWN_TEST",
            "aria-live",
            "prefers-reduced-motion",
        ):
            self.assertIn(token, text)
        for forbidden in (
            "/Users/linzezhang/Downloads/KMFA_MetaData",
            "background-clip:text",
            "border-radius:32px",
        ):
            self.assertNotIn(forbidden, text)

    def test_four_public_screenshots_have_expected_viewports(self) -> None:
        sizes = []
        for path in builder.SCREENSHOT_PATHS:
            data = path.read_bytes()[:24]
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            sizes.append(struct.unpack(">II", data[16:24]))
        self.assertEqual(sizes[0], (1440, 1000))
        self.assertEqual(sizes[2], (1440, 1000))
        self.assertEqual(sizes[1][0], 1440)
        self.assertGreaterEqual(sizes[1][1], 1000)
        self.assertEqual(sizes[3][0], 390)
        self.assertGreaterEqual(sizes[3][1], 844)

    def test_human_documents_use_plain_chinese_and_keep_s16_p3_separate(self) -> None:
        report = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        guide = builder.USER_GUIDE_PATH.read_text(encoding="utf-8")
        tests = builder.TEST_RESULTS_PATH.read_text(encoding="utf-8")
        risks = builder.RISKS_ROLLBACK_PATH.read_text(encoding="utf-8")
        self.assertIn("首页 5 个核心数字", report)
        self.assertIn("点击任一核心数字", guide)
        self.assertIn("口径与覆盖阻断", tests)
        self.assertIn("只验证交互、计算与阻断规则", risks)
        self.assertIn("新的独立 Run 中进行 S16-P3", report)


if __name__ == "__main__":
    unittest.main()
