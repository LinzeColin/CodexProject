from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from KMFA.tools import run_v015_s19_p2_policy_eligibility as runtime
from KMFA.tools import v015_s19_p2_policy_eligibility as kernel


class PolicyEligibilityRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.server, cls.thread, cls.base_url = runtime.start_server(event_path=Path(cls.temporary.name) / "events.jsonl")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        cls.temporary.cleanup()

    def request(self, path: str, body: dict[str, object] | None = None) -> tuple[int, str, bytes]:
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        request = Request(self.base_url + path, data=data, headers={"Accept": "application/json,text/html", "Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=4) as response:
                return response.status, response.headers.get_content_type(), response.read()
        except HTTPError as error:
            return error.code, error.headers.get_content_type(), error.read()

    def query(self, **values: str) -> str:
        defaults = {"user_id": "demo-owner", "role_id": "management", "company_id": "demo-north", "period": "2026-07", "policy_id": "POLICY-HIGH-TECH"}
        defaults.update(values)
        return urlencode(defaults)

    def api(self, **values: str) -> tuple[int, dict[str, object]]:
        status, _, body = self.request("/api/policy-eligibility?" + self.query(**values))
        return status, json.loads(body)

    def task_body(self, **values: str) -> dict[str, str]:
        defaults = {"user_id": "demo-owner", "role_id": "management", "company_id": "demo-north", "period": "2026-07", "task_id": "POLTASK-006", "source_evidence_ref": "", "actor_ref": "public-demo-owner", "idempotency_key": "runtime-task-6"}
        defaults.update(values)
        return defaults

    def test_page_is_plain_chinese_and_keeps_hard_boundaries(self) -> None:
        status, content_type, body = self.request("/policy-eligibility")
        text = body.decode("utf-8")
        self.assertEqual((status, content_type), (200, "text/html"))
        for token in ("政策注册表", "证据准备度", "材料任务清单", "只提示缺口和风险，不判断申报资格", "不得伪造、倒签或包装材料", "KMFA_POLICY_ELIGIBILITY_TEST"):
            self.assertIn(token, text)
        for token in ("KMFA_MetaData", ">确定符合<", ">自动申报<", ">生成申报材料<"):
            self.assertNotIn(token, text)

    def test_api_returns_registry_readiness_and_tasks(self) -> None:
        status, value = self.api()
        self.assertEqual(status, 200)
        self.assertTrue(value["allowed"])
        self.assertEqual(value["summary"]["policy_count"], 6)
        self.assertEqual(value["summary"]["evidence_item_count"], 12)
        self.assertEqual(value["summary"]["task_count"], 6)
        self.assertEqual(value["formal_eligibility_conclusion_count"], 0)
        self.assertEqual(value["fabricated_evidence_count"], 0)

    def test_superseded_rule_is_visibly_blocked(self) -> None:
        status, value = self.api(policy_id="POLICY-HIGH-TECH-LEGACY")
        self.assertEqual(status, 200)
        self.assertFalse(value["selected_policy"]["rule_use_allowed"])
        self.assertEqual(value["policy_readiness"]["status"], "POLICY_BLOCKED")
        self.assertIsNone(value["policy_readiness"]["eligibility_conclusion"])

    def test_missing_source_cannot_complete(self) -> None:
        status, _, body = self.request("/api/policy-tasks/complete", self.task_body(task_id="POLTASK-001", source_evidence_ref="", idempotency_key="missing"))
        value = json.loads(body)
        self.assertEqual(status, 400)
        self.assertFalse(value["allowed"])
        self.assertIn("无来源材料", value["reason_zh"])

    def test_verified_source_completes_and_updates_only_current_scope(self) -> None:
        source = next(row["source_ref"] for row in kernel.evidence_items() if row["evidence_id"] == "EVD-RD-001")
        status, _, body = self.request("/api/policy-tasks/complete", self.task_body(source_evidence_ref=source))
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["allowed"])
        _, north = self.api()
        completed = next(row for row in north["tasks"] if row["task_id"] == "POLTASK-006")
        self.assertEqual(completed["status"], "COMPLETED")
        _, west = self.api(company_id="demo-west")
        west_task = next(row for row in west["tasks"] if row["task_id"] == "POLTASK-006")
        self.assertEqual(west_task["status"], "READY_TO_COMPLETE")

    def test_policy_filter_updates_tasks_without_changing_evidence_scope(self) -> None:
        status, value = self.api(policy_id="POLICY-RD-DEDUCTION")
        self.assertEqual(status, 200)
        self.assertEqual(value["selected_policy_id"], "POLICY-RD-DEDUCTION")
        self.assertEqual(value["policy_readiness"]["required_category_count"], 2)
        self.assertTrue(all("POLICY-RD-DEDUCTION" in row["policy_ids"] for row in value["tasks"]))

    def test_unauthorised_company_returns_no_policy_material(self) -> None:
        status, value = self.api(user_id="demo-finance", role_id="finance", company_id="demo-south")
        self.assertEqual(status, 403)
        self.assertFalse(value["allowed"])
        self.assertNotIn("evidence_items", value)

    def test_existing_pages_remain_available(self) -> None:
        for path, token in (("/tax-policy", "tax-invoice-view"), ("/funds-report", "funds-report-view"), ("/funds", "funds-view"), ("/projects", "project-list-view")):
            status, content_type, body = self.request(path)
            self.assertEqual((status, content_type), (200, "text/html"))
            self.assertIn(token, body.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
