from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from KMFA.tools import run_v015_s18_p1_receivables_collections as runtime


class ReceivablesRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.server, cls.thread, cls.base_url = runtime.start_server(
            event_path=Path(cls.temporary.name) / "events.jsonl"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        cls.temporary.cleanup()

    def request(self, path: str) -> tuple[int, str, bytes]:
        request = Request(self.base_url + path, headers={"Accept": "application/json,text/html"})
        try:
            with urlopen(request, timeout=4) as response:
                return response.status, response.headers.get_content_type(), response.read()
        except HTTPError as error:
            return error.code, error.headers.get_content_type(), error.read()

    def api(self, **values: str) -> tuple[int, dict[str, object]]:
        defaults = {
            "user_id": "demo-owner",
            "role_id": "management",
            "company_id": "demo-north",
            "period": "2026-07",
        }
        defaults.update(values)
        status, _, body = self.request("/api/receivables?" + urlencode(defaults))
        return status, json.loads(body)

    def test_page_contains_plain_chinese_ui_and_test_hook(self) -> None:
        status, content_type, body = self.request("/collections")
        text = body.decode("utf-8")
        self.assertEqual((status, content_type), (200, "text/html"))
        for token in ("先看欠款", "只统计已开票未回款", "多维汇总", "应收明细", "未开票节点", "KMFA_RECEIVABLES_TEST"):
            self.assertIn(token, text)
        self.assertNotIn("KMFA_MetaData", text)
        self.assertNotIn("联系客户", text.replace("不会自动联系客户", ""))

    def test_api_returns_exact_public_receivables(self) -> None:
        status, value = self.api()
        self.assertEqual(status, 200)
        self.assertTrue(value["allowed"])
        self.assertEqual(value["data_classification"], "PUBLIC_SYNTHETIC")
        self.assertEqual(value["money_difference_cents"], 0)
        self.assertEqual(value["group_difference_cents"], 0)
        self.assertEqual(value["cross_company_leak_count"], 0)
        self.assertEqual(value["unsupported_recommendation_count"], 0)

    def test_all_dimensions_filter_and_group(self) -> None:
        cases = (
            {"project": "PUB-PROJ-001", "group_by": "project"},
            {"customer": "示例制造集团", "group_by": "customer"},
            {"invoice_period": "2026-07", "group_by": "period"},
            {"owner": "陈工", "group_by": "owner"},
            {"aging_bucket": "D90_PLUS", "priority": "HIGH"},
        )
        for values in cases:
            with self.subTest(values=values):
                status, value = self.api(**values)
                self.assertEqual(status, 200)
                self.assertEqual(value["group_difference_cents"], 0)
                self.assertEqual(
                    value["summary"]["receivable_cents"],
                    sum(row["receivable_cents"] for row in value["rows"]),
                )

    def test_company_scope_is_exact_and_values_are_distinct(self) -> None:
        totals = set()
        for company in ("demo-north", "demo-south", "demo-west"):
            status, value = self.api(company_id=company)
            self.assertEqual(status, 200)
            self.assertTrue(all(row["company_id"] == company for row in value["rows"]))
            totals.add(value["summary"]["receivable_cents"])
        self.assertEqual(len(totals), 3)

    def test_unauthorised_company_returns_no_rows(self) -> None:
        status, value = self.api(user_id="demo-finance", role_id="finance", company_id="demo-south")
        self.assertEqual(status, 403)
        self.assertFalse(value["allowed"])
        self.assertNotIn("rows", value)

    def test_invalid_dimension_fails_closed(self) -> None:
        status, value = self.api(group_by="secret")
        self.assertEqual(status, 400)
        self.assertFalse(value["allowed"])
        self.assertNotIn("rows", value)

    def test_existing_projects_and_reports_remain_available(self) -> None:
        for path, token in (("/projects", "project-list-view"), ("/projects/PUB-PROJ-001", "project-detail-view"), ("/reports", "KMFA_HOMEPAGE_TEST")):
            status, content_type, body = self.request(path)
            self.assertEqual((status, content_type), (200, "text/html"))
            self.assertIn(token, body.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
