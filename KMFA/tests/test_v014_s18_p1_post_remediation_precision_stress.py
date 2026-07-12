from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


GENERATOR_MODULE = "KMFA.tools.v014_s18_p1_post_remediation_precision_stress"
CHECKER_MODULE = "KMFA.tools.check_v014_s18_p1_post_remediation_precision_stress"
IMPLEMENTATION_EXISTS = importlib.util.find_spec(GENERATOR_MODULE) is not None and importlib.util.find_spec(CHECKER_MODULE) is not None


class V014S18P1PostRemediationPrecisionStressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not IMPLEMENTATION_EXISTS:
            return
        from KMFA.tools import v014_s18_p1_post_remediation_precision_stress as phase
        from KMFA.tools.check_v014_s18_p1_post_remediation_precision_stress import (
            validate_v014_s18_p1_post_remediation_precision_stress,
        )

        cls.phase = phase
        cls.manifest = validate_v014_s18_p1_post_remediation_precision_stress(
            require_private_evidence=True,
            require_final_evidence=True,
        )
        cls.summary = cls.manifest["summary"]
        cls.scenarios = phase._read_jsonl(phase.SCENARIO_RESULTS_PATH)
        cls.import_runs = phase._read_jsonl(phase.IMPORT_RUN_RESULTS_PATH)
        cls.error_reports = phase._read_jsonl(phase.ERROR_REPORTS_PATH)

    def test_implementation_exists(self) -> None:
        self.assertTrue(IMPLEMENTATION_EXISTS, "current S18-P1 generator/checker not written yet")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_current_stage17_dependency_and_historical_s18_are_quarantined(self) -> None:
        dependency = self.manifest["stage17_review_dependency"]
        self.assertEqual(dependency["phase_id"], "V014_S17_POST_REMEDIATION_STAGE_REVIEW")
        self.assertTrue(dependency["validated"])
        self.assertTrue(self.manifest["historical_s18_p1_structural_baseline_validated"])
        self.assertFalse(self.manifest["historical_s18_p1_dynamic_state_authoritative"])
        self.assertEqual(self.manifest["taskpack_contract"]["roadmap_phase_id"], "S18-P1")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_amount_precision_and_rejections_execute_real_tools(self) -> None:
        self.assertEqual(self.summary["amount_case_count"], 9)
        self.assertEqual(self.summary["amount_case_pass_count"], 9)
        self.assertEqual(self.summary["amount_rejection_case_count"], 9)
        self.assertEqual(self.summary["amount_rejection_pass_count"], 9)
        self.assertTrue(self.summary["repository_no_float_scan_passed"])
        scenario = next(row for row in self.scenarios if row["scenario_type"] == "amount_precision")
        self.assertEqual(scenario["minimum_fail_difference_cents"], 1)
        self.assertTrue(scenario["float_money_rejected"])
        self.assertTrue(scenario["fractional_cent_rejected"])

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_zero_delta_exact_passes_and_one_cent_mismatch_blocks(self) -> None:
        self.assertTrue(self.summary["zero_delta_exact_passed"])
        self.assertTrue(self.summary["one_cent_mismatch_rejected"])
        self.assertEqual(self.summary["one_cent_mismatch_count"], 1)
        scenario = next(row for row in self.scenarios if row["scenario_type"] == "zero_delta")
        self.assertEqual(scenario["minimum_fail_difference_cents"], 1)
        self.assertTrue(scenario["difference_queue_required"])
        self.assertTrue(scenario["report_grade_upgrade_blocked"])

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_three_imports_are_idempotent_and_final_state_is_identical(self) -> None:
        self.assertEqual([row["run_sequence"] for row in self.import_runs], [1, 2, 3])
        self.assertEqual(len({row["final_state_hash"] for row in self.import_runs}), 1)
        self.assertEqual(self.import_runs[0]["inserted_record_count"], 1198)
        self.assertEqual(self.import_runs[0]["duplicate_record_count"], 0)
        self.assertEqual([row["inserted_record_count"] for row in self.import_runs[1:]], [0, 0])
        self.assertEqual([row["duplicate_record_count"] for row in self.import_runs[1:]], [1198, 1198])
        self.assertTrue(all(row["blocking_error_count"] == 2 for row in self.import_runs))

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_actual_large_batch_performance_and_errors_are_locked(self) -> None:
        self.assertEqual(self.summary["synthetic_batch_item_count"], 1200)
        self.assertEqual(self.summary["valid_synthetic_record_count"], 1198)
        self.assertEqual(self.summary["blocking_error_report_count"], 2)
        self.assertLessEqual(
            self.summary["max_elapsed_ms"],
            self.summary["performance_budget_ms"],
        )
        self.assertEqual({row["error_type"] for row in self.error_reports}, {"bad_file", "missing_field"})
        self.assertTrue(all(row["severity"] == "blocking" for row in self.error_reports))
        self.assertTrue(all(row["raw_payload_committed"] is False for row in self.error_reports))

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_suite_tampering_is_rejected(self) -> None:
        suite = self.phase.run_precision_stress_suite()
        bad_hash = copy.deepcopy(suite)
        bad_hash["import_runs"][2]["final_state_hash"] = "sha256:" + "0" * 64
        with self.assertRaises(ValueError):
            self.phase.validate_precision_stress_suite(bad_hash)

        bad_performance = copy.deepcopy(suite)
        bad_performance["summary"]["max_elapsed_ms"] = bad_performance["summary"]["performance_budget_ms"] + 1
        with self.assertRaises(ValueError):
            self.phase.validate_precision_stress_suite(bad_performance)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_public_metadata_mirrors_are_exact_and_public_safe(self) -> None:
        self.assertEqual(self.phase._read_json(self.phase.METADATA_MANIFEST_PATH), self.manifest)
        self.assertEqual(self.phase._read_jsonl(self.phase.METADATA_SCENARIOS_PATH), self.scenarios)
        self.assertEqual(self.phase._read_jsonl(self.phase.METADATA_IMPORT_RUNS_PATH), self.import_runs)
        self.assertEqual(self.phase._read_jsonl(self.phase.METADATA_ERROR_REPORTS_PATH), self.error_reports)
        payload = json.dumps([self.manifest, self.scenarios, self.import_runs, self.error_reports], ensure_ascii=False)
        for token in self.phase.FORBIDDEN_PUBLIC_TEXT:
            self.assertNotIn(token, payload)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_raw_snapshot_and_all_downstream_boundaries_are_locked(self) -> None:
        self.assertEqual(self.summary["raw_source_file_count"], 5)
        self.assertTrue(self.summary["raw_snapshot_exact_match"])
        self.assertTrue(self.summary["raw_cross_phase_snapshot_exact_match"])
        self.assertEqual(self.summary["current_data_quality_grade"], "Q4")
        self.assertEqual(self.summary["current_report_grade"], "D")
        self.assertEqual(self.summary["decision"], "NO_GO")
        boundaries = self.manifest["phase_boundaries"]
        true_keys = {
            "stage17_post_remediation_review_dependency_reused",
            "historical_s18_p1_structural_baseline_reused",
            "s18_p1_precision_stress_performed",
            "actual_synthetic_stress_execution_performed",
            "private_raw_snapshot_validation_performed",
        }
        for key, value in boundaries.items():
            self.assertEqual(value, key in true_keys, key)

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
        for path in (
            self.phase.DEVELOPMENT_EVENTS_PATH,
            self.phase.STAGE_STATUS_PATH,
            self.phase.TASK_STATUS_PATH,
        ):
            rows = self.phase._read_jsonl(path)
            self.assertEqual(sum(row.get("phase_id") == self.phase.PHASE_ID for row in rows), 1)
            self.assertEqual(sum(row.get("phase_id") == self.phase.s17_review.PHASE_ID for row in rows), 1)
        if f'current_phase: "{self.phase.PHASE_ID}"' in version_matrix:
            self.assertIn("下一步只能执行 S18-P2", handoff)
            self.assertIn("不得执行 S18-P3", handoff)
            self.assertIn("不得执行 Stage 18 整体复审", handoff)
            self.assertIn("不得执行 GitHub upload", handoff)


if __name__ == "__main__":
    unittest.main()
