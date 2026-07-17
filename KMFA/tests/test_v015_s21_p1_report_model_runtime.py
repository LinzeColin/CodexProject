from __future__ import annotations

import json
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from KMFA.tools import run_v015_s21_p1_report_model as runtime


class ReportModelRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.report_path = root / "report_models.jsonl"
        self.server, self.thread, self.base_url = runtime.start_server(
            event_path=root / "base.jsonl", data_root=root / "data-update",
            confirmation_event_path=root / "confirmation.jsonl",
            publication_event_path=root / "publication.jsonl",
            report_model_event_path=self.report_path,
        )

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temporary.cleanup()

    def request(self, path: str, body=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(self.base_url + path, data=data, headers={"Content-Type": "application/json"} if data else {})
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def create(self, *, key="runtime-create-001", readiness="COMPLETE", period_kind="MONTHLY", period_key="2026-07"):
        return self.request("/api/report-models", {
            "company_id": "demo-north", "period_kind": period_kind, "period_key": period_key,
            "readiness_case": readiness, "created_by": "运行时测试负责人", "idempotency_key": key,
        })

    def test_latest_and_predecessor_pages_remain_available(self) -> None:
        for path, marker in (("/recalculation-publication", "报告模型"), ("/report-model", "先确定报告期间、版本和阅读层次")):
            with urllib.request.urlopen(self.base_url + path) as response:
                self.assertIn(marker, response.read().decode("utf-8"))
        status, current = self.request("/api/recalculation/current")
        self.assertEqual((status, current["publication_version_id"]), (200, "PUB-S20P3-0001"))

    def test_options_cover_five_periods_and_two_audiences(self) -> None:
        status, value = self.request("/api/report-model/options")
        self.assertEqual(status, 200)
        self.assertEqual([row["value"] for row in value["period_kinds"]], list(runtime.kernel.PERIOD_KINDS))
        self.assertEqual([row["value"] for row in value["audiences"]], ["MANAGEMENT", "PROFESSIONAL"])

    def test_create_and_get_bind_current_publication_and_formulas(self) -> None:
        status, created = self.create()
        self.assertEqual(status, 201)
        publication = next(row for row in created["source_bindings"] if row["domain_id"] == "published_metrics")
        self.assertEqual(publication["version_ref"], "PUB-S20P3-0001")
        self.assertEqual(len(created["formula_bindings"]), 2)
        status, fetched = self.request("/api/report-models/" + created["report_version_id"])
        self.assertEqual((status, fetched["event_hash"]), (200, created["event_hash"]))

    def test_duplicate_period_must_use_revision(self) -> None:
        _, first = self.create()
        status, error = self.create(key="runtime-create-002")
        self.assertEqual((status, error["code"]), (409, "REVISION_REQUIRED"))
        status, revision = self.request(f"/api/report-models/{first['report_version_id']}/revisions", {
            "revision_reason_zh": "补充本期管理说明并保留初版", "created_by": "运行时测试负责人",
            "idempotency_key": "runtime-revise-001",
        })
        self.assertEqual((status, revision["version_number"]), (201, 2))
        _, listing = self.request("/api/report-models?company_id=demo-north")
        self.assertEqual((listing["report_family_count"], listing["report_version_count"]), (1, 2))

    def test_incomplete_case_cannot_claim_complete_report(self) -> None:
        status, report = self.create(readiness="MISSING")
        self.assertEqual(status, 201)
        trust = report["trust_and_limitations"]
        self.assertFalse(trust["complete_report_claim_allowed"])
        self.assertIn("不能称为完整报告", trust["explanation_zh"])

    def test_management_and_professional_audiences_are_separate(self) -> None:
        _, report = self.create()
        version = report["report_version_id"]
        _, management = self.request(f"/api/report-models/{version}/audiences/management")
        _, professional = self.request(f"/api/report-models/{version}/audiences/professional")
        self.assertEqual((management["section_count"], professional["section_count"]), (5, 1))
        self.assertEqual(management["data_check_board_backend_content_count"], 0)
        self.assertEqual(management["technical_log_content_count"], 0)

    def test_invalid_period_and_unknown_version_fail_closed(self) -> None:
        status, error = self.create(period_key="2026-13")
        self.assertEqual((status, error["code"]), (400, "INVALID_PERIOD"))
        status, error = self.request("/api/report-models/REPORT-DEMO-NORTH-MONTHLY-2026-07-V9999")
        self.assertEqual((status, error["code"]), (404, "REPORT_VERSION_NOT_FOUND"))

    def test_restart_recovers_identical_versions(self) -> None:
        _, created = self.create()
        self.server.report_model_journal = runtime.kernel.ReportModelJournal(self.report_path)
        _, fetched = self.request("/api/report-models/" + created["report_version_id"])
        self.assertEqual(fetched["event_hash"], created["event_hash"])


if __name__ == "__main__":
    unittest.main()
