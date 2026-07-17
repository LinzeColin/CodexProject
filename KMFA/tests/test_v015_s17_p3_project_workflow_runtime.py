from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from KMFA.tools import run_v015_s17_p3_project_workflow as runtime


class ProjectWorkflowRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.event_path = Path(self.temp.name) / "events.jsonl"
        self.server, self.thread, self.base_url = runtime.start_server(event_path=self.event_path)

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.temp.cleanup()

    @staticmethod
    def query() -> dict[str, str]:
        return {
            "user_id": "demo-owner",
            "role_id": "management",
            "company_id": "demo-north",
            "period": "2026-07",
            "project_id": "PUB-PROJ-001",
        }

    def get_json(self, path: str) -> tuple[int, dict[str, object]]:
        url = self.base_url + path + "?" + urlencode(self.query())
        with urlopen(url, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def post_json(self, path: str, payload: dict[str, str]) -> tuple[int, dict[str, object]]:
        body = {**self.query(), "actor_ref": "runtime-test-owner", **payload}
        request = Request(
            self.base_url + path,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            return error.code, json.loads(error.read().decode("utf-8"))

    def test_page_contains_human_workflow_and_test_hook(self) -> None:
        with urlopen(self.base_url + "/projects/PUB-PROJ-001", timeout=5) as response:
            html = response.read().decode("utf-8")
        self.assertIn("先看依据和影响，再确认处理", html)
        self.assertIn("所有动作都写入可撤销记录，不修改原始数据", html)
        self.assertIn("项目成本专题报告", html)
        self.assertIn("KMFA_PROJECT_WORKFLOW_TEST", html)

    def test_workflow_api_and_detail_use_same_projection(self) -> None:
        status, before = self.get_json("/api/projects/workflow")
        self.assertEqual(status, 200)
        self.assertEqual(before["event_count"], 0)
        status, result = self.post_json(
            "/api/projects/workflow/assignment",
            {
                "candidate_id": "CAND-S17P3-001",
                "reason_zh": "已核对候选依据和金额影响后确认归集",
                "idempotency_key": "runtime-assignment-001",
            },
        )
        self.assertEqual(status, 200)
        self.assertTrue(result["allowed"])
        _, workflow_payload = self.get_json("/api/projects/workflow")
        _, detail_payload = self.get_json("/api/projects/detail")
        workflow_cost = workflow_payload["projection"]["cost"]
        self.assertEqual(workflow_cost["unallocated"]["amount_cents"], 0)
        self.assertEqual(workflow_cost["actual_total_cents"], detail_payload["cost"]["actual_total_cents"])
        self.assertEqual(workflow_cost["categories"], detail_payload["cost"]["categories"])

    def test_low_confidence_assignment_is_rejected_without_event(self) -> None:
        status, result = self.post_json(
            "/api/projects/workflow/assignment",
            {
                "candidate_id": "CAND-S17P3-003",
                "reason_zh": "尝试自动归集低置信候选用于失败关闭测试",
                "idempotency_key": "runtime-low-001",
            },
        )
        self.assertEqual(status, 400)
        self.assertIn("低置信", result["reason_zh"])
        _, snapshot = self.get_json("/api/projects/workflow")
        self.assertEqual(snapshot["event_count"], 0)

    def test_variance_rerun_persists_after_server_restart(self) -> None:
        status, result = self.post_json(
            "/api/projects/workflow/variance",
            {
                "option_id": "USE_SETTLEMENT_SUPPORT",
                "reason_zh": "已并排核对两项来源和影响后确认口径",
                "idempotency_key": "runtime-variance-001",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["projection"]["workflow_projection"]["report_sync_status"], "PASS")
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.server, self.thread, self.base_url = runtime.start_server(event_path=self.event_path)
        _, snapshot = self.get_json("/api/projects/workflow")
        self.assertEqual(snapshot["event_count"], 2)
        self.assertEqual(snapshot["projection"]["workflow_projection"]["report_sync_status"], "PASS")
        self.assertEqual(
            snapshot["projection"]["cost"]["actual_total_cents"],
            snapshot["variance_work_item"]["sources"][1]["amount_cents"],
        )

    def test_assignment_can_be_reversed_through_api(self) -> None:
        _, created = self.post_json(
            "/api/projects/workflow/assignment",
            {
                "candidate_id": "CAND-S17P3-001",
                "reason_zh": "已核对候选依据和金额影响后确认归集",
                "idempotency_key": "runtime-assignment-reverse-001",
            },
        )
        event_id = created["event"]["event_id"]
        status, result = self.post_json(
            "/api/projects/workflow/reverse",
            {
                "event_id": event_id,
                "reason_zh": "复核后撤销本次处理并恢复上一版投影",
                "idempotency_key": "runtime-reversal-001",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["projection"]["cost"]["unallocated"]["amount_cents"], 5_070_388)
        _, snapshot = self.get_json("/api/projects/workflow")
        self.assertEqual(snapshot["event_count"], 2)
        self.assertEqual(snapshot["reversal_event_count"], 1)


if __name__ == "__main__":
    unittest.main()
