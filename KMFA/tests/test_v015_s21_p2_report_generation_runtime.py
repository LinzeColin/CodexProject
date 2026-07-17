from __future__ import annotations

import json
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from KMFA.tools import run_v015_s21_p2_report_generation as runtime


class ReportGenerationRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.server, self.thread, self.base_url = runtime.start_server(
            event_path=root / "base.jsonl", data_root=root / "data-update",
            confirmation_event_path=root / "confirmation.jsonl", publication_event_path=root / "publication.jsonl",
            report_model_event_path=root / "report-models.jsonl", export_event_path=root / "exports.jsonl",
            export_bundle_root=root / "bundles",
        )

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temporary.cleanup()

    def request_json(self, path: str, body=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(self.base_url + path, data=data, headers={"Content-Type": "application/json"} if data else {})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def create_report(self, *, readiness="COMPLETE"):
        status, value = self.request_json("/api/report-models", {
            "company_id": "demo-north", "period_kind": "MONTHLY", "period_key": "2026-07",
            "readiness_case": readiness, "created_by": "运行时测试负责人", "idempotency_key": "runtime-model-001",
        })
        self.assertEqual(status, 201)
        return value

    def create_export(self, report):
        return self.request_json("/api/report-exports", {"report_version_id": report["report_version_id"], "idempotency_key": "runtime-export-001"})

    def test_report_model_page_links_to_report_generation(self) -> None:
        with urllib.request.urlopen(self.base_url + "/report-model") as response:
            self.assertIn("报告生成", response.read().decode("utf-8"))
        with urllib.request.urlopen(self.base_url + "/report-generation") as response:
            self.assertIn("一份事实数据，生成三种一致的报告", response.read().decode("utf-8"))

    def test_options_list_three_formats_and_keep_publication_closed(self) -> None:
        status, value = self.request_json("/api/report-exports/options")
        self.assertEqual(status, 200)
        self.assertEqual([row["value"] for row in value["formats"]], ["HTML", "PDF", "CSV"])
        self.assertFalse(value["approval_or_publication_in_scope"])

    def test_create_export_binds_report_and_three_files(self) -> None:
        report = self.create_report()
        status, value = self.create_export(report)
        self.assertEqual(status, 201)
        self.assertEqual(value["report_version_id"], report["report_version_id"])
        self.assertEqual(set(value["files"]), set(runtime.kernel.FORMATS))
        self.assertEqual(value["cross_format_consistency"]["difference_integer"], 0)

    def test_incomplete_report_is_refused(self) -> None:
        report = self.create_report(readiness="MISSING")
        status, error = self.create_export(report)
        self.assertEqual((status, error["code"]), (409, "REPORT_INPUTS_INCOMPLETE"))

    def test_html_pdf_and_csv_download_headers_and_bodies(self) -> None:
        status, export = self.create_export(self.create_report())
        self.assertEqual(status, 201)
        expectations = {
            "html": ("text/html", b"<!doctype html>"),
            "pdf": ("application/pdf", b"%PDF"),
            "appendix.csv": ("text/csv", b"\xef\xbb\xbf"),
        }
        for suffix, (content_type, prefix) in expectations.items():
            with urllib.request.urlopen(f"{self.base_url}/api/report-exports/{export['export_id']}/{suffix}", timeout=10) as response:
                body = response.read()
                self.assertEqual(response.status, 200)
                self.assertTrue(response.headers["Content-Type"].startswith(content_type))
                self.assertIn("filename=", response.headers["Content-Disposition"])
                self.assertTrue(body.startswith(prefix))

    def test_list_get_and_restart_preserve_identical_export(self) -> None:
        _, export = self.create_export(self.create_report())
        _, listing = self.request_json("/api/report-exports")
        _, fetched = self.request_json("/api/report-exports/" + export["export_id"])
        self.assertEqual((listing["export_count"], fetched["event_hash"]), (1, export["event_hash"]))
        self.server.report_export_journal = runtime.kernel.ReportExportJournal(
            self.server.report_export_journal.path, self.server.report_export_journal.bundle_root
        )
        _, restarted = self.request_json("/api/report-exports/" + export["export_id"])
        self.assertEqual(restarted["event_hash"], export["event_hash"])

    def test_unknown_report_export_and_file_fail_closed(self) -> None:
        status, error = self.request_json("/api/report-exports/EXPORT-NOT-FOUND")
        self.assertEqual((status, error["code"]), (404, "EXPORT_NOT_FOUND"))
        status, error = self.request_json("/api/report-exports/EXPORT-NOT-FOUND/pdf")
        self.assertEqual((status, error["code"]), (404, "EXPORT_NOT_FOUND"))

    def test_export_endpoint_never_exposes_approval_or_publication(self) -> None:
        _, export = self.create_export(self.create_report())
        self.assertFalse(export["approval_or_publication_performed"])
        self.assertFalse(export["formal_business_report"])
        self.assertEqual(export["raw_access_count"], 0)


if __name__ == "__main__":
    unittest.main()
