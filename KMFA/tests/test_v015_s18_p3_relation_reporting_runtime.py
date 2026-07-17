from __future__ import annotations

import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from KMFA.tools import run_v015_s18_p3_relation_reporting as runtime


class RelationReportingRuntimeTests(unittest.TestCase):
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

    def request(self, path: str) -> tuple[int, str, bytes, dict[str, str]]:
        request = Request(self.base_url + path, headers={"Accept": "application/json,text/html,text/csv"})
        try:
            with urlopen(request, timeout=4) as response:
                return response.status, response.headers.get_content_type(), response.read(), dict(response.headers)
        except HTTPError as error:
            return error.code, error.headers.get_content_type(), error.read(), dict(error.headers)

    def query(self, **values: str) -> str:
        defaults = {
            "user_id": "demo-owner",
            "role_id": "management",
            "company_id": "demo-north",
            "period": "2026-07",
            "scenario": "collection_delay",
            "verification": "VERIFIED",
        }
        defaults.update(values)
        return urlencode(defaults)

    def api(self, **values: str) -> tuple[int, dict[str, object]]:
        status, _, body, _ = self.request("/api/funds-report?" + self.query(**values))
        return status, json.loads(body)

    def test_page_is_plain_chinese_and_has_no_execution_language(self) -> None:
        status, content_type, body, _ = self.request("/funds-report")
        value = body.decode("utf-8")
        self.assertEqual((status, content_type), (200, "text/html"))
        for token in ("利润和现金分开看", "项目利润与资金占用双视图", "回款、资金缺口与贷款到期预警", "下载附表 CSV", "KMFA_RELATION_TEST"):
            self.assertIn(token, value)
        self.assertNotIn("KMFA_MetaData", value)
        self.assertNotIn(">立即付款<", value)
        self.assertNotIn(">发送提醒<", value)

    def test_api_returns_reconciled_sanitised_view(self) -> None:
        status, value = self.api()
        self.assertEqual(status, 200)
        self.assertTrue(value["allowed"])
        self.assertEqual(value["dual_view"]["project_count"], 6)
        self.assertEqual(value["alert_view"]["alert_count"], 5)
        self.assertEqual(value["money_difference_cents"], 0)
        self.assertEqual(value["profit_used_as_cash_count"], 0)
        self.assertEqual(value["full_sensitive_detail_count"], 0)
        self.assertTrue(value["thresholds_externalized"])
        self.assertFalse(value["formal_business_report"])

    def test_html_report_and_csv_appendix_match_api(self) -> None:
        _, value = self.api()
        status, content_type, html, _ = self.request("/reports/funds-receivables.html?" + self.query())
        self.assertEqual((status, content_type), (200, "text/html"))
        self.assertIn("页面与附表允许差异 0 分", html.decode("utf-8"))
        status, content_type, body, headers = self.request("/reports/funds-receivables.csv?" + self.query())
        self.assertEqual((status, content_type), (200, "text/csv"))
        self.assertIn("attachment", headers.get("Content-Disposition", ""))
        rows = list(csv.DictReader(io.StringIO(body.decode("utf-8-sig"))))
        self.assertEqual(
            [int(row["资金占用(分)"]) for row in rows],
            [row["cash_occupied_cents"] for row in value["report"]["page_rows"]],
        )

    def test_unverified_api_and_exports_are_degraded(self) -> None:
        status, value = self.api(verification="UNVERIFIED")
        self.assertEqual(status, 200)
        self.assertTrue(value["report_degraded"])
        self.assertEqual(value["report"]["report_grade"], "D")
        self.assertEqual(value["alert_view"]["alert_count"], 0)
        status, _, body, _ = self.request("/reports/funds-receivables.csv?" + self.query(verification="UNVERIFIED"))
        rows = list(csv.DictReader(io.StringIO(body.decode("utf-8-sig"))))
        self.assertEqual(status, 200)
        self.assertTrue(all(not row["收入(分)"] and not row["资金占用(分)"] for row in rows))

    def test_company_scope_is_exact(self) -> None:
        totals = set()
        for company_id in ("demo-north", "demo-south", "demo-west"):
            status, value = self.api(company_id=company_id)
            self.assertEqual(status, 200)
            self.assertTrue(all(row["company_id"] == company_id for row in value["dual_view"]["rows"]))
            totals.add(value["dual_view"]["totals"]["cash_occupied_cents"])
        self.assertEqual(len(totals), 3)

    def test_unauthorised_company_returns_no_report(self) -> None:
        status, value = self.api(user_id="demo-finance", role_id="finance", company_id="demo-south")
        self.assertEqual(status, 403)
        self.assertFalse(value["allowed"])
        self.assertNotIn("report", value)

    def test_invalid_scenario_or_verification_fails_closed(self) -> None:
        status, value = self.api(scenario="certain")
        self.assertEqual(status, 400)
        self.assertFalse(value["allowed"])
        status, value = self.api(verification="trusted")
        self.assertEqual(status, 400)
        self.assertFalse(value["allowed"])

    def test_existing_pages_remain_available(self) -> None:
        for path, token in (("/funds", "funds-view"), ("/collections", "receivables-view"), ("/projects", "project-list-view"), ("/reports", "KMFA_HOMEPAGE_TEST")):
            status, content_type, body, _ = self.request(path)
            self.assertEqual((status, content_type), (200, "text/html"))
            self.assertIn(token, body.decode("utf-8"))

    def test_current_project_event_updates_page_and_both_exports_only_in_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            server, thread, base_url = runtime.start_server(event_path=Path(directory) / "events.jsonl")
            query = self.query()

            def get(path: str) -> bytes:
                with urlopen(base_url + path, timeout=4) as response:
                    self.assertEqual(response.status, 200)
                    return response.read()

            try:
                before = json.loads(get("/api/funds-report?" + query))
                before_south = json.loads(get("/api/funds-report?" + self.query(company_id="demo-south")))
                body = {
                    "user_id": "demo-owner",
                    "role_id": "management",
                    "company_id": "demo-north",
                    "period": "2026-07",
                    "project_id": "PUB-PROJ-001",
                    "actor_ref": "s18-stage-review",
                    "option_id": "USE_SETTLEMENT_SUPPORT",
                    "reason_zh": "整体复审核对当前项目成本后同步报告和附表",
                    "idempotency_key": "s18-review-current-projection-001",
                }
                request = Request(
                    base_url + "/api/projects/workflow/variance",
                    data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(request, timeout=4) as response:
                    self.assertEqual(response.status, 200)

                after = json.loads(get("/api/funds-report?" + query))
                after_south = json.loads(get("/api/funds-report?" + self.query(company_id="demo-south")))
                first = next(row for row in after["report"]["page_rows"] if row["project_id"] == "PUB-PROJ-001")
                self.assertEqual(before["report"]["page_rows"][0]["cost_cents"], 235_832_000)
                self.assertEqual(first["cost_cents"], 234_552_000)
                self.assertEqual(after["dual_view"]["rows"], after["report"]["page_rows"])
                self.assertEqual(after["dual_view"]["totals"], after["report"]["summary"])
                self.assertNotEqual(before["dual_view"]["totals"]["cost_cents"], after["dual_view"]["totals"]["cost_cents"])
                self.assertEqual(before_south["dual_view"]["totals"], after_south["dual_view"]["totals"])

                html = get("/reports/funds-receivables.html?" + query).decode("utf-8")
                self.assertIn("¥2,345,520.00", html)
                rows = list(csv.DictReader(io.StringIO(get("/reports/funds-receivables.csv?" + query).decode("utf-8-sig"))))
                exported = next(row for row in rows if row["项目编号"] == "PUB-PROJ-001")
                self.assertEqual(int(exported["成本(分)"]), 234_552_000)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
