from __future__ import annotations

import json
import struct
import unittest

from KMFA.tools import build_v015_s22_p1_notifications as builder


class NotificationArtifactTests(unittest.TestCase):
    def value(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_manifest_is_pending_or_final_and_stays_inside_s22_p1(self) -> None:
        value = self.value(builder.MANIFEST_PATH)
        self.assertIn(value["phase_acceptance_status"], {"PENDING_FINAL_VALIDATION", "PASSED"})
        self.assertEqual((value["run_phase_id"], value["roadmap_phase_id"], value["recipient_count"]), ("V015_S22_P1_NOTIFICATIONS", "S22-P1", 1))
        self.assertEqual((value["external_email_delivery_count"], value["raw_root_access_count"], value["external_network_request_count"]), (0, 0, 0))
        self.assertFalse(value["s22_p2_started"] or value["s22_p3_started"] or value["github_upload_performed"] or value["app_reinstall_performed"])

    def test_rule_safety_frequency_and_retry_contracts_are_complete(self) -> None:
        rules, safety = self.value(builder.RULES_PATH), self.value(builder.SAFETY_PATH)
        frequency = self.value(builder.FREQUENCY_RETRY_PATH)
        self.assertEqual((rules["rule_catalog_count"], rules["enabled_confirmed_rule_count"], rules["unconfirmed_rule_enabled_count"], rules["alert_category_count"]), (7, 6, 0, 5))
        self.assertEqual((safety["safe_body_field_count"], safety["full_report_body_count"], safety["amount_detail_count"], safety["attachment_count"], safety["credential_field_count"]), (4, 0, 0, 0, 0))
        self.assertEqual((frequency["dedupe_window_minutes"], frequency["frequency_limit_per_day"], frequency["duplicate_dispatch_count"], frequency["silence_action_count"]), (360, 3, 0, 2))
        self.assertTrue(frequency["failure_reason_recorded"] and frequency["retry_idempotent"])

    def test_public_checks_browser_and_task_matrix_are_complete(self) -> None:
        checks, browser, matrix = self.value(builder.PUBLIC_CHECKS_PATH), self.value(builder.BROWSER_PATH), self.value(builder.TASK_MATRIX_PATH)
        self.assertEqual((checks["status"], checks["public_check_count"], checks["public_check_pass_count"], checks["public_check_failed_count"]), ("PASS", 65, 65, 0))
        self.assertEqual((browser["browser_flow_count"], browser["visual_evidence_count"], browser["external_network_request_count"]), (8, 6, 0))
        self.assertEqual((matrix["phase_task_count"], len(matrix["tasks"])), (3, 3))
        self.assertTrue(all(row["status"] == "PASS" for row in matrix["tasks"]))

    def test_six_formal_screenshots_have_expected_dimensions(self) -> None:
        sizes = []
        for path in builder.FORMAL_SCREENSHOT_PATHS:
            data = path.read_bytes()[:24]; self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            sizes.append(struct.unpack(">II", data[16:24]))
        self.assertTrue(all(width >= 1000 and height >= 700 for width, height in sizes[:5]))
        self.assertEqual(sizes[5][0], 390); self.assertGreaterEqual(sizes[5][1], 800)

    def test_human_documents_are_plain_chinese_and_present(self) -> None:
        for path in (builder.IMPLEMENTATION_REPORT_PATH, builder.USER_GUIDE_PATH, builder.TEST_RESULTS_PATH, builder.RISKS_ROLLBACK_PATH):
            self.assertGreater(len(path.read_text(encoding="utf-8")), 120)
        self.assertIn("本地邮件沙箱", builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8"))
        self.assertIn("外部发送必须一直为 0", builder.USER_GUIDE_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
