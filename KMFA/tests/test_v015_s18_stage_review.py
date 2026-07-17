from __future__ import annotations

import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from KMFA.tools import run_v015_s18_p3_relation_reporting as runtime


class S18StageReviewIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.server, self.thread, self.base_url = runtime.start_server(
            event_path=Path(self.temp.name) / "events.jsonl"
        )

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temp.cleanup()

    @staticmethod
    def query(**extra: str) -> dict[str, str]:
        value = {
            "user_id": "demo-owner",
            "role_id": "management",
            "company_id": "demo-north",
            "period": "2026-07",
            "project_id": "PUB-PROJ-001",
            "scenario": "collection_delay",
            "verification": "VERIFIED",
        }
        value.update(extra)
        return value

    def get_json(self, path: str, **extra: str) -> dict[str, object]:
        query = urlencode(self.query(**extra))
        with urlopen(self.base_url + path + "?" + query, timeout=5) as response:
            self.assertEqual(response.status, 200)
            return json.loads(response.read().decode("utf-8"))

    def get_text(self, path: str, **extra: str) -> str:
        query = urlencode(self.query(**extra))
        with urlopen(self.base_url + path + "?" + query, timeout=5) as response:
            self.assertEqual(response.status, 200)
            return response.read().decode("utf-8-sig")

    def resolve_variance(self) -> None:
        body = {
            **self.query(),
            "actor_ref": "s18-stage-review",
            "option_id": "USE_SETTLEMENT_SUPPORT",
            "reason_zh": "整体复审核对当前项目成本后同步报告和附表",
            "idempotency_key": "s18-review-current-projection-001",
        }
        request = Request(
            self.base_url + "/api/projects/workflow/variance",
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            self.assertEqual(response.status, 200)

    @staticmethod
    def project_row(payload: dict[str, object]) -> dict[str, object]:
        rows = payload["dual_view"]["rows"]
        assert isinstance(rows, list)
        return next(row for row in rows if row["project_id"] == "PUB-PROJ-001")

    def test_current_cost_is_shared_by_detail_report_html_and_csv(self) -> None:
        before = self.get_json("/api/funds-report")
        self.assertEqual(self.project_row(before)["cost_cents"], 235_832_000)
        self.resolve_variance()
        detail = self.get_json("/api/projects/detail")
        report = self.get_json("/api/funds-report")
        row = self.project_row(report)
        self.assertEqual(row["cost_cents"], 234_552_000)
        self.assertEqual(row["cost_cents"], detail["cost"]["actual_total_cents"])
        self.assertEqual(report["dual_view"]["rows"], report["report"]["page_rows"])
        self.assertEqual(report["dual_view"]["totals"], report["report"]["summary"])
        self.assertEqual(report["money_difference_cents"], 0)

        html = self.get_text("/reports/funds-receivables.html")
        self.assertIn("¥2,345,520.00", html)
        exported = list(csv.DictReader(io.StringIO(self.get_text("/reports/funds-receivables.csv"))))
        exported_row = next(item for item in exported if item["项目编号"] == "PUB-PROJ-001")
        self.assertEqual(int(exported_row["成本(分)"]), 234_552_000)

    def test_project_events_are_isolated_by_company_and_period(self) -> None:
        south_before = self.get_json("/api/funds-report", company_id="demo-south")
        other_period_before = self.get_json("/api/funds-report", period="2026-Q2")
        self.resolve_variance()
        north_after = self.get_json("/api/funds-report")
        south_after = self.get_json("/api/funds-report", company_id="demo-south")
        other_period_after = self.get_json("/api/funds-report", period="2026-Q2")
        self.assertEqual(self.project_row(north_after)["cost_cents"], 234_552_000)
        self.assertEqual(south_before["dual_view"]["totals"], south_after["dual_view"]["totals"])
        self.assertEqual(other_period_before["dual_view"]["totals"], other_period_after["dual_view"]["totals"])

    def test_unverified_report_hides_all_money_and_alerts_after_event(self) -> None:
        self.resolve_variance()
        value = self.get_json("/api/funds-report", verification="UNVERIFIED")
        self.assertTrue(value["report_degraded"])
        self.assertEqual(value["alert_view"]["alert_count"], 0)
        self.assertTrue(all(number is None for number in value["dual_view"]["totals"].values()))
        exported = list(
            csv.DictReader(
                io.StringIO(
                    self.get_text(
                        "/reports/funds-receivables.csv",
                        verification="UNVERIFIED",
                    )
                )
            )
        )
        self.assertTrue(all(not row["收入(分)"] and not row["资金占用(分)"] for row in exported))

    def test_alert_routes_are_actionable_and_context_preserving(self) -> None:
        value = self.get_json("/api/funds-report")
        routes = [row["detail_route"] for row in value["alert_view"]["alerts"]]
        self.assertTrue(any(route.startswith("/collections?project=") for route in routes))
        self.assertIn("/funds", routes)
        html = runtime.render_html()
        for token in ("rr-alert-action", "打开回款明细", "打开资金明细", "company_id", "period"):
            self.assertIn(token, html)

    def test_stage_contract_has_zero_business_side_effects(self) -> None:
        value = self.get_json("/api/funds-report")
        for key in (
            "raw_root_access_count",
            "live_source_read_count",
            "external_network_request_count",
            "source_data_write_count",
            "fact_layer_write_count",
            "notification_send_count",
            "external_message_count",
            "payment_execution_count",
            "bank_operation_count",
            "real_business_action_count",
        ):
            self.assertEqual(value[key], 0)
        self.assertFalse(value["formal_business_report"])


if __name__ == "__main__":
    unittest.main()
