from __future__ import annotations

import json
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from KMFA.tools import run_v015_s20_p3_recalculation_publication as runtime


class RecalculationPublicationRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.confirmation_path = root / "confirmation.jsonl"
        self.publication_path = root / "publication.jsonl"
        self.server, self.thread, self.base_url = runtime.start_server(
            event_path=root / "base.jsonl", data_root=root / "data-update",
            confirmation_event_path=self.confirmation_path, publication_event_path=self.publication_path,
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

    def confirm(self, issue_id="ISSUE-S20P2-001", action_id="USE_REGISTERED_PROJECT", suffix="one"):
        status, preview = self.request(f"/api/confirmation/issues/{issue_id}/preview", {
            "action_id": action_id, "actor_role": "ROLE::DATA_STEWARD",
        })
        self.assertEqual(status, 200)
        status, value = self.request(f"/api/confirmation/issues/{issue_id}/confirm", {
            "action_id": action_id, "actor_id": "steward", "actor_role": "ROLE::DATA_STEWARD",
            "reason_zh": "已核对业务依据并允许受影响链重算", "preview_id": preview["preview_id"],
            "preview_token": preview["preview_token"], "idempotency_key": f"runtime-confirm-{suffix}-001",
        })
        self.assertEqual(status, 200)
        return value["event"]

    def start(self, event, suffix="one"):
        status, job = self.request("/api/recalculation/start", {
            "control_event_id": event["event_id"], "actor_id": "steward", "actor_role": "ROLE::DATA_STEWARD",
            "idempotency_key": f"runtime-recalculate-{suffix}-001",
        })
        self.assertEqual(status, 200)
        return job

    def preview(self, job, decision="PUBLISH_CANDIDATE"):
        status, value = self.request(f"/api/recalculation/jobs/{job['job_id']}/preview", {
            "decision": decision, "actor_role": "ROLE::MANAGEMENT",
        })
        self.assertEqual(status, 200)
        return value

    def decide(self, job, decision="PUBLISH_CANDIDATE", suffix="one"):
        preview = self.preview(job, decision)
        return self.request(f"/api/recalculation/jobs/{job['job_id']}/decide", {
            "decision": decision, "actor_id": "manager", "actor_role": "ROLE::MANAGEMENT",
            "reason_zh": "已核对数字、报告和四页面一致性", "preview_id": preview["preview_id"],
            "preview_token": preview["preview_token"], "idempotency_key": f"runtime-decision-{suffix}-001",
        })

    def test_p1_p2_and_p3_pages_and_routes_remain_available(self) -> None:
        for path, marker in [
            ("/data-update", "打开人工确认工作台"),
            ("/confirmation-workbench", "重新计算与发布联动"),
            ("/recalculation-publication", "只更新受影响的数字，一次同步四个页面"),
        ]:
            with urllib.request.urlopen(self.base_url + path) as response:
                self.assertIn(marker, response.read().decode("utf-8"))
        status, options = self.request("/api/data-update/options")
        self.assertEqual((status, options["max_upload_bytes"]), (200, 16 * 1024 * 1024))

    def test_eligible_and_current_api(self) -> None:
        status, eligible = self.request("/api/recalculation/eligible")
        self.assertEqual((status, eligible["eligible_count"]), (200, 0))
        self.confirm()
        _, eligible = self.request("/api/recalculation/eligible")
        self.assertEqual(eligible["eligible_count"], 1)
        status, current = self.request("/api/recalculation/current")
        self.assertEqual((status, current["publication_version_id"], current["consistency"]["view_count"]), (200, "PUB-S20P3-0001", 4))

    def test_start_job_and_comparison_api(self) -> None:
        job = self.start(self.confirm())
        status, fetched = self.request(f"/api/recalculation/jobs/{job['job_id']}")
        self.assertEqual((status, fetched["affected_node_count"]), (200, 8))
        status, comparison = self.request(f"/api/recalculation/jobs/{job['job_id']}/comparison")
        self.assertEqual((status, comparison["report_change_count"]), (200, 4))
        _, eligible = self.request("/api/recalculation/eligible")
        self.assertEqual(eligible["eligible_count"], 0)

    def test_unauthorised_and_missing_preview_fail(self) -> None:
        event = self.confirm()
        status, value = self.request("/api/recalculation/start", {
            "control_event_id": event["event_id"], "actor_id": "manager", "actor_role": "ROLE::MANAGEMENT",
            "idempotency_key": "runtime-forbidden-recalc-001",
        })
        self.assertEqual((status, value["code"]), (403, "RECALCULATION_FORBIDDEN"))
        job = self.start(event)
        status, value = self.request(f"/api/recalculation/jobs/{job['job_id']}/decide", {
            "decision": "PUBLISH_CANDIDATE", "actor_id": "manager", "actor_role": "ROLE::MANAGEMENT",
            "reason_zh": "不能绕过预览", "idempotency_key": "runtime-no-preview-001",
        })
        self.assertEqual((status, value["code"]), (409, "PUBLICATION_PREVIEW_REQUIRED"))

    def test_retain_old_version(self) -> None:
        status, result = self.decide(self.start(self.confirm()), "KEEP_CURRENT")
        self.assertEqual((status, result["event"]["event_type"]), (200, "PUBLICATION_RETAINED"))
        self.assertEqual(result["current_publication"]["publication_version_id"], "PUB-S20P3-0001")

    def test_publish_updates_all_four_view_apis_consistently(self) -> None:
        status, result = self.decide(self.start(self.confirm()))
        self.assertEqual(status, 200)
        version = result["current_publication"]["publication_version_id"]
        views = []
        for view_id in runtime.kernel.VIEW_IDS:
            status, value = self.request(f"/api/recalculation/views/{view_id}")
            self.assertEqual(status, 200)
            views.append(value)
        self.assertEqual({row["publication_version_id"] for row in views}, {version})
        self.assertEqual(len({row["shared_metric_fingerprint"] for row in views}), 1)

    def test_restart_recovers_publication_and_history(self) -> None:
        _, result = self.decide(self.start(self.confirm()))
        self.server.recalculation_workbench = runtime.kernel.RecalculationPublicationWorkbench(
            self.confirmation_path, self.publication_path,
        )
        _, current = self.request("/api/recalculation/current")
        _, history = self.request("/api/recalculation/history")
        self.assertEqual(current["snapshot_hash"], result["current_publication"]["snapshot_hash"])
        self.assertEqual(history["event_count"], 2)

    def test_unknown_job_and_view_fail_closed(self) -> None:
        status, value = self.request("/api/recalculation/jobs/JOB-S20P3-9999")
        self.assertEqual((status, value["code"]), (404, "JOB_NOT_FOUND"))
        status, _ = self.request("/api/recalculation/views/unknown")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
