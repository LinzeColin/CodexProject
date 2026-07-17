from __future__ import annotations

import json
import unittest
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from KMFA.tools import run_v015_s16_p1_homepage as runtime


class HomepageRuntimeTests(unittest.TestCase):
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

    def query(self, **values: str) -> tuple[int, str, str]:
        return self.request("/api/homepage?" + urlencode(values))

    def test_overview_contains_human_homepage_and_test_hook(self) -> None:
        status, content_type, body = self.request("/overview")
        self.assertEqual((status, content_type), (200, "text/html"))
        for token in ("今天先看这 5 件事", "核心经营摘要", "本期重点事项", "近四期趋势", "项目组合", "KMFA_HOMEPAGE_TEST"):
            self.assertIn(token, body)

    def test_existing_deep_links_keep_full_app_shell(self) -> None:
        for path in ("/projects/demo-project", "/collections", "/settings"):
            status, content_type, body = self.request(path)
            self.assertEqual((status, content_type), (200, "text/html"))
            self.assertIn("KMFA_HOMEPAGE_TEST", body)
            self.assertIn("KMFA_EXPERIENCE_TEST", body)
            self.assertIn("KMFA_ROLE_TEST", body)

    def test_complete_api_returns_five_metrics_and_focus_items(self) -> None:
        status, _, body = self.query(
            user_id="demo-owner", role_id="management", company_id="demo-north", period="2026-07", data_state="complete"
        )
        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(payload["overall_completeness"], "COMPLETE")
        self.assertEqual(len(payload["summary_metrics"]), 5)
        self.assertEqual(len(payload["focus_items"]), 5)
        self.assertEqual(payload["primary_action_count"], 5)

    def test_partial_api_is_honest_about_missing_data(self) -> None:
        status, _, body = self.query(
            user_id="demo-owner", role_id="management", company_id="demo-north", period="2026-07", data_state="partial"
        )
        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(payload["overall_completeness"], "INCOMPLETE")
        self.assertFalse(payload["complete_management_conclusion_available"])
        self.assertIn("先补资料", payload["honest_summary_zh"])
        self.assertIn("资料不足", [row["display_zh"] for row in payload["summary_metrics"]])

    def test_company_and_period_are_bound_to_response(self) -> None:
        status, _, body = self.query(
            user_id="demo-owner", role_id="management", company_id="demo-west", period="2026-H1", data_state="complete"
        )
        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(payload["context"]["company_id"], "demo-west")
        self.assertEqual(payload["context"]["period"], "2026-H1")
        self.assertEqual(payload["context_labels"]["company"], "西区示例公司")

    def test_unauthorized_company_is_denied_without_business_payload(self) -> None:
        status, _, body = self.query(
            user_id="demo-finance", role_id="finance", company_id="demo-south", period="2026-07", data_state="complete"
        )
        payload = json.loads(body)
        self.assertEqual(status, 403)
        self.assertFalse(payload["allowed"])
        self.assertEqual(payload["summary_metrics"], [])

    def test_invalid_period_and_state_return_bad_request(self) -> None:
        period_status, _, period_body = self.query(
            user_id="demo-owner", role_id="management", company_id="demo-north", period="2099-01", data_state="complete"
        )
        state_status, _, state_body = self.query(
            user_id="demo-owner", role_id="management", company_id="demo-north", period="2026-07", data_state="bad"
        )
        self.assertEqual((period_status, state_status), (400, 400))
        self.assertFalse(json.loads(period_body)["allowed"])
        self.assertFalse(json.loads(state_body)["allowed"])


if __name__ == "__main__":
    unittest.main()
