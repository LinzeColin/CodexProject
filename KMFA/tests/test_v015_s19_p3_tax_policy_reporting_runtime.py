from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from KMFA.tools import run_v015_s19_p3_tax_policy_reporting as runtime


class TaxPolicyReportingRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.server, cls.thread, cls.base_url = runtime.start_server(event_path=Path(cls.temporary.name) / "events.jsonl")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join(timeout=3); cls.temporary.cleanup()

    def request(self, path: str, body: dict[str, object] | None = None) -> tuple[int, str, bytes]:
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        request = Request(self.base_url + path, data=data, headers={"Accept": "application/json,text/html", "Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=4) as response:
                return response.status, response.headers.get_content_type(), response.read()
        except HTTPError as error:
            return error.code, error.headers.get_content_type(), error.read()

    def query(self, **values: str) -> str:
        defaults = {"user_id": "demo-owner", "role_id": "tax", "company_id": "demo-north", "period": "2026-07"}
        defaults.update(values)
        return urlencode(defaults)

    def api(self, **values: str) -> tuple[int, dict[str, object]]:
        status, _, body = self.request("/api/tax-policy-report?" + self.query(**values))
        return status, json.loads(body)

    def review_body(self, **values: object) -> dict[str, object]:
        _, view = self.api()
        defaults: dict[str, object] = {
            "report_id": view["report_id"], "company_id": "demo-north", "period": "2026-07",
            "user_id": "demo-owner", "role_id": "tax", "opinion_code": "NEEDS_SOURCE_CHECK",
            "comment_zh": "请核对票据和合同依据", "basis_refs": [view["review_basis"][0]["basis_ref"]], "idempotency_key": "runtime-1",
        }
        defaults.update(values)
        return defaults

    def test_page_uses_plain_chinese_and_keeps_report_boundaries(self) -> None:
        status, content_type, body = self.request("/tax-policy-report")
        text = body.decode("utf-8")
        self.assertEqual((status, content_type), (200, "text/html"))
        for token in ("本期需要确认的事项", "本周期材料准备报告", "专业复核意见", "仅供内部管理复核", "KMFA_TAX_POLICY_REPORT_TEST"):
            self.assertIn(token, text)
        for token in ("KMFA_MetaData", ">自动调税<", ">正式申报<", ">承诺认定<", "爆雷"):
            self.assertNotIn(token, text)

    def test_api_combines_tax_policy_and_review_permission(self) -> None:
        status, value = self.api()
        self.assertEqual(status, 200)
        self.assertEqual(value["tax_risk_summary"]["review_invoice_count"], 4)
        self.assertEqual(value["policy_preparation_report"]["missing_evidence_count"], 3)
        self.assertTrue(value["review_permission"]["allowed"])
        self.assertEqual(value["formal_filing_conclusion_count"], 0)
        self.assertEqual(value["formal_eligibility_conclusion_count"], 0)

    def test_management_can_view_but_cannot_write_review(self) -> None:
        status, value = self.api(role_id="management")
        self.assertEqual(status, 200)
        self.assertFalse(value["review_permission"]["allowed"])
        status, _, body = self.request("/api/tax-policy-reviews", self.review_body(role_id="management", idempotency_key="denied-1"))
        self.assertEqual(status, 400)
        self.assertIn("只有税务或审核角色", json.loads(body)["reason_zh"])

    def test_authorised_review_appends_and_is_idempotent(self) -> None:
        body = self.review_body(idempotency_key="accepted-1")
        first_status, _, first_body = self.request("/api/tax-policy-reviews", body)
        second_status, _, second_body = self.request("/api/tax-policy-reviews", body)
        self.assertEqual((first_status, second_status), (200, 200))
        self.assertFalse(json.loads(first_body)["idempotent_replay"])
        self.assertTrue(json.loads(second_body)["idempotent_replay"])
        _, value = self.api()
        self.assertEqual(value["review_event_count"], 1)

    def test_review_event_is_isolated_by_company_and_period(self) -> None:
        _, north = self.api()
        _, west = self.api(company_id="demo-west")
        _, quarter = self.api(period="2026-Q2")
        self.assertGreaterEqual(north["review_event_count"], 1)
        self.assertEqual(west["review_event_count"], 0)
        self.assertEqual(quarter["review_event_count"], 0)

    def test_ungranted_company_returns_no_report(self) -> None:
        status, value = self.api(user_id="demo-finance", role_id="reviewer", company_id="demo-south")
        self.assertEqual(status, 403)
        self.assertFalse(value["allowed"])
        self.assertNotIn("tax_risk_summary", value)

    def test_unknown_basis_is_rejected_without_event(self) -> None:
        before = len(self.server.review_journal.read())
        status, _, body = self.request("/api/tax-policy-reviews", self.review_body(basis_refs=["UNKNOWN"], idempotency_key="unknown-1"))
        self.assertEqual(status, 400)
        self.assertIn("不属于当前报告", json.loads(body)["reason_zh"])
        self.assertEqual(len(self.server.review_journal.read()), before)

    def test_existing_s19_pages_remain_available(self) -> None:
        for path, token in (("/policy-eligibility", "policy-eligibility-view"), ("/tax-policy", "tax-invoice-view"), ("/funds-report", "funds-report-view")):
            status, content_type, body = self.request(path)
            self.assertEqual((status, content_type), (200, "text/html"))
            self.assertIn(token, body.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
