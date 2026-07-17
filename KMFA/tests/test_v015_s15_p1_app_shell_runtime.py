from __future__ import annotations

import json
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from KMFA.tools import run_v015_s15_p1_app_shell as runtime


class AppShellRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server, cls.thread, cls.base_url = runtime.start_server()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def read(self, path: str) -> tuple[int, str, str]:
        request = Request(self.base_url + path, headers={"Accept": "application/json,text/html"})
        try:
            with urlopen(request, timeout=4) as response:
                return response.status, response.headers.get_content_type(), response.read().decode("utf-8")
        except HTTPError as error:
            return error.code, error.headers.get_content_type(), error.read().decode("utf-8")

    def test_root_and_every_deep_link_return_runtime_shell(self) -> None:
        for path in ("/overview", "/projects/demo-project/update", "/reports/demo-business-report"):
            status, content_type, body = self.read(path)
            self.assertEqual(status, 200)
            self.assertEqual(content_type, "text/html")
            self.assertIn("KMFA 经营工作台", body)
            self.assertIn("fetch('/api/context?'", body)
            self.assertIn("history[push?'pushState':'replaceState']", body)

    def test_context_api_changes_with_all_four_dimensions(self) -> None:
        status, content_type, body = self.read(
            "/api/context?company=demo-west&period=2026-H1&project_status=attention&report_version=previous"
        )
        self.assertEqual((status, content_type), (200, "application/json"))
        payload = json.loads(body)
        self.assertEqual(
            payload["context"],
            {
                "company": "demo-west",
                "period": "2026-H1",
                "project_status": "attention",
                "report_version": "previous",
            },
        )
        self.assertTrue(all(item["company_id"] == "demo-west" for item in payload["items"]))
        self.assertIn("西区示例公司", payload["summary"]["message_zh"])

    def test_invalid_context_is_not_echoed_or_exposed(self) -> None:
        status, _, body = self.read("/api/context?company=real-company&period=secret")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["context"]["company"], "demo-north")
        self.assertEqual(payload["context"]["period"], "2026-07")
        self.assertNotIn("real-company", body)
        self.assertNotIn("secret", body)

    def test_four_fault_transports_are_explicit(self) -> None:
        expectations = {"network": 503, "parse": 200, "calculation": 422, "permission": 403}
        for fault, expected_status in expectations.items():
            status, content_type, body = self.read(f"/api/context?fault={fault}")
            self.assertEqual(status, expected_status)
            self.assertEqual(content_type, "application/json")
            if fault == "parse":
                with self.assertRaises(json.JSONDecodeError):
                    json.loads(body)
            else:
                payload = json.loads(body)
                self.assertEqual(payload["error_type"], fault)
                self.assertTrue(payload["message_zh"])

    def test_unknown_deep_link_still_bootstraps_recoverable_shell(self) -> None:
        status, content_type, body = self.read("/not-a-real-page")
        self.assertEqual((status, content_type), (200, "text/html"))
        self.assertIn("这个页面暂时找不到", body)
        self.assertIn("返回经营首页", body)


if __name__ == "__main__":
    unittest.main()
