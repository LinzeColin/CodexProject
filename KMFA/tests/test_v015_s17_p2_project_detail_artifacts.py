from __future__ import annotations

import json
import struct
import unittest

from KMFA.tools import build_v015_s17_p2_project_detail as builder


class ProjectDetailArtifactTests(unittest.TestCase):
    def value(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_builder_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_manifest_stays_pending_until_receipt_bound_validation(self) -> None:
        value = self.value(builder.MANIFEST_PATH)
        if builder.receipts():
            self.assertEqual(value["phase_acceptance_status"], "PASSED")
            self.assertEqual(value["phase_task_accepted_count"], 3)
            self.assertTrue(value["s17_p3_entry_allowed"])
        else:
            self.assertEqual(value["phase_acceptance_status"], "PENDING_FINAL_VALIDATION")
            self.assertEqual(value["phase_task_accepted_count"], 0)
            self.assertFalse(value["s17_p3_entry_allowed"])
        self.assertTrue(value["s17_p1_started"])
        self.assertTrue(value["s17_p2_started"])
        self.assertFalse(value["s17_p3_started"])
        self.assertEqual(value["stage_execution_percentage"], 67)

    def test_overview_cost_and_navigation_contracts_are_complete(self) -> None:
        overview = self.value(builder.OVERVIEW_CONTRACT_PATH)
        cost = self.value(builder.COST_CONTRACT_PATH)
        navigation = self.value(builder.TAB_NAVIGATION_CONTRACT_PATH)
        self.assertTrue(overview["business_summary_first"])
        self.assertEqual(overview["technical_status_code_first_count"], 0)
        self.assertEqual(overview["money_equation_difference_cents"], 0)
        self.assertTrue(overview["engine_zero_difference_pass"])
        self.assertEqual(set(overview["engine_golden_difference_cents"].values()), {0})
        self.assertEqual(cost["category_count"], 10)
        self.assertEqual(cost["trend_period_count"], 4)
        self.assertEqual(cost["engine_difference_cents"], 0)
        self.assertEqual(cost["chart_table_difference_cents"], 0)
        self.assertTrue(cost["zero_difference_pass"])
        self.assertEqual(navigation["tab_count"], 5)
        self.assertEqual(navigation["section_overlap_count"], 0)
        self.assertTrue(navigation["preserves_list_context"])
        self.assertIn("page=2", navigation["return_url"])

    def test_html_is_human_readable_accessible_and_restrained(self) -> None:
        text = builder.HTML_PATH.read_text(encoding="utf-8")
        for token in (
            "返回项目列表",
            "当前判断",
            "成本",
            "收入与回款",
            "差异",
            "资料",
            "KMFA_PROJECT_DETAIL_TEST",
            "aria-live",
            "prefers-reduced-motion",
        ):
            self.assertIn(token, text)
        self.assertNotIn("/Users/linzezhang/Downloads/KMFA_MetaData", text)

    def test_five_public_screenshots_have_required_viewports(self) -> None:
        sizes = []
        for path in builder.SCREENSHOT_PATHS:
            data = path.read_bytes()[:24]
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            sizes.append(struct.unpack(">II", data[16:24]))
        for width, height in sizes[:4]:
            self.assertEqual(width, 1440)
            self.assertGreaterEqual(height, 1000)
        self.assertEqual(sizes[4][0], 390)
        self.assertGreaterEqual(sizes[4][1], 844)

    def test_human_documents_state_scope_and_next_gate_plainly(self) -> None:
        report = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        guide = builder.USER_GUIDE_PATH.read_text(encoding="utf-8")
        risks = builder.RISKS_ROLLBACK_PATH.read_text(encoding="utf-8")
        self.assertIn("项目目前赚钱", report)
        self.assertIn("差异均为 0 分", report)
        self.assertIn("返回项目列表", guide)
        self.assertIn("未归集成本", risks)
        self.assertIn("新的独立 Run 中进行 S17-P3", report)


if __name__ == "__main__":
    unittest.main()
