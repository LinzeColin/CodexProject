from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from KMFA.tools import run_v015_s19_p1_tax_invoice_facts as runtime


class TaxInvoiceRuntimeTests(unittest.TestCase):
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

    def request(self, path: str) -> tuple[int, str, bytes]:
        request = Request(self.base_url + path, headers={"Accept": "application/json,text/html"})
        try:
            with urlopen(request, timeout=4) as response:
                return response.status, response.headers.get_content_type(), response.read()
        except HTTPError as error:
            return error.code, error.headers.get_content_type(), error.read()

    def query(self, **values: str) -> str:
        defaults = {"user_id": "demo-owner", "role_id": "management", "company_id": "demo-north", "period": "2026-07"}
        defaults.update(values)
        return urlencode(defaults)

    def api(self, **values: str) -> tuple[int, dict[str, object]]:
        status, _, body = self.request("/api/tax-invoices?" + self.query(**values))
        return status, json.loads(body)

    def test_page_is_plain_chinese_and_has_management_boundary(self) -> None:
        status, content_type, body = self.request("/tax-policy")
        text = body.decode("utf-8")
        self.assertEqual((status, content_type), (200, "text/html"))
        for token in ("先把税票事实对齐", "税票事实", "需要人工复核的异常", "项目税负管理视图", "管理分析，不是正式申报", "KMFA_TAX_INVOICE_TEST"):
            self.assertIn(token, text)
        for token in ("KMFA_MetaData", ">自动调税<", ">立即申报<", ">开具发票<"):
            self.assertNotIn(token, text)

    def test_api_returns_exact_facts_matches_and_burden(self) -> None:
        status, value = self.api()
        self.assertEqual(status, 200)
        self.assertTrue(value["allowed"])
        self.assertEqual(value["all_fact_count"], 8)
        self.assertEqual(value["summary"]["matched_count"], 4)
        self.assertEqual(value["summary"]["review_count"], 4)
        self.assertEqual(value["anomaly_count"], 5)
        self.assertEqual(value["project_burden_count"], 3)
        self.assertTrue(value["management_analysis_only"])
        self.assertFalse(value["formal_filing_conclusion"])

    def test_unknown_rate_is_visible_but_not_inferred(self) -> None:
        _, value = self.api(invoice_status="PENDING_CONFIRMATION")
        self.assertEqual(value["summary"]["fact_count"], 1)
        row = value["rows"][0]
        self.assertEqual(row["tax_rate_display_zh"], "待确认")
        self.assertIsNone(row["tax_rate_bps"])
        self.assertIsNone(row["tax_cents"])
        self.assertFalse(row["rate_inferred"])
        self.assertEqual(value["rate_inference_count"], 0)

    def test_filters_return_only_requested_scope(self) -> None:
        status, value = self.api(direction="INPUT", match_state="REVIEW_REQUIRED")
        self.assertEqual(status, 200)
        self.assertEqual(value["summary"]["fact_count"], 2)
        self.assertTrue(all(row["direction"] == "INPUT" and row["match_state"] == "REVIEW_REQUIRED" for row in value["rows"]))

    def test_company_and_period_scope_is_exact(self) -> None:
        totals = set()
        for company_id in ("demo-north", "demo-south", "demo-west"):
            status, value = self.api(company_id=company_id, period="2026-Q2")
            self.assertEqual(status, 200)
            self.assertTrue(all(row["company_id"] == company_id and row["contract_period"] == "2026-Q2" for row in value["rows"]))
            totals.add(value["summary"]["explicit_tax_cents"])
        self.assertEqual(len(totals), 3)

    def test_unauthorised_company_returns_no_tax_facts(self) -> None:
        status, value = self.api(user_id="demo-finance", role_id="finance", company_id="demo-south")
        self.assertEqual(status, 403)
        self.assertFalse(value["allowed"])
        self.assertNotIn("rows", value)

    def test_invalid_filter_and_company_fail_closed(self) -> None:
        status, value = self.api(match_state="CERTAIN")
        self.assertEqual(status, 400)
        self.assertFalse(value["allowed"])
        status, value = self.api(company_id="unknown-company")
        self.assertIn(status, (400, 403))
        self.assertFalse(value["allowed"])

    def test_existing_pages_remain_available(self) -> None:
        for path, token in (("/funds-report", "funds-report-view"), ("/funds", "funds-view"), ("/collections", "receivables-view"), ("/projects", "project-list-view")):
            status, content_type, body = self.request(path)
            self.assertEqual((status, content_type), (200, "text/html"))
            self.assertIn(token, body.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
