from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools import v015_s21_p1_report_model as report_model
from KMFA.tools import v015_s21_p2_report_generation as report_generation
from KMFA.tools import v015_s21_p3_report_workflow as workflow


class ReportWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.models = report_model.ReportModelJournal(root / "models.jsonl")
        self.exports = report_generation.ReportExportJournal(root / "exports.jsonl", root / "bundles")
        self.workflows = workflow.ReportWorkflowJournal(root / "workflows.jsonl")
        self.report = self.models.create(
            company_id="demo-north", period_kind="MONTHLY", period_key="2026-07",
            source_bindings=report_model.default_source_bindings(),
            formula_bindings=report_model.default_formula_bindings(), created_by="测试负责人",
            idempotency_key="unit-s21p3-model-001", recorded_at="2026-07-17T00:00:00+00:00",
        )
        self.export = self.exports.create(
            self.report, idempotency_key="unit-s21p3-export-001", recorded_at="2026-07-17T00:01:00+00:00"
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def preview(self):
        return self.workflows.preview(
            self.report, self.export, user_id="demo-owner", role_id="finance", company_id="demo-north",
            comment_zh="已核对三种报告文件", idempotency_key="unit-s21p3-preview-001",
            occurred_at="2026-07-17T00:02:00+00:00",
        )

    def complete(self):
        case = self.preview()
        case = self.workflows.submit(
            case["case_id"], user_id="demo-owner", role_id="finance", company_id="demo-north",
            comment_zh="提交报告复核", idempotency_key="unit-s21p3-submit-001",
        )
        case = self.workflows.review(
            case["case_id"], user_id="demo-owner", role_id="reviewer", company_id="demo-north",
            comment_zh="数字来源和限制说明完整", decision="PASS", idempotency_key="unit-s21p3-review-001",
        )
        case = self.workflows.approve(
            case["case_id"], user_id="demo-owner", role_id="reviewer", company_id="demo-north",
            comment_zh="批准内部发布", idempotency_key="unit-s21p3-approve-001",
        )
        return self.workflows.publish(
            case["case_id"], user_id="demo-owner", role_id="management", company_id="demo-north",
            comment_zh="发布到内部报告中心", idempotency_key="unit-s21p3-publish-001",
        )

    def test_quality_gate_binds_report_export_and_exact_values(self) -> None:
        gate = workflow.quality_gate(self.report, self.export)
        self.assertEqual((gate["status"], gate["check_count"], gate["failed_count"]), ("PASS", 15, 0))
        self.assertTrue(gate["quality_fingerprint"].startswith("sha256:"))

    def test_tampered_export_fails_quality_gate(self) -> None:
        export = json.loads(json.dumps(self.export))
        export["cross_format_consistency"]["difference_integer"] = 1
        gate = workflow.quality_gate(self.report, export)
        self.assertEqual((gate["status"], gate["failed_count"]), ("FAIL", 1))
        with self.assertRaisesRegex(workflow.ReportWorkflowError, "质量门禁"):
            self.workflows.preview(
                self.report, export, user_id="demo-owner", role_id="finance", company_id="demo-north",
                comment_zh="尝试预览错误文件", idempotency_key="unit-s21p3-bad-preview",
            )

    def test_workflow_records_five_people_time_comment_steps(self) -> None:
        case = self.complete()
        self.assertEqual((case["state"], case["event_count"]), ("PUBLISHED_INTERNAL", 5))
        self.assertTrue(all(row["actor_user_id"] and row["actor_role"] and row["occurred_at"] and row["comment_zh"] for row in case["events"]))
        self.assertFalse(case["external_publication_performed"])
        self.assertIsNone(case["public_share_link"])

    def test_publish_before_review_and_wrong_role_fail_closed(self) -> None:
        case = self.preview()
        with self.assertRaisesRegex(workflow.ReportWorkflowError, "当前状态"):
            self.workflows.publish(
                case["case_id"], user_id="demo-owner", role_id="management", company_id="demo-north",
                comment_zh="跳过复核直接发布", idempotency_key="unit-s21p3-early-publish",
            )
        with self.assertRaisesRegex(workflow.ReportWorkflowError, "角色"):
            self.workflows.submit(
                case["case_id"], user_id="demo-owner", role_id="tax", company_id="demo-north",
                comment_zh="无权提交报告", idempotency_key="unit-s21p3-tax-submit",
            )

    def test_review_can_request_revision_and_blocks_approval(self) -> None:
        case = self.preview()
        case = self.workflows.submit(
            case["case_id"], user_id="demo-owner", role_id="finance", company_id="demo-north",
            comment_zh="提交报告复核", idempotency_key="unit-s21p3-submit-changes",
        )
        case = self.workflows.review(
            case["case_id"], user_id="demo-owner", role_id="reviewer", company_id="demo-north",
            comment_zh="重点事项来源需要更新", decision="REQUEST_CHANGES", idempotency_key="unit-s21p3-review-changes",
        )
        self.assertEqual(case["state"], "CHANGES_REQUESTED")
        with self.assertRaisesRegex(workflow.ReportWorkflowError, "当前状态"):
            self.workflows.approve(
                case["case_id"], user_id="demo-owner", role_id="reviewer", company_id="demo-north",
                comment_zh="错误批准", idempotency_key="unit-s21p3-bad-approve",
            )

    def test_idempotency_and_hash_chain_detect_tamper(self) -> None:
        case = self.complete()
        same = self.workflows.publish(
            case["case_id"], user_id="demo-owner", role_id="management", company_id="demo-north",
            comment_zh="发布到内部报告中心", idempotency_key="unit-s21p3-publish-001",
        )
        self.assertEqual(same["event_count"], 5)
        lines = self.workflows.path.read_text(encoding="utf-8").splitlines()
        value = json.loads(lines[0])
        value["comment_zh"] = "被篡改"
        lines[0] = json.dumps(value, ensure_ascii=False, sort_keys=True)
        self.workflows.path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(workflow.ReportWorkflowError, "完整性"):
            self.workflows.read()

    def test_revision_creates_new_version_and_explained_comparison(self) -> None:
        bindings = workflow.revision_bindings(self.report, {"key_matters": "S20P2-CONFIRMATIONS-2026-07-V2"})
        revised = self.models.revise(
            self.report["report_version_id"], source_bindings=bindings,
            revision_reason_zh="补充重点事项复核结果和负责人意见", created_by="测试负责人",
            idempotency_key="unit-s21p3-model-002",
        )
        result = workflow.compare_versions(self.report, revised)
        self.assertEqual((revised["version_number"], result["direct_revision"], result["unexplained_difference_count"]), (2, True, 0))
        self.assertGreaterEqual(result["source_difference_count"], 1)
        self.assertTrue(result["publication_allowed"])
        self.assertEqual(self.models.get(self.report["report_version_id"])["event_hash"], self.report["event_hash"])

    def test_revision_rejects_unknown_or_unchanged_source(self) -> None:
        with self.assertRaisesRegex(workflow.ReportWorkflowError, "未知"):
            workflow.revision_bindings(self.report, {"unknown": "V2"})
        current = next(row["version_ref"] for row in self.report["source_bindings"] if row["domain_id"] == "key_matters")
        with self.assertRaisesRegex(workflow.ReportWorkflowError, "相同"):
            workflow.revision_bindings(self.report, {"key_matters": current})

    def test_report_center_search_and_permissions(self) -> None:
        case = self.complete()
        center = workflow.report_center(
            [self.report], [self.export], [case],
            user_id="demo-owner", role_id="management", company_id="demo-north",
            period_kind="MONTHLY", status="PUBLISHED_INTERNAL",
        )
        self.assertEqual((center["result_count"], center["filter_count"], center["public_link_count"]), (1, 2, 0))
        self.assertEqual(set(center["reports"][0]["download_formats"]), workflow.FORMATS)
        tax = workflow.report_center(
            [self.report], [self.export], [case], user_id="demo-owner", role_id="tax", company_id="demo-north"
        )
        self.assertEqual(tax["reports"][0]["download_formats"], [])

    def test_cross_company_search_and_public_link_are_denied(self) -> None:
        with self.assertRaisesRegex(workflow.ReportWorkflowError, "没有查看"):
            workflow.report_center(
                [self.report], [self.export], [], user_id="demo-finance", role_id="finance", company_id="demo-south"
            )
        center = workflow.report_center(
            [self.report], [self.export], [], user_id="demo-owner", role_id="finance", company_id="demo-north"
        )
        self.assertFalse(center["reports"][0]["share_link_enabled"])
        self.assertIsNone(center["reports"][0]["public_url"])

    def test_phase_verification_has_fifty_three_real_checks(self) -> None:
        result = workflow.verify_phase()
        self.assertEqual((result["status"], result["public_check_count"], result["public_check_pass_count"], result["public_check_failed_count"]), ("PASS", 53, 53, 0))


if __name__ == "__main__":
    unittest.main()
