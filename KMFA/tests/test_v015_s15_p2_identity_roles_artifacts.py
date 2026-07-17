from __future__ import annotations

import json
import struct
import unittest

from KMFA.tools import build_v015_s15_p2_identity_roles as builder


class IdentityRoleArtifactTests(unittest.TestCase):
    def value(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_builder_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_manifest_is_pending_before_formal_validation(self) -> None:
        manifest = self.value(builder.MANIFEST_PATH)
        if builder.receipts():
            self.assertEqual(manifest["phase_acceptance_status"], "PASSED")
            self.assertEqual(manifest["phase_task_accepted_count"], 3)
            self.assertTrue(manifest["s15_p3_entry_allowed"])
        else:
            self.assertEqual(manifest["phase_acceptance_status"], "PENDING_FINAL_VALIDATION")
            self.assertEqual(manifest["phase_task_accepted_count"], 0)
            self.assertFalse(manifest["s15_p3_entry_allowed"])
        self.assertTrue(manifest["s15_p2_started"])
        self.assertFalse(manifest["s15_p3_started"])
        self.assertFalse(manifest["s15_stage_review_started"])
        self.assertEqual(manifest["stage_execution_percentage"], 67)

    def test_identity_permission_audit_and_approval_contracts_are_complete(self) -> None:
        identity = self.value(builder.IDENTITY_CONTRACT_PATH)
        permission = self.value(builder.PERMISSION_CONTRACT_PATH)
        audit = self.value(builder.AUDIT_CONTRACT_PATH)
        approval = self.value(builder.APPROVAL_CONTRACT_PATH)
        self.assertEqual(identity["public_user_count"], 2)
        self.assertEqual(identity["role_hat_count"], 4)
        self.assertEqual(permission["default_policy"], "DENY")
        self.assertEqual(permission["resource_domain_count"], 5)
        self.assertEqual(permission["permission_grant_count"], 28)
        self.assertTrue(audit["unauthorized_access_logged"])
        self.assertEqual(audit["role_and_reason_bound_count"], audit["event_count"])
        self.assertFalse(approval["same_role_confirmation_allowed"])
        self.assertTrue(approval["same_person_different_role_confirmation_allowed"])
        self.assertFalse(approval["invented_person_required"])

    def test_html_snapshot_contains_human_readable_role_controls(self) -> None:
        text = builder.HTML_PATH.read_text(encoding="utf-8")
        for token in ("当前操作身份", "授权范围", "本次操作记录", "KMFA_ROLE_TEST", "localStorage", "aria-live"):
            self.assertIn(token, text)
        self.assertNotIn("/Users/linzezhang/Downloads/KMFA_MetaData", text)

    def test_four_public_screenshots_have_expected_viewports(self) -> None:
        sizes = []
        for path in builder.SCREENSHOT_PATHS:
            data = path.read_bytes()[:24]
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            sizes.append(struct.unpack(">II", data[16:24]))
        self.assertEqual(sizes[:3], [(1440, 1000), (1440, 1000), (1440, 1000)])
        self.assertEqual(sizes[3][0], 390)
        self.assertGreaterEqual(sizes[3][1], 844)

    def test_human_documents_state_plain_chinese_and_current_boundary(self) -> None:
        report = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        guide = builder.USER_GUIDE_PATH.read_text(encoding="utf-8")
        tests = builder.TEST_RESULTS_PATH.read_text(encoding="utf-8")
        risks = builder.RISKS_ROLLBACK_PATH.read_text(encoding="utf-8")
        self.assertIn("当前是谁、以什么角色", report)
        self.assertIn("同一角色不能自批", guide)
        self.assertIn("真实账号、凭据、外部网络和真实业务动作均为 0", tests)
        self.assertIn("不是生产登录系统", risks)


if __name__ == "__main__":
    unittest.main()
