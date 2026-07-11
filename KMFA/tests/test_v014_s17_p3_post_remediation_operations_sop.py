#!/usr/bin/env python3
"""Behavior tests for current KMFA v0.1.4 S17-P3 operations SOP."""

from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path


GENERATOR_PATH = Path("KMFA/tools/v014_s17_p3_post_remediation_operations_sop.py")
CHECKER_PATH = Path("KMFA/tools/check_v014_s17_p3_post_remediation_operations_sop.py")
IMPLEMENTATION_EXISTS = GENERATOR_PATH.is_file() and CHECKER_PATH.is_file()


class V014S17P3PostRemediationOperationsSopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not IMPLEMENTATION_EXISTS:
            return
        from KMFA.tools import v014_s17_p3_post_remediation_operations_sop as phase
        from KMFA.tools.check_v014_s17_p3_post_remediation_operations_sop import (
            validate_v014_s17_p3_post_remediation_operations_sop,
        )

        cls.phase = phase
        cls.manifest = validate_v014_s17_p3_post_remediation_operations_sop(
            require_private_evidence=True,
            require_final_evidence=True,
        )
        cls.summary = json.loads(phase.SUMMARY_PATH.read_text(encoding="utf-8"))
        cls.runbooks = cls._read_jsonl(phase.RUNBOOK_PATH)
        cls.knowledge = cls._read_jsonl(phase.KNOWLEDGE_INDEX_PATH)
        cls.error_drills = cls._read_jsonl(phase.ERROR_DRILL_PATH)
        cls.backup_drills = cls._read_jsonl(phase.BACKUP_DRILL_PATH)

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, object]]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_implementation_exists(self) -> None:
        self.assertTrue(GENERATOR_PATH.is_file(), f"missing generator: {GENERATOR_PATH}")
        self.assertTrue(CHECKER_PATH.is_file(), f"missing checker: {CHECKER_PATH}")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_identity_dependencies_and_historical_quarantine(self) -> None:
        self.assertEqual(self.manifest["phase_id"], self.phase.PHASE_ID)
        self.assertEqual(self.manifest["roadmap_phase_id"], "S17-P3")
        self.assertEqual(self.manifest["task_id"], self.phase.TASK_ID)
        self.assertEqual(self.manifest["acceptance_id"], self.phase.ACCEPTANCE_ID)
        self.assertTrue(self.manifest["current_s17_p2_validated"])
        self.assertTrue(self.manifest["historical_s17_p3_validated"])
        self.assertFalse(self.manifest["historical_s17_p3_dynamic_state_is_authoritative"])
        self.assertEqual(self.manifest["next_phase"], "S17_STAGE_REVIEW")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_four_manual_runbooks_are_complete_and_fail_closed(self) -> None:
        self.assertEqual(len(self.runbooks), 4)
        self.assertEqual({row["runbook_type"] for row in self.runbooks}, set(self.phase.REQUIRED_RUNBOOK_TYPES))
        for row in self.runbooks:
            self.assertEqual(row["execution_mode"], "manual_sop_only")
            self.assertEqual(len(row["steps_zh"]), 5)
            self.assertTrue(row["precheck_required"])
            self.assertTrue(row["evidence_required"])
            self.assertTrue(row["rollback_required"])
            self.assertFalse(row["raw_mutation_allowed"])
            self.assertFalse(row["external_service_allowed"])
            self.assertFalse(row["business_execution_allowed"])
            self.assertFalse(row["formal_report_release_allowed"])
        self.assertEqual({row["owner_role"] for row in self.runbooks}, {"management", "finance", "reviewer"})
        self.assertEqual(
            {row["audit_action_type"] for row in self.runbooks},
            {"import", "processing", "report"},
        )
        self.assertTrue(all(len(row["audit_required_fields"]) == 7 for row in self.runbooks))

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_finance_sop_and_handoff_are_index_only(self) -> None:
        self.assertEqual(len(self.knowledge), 2)
        self.assertEqual({row["item_type"] for row in self.knowledge}, set(self.phase.REQUIRED_KNOWLEDGE_TYPES))
        for row in self.knowledge:
            self.assertEqual(row["storage_mode"], "public_safe_knowledge_index_only")
            self.assertEqual(row["execution_mode"], "knowledge_and_checklist_only")
            self.assertEqual(len(row["checklist_zh"]), 6)
            self.assertFalse(row["automated_finance_execution_allowed"])
            self.assertFalse(row["private_document_committed"])
            self.assertFalse(row["raw_business_data_committed"])
        self.assertEqual({row["owner_role"] for row in self.knowledge}, {"finance", "reviewer"})

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_error_handling_drill_rejects_both_invalid_candidates(self) -> None:
        self.assertEqual(len(self.error_drills), 1)
        row = self.error_drills[0]
        self.assertEqual(row["execution_mode"], "isolated_synthetic_runtime_drill")
        self.assertEqual(row["scenario_count"], 2)
        self.assertEqual(row["rejected_candidate_count"], 2)
        self.assertEqual(row["unexpected_accept_count"], 0)
        self.assertEqual(row["result_status"], "PASS")
        self.assertFalse(row["raw_source_used"])
        self.assertFalse(row["business_execution_performed"])

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_import_candidate_tampering_is_rejected(self) -> None:
        base = {
            "schema_version": self.phase.SYNTHETIC_SCHEMA_VERSION,
            "record_type": "synthetic_operation_fixture",
            "operation_ref": "S17P3-SYNTHETIC",
            "public_safe": True,
        }
        self.assertTrue(self.phase.validate_import_candidate(base)["valid"])
        cases = (
            ("schema_version", "wrong", "schema_version_invalid"),
            ("record_type", "wrong", "record_type_invalid"),
            ("operation_ref", "", "operation_ref_required"),
            ("public_safe", False, "public_safe_required"),
            ("raw_payload_present", True, "raw_payload_forbidden"),
        )
        for key, value, reason in cases:
            with self.subTest(key=key):
                candidate = deepcopy(base)
                candidate[key] = value
                result = self.phase.validate_import_candidate(candidate)
                self.assertFalse(result["valid"])
                self.assertIn(reason, result["errors"])

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_backup_restore_drill_is_byte_exact_and_private(self) -> None:
        self.assertEqual(len(self.backup_drills), 1)
        row = self.backup_drills[0]
        self.assertEqual(row["execution_mode"], "isolated_synthetic_runtime_drill")
        self.assertEqual(row["synthetic_fixture_count"], 1)
        self.assertEqual(row["backup_created_count"], 1)
        self.assertEqual(row["corruption_detected_count"], 1)
        self.assertEqual(row["restore_completed_count"], 1)
        self.assertTrue(row["restored_byte_exact"])
        self.assertEqual(row["result_status"], "PASS")
        self.assertFalse(row["production_restore_performed"])
        self.assertFalse(row["raw_source_used"])

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_public_metadata_mirrors_are_exact(self) -> None:
        self.assertEqual(self.runbooks, self._read_jsonl(self.phase.METADATA_RUNBOOK_PATH))
        self.assertEqual(self.knowledge, self._read_jsonl(self.phase.METADATA_KNOWLEDGE_INDEX_PATH))
        self.assertEqual(self.error_drills, self._read_jsonl(self.phase.METADATA_ERROR_DRILL_PATH))
        self.assertEqual(self.backup_drills, self._read_jsonl(self.phase.METADATA_BACKUP_DRILL_PATH))

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_raw_snapshots_remain_exact(self) -> None:
        self.assertEqual(self.summary["raw_source_file_count"], 5)
        self.assertTrue(self.summary["raw_snapshot_exact_match"])
        self.assertTrue(self.summary["raw_cross_phase_snapshot_exact_match"])
        boundary = self.manifest["raw_boundary"]
        self.assertTrue(boundary["raw_snapshot_read_performed"])
        for key, value in boundary.items():
            if key != "raw_snapshot_read_performed":
                self.assertFalse(value, key)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_quality_and_all_downstream_actions_remain_closed(self) -> None:
        self.assertEqual(self.summary["current_data_quality_grade"], "Q4")
        self.assertEqual(self.summary["current_report_grade"], "D")
        self.assertEqual(self.summary["decision"], "NO_GO")
        self.assertEqual(
            (
                self.summary["open_final_difference_accepted_count"],
                self.summary["nonzero_delta_reconciliation_count"],
                self.summary["zero_delta_reconciliation_count"],
                self.summary["incomplete_reconciliation_count"],
            ),
            (3, 9, 2, 1),
        )
        for key, value in self.phase._phase_boundaries().items():
            if key in {
                "s17_p1_performed",
                "s17_p2_performed",
                "s17_p3_performed",
                "private_synthetic_drill_performed",
            }:
                self.assertTrue(value, key)
            else:
                self.assertFalse(value, key)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_governance_and_next_run_boundary_are_locked(self) -> None:
        formula = Path("KMFA/docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        parameters = Path("KMFA/docs/governance/parameter_registry.csv").read_text(encoding="utf-8")
        version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn(self.phase.FORMULA_ID, formula)
        for parameter_id in self.phase.PARAMETER_IDS:
            self.assertIn(parameter_id, parameters)
        self.assertIn(self.phase.MODEL_REGISTRY_KEY, version_matrix)
        self.assertIn(self.phase.VERSION, version_matrix)
        if f'current_phase: "{self.phase.PHASE_ID}"' in version_matrix:
            self.assertIn("下一步只能执行 Stage 17 整体复审", handoff)
            self.assertIn("不得执行 Stage 18", handoff)
            self.assertIn("不得执行 GitHub upload", handoff)


if __name__ == "__main__":
    unittest.main()
