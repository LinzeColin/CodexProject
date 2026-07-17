from __future__ import annotations

import json
import struct
import unittest

from KMFA.tools import build_v015_s17_p1_project_list as builder


class ProjectListArtifactTests(unittest.TestCase):
    def value(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_builder_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_manifest_stays_pending_until_receipt_bound_validation(self) -> None:
        value = self.value(builder.MANIFEST_PATH)
        if builder.receipts():
            self.assertEqual(value["phase_acceptance_status"], "PASSED")
            self.assertEqual(value["phase_task_accepted_count"], 3)
            self.assertTrue(value["s17_p2_entry_allowed"])
        else:
            self.assertEqual(value["phase_acceptance_status"], "PENDING_FINAL_VALIDATION")
            self.assertEqual(value["phase_task_accepted_count"], 0)
            self.assertFalse(value["s17_p2_entry_allowed"])
        self.assertTrue(value["s17_p1_started"])
        self.assertFalse(value["s17_p2_started"])
        self.assertFalse(value["s17_p3_started"])
        self.assertEqual(value["stage_execution_percentage"], 33)

    def test_table_order_and_batch_contracts_are_complete(self) -> None:
        table = self.value(builder.TABLE_CONTRACT_PATH)
        order = self.value(builder.ORDER_CONTRACT_PATH)
        batch = self.value(builder.BATCH_CONTRACT_PATH)
        self.assertEqual(table["catalog_project_count"], 18)
        self.assertEqual(table["company_count"], 3)
        self.assertEqual(table["project_count_per_company"], 6)
        self.assertEqual(table["available_column_count"], 12)
        self.assertEqual(table["default_visible_column_count"], 8)
        self.assertEqual(table["filter_dimension_count"], 7)
        self.assertEqual(len(table["stable_project_ids"]), 6)
        self.assertEqual(order["group_option_count"], 6)
        self.assertEqual(order["sort_option_count"], 5)
        self.assertEqual(order["hidden_composite_score_count"], 0)
        self.assertEqual(order["stable_tie_breaker"], "project_id")
        self.assertEqual(batch["minimum_project_count"], 2)
        self.assertEqual(batch["maximum_project_count"], 6)
        self.assertTrue(batch["export_source_columns_present"])
        self.assertEqual(batch["fact_layer_write_count"], 0)

    def test_html_is_human_readable_accessible_and_restrained(self) -> None:
        text = builder.HTML_PATH.read_text(encoding="utf-8")
        for token in (
            "项目列表",
            "设置显示列",
            "对比所选",
            "导出附表",
            "KMFA_PROJECT_LIST_TEST",
            "aria-live",
            "prefers-reduced-motion",
        ):
            self.assertIn(token, text)
        self.assertNotIn("/Users/linzezhang/Downloads/KMFA_MetaData", text)

    def test_four_public_screenshots_have_required_viewports(self) -> None:
        sizes = []
        for path in builder.SCREENSHOT_PATHS:
            data = path.read_bytes()[:24]
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            sizes.append(struct.unpack(">II", data[16:24]))
        for width, height in sizes[:3]:
            self.assertEqual(width, 1440)
            self.assertGreaterEqual(height, 1000)
        self.assertEqual(sizes[3][0], 390)
        self.assertGreaterEqual(sizes[3][1], 844)

    def test_human_documents_state_scope_and_next_gate_plainly(self) -> None:
        report = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        guide = builder.USER_GUIDE_PATH.read_text(encoding="utf-8")
        risks = builder.RISKS_ROLLBACK_PATH.read_text(encoding="utf-8")
        self.assertIn("默认只显示", report)
        self.assertIn("没有隐藏评分", guide)
        self.assertIn("公开合成内容", risks)
        self.assertIn("新的独立 Run 中进行 S17-P2", report)


if __name__ == "__main__":
    unittest.main()
