from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from KMFA.tools import run_v015_s23_p1_end_to_end_business_flow as runtime


class EndToEndBusinessFlowRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.server, self.thread, self.base_url = runtime.start_server(
            event_path=root / "base.jsonl",
            data_root=root / "data",
            confirmation_event_path=root / "confirmations.jsonl",
            publication_event_path=root / "publications.jsonl",
            report_model_event_path=root / "models.jsonl",
            export_event_path=root / "exports.jsonl",
            export_bundle_root=root / "bundles",
            workflow_event_path=root / "workflows.jsonl",
            notification_event_path=root / "notifications.jsonl",
            audit_event_path=root / "audit.jsonl",
            operations_root=root / "operations",
            xlsx_preview_root=root / "previews",
            secret_values={
                "KMFA_LOCAL_AUTH_KEY": hashlib.sha256(b"s23p1-auth").hexdigest(),
                "KMFA_SESSION_SIGNING_KEY": hashlib.sha256(b"s23p1-sign").hexdigest(),
            },
        )

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temporary.cleanup()

    def json_get(self, path: str) -> tuple[int, dict]:
        try:
            with urllib.request.urlopen(self.base_url + path, timeout=15) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def test_human_page_and_ready_status_are_available(self) -> None:
        page = urllib.request.urlopen(self.base_url + "/end-to-end", timeout=15).read().decode("utf-8")
        status_code, status = self.json_get("/api/end-to-end/status")
        self.assertEqual(status_code, 200)
        self.assertEqual(status["status"], "READY")
        self.assertIn("一套数字，贯穿首页、项目重算和经营报告", page)
        self.assertIn("window.KMFA_END_TO_END_TEST", page)
        self.assertIn("/report-workflow", page)

    def test_homepage_api_is_bound_to_backend_publication(self) -> None:
        status_code, home = self.json_get("/api/homepage?user_id=demo-owner&role_id=management&company_id=demo-north&period=2026-07")
        publication = self.server.recalculation_workbench.current_publication()
        project = next(row for row in home["summary_metrics"] if row["metric_id"] == "PROJECT_GROSS_PROFIT")
        self.assertEqual(status_code, 200)
        self.assertEqual(home["publication_version_id"], publication["publication_version_id"])
        self.assertEqual(home["shared_metric_fingerprint"], publication["consistency"]["shared_metric_fingerprint"])
        self.assertEqual(project["primary_value"], publication["metrics"]["project_margin_cents"])
        self.assertEqual(project["route"], "/data-update")

    def test_xlsx_route_is_fail_closed_without_an_export(self) -> None:
        status_code, value = self.json_get("/api/report-exports/EXPORT-S23P1-0000000000000000/report.xlsx")
        self.assertEqual(status_code, 404)
        self.assertEqual(value["code"], "EXPORT_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
