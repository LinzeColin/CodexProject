from __future__ import annotations

import json
import struct
import unittest

from KMFA.tools import build_v015_s15_p1_app_shell as builder


class AppShellArtifactTests(unittest.TestCase):
    def value(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_builder_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_manifest_is_pending_before_formal_validation(self) -> None:
        manifest = self.value(builder.MANIFEST_PATH)
        if builder.receipts():
            self.assertEqual(manifest["phase_acceptance_status"], "PASSED")
            self.assertEqual(manifest["phase_task_accepted_count"], 3)
            self.assertTrue(manifest["s15_p2_entry_allowed"])
        else:
            self.assertEqual(manifest["phase_acceptance_status"], "PENDING_FINAL_VALIDATION")
            self.assertEqual(manifest["phase_task_accepted_count"], 0)
            self.assertFalse(manifest["s15_p2_entry_allowed"])
        self.assertFalse(manifest["s15_p2_started"])
        self.assertFalse(manifest["s15_p3_started"])
        self.assertFalse(manifest["s15_stage_review_started"])
        self.assertEqual(manifest["stage_execution_percentage"], 33)

    def test_runtime_context_error_and_isolation_contracts_are_complete(self) -> None:
        runtime = self.value(builder.RUNTIME_CONTRACT_PATH)
        context = self.value(builder.CONTEXT_CONTRACT_PATH)
        errors = self.value(builder.ERROR_CONTRACT_PATH)
        isolation = self.value(builder.ISOLATION_CONTRACT_PATH)
        browser = self.value(builder.BROWSER_CONTRACT_PATH)
        self.assertEqual(runtime["transport"], "LOCALHOST_HTTP")
        self.assertFalse(runtime["static_html_only"])
        self.assertEqual(runtime["deep_link_route_count"], 18)
        self.assertEqual(context["dimension_count"], 4)
        self.assertEqual(context["persistence_mechanisms"], ["URL_QUERY", "LOCAL_STORAGE"])
        self.assertEqual(len(errors["faults"]), 4)
        self.assertFalse(errors["white_screen_allowed"])
        self.assertFalse(errors["silent_failure_allowed"])
        self.assertEqual(isolation["guard_count"], 3)
        self.assertEqual(isolation["observed_cross_company_leak_count"], 0)
        self.assertEqual(browser["page_kind"], "LOCALHOST_RUNTIME_SPA")
        self.assertEqual(len(browser["required_flows"]), 6)

    def test_html_snapshot_contains_real_runtime_features(self) -> None:
        text = builder.HTML_PATH.read_text(encoding="utf-8")
        for token in (
            "fetch('/api/context?'",
            "AbortController",
            "localStorage",
            "pushState",
            "aria-live",
            "prefers-reduced-motion",
        ):
            self.assertIn(token, text)
        self.assertNotIn("/Users/linzezhang/Downloads/KMFA_MetaData", text)

    def test_four_public_screenshots_have_expected_viewports(self) -> None:
        self.assertEqual(len(builder.SCREENSHOT_PATHS), 4)
        sizes = []
        for path in builder.SCREENSHOT_PATHS:
            data = path.read_bytes()[:24]
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            sizes.append(struct.unpack(">II", data[16:24]))
        self.assertEqual(sizes[:3], [(1440, 1000), (1440, 1000), (1440, 1000)])
        self.assertEqual(sizes[3][0], 390)
        self.assertGreaterEqual(sizes[3][1], 844)

    def test_human_documents_are_chinese_and_state_current_boundary(self) -> None:
        report = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        tests = builder.TEST_RESULTS_PATH.read_text(encoding="utf-8")
        guide = builder.USER_GUIDE_PATH.read_text(encoding="utf-8")
        risks = builder.RISKS_ROLLBACK_PATH.read_text(encoding="utf-8")
        self.assertIn("真正通过 localhost 运行", report)
        self.assertIn("没有读取原始财务资料", report)
        self.assertIn("不可当作真实经营数据", guide)
        self.assertIn("原始资料读取、真实来源连接、外部网络和真实业务动作均为 0", tests)
        self.assertIn("还没有接入真实身份、角色权限", risks)


if __name__ == "__main__":
    unittest.main()
