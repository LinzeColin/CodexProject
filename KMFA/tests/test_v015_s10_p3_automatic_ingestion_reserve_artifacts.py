from __future__ import annotations

import json
import unittest

from KMFA.tools import build_v015_s10_p3_automatic_ingestion_reserve as builder


class AutomaticIngestionReserveArtifactTests(unittest.TestCase):
    def test_s10_p2_dependency_is_exact(self) -> None:
        dependency = builder.dependency()
        self.assertEqual(dependency["acceptance_status"], "PASSED")
        self.assertEqual(dependency["validation_receipt_count"], 19)
        self.assertEqual(dependency["final_evidence_commit"], builder.PHASE_BASE_COMMIT)
        self.assertTrue(dependency["s10_p3_entry_allowed"])
        self.assertFalse(dependency["s10_p3_started"])

    def test_outputs_are_deterministic(self) -> None:
        builder.check_outputs()

    def test_connector_contract_is_read_only_and_credential_safe(self) -> None:
        contract = json.loads(builder.CONNECTOR_CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(contract["source_count"], 5)
        self.assertEqual(len(contract["operations"]), 6)
        self.assertTrue(contract["official_authorization_required"])
        self.assertTrue(contract["read_only_scope_required"])
        self.assertFalse(contract["plaintext_credential_storage_allowed"])
        self.assertFalse(contract["source_writeback_allowed"])
        self.assertEqual(contract["live_connector_call_count"], 0)

    def test_schedule_is_bounded_and_manual_import_survives(self) -> None:
        policy = json.loads(builder.SCHEDULE_POLICY_PATH.read_text(encoding="utf-8"))
        verification = json.loads(builder.SCHEDULE_VERIFICATION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(set(policy["frequency_types"]), {"DAILY", "WEEKLY", "MONTHLY"})
        self.assertEqual(policy["retry_budget"], 3)
        self.assertEqual(policy["no_data_retry_count"], 0)
        self.assertTrue(verification["manual_import_available"])
        self.assertFalse(verification["scheduled_failure_blocks_manual_import"])

    def test_activation_gates_are_independent_and_closed(self) -> None:
        matrix = json.loads(builder.ACTIVATION_MATRIX_PATH.read_text(encoding="utf-8"))
        self.assertEqual(matrix["source_gate_count"], 5)
        self.assertEqual(matrix["criterion_count_per_source"], 8)
        self.assertTrue(matrix["independent_source_acceptance_required"])
        self.assertTrue(matrix["security_review_required_before_enable"])
        self.assertEqual(matrix["automatic_connector_enabled_count"], 0)

    def test_manifest_and_task_matrix_move_together(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        tasks = json.loads(builder.TASK_MATRIX_PATH.read_text(encoding="utf-8"))
        accepted = manifest["phase_acceptance_status"] == "PASSED"
        self.assertEqual(tasks["phase_acceptance_status"], manifest["phase_acceptance_status"])
        self.assertEqual(tasks["task_accepted_count"], 3 if accepted else 0)
        self.assertEqual(manifest["overall_accepted_phase_count"], 28 if accepted else 27)
        self.assertEqual(manifest["stage_execution_percentage"], 100)
        self.assertEqual(manifest["s10_stage_review_entry_allowed"], accepted)
        self.assertFalse(manifest["s10_stage_review_started"])

    def test_human_files_are_plain_chinese_and_scope_honest(self) -> None:
        implementation = builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8")
        flow = builder.CONNECTOR_FLOW_PATH.read_text(encoding="utf-8")
        schedule = builder.SCHEDULE_FRESHNESS_PATH.read_text(encoding="utf-8")
        for token in ("没有连接任何真实平台", "不会无限重试", "必须逐个通过安全评审", "当前自动连接数量为 0"):
            self.assertIn(token, implementation)
        self.assertIn("撤销后立即停止", flow)
        self.assertIn("仍可手工导入", implementation)
        self.assertIn("没有新数据时不重试", schedule)


if __name__ == "__main__":
    unittest.main()
