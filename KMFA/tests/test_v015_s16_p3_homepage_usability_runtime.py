from __future__ import annotations

import json
import unittest
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from KMFA.tools import run_v015_s16_p3_homepage_usability as runtime


class HomepageUsabilityRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server, cls.thread, cls.base_url = runtime.start_server()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)

    def request(self, path: str) -> tuple[int, str, str]:
        request = Request(self.base_url + path, headers={"Accept": "application/json,text/html"})
        try:
            with urlopen(request, timeout=4) as response:
                return response.status, response.headers.get_content_type(), response.read().decode("utf-8")
        except HTTPError as error:
            return error.code, error.headers.get_content_type(), error.read().decode("utf-8")

    def homepage(self, **values: str) -> tuple[int, dict[str, object]]:
        status, _, body = self.request("/api/homepage?" + urlencode(values))
        return status, json.loads(body)

    def test_homepage_contains_scan_state_and_test_hooks(self) -> None:
        status, content_type, body = self.request("/overview")
        self.assertEqual((status, content_type), (200, "text/html"))
        for token in (
            "经营状态",
            "先处理这 3 项",
            "homepage-state-panel",
            "KMFA_HOMEPAGE_USABILITY_TEST",
            "KMFA_HOMEPAGE_TEST",
            "KMFA_DRILLDOWN_TEST",
        ):
            self.assertIn(token, body)

    def test_ready_api_adds_scan_summary_without_changing_five_metrics(self) -> None:
        status, payload = self.homepage(usability_state="ready", company_id="demo-north", period="2026-07")
        self.assertEqual(status, 200)
        self.assertTrue(payload["allowed"])
        self.assertEqual(payload["usability_state"], "ready")
        self.assertEqual(len(payload["summary_metrics"]), 5)
        self.assertEqual(payload["priority_preview_count"], 3)
        self.assertIn("先处理回款", payload["scan_summary_zh"])

    def test_partial_api_is_honest(self) -> None:
        status, payload = self.homepage(usability_state="ready", data_state="partial")
        self.assertEqual(status, 200)
        self.assertEqual(payload["scan_status"], "INCOMPLETE")
        self.assertIn("当前不判断经营状态", payload["scan_summary_zh"])

    def test_empty_error_and_stale_http_states_remain_actionable(self) -> None:
        expected = {"empty": 200, "error": 503, "stale": 409}
        for state, expected_status in expected.items():
            status, payload = self.homepage(usability_state=state)
            self.assertEqual(status, expected_status)
            self.assertFalse(payload["allowed"])
            self.assertEqual(payload["usability_state"], state)
            self.assertEqual(payload["displayed_business_value_count"], 0)
            self.assertTrue(payload["state_contract"]["action_zh"])

    def test_permission_state_keeps_company_data_hidden(self) -> None:
        status, payload = self.homepage(
            usability_state="ready",
            user_id="demo-finance",
            role_id="finance",
            company_id="demo-south",
        )
        self.assertEqual(status, 403)
        self.assertEqual(payload["usability_state"], "permission")
        self.assertEqual(payload["summary_metrics"], [])
        self.assertIn("权限", payload["state_contract"]["state_zh"])

    def test_unknown_state_fails_closed(self) -> None:
        status, payload = self.homepage(usability_state="unknown")
        self.assertEqual(status, 400)
        self.assertFalse(payload["allowed"])

    def test_drilldown_dependency_remains_live(self) -> None:
        status, _, body = self.request("/api/drilldown?metric_id=AVAILABLE_CASH")
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["detail_available"])


if __name__ == "__main__":
    unittest.main()
