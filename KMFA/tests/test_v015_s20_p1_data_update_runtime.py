from __future__ import annotations

import json
import tempfile
import unittest
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from KMFA.tools import run_v015_s20_p1_data_update as runtime


class DataUpdateRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        root = Path(cls.temporary.name)
        cls.server, cls.thread, cls.base_url = runtime.start_server(
            event_path=root / "events.jsonl",
            data_root=root / "data-update",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        cls.temporary.cleanup()

    def request(self, path: str, *, method: str = "GET", body: bytes | None = None, headers: dict[str, str] | None = None) -> tuple[int, str, bytes]:
        request = Request(self.base_url + path, data=body, method=method, headers=headers or {"Accept": "application/json,text/html"})
        try:
            with urlopen(request, timeout=8) as response:
                return response.status, response.headers.get_content_type(), response.read()
        except HTTPError as error:
            return error.code, error.headers.get_content_type(), error.read()

    def upload(self, filename: str = "sample.csv", content: bytes = b"project,cost\nA,100\n") -> tuple[int, dict[str, object]]:
        boundary = "----KMFA" + uuid.uuid4().hex
        parts: list[bytes] = []
        fields = {
            "source_id": "SRC-local-upload-a1b2c3d4",
            "entity_id": "demo-north",
            "scope_id": "SEGMENT::PROJECT_COST",
            "period": "2026-07",
        }
        for name, value in fields.items():
            parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode())
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{filename}\"\r\nContent-Type: application/octet-stream\r\n\r\n".encode() + content + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        status, _, body = self.request(
            "/api/data-update/jobs",
            method="POST",
            body=b"".join(parts),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}", "Accept": "application/json"},
        )
        return status, json.loads(body)

    def post_json(self, path: str, value: dict[str, object]) -> tuple[int, dict[str, object]]:
        status, _, body = self.request(path, method="POST", body=json.dumps(value).encode(), headers={"Content-Type": "application/json", "Accept": "application/json"})
        return status, json.loads(body)

    def test_page_is_plain_chinese_three_step_flow(self) -> None:
        status, content_type, body = self.request("/data-update")
        text = body.decode()
        self.assertEqual((status, content_type), (200, "text/html"))
        for token in ("先上传检查，再确认处理", "选择并上传", "预览并确认", "处理与结果", "返回修改", "取消本次更新", "KMFA_DATA_UPDATE_TEST"):
            self.assertIn(token, text)
        self.assertNotIn("KMFA_MetaData", text)

    def test_options_expose_bounded_choices(self) -> None:
        status, _, body = self.request("/api/data-update/options")
        value = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(len(value["steps"]), 3)
        self.assertFalse(value["raw_write_allowed"])

    def test_upload_preview_refresh_confirm_and_result(self) -> None:
        status, job = self.upload()
        self.assertEqual(status, 201)
        self.assertEqual(job["status"], "AWAITING_CONFIRMATION")
        status, _, body = self.request("/api/data-update/jobs/" + job["job_id"])
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), job)
        status, result = self.post_json(
            "/api/data-update/jobs/" + job["job_id"] + "/confirm",
            {"preview_id": job["preview"]["preview_id"], "confirm_token": job["preview"]["confirm_token"], "operator_role": "ROLE::DATA_STEWARD"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "COMPLETED")
        self.assertTrue(result["result"]["validation_passed"])
        self.assertFalse(result["result"]["impact"]["recalculation_executed"])

    def test_confirmation_tamper_is_rejected(self) -> None:
        _, job = self.upload("tamper.csv")
        status, value = self.post_json(
            "/api/data-update/jobs/" + job["job_id"] + "/confirm",
            {"preview_id": job["preview"]["preview_id"], "confirm_token": "wrong"},
        )
        self.assertEqual(status, 409)
        self.assertEqual(value["code"], "PREVIEW_CONFIRMATION_MISMATCH")

    def test_cancel_api_removes_pending_upload(self) -> None:
        _, job = self.upload("cancel.csv")
        status, value = self.post_json("/api/data-update/jobs/" + job["job_id"] + "/cancel", {})
        self.assertEqual(status, 200)
        self.assertEqual(value["status"], "CANCELLED")
        self.assertFalse(value["source_copy_present"])

    def test_broken_file_returns_visible_blocked_preview(self) -> None:
        status, value = self.upload("broken.pdf", b"broken")
        self.assertEqual(status, 201)
        self.assertEqual(value["status"], "PREVIEW_BLOCKED")
        self.assertTrue(value["issues"][0]["blocks_processing"])

    def test_unknown_job_and_bad_upload_fail_closed(self) -> None:
        status, _, body = self.request("/api/data-update/jobs/DU-" + "0" * 24)
        self.assertEqual(status, 404)
        self.assertEqual(json.loads(body)["code"], "JOB_NOT_FOUND")
        status, _, body = self.request("/api/data-update/jobs", method="POST", body=b"{}", headers={"Content-Type": "application/json"})
        self.assertEqual(status, 400)
        self.assertEqual(json.loads(body)["code"], "UPLOAD_CONTENT_TYPE_INVALID")

    def test_previous_application_pages_remain_available(self) -> None:
        for path, token in (("/tax-policy-report", "tax-policy-report-view"), ("/tax-policy", "tax-invoice-view"), ("/overview", "homepage-view")):
            status, content_type, body = self.request(path)
            self.assertEqual((status, content_type), (200, "text/html"))
            self.assertIn(token, body.decode())


if __name__ == "__main__":
    unittest.main()
