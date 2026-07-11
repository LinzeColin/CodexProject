from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


GENERATOR_MODULE = "KMFA.tools.v014_s18_post_remediation_stage_review"
CHECKER_MODULE = "KMFA.tools.check_v014_s18_post_remediation_stage_review"
IMPLEMENTATION_EXISTS = (
    importlib.util.find_spec(GENERATOR_MODULE) is not None
    and importlib.util.find_spec(CHECKER_MODULE) is not None
)


class V014S18PostRemediationStageReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not IMPLEMENTATION_EXISTS:
            return
        from KMFA.tools import v014_s18_post_remediation_stage_review as review
        from KMFA.tools.check_v014_s18_post_remediation_stage_review import (
            validate_v014_s18_post_remediation_stage_review,
        )

        cls.review = review
        cls.manifest = validate_v014_s18_post_remediation_stage_review(
            require_private_evidence=True,
            require_final_evidence=True,
        )
        cls.summary = review._read_json(review.SUMMARY_PATH)
        cls.phase_results = review._read_jsonl(review.PHASE_RESULTS_PATH)
        cls.contracts = review._read_jsonl(review.CONTRACT_MATRIX_PATH)
        cls.acceptance = review._read_json(review.ACCEPTANCE_MATRIX_PATH)
        cls.go_no_go = review._read_json(review.GO_NO_GO_PATH)

    def test_implementation_exists(self) -> None:
        self.assertTrue(IMPLEMENTATION_EXISTS, "current Stage 18 review generator/checker not written yet")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_identity_current_chain_and_historical_review_quarantine(self) -> None:
        self.assertEqual(self.manifest["phase_id"], self.review.PHASE_ID)
        self.assertEqual(self.manifest["roadmap_phase_id"], "STAGE-REVIEW")
        self.assertEqual(self.manifest["task_id"], self.review.TASK_ID)
        self.assertEqual(self.manifest["acceptance_id"], self.review.ACCEPTANCE_ID)
        self.assertEqual(self.manifest["decision"], "NO_GO")
        self.assertTrue(self.manifest["historical_stage18_review_structural_baseline_validated"])
        self.assertFalse(self.manifest["historical_stage18_review_dynamic_state_authoritative"])
        self.assertEqual(
            self.summary["phase_results"],
            {"S18-P1": "PASS", "S18-P2": "PASS", "S18-P3": "PASS"},
        )

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_all_phase_tests_and_strict_validators_are_replayed(self) -> None:
        self.assertEqual(len(self.phase_results), 3)
        self.assertEqual(sum(row["focused_test_count"] for row in self.phase_results), 30)
        self.assertTrue(all(row["focused_test_status"] == "PASS" for row in self.phase_results))
        self.assertTrue(all(row["strict_validator_status"] == "PASS" for row in self.phase_results))
        self.assertEqual(self.summary["phase_focused_test_pass_count"], 30)
        self.assertEqual(self.summary["phase_strict_validator_pass_count"], 3)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_cross_phase_contract_matrix_has_no_mismatch(self) -> None:
        self.assertGreaterEqual(len(self.contracts), 16)
        self.assertTrue(all(row["status"] == "PASS" for row in self.contracts))
        self.assertEqual(sum(row["mismatch_count"] for row in self.contracts), 0)
        self.assertEqual(self.summary["cross_phase_contract_mismatch_count"], 0)
        self.assertEqual(self.summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(self.summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(self.summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(self.summary["incomplete_reconciliation_count"], 1)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_review_findings_are_real_fixed_and_closed(self) -> None:
        findings = self.manifest["review_findings"]
        self.assertEqual(len(findings), 12)
        self.assertEqual(sum(row["status"] == "fixed" for row in findings), 3)
        self.assertEqual(sum(row["status"] == "passed" for row in findings), 9)
        self.assertEqual(sum(row["status"] == "open" for row in findings), 0)
        self.assertEqual(self.summary["fixed_review_finding_count"], 3)
        self.assertEqual(self.summary["open_review_finding_count"], 0)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_precision_regression_and_integration_stage_gate_is_exact(self) -> None:
        gate = self.manifest["stage_gate"]
        self.assertEqual(gate["precision_scenario_count"], 5)
        self.assertEqual(gate["consecutive_import_run_count"], 3)
        self.assertEqual(gate["synthetic_batch_item_count"], 1200)
        self.assertEqual(gate["blocking_error_report_count"], 2)
        self.assertEqual(gate["regression_check_category_count"], 5)
        self.assertEqual(gate["stage_evidence_count"], 18)
        self.assertEqual(gate["html_audit_pass_count"], 54)
        self.assertEqual(gate["html_audit_fail_count"], 0)
        self.assertFalse(gate["lineage_full_check_complete"])
        self.assertEqual(gate["connector_plan_count"], 3)
        self.assertEqual(gate["opme_entry_surface_count"], 4)
        self.assertEqual(gate["backlog_item_count"], 6)
        self.assertEqual(gate["live_connector_call_count"], 0)
        self.assertEqual(gate["source_mutation_allowed_count"], 0)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_raw_quality_and_current_no_go_are_fresh_and_locked(self) -> None:
        self.assertEqual(self.summary["raw_source_file_count"], 5)
        self.assertTrue(self.summary["raw_snapshot_exact_match"])
        self.assertTrue(self.summary["raw_cross_phase_snapshot_exact_match"])
        self.assertTrue(self.summary["fresh_raw_snapshot_validated"])
        self.assertEqual(self.summary["current_data_quality_grade"], "Q4")
        self.assertEqual(self.summary["current_report_grade"], "D")
        self.assertEqual(self.summary["decision"], "NO_GO")
        self.assertTrue(self.summary["stage18_review_performed"])
        self.assertFalse(self.summary["final_overall_review_performed"])

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_go_no_go_resolves_only_stage_review_and_keeps_delivery_closed(self) -> None:
        self.assertEqual(self.go_no_go["decision"], "NO_GO")
        self.assertNotIn("STAGE18_REVIEW_PENDING", self.go_no_go["blocker_ids"])
        for blocker in (
            "LINEAGE_FULL_CHECK_NOT_COMPLETE",
            "OPEN_RECONCILIATION_REMAINS",
            "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED",
            "FINAL_OVERALL_REVIEW_PENDING",
            "GITHUB_MAIN_UPLOAD_DEFERRED",
            "APP_REINSTALL_DEFERRED",
        ):
            self.assertIn(blocker, self.go_no_go["blocker_ids"])
        for key, value in self.go_no_go.items():
            if key.endswith("_allowed") or key.endswith("_performed"):
                if key == "stage18_review_performed":
                    self.assertTrue(value, key)
                else:
                    self.assertFalse(value, key)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_review_bundle_tampering_is_rejected(self) -> None:
        bundle = {
            "summary": copy.deepcopy(self.summary),
            "phase_results": copy.deepcopy(self.phase_results),
            "contracts": copy.deepcopy(self.contracts),
            "go_no_go": copy.deepcopy(self.go_no_go),
        }
        bad_phase = copy.deepcopy(bundle)
        bad_phase["phase_results"][0]["focused_test_status"] = "FAIL"
        with self.assertRaises(ValueError):
            self.review.validate_review_bundle(bad_phase)

        bad_raw = copy.deepcopy(bundle)
        bad_raw["summary"]["raw_snapshot_exact_match"] = False
        with self.assertRaises(ValueError):
            self.review.validate_review_bundle(bad_raw)

        bad_upload = copy.deepcopy(bundle)
        bad_upload["go_no_go"]["github_upload_performed"] = True
        with self.assertRaises(ValueError):
            self.review.validate_review_bundle(bad_upload)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_public_mirrors_acceptance_and_private_evidence_are_complete(self) -> None:
        self.assertEqual(self.review._read_json(self.review.METADATA_MANIFEST_PATH), self.manifest)
        self.assertEqual(self.review._read_json(self.review.METADATA_SUMMARY_PATH), self.summary)
        self.assertEqual(self.review._read_jsonl(self.review.METADATA_PHASE_RESULTS_PATH), self.phase_results)
        self.assertEqual(self.review._read_jsonl(self.review.METADATA_CONTRACT_MATRIX_PATH), self.contracts)
        self.assertEqual(self.review._read_json(self.review.METADATA_GO_NO_GO_PATH), self.go_no_go)
        self.assertEqual(self.acceptance["check_fail_count"], 0)
        self.assertEqual(self.acceptance["check_pass_count"], self.acceptance["check_count"])
        self.assertGreaterEqual(self.acceptance["check_count"], 24)
        self.assertTrue(self.review.PRIVATE_RAW_BEFORE_PATH.is_file())
        self.assertTrue(self.review.PRIVATE_RAW_AFTER_PATH.is_file())
        payload = json.dumps([self.manifest, self.summary, self.phase_results, self.contracts], ensure_ascii=False)
        for token in self.review.FORBIDDEN_PUBLIC_TEXT:
            self.assertNotIn(token, payload)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_governance_and_next_run_boundary_are_locked(self) -> None:
        for path in (
            self.review.DEVELOPMENT_EVENTS_PATH,
            self.review.STAGE_STATUS_PATH,
            self.review.TASK_STATUS_PATH,
        ):
            rows = self.review._read_jsonl(path)
            self.assertEqual(sum(row.get("phase_id") == self.review.PHASE_ID for row in rows), 1)
            self.assertEqual(sum(row.get("phase_id") == self.review.p3.PHASE_ID for row in rows), 1)
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn("下一步只能执行 v1.4 最终整体复审", handoff)
        self.assertIn("不得执行 GitHub upload", handoff)
        self.assertIn("不得执行 App 重装", handoff)
        self.assertEqual(self.manifest["next_phase"], "V014_FINAL_OVERALL_REVIEW")


if __name__ == "__main__":
    unittest.main()
