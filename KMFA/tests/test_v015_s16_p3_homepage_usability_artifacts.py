from __future__ import annotations

import json
import struct
import unittest

from KMFA.tools import build_v015_s16_p3_homepage_usability as builder


class HomepageUsabilityArtifactTests(unittest.TestCase):
    def value(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_builder_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_manifest_stays_pending_until_receipt_bound_validation(self) -> None:
        value = self.value(builder.MANIFEST_PATH)
        if builder.receipts():
            self.assertEqual(value["phase_acceptance_status"], "PASSED")
            self.assertEqual(value["phase_task_accepted_count"], 3)
            self.assertTrue(value["s16_stage_review_entry_allowed"])
        else:
            self.assertEqual(value["phase_acceptance_status"], "PENDING_FINAL_VALIDATION")
            self.assertEqual(value["phase_task_accepted_count"], 0)
            self.assertFalse(value["s16_stage_review_entry_allowed"])
        self.assertTrue(value["s16_p3_started"])
        self.assertFalse(value["s16_stage_review_started"])
        self.assertFalse(value["s17_entry_allowed"])
        self.assertEqual(value["stage_execution_percentage"], 100)

    def test_recognition_click_and_fault_contracts_are_complete(self) -> None:
        recognition = self.value(builder.RECOGNITION_CONTRACT_PATH)
        paths = self.value(builder.TASK_PATH_CONTRACT_PATH)
        states = self.value(builder.STATE_CONTRACT_PATH)
        self.assertEqual(recognition["case_count"], 6)
        self.assertEqual(recognition["pass_count"], 6)
        self.assertEqual(recognition["success_bps"], 10_000)
        self.assertGreaterEqual(recognition["success_bps"], recognition["success_threshold_bps"])
        self.assertEqual(recognition["external_human_participant_count"], 0)
        self.assertFalse(recognition["external_human_study_claimed"])
        self.assertEqual(paths["task_count"], 3)
        self.assertEqual(paths["observed_max_clicks"], 1)
        self.assertEqual(paths["dead_end_count"], 0)
        self.assertEqual(states["state_count"], 3)
        self.assertEqual(states["blank_page_count"], 0)
        self.assertEqual(states["fake_business_value_count"], 0)

    def test_html_is_human_readable_accessible_and_restrained(self) -> None:
        text = builder.HTML_PATH.read_text(encoding="utf-8")
        for token in (
            "经营状态",
            "先处理这 3 项",
            "homepage-state-panel",
            "KMFA_HOMEPAGE_USABILITY_TEST",
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

    def test_five_public_screenshots_have_exact_viewports(self) -> None:
        sizes = []
        for path in builder.SCREENSHOT_PATHS:
            data = path.read_bytes()[:24]
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            sizes.append(struct.unpack(">II", data[16:24]))
        self.assertEqual(sizes[0], (1440, 1000))
        self.assertEqual(sizes[1], (390, 844))
        self.assertEqual(sizes[2:], [(1440, 1000), (1440, 1000), (1440, 1000)])

    def test_human_documents_state_method_limit_and_next_gate_plainly(self) -> None:
        report = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        tests = builder.TEST_RESULTS_PATH.read_text(encoding="utf-8")
        risks = builder.RISKS_ROLLBACK_PATH.read_text(encoding="utf-8")
        observation = builder.OBSERVATION_PATH.read_text(encoding="utf-8")
        self.assertIn("前三项重点", report)
        self.assertIn("不是外部真人样本", tests)
        self.assertIn("不等同于真实用户研究", risks)
        self.assertIn("手机检查发现", observation)
        self.assertIn("新的独立 Run 中进行 S16 整体复审", report)


if __name__ == "__main__":
    unittest.main()
