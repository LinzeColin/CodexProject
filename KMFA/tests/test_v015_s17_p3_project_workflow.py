from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from KMFA.tools import v015_s17_p3_project_workflow as workflow


class ProjectWorkflowTests(unittest.TestCase):
    def test_taskpack_contract_is_exact_and_public(self) -> None:
        value = workflow.source_contract()
        self.assertEqual(value["roadmap_phase_id"], "S17-P3")
        self.assertEqual(value["task_ids"], ["S17P3T01", "S17P3T02", "S17P3T03"])
        self.assertEqual(len(value["actions_zh"]), 3)
        self.assertEqual(len(value["acceptance_zh"]), 3)
        self.assertEqual(len(value["stop_conditions_zh"]), 3)
        self.assertEqual(value["data_classification"], "PUBLIC_SYNTHETIC")

    def test_candidates_show_basis_impact_and_low_confidence_fails_closed(self) -> None:
        item = workflow.unallocated_work_item()
        self.assertEqual(item["candidate_count"], 3)
        self.assertTrue(all(row["basis_zh"] for row in item["candidates"]))
        high = workflow.preview_unallocated_assignment(
            project_id="PUB-PROJ-001", candidate_id="CAND-S17P3-001"
        )
        low = workflow.preview_unallocated_assignment(
            project_id="PUB-PROJ-001", candidate_id="CAND-S17P3-003"
        )
        self.assertTrue(high["auto_allocation_allowed"])
        self.assertEqual(high["impact"]["portfolio_cost_difference_cents"], 0)
        with self.assertRaisesRegex(workflow.ProjectWorkflowError, "低置信"):
            workflow.assert_auto_allocation_allowed(low)

    def test_assignment_is_persisted_idempotent_and_reversible(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            journal = workflow.EventJournal(Path(directory) / "events.jsonl")
            result = workflow.confirm_unallocated_assignment(
                journal,
                project_id="PUB-PROJ-001",
                candidate_id="CAND-S17P3-001",
                actor_ref="test-owner",
                reason_zh="已核对候选依据和金额影响后确认",
                idempotency_key="test-assignment-001",
                event_time="2026-07-16T10:00:00+10:00",
            )
            repeated = workflow.confirm_unallocated_assignment(
                journal,
                project_id="PUB-PROJ-001",
                candidate_id="CAND-S17P3-001",
                actor_ref="test-owner",
                reason_zh="已核对候选依据和金额影响后确认",
                idempotency_key="test-assignment-001",
                event_time="2026-07-16T10:00:00+10:00",
            )
            self.assertEqual(result["event"]["event_id"], repeated["event"]["event_id"])
            self.assertEqual(len(journal.read()), 1)
            self.assertEqual(result["projection"]["cost"]["unallocated"]["amount_cents"], 0)
            reversed_result = workflow.reverse_processing_event(
                journal,
                event_id=result["event"]["event_id"],
                actor_ref="test-owner",
                reason_zh="复核后撤销并恢复处理前投影",
                idempotency_key="test-reversal-001",
                event_time="2026-07-16T10:01:00+10:00",
            )
            self.assertEqual(reversed_result["projection"]["cost"]["unallocated"]["amount_cents"], 5_070_388)
            self.assertEqual(len(workflow.EventJournal(journal.path).read()), 2)

    def test_event_tamper_is_rejected(self) -> None:
        rows = workflow.canonical_demo_events()
        rows[0]["reason_zh"] = "被改写"
        with self.assertRaisesRegex(workflow.ProjectWorkflowError, "内容校验失败"):
            workflow.validate_event_chain(rows)

    def test_variance_compares_sources_previews_impact_and_reruns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            journal = workflow.EventJournal(Path(directory) / "events.jsonl")
            preview = workflow.preview_variance_resolution(
                project_id="PUB-PROJ-001", option_id="USE_SETTLEMENT_SUPPORT"
            )
            self.assertEqual(len(preview["source_comparison"]), 2)
            self.assertTrue(preview["impact_preview_passed"])
            self.assertLess(preview["impact"]["cost_after_cents"], preview["impact"]["cost_before_cents"])
            result = workflow.confirm_variance_resolution(
                journal,
                project_id="PUB-PROJ-001",
                option_id="USE_SETTLEMENT_SUPPORT",
                actor_ref="test-owner",
                reason_zh="已并排核对来源后采用已确认结算口径",
                idempotency_key="test-variance-001",
                event_time="2026-07-16T10:02:00+10:00",
            )
            self.assertEqual(len(journal.read()), 2)
            self.assertEqual(result["projection"]["workflow_projection"]["report_sync_status"], "PASS")
            self.assertEqual(
                result["rerun_event"]["payload"]["projection_fingerprint"],
                result["projection"]["workflow_projection"]["projection_fingerprint"],
            )

    def test_projection_and_report_are_zero_difference(self) -> None:
        snapshot = workflow.workflow_snapshot(events=workflow.canonical_demo_events())
        projection = snapshot["projection"]
        report = workflow.project_cost_report(snapshot)
        self.assertEqual(projection["workflow_projection"]["money_difference_cents"], 0)
        self.assertEqual(projection["cost"]["engine_difference_cents"], 0)
        self.assertEqual(report["checks"]["page_golden_difference_cents"], 0)
        self.assertEqual(report["checks"]["category_page_difference_cents"], 0)
        self.assertEqual(report["checks"]["money_tolerance_cents"], 0)
        self.assertEqual(report["checks"]["report_sync_status"], "PASS")

    def test_report_has_three_formats_and_four_evidence_groups(self) -> None:
        report = workflow.canonical_report()
        self.assertEqual(report["format_contract"]["format_count"], 3)
        self.assertEqual(set(report["evidence_index"]), {
            "source_facts",
            "processing_event_refs",
            "calculation_refs",
            "report_refs",
        })
        self.assertIn("项目成本专题报告", workflow.render_report_html(report))
        self.assertIn("允许差异 0 分", workflow.render_report_html(report))

    def test_snapshot_never_writes_or_reads_private_sources(self) -> None:
        value = workflow.workflow_snapshot(events=workflow.canonical_demo_events())
        self.assertEqual(value["source_data_write_count"], 0)
        self.assertEqual(value["fact_layer_write_count"], 0)
        self.assertEqual(value["raw_root_access_count"], 0)
        self.assertEqual(value["external_network_request_count"], 0)
        self.assertFalse(value["github_upload_performed"])
        self.assertFalse(value["app_reinstall_performed"])
        self.assertNotIn("/Users/", json.dumps(value, ensure_ascii=False))

    def test_public_checks_pass(self) -> None:
        rows = workflow.public_checks()
        self.assertEqual(len(rows), 69)
        self.assertTrue(all(row["passed"] for row in rows))


if __name__ == "__main__":
    unittest.main()
