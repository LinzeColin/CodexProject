from __future__ import annotations

import json
import struct
import unittest

from KMFA.tools import build_v015_s15_p3_app_experience as builder


class AppExperienceArtifactTests(unittest.TestCase):
    def value(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_builder_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_manifest_stays_pending_until_receipt_bound_validation(self) -> None:
        manifest = self.value(builder.MANIFEST_PATH)
        if builder.receipts():
            self.assertEqual(manifest["phase_acceptance_status"], "PASSED")
            self.assertEqual(manifest["phase_task_accepted_count"], 3)
            self.assertTrue(manifest["s15_stage_review_entry_allowed"])
        else:
            self.assertEqual(manifest["phase_acceptance_status"], "PENDING_FINAL_VALIDATION")
            self.assertEqual(manifest["phase_task_accepted_count"], 0)
            self.assertFalse(manifest["s15_stage_review_entry_allowed"])
        self.assertTrue(manifest["s15_p3_started"])
        self.assertFalse(manifest["s15_stage_review_started"])
        self.assertFalse(manifest["s16_entry_allowed"])
        self.assertEqual(manifest["stage_execution_percentage"], 100)

    def test_search_notification_and_preference_contracts_are_complete(self) -> None:
        search = self.value(builder.SEARCH_CONTRACT_PATH)
        notices = self.value(builder.NOTIFICATION_CONTRACT_PATH)
        preferences = self.value(builder.PREFERENCE_CONTRACT_PATH)
        self.assertEqual(search["search_kind_count"], 4)
        self.assertTrue(search["all_visible_results_have_source"])
        self.assertEqual(search["management_sensitive_result_count"], 0)
        self.assertEqual(search["finance_sensitive_result_count"], 1)
        self.assertEqual(search["sensitive_result_leak_count"], 0)
        self.assertEqual(notices["notification_category_count"], 4)
        self.assertEqual(notices["action_entry_count"], notices["finance_visible_count"])
        self.assertEqual(notices["notification_without_action_count"], 0)
        self.assertEqual(preferences["preference_field_count"], 4)
        self.assertEqual(preferences["persistence_scope"], "CURRENT_USER_ONLY")
        self.assertFalse(preferences["other_user_write_allowed"])
        self.assertEqual(preferences["fact_layer_write_count"], 0)
        self.assertEqual(preferences["raw_write_count"], 0)

    def test_html_snapshot_is_human_readable_accessible_and_restrained(self) -> None:
        text = builder.HTML_PATH.read_text(encoding="utf-8")
        for token in (
            "搜索项目、客户、报告或待办",
            "最近访问",
            "通知与待办",
            "偏好设置",
            "不会修改经营事实",
            "KMFA_EXPERIENCE_TEST",
            "aria-live",
            "prefers-reduced-motion",
        ):
            self.assertIn(token, text)
        for forbidden in (
            "/Users/linzezhang/Downloads/KMFA_MetaData",
            "background-clip:text",
            "border-radius:32px",
            "border-radius:40px",
        ):
            self.assertNotIn(forbidden, text)

    def test_four_public_screenshots_have_expected_viewports(self) -> None:
        sizes = []
        for path in builder.SCREENSHOT_PATHS:
            data = path.read_bytes()[:24]
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            sizes.append(struct.unpack(">II", data[16:24]))
        self.assertEqual(sizes[:3], [(1440, 1000), (1440, 1000), (1440, 1000)])
        self.assertEqual(sizes[3][0], 390)
        self.assertGreaterEqual(sizes[3][1], 844)

    def test_human_documents_use_plain_chinese_and_keep_stage_review_separate(self) -> None:
        report = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        guide = builder.USER_GUIDE_PATH.read_text(encoding="utf-8")
        tests = builder.TEST_RESULTS_PATH.read_text(encoding="utf-8")
        risks = builder.RISKS_ROLLBACK_PATH.read_text(encoding="utf-8")
        self.assertIn("每一项都有明确处理入口", report)
        self.assertIn("不会改写经营事实", guide)
        self.assertIn("无入口提醒", tests)
        self.assertIn("不是生产搜索索引", risks)
        self.assertIn("新的独立 Run 中进行 S15 整体复审", report)


if __name__ == "__main__":
    unittest.main()
