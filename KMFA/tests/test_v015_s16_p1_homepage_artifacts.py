from __future__ import annotations

import json
import struct
import unittest

from KMFA.tools import build_v015_s16_p1_homepage as builder


class HomepageArtifactTests(unittest.TestCase):
    def value(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_builder_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_manifest_stays_pending_until_receipt_bound_validation(self) -> None:
        manifest = self.value(builder.MANIFEST_PATH)
        if builder.receipts():
            self.assertEqual(manifest["phase_acceptance_status"], "PASSED")
            self.assertEqual(manifest["phase_task_accepted_count"], 3)
            self.assertTrue(manifest["s16_p2_entry_allowed"])
        else:
            self.assertEqual(manifest["phase_acceptance_status"], "PENDING_FINAL_VALIDATION")
            self.assertEqual(manifest["phase_task_accepted_count"], 0)
            self.assertFalse(manifest["s16_p2_entry_allowed"])
        self.assertTrue(manifest["s16_p1_started"])
        self.assertFalse(manifest["s16_p2_started"])
        self.assertFalse(manifest["s16_p3_started"])
        self.assertFalse(manifest["s16_stage_review_entry_allowed"])
        self.assertFalse(manifest["s17_entry_allowed"])
        self.assertEqual(manifest["stage_execution_percentage"], 33)

    def test_summary_focus_trend_and_portfolio_contracts_are_complete(self) -> None:
        summary = self.value(builder.SUMMARY_CONTRACT_PATH)
        focus = self.value(builder.FOCUS_CONTRACT_PATH)
        visual = self.value(builder.VISUAL_CONTRACT_PATH)
        self.assertEqual(summary["metric_count"], 5)
        self.assertEqual(summary["source_bound_metric_count"], 5)
        self.assertEqual(summary["cutoff_bound_metric_count"], 5)
        self.assertEqual(summary["completeness_bound_metric_count"], 5)
        self.assertEqual(summary["partial_example"]["overall_completeness"], "INCOMPLETE")
        self.assertFalse(summary["partial_example"]["complete_management_conclusion_available"])
        self.assertEqual(summary["missing_as_zero_count"], 0)
        self.assertEqual(focus["focus_item_count"], 5)
        self.assertEqual(focus["primary_action_count"], 5)
        self.assertTrue(focus["one_primary_action_each"])
        self.assertEqual(focus["automatic_execution_count"], 0)
        self.assertEqual(visual["trend_series_count"], 3)
        self.assertEqual(visual["trend_period_count"], 4)
        self.assertEqual(visual["trend_table_alternative_count"], 3)
        self.assertEqual(visual["project_portfolio_count"], 4)
        self.assertEqual(visual["decorative_radar_chart_count"], 0)

    def test_html_snapshot_is_human_readable_accessible_and_restrained(self) -> None:
        text = builder.HTML_PATH.read_text(encoding="utf-8")
        for token in (
            "今天先看这 5 件事",
            "核心经营摘要",
            "本期重点事项",
            "近四期趋势",
            "趋势数据表",
            "项目组合",
            "资料不完整",
            "KMFA_HOMEPAGE_TEST",
            "aria-live",
            "prefers-reduced-motion",
        ):
            self.assertIn(token, text)
        for forbidden in (
            "/Users/linzezhang/Downloads/KMFA_MetaData",
            "background-clip:text",
            "border-radius:32px",
            "radar",
        ):
            self.assertNotIn(forbidden, text)

    def test_four_public_screenshots_have_expected_viewports(self) -> None:
        sizes = []
        for path in builder.SCREENSHOT_PATHS:
            data = path.read_bytes()[:24]
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            sizes.append(struct.unpack(">II", data[16:24]))
        self.assertEqual(sizes[:2], [(1440, 1000), (1440, 1000)])
        self.assertEqual(sizes[2][0], 1440)
        self.assertGreaterEqual(sizes[2][1], 1000)
        self.assertEqual(sizes[3][0], 390)
        self.assertGreaterEqual(sizes[3][1], 844)

    def test_human_documents_use_plain_chinese_and_keep_s16_p2_separate(self) -> None:
        report = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        guide = builder.USER_GUIDE_PATH.read_text(encoding="utf-8")
        tests = builder.TEST_RESULTS_PATH.read_text(encoding="utf-8")
        risks = builder.RISKS_ROLLBACK_PATH.read_text(encoding="utf-8")
        self.assertIn("资料缺失时显示“资料不足”", report)
        self.assertIn("每个数字下方都写明来源", guide)
        self.assertIn("缺失值伪装为 0", tests)
        self.assertIn("只验证首页结构与交互", risks)
        self.assertIn("新的独立 Run 中进行 S16-P2", report)


if __name__ == "__main__":
    unittest.main()
