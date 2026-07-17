from __future__ import annotations

import json
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from KMFA.tools import run_v015_s15_p2_identity_roles as runtime


class IdentityRoleRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server, cls.thread, cls.base_url = runtime.start_server()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def request(self, path: str, value=None) -> tuple[int, str, str]:
        data = None if value is None else json.dumps(value).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=data,
            headers={"Accept": "application/json,text/html", "Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=4) as response:
                return response.status, response.headers.get_content_type(), response.read().decode("utf-8")
        except HTTPError as error:
            return error.code, error.headers.get_content_type(), error.read().decode("utf-8")

    def test_deep_links_return_identity_role_runtime(self) -> None:
        for path in ("/overview", "/projects/demo-project/update", "/reports/demo-business-report"):
            status, content_type, body = self.request(path)
            self.assertEqual((status, content_type), (200, "text/html"))
            self.assertIn("当前操作身份", body)
            self.assertIn("KMFA_ROLE_TEST", body)
            self.assertIn("/api/authorize", body)
            self.assertIn("/api/approvals", body)

    def test_identity_snapshot_is_allowed_only_for_assigned_role_and_company(self) -> None:
        status, _, body = self.request("/api/identity?user_id=demo-owner&role_id=finance&company_id=demo-south")
        self.assertEqual(status, 200)
        allowed = json.loads(body)
        self.assertTrue(allowed["allowed"])
        self.assertEqual(allowed["role_label_zh"], "财务")
        denied_status, _, denied_body = self.request("/api/identity?user_id=demo-finance&role_id=tax&company_id=demo-north")
        self.assertEqual(denied_status, 403)
        self.assertEqual(json.loads(denied_body)["reason_code"], "ROLE_NOT_ASSIGNED")

    def test_authorization_allows_finance_and_logs_management_denial(self) -> None:
        base = {
            "user_id": "demo-owner",
            "company_id": "demo-north",
            "resource": "DATA_SOURCE",
            "action": "VIEW_SENSITIVE",
            "reason": "核对敏感来源说明",
        }
        denied_status, _, denied_body = self.request("/api/authorize", {**base, "role_id": "management"})
        self.assertEqual(denied_status, 403)
        self.assertFalse(json.loads(denied_body)["event"]["allowed"])
        allowed_status, _, allowed_body = self.request("/api/authorize", {**base, "role_id": "finance"})
        self.assertEqual(allowed_status, 200)
        self.assertTrue(json.loads(allowed_body)["event"]["allowed"])
        _, _, audit_body = self.request("/api/audit")
        events = json.loads(audit_body)["events"]
        self.assertTrue(any(not event["allowed"] and event["actor_role"] == "management" for event in events))
        self.assertTrue(all(event.get("request_reason") for event in events))

    def test_unassigned_role_switch_is_blocked_and_recorded(self) -> None:
        status, _, body = self.request(
            "/api/role-switch",
            {
                "user_id": "demo-finance",
                "from_role": "finance",
                "to_role": "tax",
                "company_id": "demo-north",
                "reason": "尝试核对税务事项",
            },
        )
        self.assertEqual(status, 403)
        event = json.loads(body)["event"]
        self.assertEqual(event["reason_code"], "ROLE_NOT_ASSIGNED")
        self.assertFalse(event["operation_performed"])

    def test_approval_separates_roles_without_inventing_people(self) -> None:
        create_status, _, create_body = self.request(
            "/api/approvals",
            {
                "mode": "create",
                "action_type": "REPORT_PUBLISH",
                "user_id": "demo-owner",
                "role_id": "finance",
                "company_id": "demo-north",
                "reason": "申请发布公开演示报告",
            },
        )
        self.assertEqual(create_status, 200)
        request = json.loads(create_body)["request"]
        same_status, _, same_body = self.request(
            "/api/approvals",
            {
                "mode": "approve",
                "request_id": request["request_id"],
                "user_id": "demo-owner",
                "role_id": "finance",
                "company_id": "demo-north",
                "reason": "尝试由原角色确认",
            },
        )
        self.assertEqual(same_status, 403)
        self.assertEqual(json.loads(same_body)["event"]["reason_code"], "SAME_ROLE_SEPARATION_REQUIRED")
        approve_status, _, approve_body = self.request(
            "/api/approvals",
            {
                "mode": "approve",
                "request_id": request["request_id"],
                "user_id": "demo-owner",
                "role_id": "reviewer",
                "company_id": "demo-north",
                "reason": "审核发布理由与公开范围",
            },
        )
        self.assertEqual(approve_status, 200)
        approved = json.loads(approve_body)["request"]
        self.assertEqual(approved["state"], "APPROVED_DEMO_ONLY")
        self.assertTrue(approved["approval"]["same_person_different_role"])
        self.assertFalse(approved["real_business_action_performed"])

    def test_invalid_post_and_unknown_api_fail_closed(self) -> None:
        status, _, body = self.request("/api/approvals", {"mode": "unknown"})
        self.assertEqual(status, 403)
        self.assertEqual(json.loads(body)["event"]["reason_code"], "MODE_NOT_FOUND")
        unknown, _, _ = self.request("/api/not-real", {"value": 1})
        self.assertEqual(unknown, 404)


if __name__ == "__main__":
    unittest.main()
