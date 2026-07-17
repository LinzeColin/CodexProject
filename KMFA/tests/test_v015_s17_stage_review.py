from __future__ import annotations

import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from KMFA.tools import run_v015_s17_p3_project_workflow as runtime


class S17StageReviewIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.event_path = Path(self.temp.name) / "events.jsonl"
        self.server, self.thread, self.base_url = runtime.start_server(event_path=self.event_path)

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.temp.cleanup()

    @staticmethod
    def query(**extra: str) -> dict[str, str]:
        value = {
            "user_id": "demo-owner",
            "role_id": "management",
            "company_id": "demo-north",
            "period": "2026-07",
            "project_status": "all",
            "page": "1",
            "page_size": "6",
            "project_id": "PUB-PROJ-001",
        }
        value.update(extra)
        return value

    def get_json(self, path: str, **extra: str) -> dict[str, object]:
        with urlopen(self.base_url + path + "?" + urlencode(self.query(**extra)), timeout=5) as response:
            self.assertEqual(response.status, 200)
            return json.loads(response.read().decode("utf-8"))

    def get_text(self, path: str, **extra: str) -> str:
        with urlopen(self.base_url + path + "?" + urlencode(self.query(**extra)), timeout=5) as response:
            self.assertEqual(response.status, 200)
            return response.read().decode("utf-8-sig")

    def post(self, path: str, **extra: str) -> dict[str, object]:
        body = {
            **self.query(),
            "actor_ref": "s17-stage-review",
            **extra,
        }
        request = Request(
            self.base_url + path,
            data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            self.assertEqual(response.status, 200)
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def project_row(payload: dict[str, object], project_id: str = "PUB-PROJ-001") -> dict[str, object]:
        rows = payload["rows"]
        assert isinstance(rows, list)
        return next(row for row in rows if row["project_id"] == project_id)

    def resolve_variance(self, key: str = "s17-review-variance-001") -> dict[str, object]:
        return self.post(
            "/api/projects/workflow/variance",
            option_id="USE_SETTLEMENT_SUPPORT",
            reason_zh="整体复审已核对两项来源、处理依据和金额影响",
            idempotency_key=key,
        )

    def test_list_detail_and_current_html_report_share_one_projection(self) -> None:
        before_list = self.project_row(self.get_json("/api/projects"))
        before_detail = self.get_json("/api/projects/detail")
        before_report = self.get_json("/api/projects/workflow/report")
        self.assertEqual(before_list["cost_cents"], before_detail["cost"]["actual_total_cents"])
        self.assertEqual(before_list["cost_cents"], before_report["summary"]["cost_cents"])

        self.resolve_variance()
        after_list = self.project_row(self.get_json("/api/projects"))
        after_detail = self.get_json("/api/projects/detail")
        after_report = self.get_json("/api/projects/workflow/report")
        current_html = self.get_text("/reports/project-cost.html")

        expected = after_detail["cost"]["actual_total_cents"]
        self.assertEqual(after_list["cost_cents"], expected)
        self.assertEqual(after_report["summary"]["cost_cents"], expected)
        self.assertEqual(after_report["checks"]["page_golden_difference_cents"], 0)
        self.assertEqual(after_report["checks"]["category_page_difference_cents"], 0)
        self.assertIn("2,345,520.00", current_html)

    def test_resolved_cost_risk_is_removed_and_filters_follow_current_state(self) -> None:
        self.resolve_variance()
        row = self.project_row(self.get_json("/api/projects"))
        self.assertEqual(row["status"], "NORMAL")
        self.assertEqual(row["status_zh"], "进展正常")
        self.assertEqual(row["risk_level"], "LOW")
        self.assertEqual(row["risk_zh"], "低风险")
        self.assertNotIn("成本偏差待复核", row["risk_reasons_zh"])
        detail = self.get_json("/api/projects/detail")
        self.assertEqual(detail["overview"]["risk_zh"], "低风险")
        self.assertNotIn("成本偏差待复核", detail["overview"]["risk_reasons_zh"])

        low_risk = self.get_json("/api/projects", risk="LOW")
        self.assertIn("PUB-PROJ-001", low_risk["all_filtered_project_ids"])
        attention = self.get_json("/api/projects", project_status="attention")
        self.assertNotIn("PUB-PROJ-001", attention["all_filtered_project_ids"])

    def test_compare_and_export_use_the_same_current_values(self) -> None:
        self.resolve_variance()
        comparison = self.get_json(
            "/api/projects/compare",
            project_ids="PUB-PROJ-001,PUB-PROJ-002",
        )
        first = next(row for row in comparison["rows"] if row["project_id"] == "PUB-PROJ-001")
        detail = self.get_json("/api/projects/detail")
        self.assertEqual(first["cost_cents"], detail["cost"]["actual_total_cents"])
        self.assertEqual(
            comparison["totals"]["cost_cents"],
            sum(row["cost_cents"] for row in comparison["rows"]),
        )

        exported = list(
            csv.DictReader(
                io.StringIO(
                    self.get_text(
                        "/api/projects/export",
                        project_ids="PUB-PROJ-001,PUB-PROJ-002",
                    )
                )
            )
        )
        exported_first = next(row for row in exported if row["项目编号"] == "PUB-PROJ-001")
        self.assertEqual(int(exported_first["成本(分)"]), detail["cost"]["actual_total_cents"])

    def test_reversal_restores_list_detail_report_and_risk_together(self) -> None:
        created = self.resolve_variance()
        event_id = created["event"]["event_id"]
        self.post(
            "/api/projects/workflow/reverse",
            event_id=event_id,
            reason_zh="整体复审验证撤销后所有页面恢复上一版",
            idempotency_key="s17-review-reverse-001",
        )
        row = self.project_row(self.get_json("/api/projects"))
        detail = self.get_json("/api/projects/detail")
        report = self.get_json("/api/projects/workflow/report")
        self.assertEqual(row["cost_cents"], 235_832_000)
        self.assertEqual(row["cost_cents"], detail["cost"]["actual_total_cents"])
        self.assertEqual(row["cost_cents"], report["summary"]["cost_cents"])
        self.assertEqual(row["status"], "ATTENTION")
        self.assertEqual(row["risk_level"], "MEDIUM")
        self.assertIn("成本偏差待复核", row["risk_reasons_zh"])

    def test_processing_events_do_not_cross_company_or_project_boundaries(self) -> None:
        south_before = self.get_json(
            "/api/projects/detail",
            company_id="demo-south",
            project_id="PUB-PROJ-001",
        )
        other_before = self.get_json(
            "/api/projects/detail",
            company_id="demo-north",
            project_id="PUB-PROJ-002",
        )
        self.resolve_variance()
        south_after = self.get_json(
            "/api/projects/detail",
            company_id="demo-south",
            project_id="PUB-PROJ-001",
        )
        other_after = self.get_json(
            "/api/projects/detail",
            company_id="demo-north",
            project_id="PUB-PROJ-002",
        )
        south_workflow = self.get_json(
            "/api/projects/workflow",
            company_id="demo-south",
            project_id="PUB-PROJ-001",
        )
        other_workflow = self.get_json(
            "/api/projects/workflow",
            company_id="demo-north",
            project_id="PUB-PROJ-002",
        )
        self.assertEqual(south_before["cost"], south_after["cost"])
        self.assertEqual(other_before["cost"], other_after["cost"])
        self.assertEqual(south_workflow["event_count"], 0)
        self.assertEqual(other_workflow["event_count"], 0)


if __name__ == "__main__":
    unittest.main()
