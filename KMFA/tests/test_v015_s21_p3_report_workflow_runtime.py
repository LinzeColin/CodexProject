from __future__ import annotations

import json
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from KMFA.tools import run_v015_s21_p3_report_workflow as runtime


class ReportWorkflowRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.server, self.thread, self.base_url = runtime.start_server(
            event_path=root / "base.jsonl", data_root=root / "data-update",
            confirmation_event_path=root / "confirmation.jsonl", publication_event_path=root / "publication.jsonl",
            report_model_event_path=root / "models.jsonl", export_event_path=root / "exports.jsonl",
            export_bundle_root=root / "bundles", workflow_event_path=root / "workflows.jsonl",
        )
        self.report = self.server.report_model_journal.create(
            company_id="demo-north", period_kind="MONTHLY", period_key="2026-07",
            source_bindings=runtime.base_runtime.base_runtime.kernel.default_source_bindings(),
            formula_bindings=runtime.base_runtime.base_runtime.kernel.default_formula_bindings(),
            created_by="运行时测试负责人", idempotency_key="runtime-s21p3-model-001",
        )
        self.export = self.server.report_export_journal.create(
            self.report, idempotency_key="runtime-s21p3-export-001"
        )

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temporary.cleanup()

    def request_json(self, path: str, body=None, headers=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request_headers = dict(headers or {})
        if data:
            request_headers["Content-Type"] = "application/json"
        request = urllib.request.Request(self.base_url + path, data=data, headers=request_headers)
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as error:
            return error.code, json.load(error)

    def preview(self):
        status, value = self.request_json("/api/report-workflows/preview", {
            "report_version_id": self.report["report_version_id"], "export_id": self.export["export_id"],
            "user_id": "demo-owner", "role_id": "finance", "company_id": "demo-north",
            "comment_zh": "已核对报告文件和来源", "idempotency_key": "runtime-s21p3-preview-001",
        })
        self.assertEqual(status, 201)
        return value

    def action(self, case_id, name, role, key, decision=None):
        body = {
            "user_id": "demo-owner", "role_id": role, "company_id": "demo-north",
            "comment_zh": "完成本步骤并记录处理意见", "idempotency_key": key,
        }
        if decision:
            body["decision"] = decision
        return self.request_json(f"/api/report-workflows/{case_id}/{name}", body)

    def complete(self):
        case = self.preview()
        for name, role, key, decision in (
            ("submit", "finance", "runtime-s21p3-submit-001", None),
            ("review", "reviewer", "runtime-s21p3-review-001", "PASS"),
            ("approve", "reviewer", "runtime-s21p3-approve-001", None),
            ("publish", "management", "runtime-s21p3-publish-001", None),
        ):
            status, case = self.action(case["case_id"], name, role, key, decision)
            self.assertEqual(status, 200)
        return case

    def test_page_and_predecessor_link_are_available(self) -> None:
        with urllib.request.urlopen(self.base_url + "/report-workflow") as response:
            text = response.read().decode("utf-8")
        self.assertIn("看清变化，按角色复核", text)
        with urllib.request.urlopen(self.base_url + "/report-generation") as response:
            self.assertIn("报告工作流", response.read().decode("utf-8"))

    def test_options_expose_workflow_filters_and_keep_release_closed(self) -> None:
        status, value = self.request_json("/api/report-workflows/options")
        self.assertEqual(status, 200)
        self.assertEqual(value["workflow_actions"], ["PREVIEW", "SUBMIT", "REVIEW", "APPROVE", "PUBLISH"])
        self.assertEqual(len(value["report_center_filters"]), 6)
        self.assertFalse(value["public_share_links_allowed"])
        self.assertFalse(value["github_upload_in_scope"])

    def test_five_step_workflow_reaches_internal_publication(self) -> None:
        case = self.complete()
        self.assertEqual((case["state"], case["event_count"]), ("PUBLISHED_INTERNAL", 5))
        self.assertTrue(case["internal_report_center_published"])
        self.assertFalse(case["external_publication_performed"])

    def test_quality_gate_and_state_order_fail_closed(self) -> None:
        case = self.preview()
        status, error = self.action(case["case_id"], "publish", "management", "runtime-s21p3-early-publish", None)
        self.assertEqual((status, error["code"]), (409, "WORKFLOW_STATE_INVALID"))
        status, error = self.request_json("/api/report-workflows/preview", {
            "report_version_id": self.report["report_version_id"], "export_id": "EXPORT-NOT-FOUND",
            "user_id": "demo-owner", "role_id": "finance", "company_id": "demo-north",
            "comment_zh": "错误预览", "idempotency_key": "runtime-s21p3-missing-export",
        })
        self.assertEqual((status, error["code"]), (404, "EXPORT_NOT_FOUND"))

    def test_revision_endpoint_preserves_old_version_and_returns_comparison(self) -> None:
        status, value = self.request_json("/api/report-revisions", {
            "base_report_version_id": self.report["report_version_id"],
            "source_version_updates": {"key_matters": "S20P2-CONFIRMATIONS-2026-07-V2"},
            "revision_reason_zh": "补充重点事项复核结果和负责人意见",
            "created_by": "运行时测试负责人", "idempotency_key": "runtime-s21p3-revision-001",
        })
        self.assertEqual(status, 201)
        self.assertEqual(value["report"]["version_number"], 2)
        self.assertEqual(value["comparison"]["unexplained_difference_count"], 0)
        self.assertTrue(value["comparison"]["publication_allowed"])
        self.assertEqual(self.server.report_model_journal.get(self.report["report_version_id"])["event_hash"], self.report["event_hash"])

    def test_comparison_endpoint_requires_correct_version_order(self) -> None:
        status, value = self.request_json("/api/report-revisions", {
            "base_report_version_id": self.report["report_version_id"],
            "source_version_updates": {"key_matters": "S20P2-CONFIRMATIONS-2026-07-V2"},
            "revision_reason_zh": "补充重点事项复核结果和负责人意见",
            "created_by": "运行时测试负责人", "idempotency_key": "runtime-s21p3-revision-002",
        })
        self.assertEqual(status, 201)
        revised = value["report"]
        status, comparison = self.request_json(
            f"/api/report-comparisons?from={self.report['report_version_id']}&to={revised['report_version_id']}"
        )
        self.assertEqual((status, comparison["direct_revision"]), (200, True))
        status, error = self.request_json(
            f"/api/report-comparisons?from={revised['report_version_id']}&to={self.report['report_version_id']}"
        )
        self.assertEqual((status, error["code"]), (409, "VERSION_ORDER_INVALID"))

    def test_report_center_filters_and_cross_company_access(self) -> None:
        self.complete()
        status, center = self.request_json(
            "/api/report-center?user_id=demo-owner&role_id=management&company_id=demo-north&status=PUBLISHED_INTERNAL"
        )
        self.assertEqual((status, center["result_count"], center["public_link_count"]), (200, 1, 0))
        status, error = self.request_json(
            "/api/report-center?user_id=demo-finance&role_id=finance&company_id=demo-south"
        )
        self.assertEqual((status, error["code"]), (403, "COMPANY_NOT_GRANTED"))

    def test_download_requires_identity_and_correct_role_state(self) -> None:
        url = f"/api/report-exports/{self.export['export_id']}/pdf"
        status, error = self.request_json(url)
        self.assertEqual(status, 403)
        status, error = self.request_json(url, headers={
            "X-KMFA-User": "demo-owner", "X-KMFA-Role": "management", "X-KMFA-Company": "demo-north",
        })
        self.assertEqual((status, error["code"]), (403, "REPORT_NOT_PUBLISHED"))
        self.complete()
        request = urllib.request.Request(self.base_url + url, headers={
            "X-KMFA-User": "demo-owner", "X-KMFA-Role": "management", "X-KMFA-Company": "demo-north",
        })
        with urllib.request.urlopen(request, timeout=15) as response:
            self.assertTrue(response.read().startswith(b"%PDF"))

    def test_tax_can_view_but_cannot_download(self) -> None:
        self.complete()
        status, center = self.request_json(
            "/api/report-center?user_id=demo-owner&role_id=tax&company_id=demo-north"
        )
        self.assertEqual((status, center["result_count"], center["reports"][0]["download_formats"]), (200, 1, []))
        status, error = self.request_json(
            f"/api/report-exports/{self.export['export_id']}/html",
            headers={"X-KMFA-User": "demo-owner", "X-KMFA-Role": "tax", "X-KMFA-Company": "demo-north"},
        )
        self.assertEqual((status, error["code"]), (403, "ROLE_NOT_ALLOWED"))


if __name__ == "__main__":
    unittest.main()
