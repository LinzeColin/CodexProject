from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


GENERATOR_MODULE = "KMFA.tools.v014_s18_p2_post_remediation_full_regression_acceptance"
CHECKER_MODULE = "KMFA.tools.check_v014_s18_p2_post_remediation_full_regression_acceptance"
IMPLEMENTATION_EXISTS = (
    importlib.util.find_spec(GENERATOR_MODULE) is not None
    and importlib.util.find_spec(CHECKER_MODULE) is not None
)


class V014S18P2PostRemediationFullRegressionAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not IMPLEMENTATION_EXISTS:
            return
        from KMFA.tools import v014_s18_p2_post_remediation_full_regression_acceptance as phase
        from KMFA.tools.check_v014_s18_p2_post_remediation_full_regression_acceptance import (
            validate_v014_s18_p2_post_remediation_full_regression_acceptance,
        )

        cls.phase = phase
        cls.manifest = validate_v014_s18_p2_post_remediation_full_regression_acceptance(
            require_private_evidence=True,
            require_final_evidence=True,
        )
        cls.summary = cls.manifest["summary"]
        cls.checks = phase._read_jsonl(phase.CHECK_RESULTS_PATH)
        cls.stage_evidence = phase._read_jsonl(phase.STAGE_EVIDENCE_PATH)
        cls.html_audit = phase._read_json(phase.HTML_AUDIT_SUMMARY_PATH)
        cls.go_no_go = phase._read_json(phase.GO_NO_GO_PATH)

    def test_implementation_exists(self) -> None:
        self.assertTrue(IMPLEMENTATION_EXISTS, "current S18-P2 generator/checker not written yet")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_current_s18_p1_dependency_and_historical_s18_p2_are_quarantined(self) -> None:
        dependency = self.manifest["s18_p1_dependency"]
        self.assertEqual(dependency["phase_id"], "V014_S18_P1_POST_REMEDIATION_PRECISION_STRESS")
        self.assertTrue(dependency["validated"])
        self.assertTrue(self.manifest["historical_s18_p2_structural_baseline_validated"])
        self.assertFalse(self.manifest["historical_s18_p2_dynamic_state_authoritative"])
        self.assertEqual(self.manifest["taskpack_contract"]["roadmap_phase_id"], "S18-P2")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_five_regression_categories_are_actually_executed(self) -> None:
        self.assertEqual([row["check_category"] for row in self.checks], list(self.phase.CHECK_CATEGORIES))
        self.assertTrue(all(row["executed"] for row in self.checks))
        self.assertTrue(all(row["command_exit_code"] == 0 for row in self.checks))
        result_by_category = {row["check_category"]: row["result"] for row in self.checks}
        self.assertEqual(result_by_category["no_omission"], "PASS")
        self.assertEqual(result_by_category["zero_delta"], "PASS")
        self.assertEqual(result_by_category["schema"], "PASS")
        self.assertEqual(result_by_category["lineage"], "BLOCKED_SAFE")
        self.assertEqual(result_by_category["ui"], "PASS")
        self.assertTrue(self.summary["lineage_check_ran"])
        self.assertFalse(self.summary["lineage_full_check_complete"])

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_eighteen_stage_current_evidence_is_present_without_upload_evidence(self) -> None:
        self.assertEqual([row["stage_id"] for row in self.stage_evidence], [f"S{i:02d}" for i in range(1, 19)])
        self.assertTrue(all(row["evidence_present"] for row in self.stage_evidence))
        for row in self.stage_evidence:
            refs = json.dumps(row.get("evidence_refs", []), ensure_ascii=False)
            self.assertNotIn("GITHUB_UPLOAD", refs.upper())
            self.assertNotIn("github_upload_record", refs)
        self.assertTrue(all(row["stage_review_validated"] for row in self.stage_evidence[:17]))
        s18 = self.stage_evidence[-1]
        self.assertEqual(s18["completed_phase_ids"], ["S18-P1", "S18-P2"])
        self.assertEqual(s18["pending_phase_ids"], ["S18-P3"])
        self.assertFalse(s18["stage_review_validated"])

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_html_human_flow_audit_is_current_and_fail_closed(self) -> None:
        self.assertTrue(self.html_audit["audit_executed"])
        self.assertEqual(self.html_audit["file_count"], 6)
        self.assertEqual(self.html_audit["row_count"], 54)
        self.assertEqual(self.html_audit["pass_count"], 54)
        self.assertEqual(self.html_audit["warn_count"], 0)
        self.assertEqual(self.html_audit["fail_count"], 0)
        self.assertFalse(self.html_audit["raw_business_data_used"])

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_current_go_no_go_keeps_every_delivery_gate_closed(self) -> None:
        self.assertEqual(self.go_no_go["decision"], "NO_GO")
        self.assertEqual(self.go_no_go["maximum_report_grade"], "D")
        for blocker in (
            "LINEAGE_FULL_CHECK_NOT_COMPLETE",
            "OPEN_RECONCILIATION_REMAINS",
            "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED",
            "S18_P3_PENDING",
            "STAGE18_REVIEW_PENDING",
        ):
            self.assertIn(blocker, self.go_no_go["blocker_ids"])
        for key, value in self.go_no_go.items():
            if key.endswith("_allowed") or key.endswith("_allowed_in_this_run"):
                self.assertFalse(value, key)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_raw_snapshot_and_downstream_boundaries_are_locked(self) -> None:
        self.assertEqual(self.summary["raw_source_file_count"], 5)
        self.assertTrue(self.summary["raw_snapshot_exact_match"])
        self.assertTrue(self.summary["raw_cross_phase_snapshot_exact_match"])
        self.assertEqual(self.summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(self.summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(self.summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(self.summary["incomplete_reconciliation_count"], 1)
        self.assertEqual(self.summary["current_data_quality_grade"], "Q4")
        self.assertEqual(self.summary["current_report_grade"], "D")
        self.assertEqual(self.summary["decision"], "NO_GO")
        true_keys = {
            "s18_p1_dependency_reused",
            "historical_s18_p2_structural_baseline_reused",
            "s18_p2_full_regression_performed",
            "private_raw_snapshot_validation_performed",
        }
        for key, value in self.manifest["phase_boundaries"].items():
            self.assertEqual(value, key in true_keys, key)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_bundle_tampering_is_rejected(self) -> None:
        bundle = {
            "summary": copy.deepcopy(self.summary),
            "checks": copy.deepcopy(self.checks),
            "stage_evidence": copy.deepcopy(self.stage_evidence),
            "html_audit": copy.deepcopy(self.html_audit),
            "go_no_go": copy.deepcopy(self.go_no_go),
        }
        bad_lineage = copy.deepcopy(bundle)
        bad_lineage["summary"]["lineage_full_check_complete"] = True
        with self.assertRaises(ValueError):
            self.phase.validate_regression_bundle(bad_lineage)

        bad_stage_ref = copy.deepcopy(bundle)
        bad_stage_ref["stage_evidence"][0]["evidence_refs"] = ["KMFA/stage_artifacts/S01_GITHUB_UPLOAD/x"]
        with self.assertRaises(ValueError):
            self.phase.validate_regression_bundle(bad_stage_ref)

        bad_ui = copy.deepcopy(bundle)
        bad_ui["html_audit"]["fail_count"] = 1
        with self.assertRaises(ValueError):
            self.phase.validate_regression_bundle(bad_ui)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_public_metadata_mirrors_are_exact_and_public_safe(self) -> None:
        self.assertEqual(self.phase._read_json(self.phase.METADATA_MANIFEST_PATH), self.manifest)
        self.assertEqual(self.phase._read_jsonl(self.phase.METADATA_CHECK_RESULTS_PATH), self.checks)
        self.assertEqual(self.phase._read_jsonl(self.phase.METADATA_STAGE_EVIDENCE_PATH), self.stage_evidence)
        self.assertEqual(self.phase._read_json(self.phase.METADATA_HTML_AUDIT_SUMMARY_PATH), self.html_audit)
        self.assertEqual(self.phase._read_json(self.phase.METADATA_GO_NO_GO_PATH), self.go_no_go)
        payload = json.dumps(
            [self.manifest, self.checks, self.stage_evidence, self.html_audit, self.go_no_go],
            ensure_ascii=False,
        )
        for token in self.phase.FORBIDDEN_PUBLIC_TEXT:
            self.assertNotIn(token, payload)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_governance_history_and_next_run_boundary_are_locked(self) -> None:
        for path in (
            self.phase.DEVELOPMENT_EVENTS_PATH,
            self.phase.STAGE_STATUS_PATH,
            self.phase.TASK_STATUS_PATH,
        ):
            rows = self.phase._read_jsonl(path)
            self.assertEqual(sum(row.get("phase_id") == self.phase.PHASE_ID for row in rows), 1)
            self.assertEqual(sum(row.get("phase_id") == self.phase.s18_p1.PHASE_ID for row in rows), 1)
        version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        if f'current_phase: "{self.phase.PHASE_ID}"' in version_matrix:
            handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
            self.assertIn("下一步只能执行 S18-P3", handoff)
            self.assertIn("不得执行 Stage 18 整体复审", handoff)
            self.assertIn("不得执行 GitHub upload", handoff)
        self.assertEqual(self.manifest["next_phase"], "S18-P3")


if __name__ == "__main__":
    unittest.main()
