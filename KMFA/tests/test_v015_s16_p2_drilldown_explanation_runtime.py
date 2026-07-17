from __future__ import annotations

import json
import unittest
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from KMFA.tools import run_v015_s16_p2_drilldown_explanation as runtime


class DrilldownRuntimeTests(unittest.TestCase):
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
        return self.request("/api/drilldown?" + urlencode(values))

    def test_detail_route_contains_human_sections_and_hook(self) -> None:
        status, content_type, body = self.request("/overview/detail/available-cash")
        self.assertEqual((status, content_type), (200, "text/html"))
        for token in ("返回经营首页", "当前数字", "这个数字怎么来的", "组成明细", "期间比较", "查看专业依据", "KMFA_DRILLDOWN_TEST"):
            self.assertIn(token, body)

    def test_all_direct_deep_links_keep_full_app(self) -> None:
        for slug in ("available-cash", "expected-flow", "project-gross-profit", "overdue-receivable", "confirmations"):
            status, content_type, body = self.request("/overview/detail/" + slug)
            self.assertEqual((status, content_type), (200, "text/html"))
            self.assertIn("KMFA_HOMEPAGE_TEST", body)
            self.assertIn("KMFA_ROLE_TEST", body)

    def test_all_metrics_return_consistent_details(self) -> None:
        for metric_id in ("AVAILABLE_CASH", "EXPECTED_RECEIPTS_PAYMENTS", "PROJECT_GROSS_PROFIT", "OVERDUE_RECEIVABLE", "CONFIRMATIONS"):
            status, _, body = self.query(metric_id=metric_id)
            payload = json.loads(body)
            self.assertEqual(status, 200)
            self.assertTrue(payload["detail_available"])
            self.assertEqual(payload["consistency"]["primary_difference"], 0)

    def test_four_filters_are_returned_unchanged(self) -> None:
        status, _, body = self.query(
            metric_id="AVAILABLE_CASH",
            company="demo-west",
            period="2026-H1",
            project_status="normal",
            report_version="approved",
        )
        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(payload["filter_count"], 4)
        self.assertEqual(payload["context"]["company"], "demo-west")
        self.assertEqual(payload["context"]["report_version"], "approved")

    def test_comparison_mismatch_is_blocked(self) -> None:
        status, _, body = self.query(metric_id="AVAILABLE_CASH", comparison_state="basis_mismatch")
        payload = json.loads(body)
        self.assertEqual(status, 200)
        self.assertFalse(payload["comparison"]["comparison_allowed"])
        self.assertIn("口径不同", payload["comparison"]["block_reason_zh"])

    def test_missing_data_and_lineage_are_not_rendered_as_detail(self) -> None:
        for query in (
            {"metric_id": "OVERDUE_RECEIVABLE", "data_state": "partial"},
            {"metric_id": "AVAILABLE_CASH", "lineage_state": "missing"},
        ):
            status, _, body = self.query(**query)
            payload = json.loads(body)
            self.assertEqual(status, 200)
            self.assertFalse(payload["detail_available"])
            self.assertEqual(payload["detail_rows"], [])

    def test_permission_and_invalid_input_fail_closed(self) -> None:
        denied_status, _, denied_body = self.query(
            metric_id="AVAILABLE_CASH", user_id="demo-finance", role_id="finance", company="demo-south"
        )
        invalid_status, _, invalid_body = self.query(metric_id="NOT_A_METRIC")
        self.assertEqual(denied_status, 403)
        self.assertEqual(json.loads(denied_body)["detail_rows"], [])
        self.assertEqual(invalid_status, 400)
        self.assertFalse(json.loads(invalid_body)["allowed"])

    def test_homepage_api_remains_available(self) -> None:
        status, _, body = self.request("/api/homepage?company_id=demo-north&period=2026-07")
        self.assertEqual(status, 200)
        self.assertEqual(len(json.loads(body)["summary_metrics"]), 5)


if __name__ == "__main__":
    unittest.main()
