from __future__ import annotations

import json
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from KMFA.tools import run_v015_s20_p2_confirmation_workbench as runtime


class ConfirmationWorkbenchRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.event_path = root / "confirmation.jsonl"
        self.server, self.thread, self.base_url = runtime.start_server(
            event_path=root / "base.jsonl", data_root=root / "data-update", confirmation_event_path=self.event_path,
        )

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temporary.cleanup()

    def request(self, path: str, body=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(self.base_url + path, data=data, headers={"Content-Type": "application/json"} if data else {})
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def preview(self):
        status, value = self.request("/api/confirmation/issues/ISSUE-S20P2-001/preview", {"action_id": "USE_REGISTERED_PROJECT", "actor_role": "ROLE::DATA_STEWARD"})
        self.assertEqual(status, 200)
        return value

    def confirm(self):
        preview = self.preview()
        status, value = self.request("/api/confirmation/issues/ISSUE-S20P2-001/confirm", {
            "action_id": "USE_REGISTERED_PROJECT", "actor_id": "demo-owner", "actor_role": "ROLE::DATA_STEWARD",
            "reason_zh": "已核对两侧项目依据和影响", "preview_id": preview["preview_id"], "preview_token": preview["preview_token"],
            "idempotency_key": "runtime-confirm-project-001",
        })
        self.assertEqual(status, 200)
        return value

    def test_page_and_s20_p1_route_remain_available(self) -> None:
        with urllib.request.urlopen(self.base_url + "/confirmation-workbench") as response:
            html = response.read().decode("utf-8")
        self.assertIn("先看业务影响，再决定怎么处理", html)
        self.assertIn("打开人工确认工作台", html)
        with urllib.request.urlopen(self.base_url + "/api/data-update/options") as response:
            self.assertEqual(json.load(response)["max_upload_bytes"], 16 * 1024 * 1024)

    def test_list_detail_and_history_api(self) -> None:
        status, value = self.request("/api/confirmation/issues")
        self.assertEqual((status, value["issue_count"], value["governance_log_count_in_main_list"]), (200, 5, 0))
        status, detail = self.request("/api/confirmation/issues/ISSUE-S20P2-001")
        self.assertEqual(status, 200)
        self.assertFalse(detail["raw_value_edit_allowed"])
        status, history = self.request("/api/confirmation/history")
        self.assertEqual((status, history["event_count"]), (200, 0))

    def test_unauthorised_and_no_preview_actions_fail(self) -> None:
        status, value = self.request("/api/confirmation/issues/ISSUE-S20P2-001/preview", {"action_id": "USE_REGISTERED_PROJECT", "actor_role": "ROLE::MANAGEMENT"})
        self.assertEqual((status, value["code"]), (403, "ACTION_FORBIDDEN"))
        status, value = self.request("/api/confirmation/issues/ISSUE-S20P2-001/confirm", {
            "action_id": "USE_REGISTERED_PROJECT", "actor_id": "demo-owner", "actor_role": "ROLE::DATA_STEWARD",
            "reason_zh": "不能绕过预览", "idempotency_key": "runtime-missing-preview-001",
        })
        self.assertEqual((status, value["code"]), (409, "HIGH_IMPACT_PREVIEW_REQUIRED"))

    def test_confirm_updates_projection_but_not_sources(self) -> None:
        value = self.confirm()
        self.assertEqual(value["detail"]["status"], "RESOLVED")
        self.assertFalse(value["event"]["raw_source_mutation_performed"])
        status, listed = self.request("/api/confirmation/issues")
        self.assertEqual(status, 200)
        self.assertNotIn("ISSUE-S20P2-001", {row["issue_id"] for row in listed["issues"]})

    def test_undo_preview_confirm_and_history(self) -> None:
        confirmed = self.confirm()
        event_id = confirmed["event"]["event_id"]
        status, preview = self.request(f"/api/confirmation/events/{event_id}/undo-preview", {"actor_role": "ROLE::AUDITOR"})
        self.assertEqual(status, 200)
        status, undone = self.request(f"/api/confirmation/events/{event_id}/undo", {
            "actor_id": "demo-auditor", "actor_role": "ROLE::AUDITOR", "reason_zh": "复核后撤销并恢复待处理",
            "preview_id": preview["preview_id"], "preview_token": preview["preview_token"], "idempotency_key": "runtime-undo-project-001",
        })
        self.assertEqual(status, 200)
        self.assertEqual(undone["detail"]["status"], "OPEN")
        _, history = self.request("/api/confirmation/history")
        self.assertEqual(history["event_count"], 2)

    def test_refresh_restart_recovers_history(self) -> None:
        self.confirm()
        replacement = runtime.kernel.ConfirmationWorkbench(self.event_path)
        self.server.confirmation_workbench = replacement
        status, history = self.request("/api/confirmation/history")
        self.assertEqual((status, history["event_count"]), (200, 1))

    def test_unknown_issue_fails_closed(self) -> None:
        status, value = self.request("/api/confirmation/issues/ISSUE-S20P2-999")
        self.assertEqual((status, value["code"]), (404, "ISSUE_NOT_FOUND"))


if __name__ == "__main__":
    unittest.main()
