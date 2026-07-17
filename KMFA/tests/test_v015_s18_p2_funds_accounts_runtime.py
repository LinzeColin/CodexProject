from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from KMFA.tools import run_v015_s18_p2_funds_accounts as runtime


class FundsAccountsRuntimeTests(unittest.TestCase):
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

    def api(self, **values: str) -> tuple[int, dict[str, object]]:
        defaults = {"user_id": "demo-owner", "role_id": "management", "company_id": "demo-north", "period": "2026-07", "scenario": "base"}
        defaults.update(values)
        status, _, body = self.request("/api/funds?" + urlencode(defaults))
        return status, json.loads(body)

    def test_page_is_plain_chinese_and_has_no_payment_button(self) -> None:
        status, content_type, body = self.request("/funds")
        value = body.decode("utf-8")
        self.assertEqual((status, content_type), (200, "text/html"))
        for token in ("账户先核清", "先分清三种数字", "银行账户事实", "未来四周现金预测", "贷款到期与资金缺口", "KMFA_FUNDS_TEST"):
            self.assertIn(token, value)
        self.assertNotIn("KMFA_MetaData", value)
        self.assertNotIn(">立即付款<", value)
        self.assertNotIn(">发起还款<", value)

    def test_api_returns_reconciled_public_view(self) -> None:
        status, value = self.api()
        self.assertEqual(status, 200)
        self.assertTrue(value["allowed"])
        self.assertEqual(value["data_classification"], "PUBLIC_SYNTHETIC")
        self.assertEqual(value["money_difference_cents"], 0)
        self.assertEqual(value["cross_company_leak_count"], 0)
        self.assertEqual(value["forecast_presented_as_certainty_count"], 0)
        self.assertEqual(value["payment_execution_count"], 0)
        self.assertEqual(value["payment_button_count"], 0)

    def test_scenarios_are_distinct_and_reconciled(self) -> None:
        endings = set()
        for scenario in ("base", "collection_delay", "cost_pressure"):
            status, value = self.api(scenario=scenario)
            self.assertEqual(status, 200)
            forecast = value["forecast"]
            self.assertEqual(forecast["scenario_difference_cents"], 0)
            self.assertTrue(forecast["fact_plan_assumption_separated"])
            endings.add(forecast["rows"][-1]["scenario_closing_cents"])
        self.assertEqual(len(endings), 3)

    def test_company_scope_is_exact(self) -> None:
        totals = set()
        for company_id in ("demo-north", "demo-south", "demo-west"):
            status, value = self.api(company_id=company_id)
            self.assertEqual(status, 200)
            self.assertTrue(all(row["company_id"] == company_id for row in value["accounts"]["accounts"]))
            totals.add(value["summary"]["available_cash_cents"])
        self.assertEqual(len(totals), 3)

    def test_unauthorised_company_returns_no_funds(self) -> None:
        status, value = self.api(user_id="demo-finance", role_id="finance", company_id="demo-south")
        self.assertEqual(status, 403)
        self.assertFalse(value["allowed"])
        self.assertNotIn("accounts", value)

    def test_invalid_scenario_fails_closed(self) -> None:
        status, value = self.api(scenario="certain")
        self.assertEqual(status, 400)
        self.assertFalse(value["allowed"])
        self.assertNotIn("accounts", value)

    def test_existing_pages_remain_available(self) -> None:
        for path, token in (("/collections", "receivables-view"), ("/projects", "project-list-view"), ("/reports", "KMFA_HOMEPAGE_TEST")):
            status, content_type, body = self.request(path)
            self.assertEqual((status, content_type), (200, "text/html"))
            self.assertIn(token, body.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
