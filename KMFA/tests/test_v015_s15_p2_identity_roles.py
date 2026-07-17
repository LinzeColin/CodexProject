from __future__ import annotations

import unittest

from KMFA.tools import v015_s15_p2_identity_roles as subject


class IdentityRoleKernelTests(unittest.TestCase):
    def test_public_contract_has_no_failed_checks(self) -> None:
        contract = subject.build_contract()
        self.assertEqual(contract["public_check_total"], 12)
        self.assertEqual(contract["public_check_pass_count"], 12)
        self.assertEqual(contract["public_check_failed_count"], 0)
        self.assertEqual(contract["real_identity_count"], 0)
        self.assertEqual(contract["credential_count"], 0)
        self.assertEqual(contract["real_business_action_count"], 0)

    def test_same_public_user_can_hold_four_explicit_role_hats(self) -> None:
        snapshot = subject.identity_snapshot("demo-owner", "management", "demo-north")
        self.assertTrue(snapshot["allowed"])
        self.assertEqual([item["role_id"] for item in snapshot["assigned_roles"]], ["management", "finance", "tax", "reviewer"])
        self.assertEqual(snapshot["role_label_zh"], "经营负责人")
        self.assertEqual(len(snapshot["permission_summary"]), 5)

    def test_unassigned_role_and_company_are_denied(self) -> None:
        role = subject.role_switch_decision(
            event_id="E1",
            occurred_at="T",
            user_id="demo-finance",
            from_role="finance",
            to_role="tax",
            company_id="demo-north",
            reason="核对税务工作",
        )
        self.assertFalse(role["allowed"])
        self.assertEqual(role["reason_code"], "ROLE_NOT_ASSIGNED")
        company = subject.authorization_decision(
            event_id="E2",
            occurred_at="T",
            user_id="demo-finance",
            role_id="finance",
            company_id="demo-south",
            resource="REPORT",
            action="VIEW",
            reason="核对报告",
        )
        self.assertFalse(company["allowed"])
        self.assertEqual(company["reason_code"], "COMPANY_NOT_GRANTED")

    def test_unknown_and_ungranted_operations_default_to_deny(self) -> None:
        unknown = subject.authorization_decision(
            event_id="E3",
            occurred_at="T",
            user_id="demo-owner",
            role_id="management",
            company_id="demo-north",
            resource="UNKNOWN",
            action="VIEW",
            reason="测试默认拒绝",
        )
        sensitive = subject.authorization_decision(
            event_id="E4",
            occurred_at="T",
            user_id="demo-owner",
            role_id="management",
            company_id="demo-north",
            resource="DATA_SOURCE",
            action="VIEW_SENSITIVE",
            reason="查看敏感来源",
        )
        self.assertFalse(unknown["allowed"])
        self.assertEqual(unknown["reason_code"], "RESOURCE_NOT_FOUND")
        self.assertFalse(sensitive["allowed"])
        self.assertEqual(sensitive["reason_code"], "PERMISSION_NOT_GRANTED")
        self.assertEqual(sensitive["actor_role"], "management")
        self.assertEqual(sensitive["request_reason"], "查看敏感来源")

    def test_permissions_are_separate_by_resource_and_role(self) -> None:
        self.assertIn(("DATA_SOURCE", "VIEW_SENSITIVE"), subject.ROLE_PERMISSIONS["finance"])
        self.assertNotIn(("DATA_SOURCE", "VIEW_SENSITIVE"), subject.ROLE_PERMISSIONS["management"])
        self.assertIn(("PARAMETER", "PROPOSE_CHANGE"), subject.ROLE_PERMISSIONS["management"])
        self.assertNotIn(("PARAMETER", "APPROVE_CHANGE"), subject.ROLE_PERMISSIONS["management"])
        self.assertIn(("PARAMETER", "APPROVE_CHANGE"), subject.ROLE_PERMISSIONS["reviewer"])
        self.assertIn(("PUBLISH", "REQUEST"), subject.ROLE_PERMISSIONS["finance"])
        self.assertIn(("PUBLISH", "APPROVE"), subject.ROLE_PERMISSIONS["reviewer"])

    def test_role_switch_requires_assigned_role_and_reason(self) -> None:
        missing_reason = subject.role_switch_decision(
            event_id="E5",
            occurred_at="T",
            user_id="demo-owner",
            from_role="management",
            to_role="finance",
            company_id="demo-north",
            reason="",
        )
        allowed = subject.role_switch_decision(
            event_id="E6",
            occurred_at="T",
            user_id="demo-owner",
            from_role="management",
            to_role="finance",
            company_id="demo-north",
            reason="核对财务来源",
        )
        self.assertFalse(missing_reason["allowed"])
        self.assertEqual(missing_reason["reason_code"], "REASON_REQUIRED")
        self.assertTrue(allowed["allowed"])
        self.assertEqual(allowed["actor_role"], "management")
        self.assertEqual(allowed["target_role"], "finance")

    def test_same_role_cannot_approve_but_same_person_different_role_can(self) -> None:
        created = subject.approval_request_decision(
            event_id="E7",
            request_id="APR-0001",
            occurred_at="T1",
            action_type="REPORT_PUBLISH",
            user_id="demo-owner",
            role_id="finance",
            company_id="demo-north",
            reason="申请发布公开演示报告",
        )
        self.assertTrue(created["allowed"])
        same_role = subject.approval_confirmation_decision(
            event_id="E8",
            occurred_at="T2",
            request=created["request"],
            user_id="demo-owner",
            role_id="finance",
            company_id="demo-north",
            reason="确认发布公开演示报告",
        )
        self.assertFalse(same_role["allowed"])
        self.assertEqual(same_role["event"]["reason_code"], "SAME_ROLE_SEPARATION_REQUIRED")
        reviewer = subject.approval_confirmation_decision(
            event_id="E9",
            occurred_at="T3",
            request=created["request"],
            user_id="demo-owner",
            role_id="reviewer",
            company_id="demo-north",
            reason="审核发布理由和范围",
        )
        self.assertTrue(reviewer["allowed"])
        self.assertEqual(reviewer["request"]["state"], "APPROVED_DEMO_ONLY")
        self.assertTrue(reviewer["request"]["approval"]["same_person_different_role"])
        self.assertFalse(reviewer["request"]["real_business_action_performed"])

    def test_all_operation_events_bind_role_reason_and_no_real_action(self) -> None:
        event = subject.authorization_decision(
            event_id="E10",
            occurred_at="T",
            user_id="demo-owner",
            role_id="reviewer",
            company_id="demo-north",
            resource="PUBLISH",
            action="APPROVE",
            reason="确认演示权限",
        )
        self.assertTrue(event["allowed"])
        self.assertEqual(event["actor_role"], "reviewer")
        self.assertEqual(event["request_reason"], "确认演示权限")
        self.assertFalse(event["operation_performed"])


if __name__ == "__main__":
    unittest.main()
