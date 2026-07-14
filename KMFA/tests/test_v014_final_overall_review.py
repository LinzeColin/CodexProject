from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path


GENERATOR_MODULE = "KMFA.tools.v014_final_overall_review"
CHECKER_MODULE = "KMFA.tools.check_v014_final_overall_review"
IMPLEMENTATION_EXISTS = (
    importlib.util.find_spec(GENERATOR_MODULE) is not None
    and importlib.util.find_spec(CHECKER_MODULE) is not None
)


class V014FinalOverallReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not IMPLEMENTATION_EXISTS:
            return
        from KMFA.tools import v014_final_overall_review as review
        from KMFA.tools.check_v014_final_overall_review import validate_v014_final_overall_review

        cls.review = review
        cls.manifest = validate_v014_final_overall_review(
            require_private_evidence=True,
            require_final_evidence=True,
        )
        cls.summary = review._read_json(review.SUMMARY_PATH)
        cls.stage_results = review._read_jsonl(review.STAGE_RESULTS_PATH)
        cls.contracts = review._read_jsonl(review.CONTRACT_MATRIX_PATH)
        cls.acceptance = review._read_json(review.ACCEPTANCE_MATRIX_PATH)
        cls.go_no_go = review._read_json(review.GO_NO_GO_PATH)

    def test_implementation_exists(self) -> None:
        self.assertTrue(IMPLEMENTATION_EXISTS, "v0.1.4 final overall review generator/checker not written yet")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_identity_current_chain_and_historical_quarantine(self) -> None:
        self.assertEqual(self.manifest["phase_id"], self.review.PHASE_ID)
        self.assertEqual(self.manifest["stage_id"], "S01-S18")
        self.assertEqual(self.manifest["roadmap_phase_id"], "FINAL-OVERALL-REVIEW")
        self.assertEqual(self.manifest["task_id"], self.review.TASK_ID)
        self.assertEqual(self.manifest["acceptance_id"], self.review.ACCEPTANCE_ID)
        self.assertEqual(self.manifest["decision"], "NO_GO")
        self.assertTrue(self.manifest["historical_overall_review_structural_baseline_validated"])
        self.assertFalse(self.manifest["historical_overall_review_dynamic_state_authoritative"])
        self.assertFalse(self.manifest["historical_overall_review_upload_state_authoritative"])

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_all_current_stage_validators_and_full_suite_are_recorded(self) -> None:
        self.assertEqual(len(self.stage_results), 18)
        self.assertEqual([row["stage_id"] for row in self.stage_results], [f"S{i:02d}" for i in range(1, 19)])
        self.assertTrue(all(row["strict_validator_status"] == "PASS" for row in self.stage_results))
        self.assertEqual(self.summary["current_stage_review_count"], 18)
        self.assertEqual(self.summary["current_stage_review_pass_count"], 18)
        self.assertEqual(self.summary["current_stage_validator_pass_count"], 18)
        self.assertGreaterEqual(self.summary["full_suite_test_count"], 1502)
        self.assertEqual(self.summary["full_suite_test_pass_count"], self.summary["full_suite_test_count"])

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_current_stage_review_selection_is_exact(self) -> None:
        for row in self.stage_results[:8]:
            self.assertEqual(row["review_kind"], "original")
            self.assertNotIn("POST_REMEDIATION", row["review_phase_id"])
        for row in self.stage_results[8:]:
            self.assertEqual(row["review_kind"], "post_remediation")
            self.assertIn("POST_REMEDIATION", row["review_phase_id"])
        self.assertTrue(all(row["historical_dynamic_state_authoritative"] is False for row in self.stage_results))

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_review_findings_are_fixed_and_closed(self) -> None:
        findings = self.manifest["review_findings"]
        self.assertEqual(len(findings), 14)
        self.assertEqual(sum(row["status"] == "fixed" for row in findings), 6)
        self.assertEqual(sum(row["status"] == "passed" for row in findings), 8)
        self.assertEqual(sum(row["status"] == "open" for row in findings), 0)
        self.assertEqual(self.summary["fixed_review_finding_count"], 6)
        self.assertEqual(self.summary["open_review_finding_count"], 0)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_cross_stage_contracts_raw_quality_and_ui_are_exact(self) -> None:
        self.assertGreaterEqual(len(self.contracts), 18)
        self.assertTrue(all(row["status"] == "PASS" for row in self.contracts))
        self.assertEqual(sum(row["mismatch_count"] for row in self.contracts), 0)
        self.assertEqual(self.summary["raw_source_file_count"], 5)
        self.assertTrue(self.summary["raw_snapshot_exact_match"])
        self.assertTrue(self.summary["raw_cross_phase_snapshot_exact_match"])
        self.assertEqual(self.summary["tracked_raw_filename_leak_count"], 0)
        self.assertEqual(self.summary["html_audit_pass_count"], 54)
        self.assertEqual(self.summary["html_audit_warn_count"], 0)
        self.assertEqual(self.summary["html_audit_fail_count"], 0)
        self.assertEqual(self.summary["current_data_quality_grade"], "Q4")
        self.assertEqual(self.summary["current_report_grade"], "D")
        self.assertEqual(self.summary["decision"], "NO_GO")
        self.assertEqual(
            [
                self.summary["open_final_difference_accepted_count"],
                self.summary["nonzero_delta_reconciliation_count"],
                self.summary["zero_delta_reconciliation_count"],
                self.summary["incomplete_reconciliation_count"],
            ],
            [3, 9, 2, 1],
        )

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_code_upload_is_ready_but_not_performed_and_business_release_is_blocked(self) -> None:
        self.assertEqual(self.go_no_go["decision"], "NO_GO")
        self.assertTrue(self.go_no_go["github_main_upload_ready"])
        self.assertFalse(self.go_no_go["github_upload_performed"])
        self.assertFalse(self.go_no_go["app_reinstall_performed"])
        self.assertFalse(self.go_no_go["delivery_allowed"])
        self.assertFalse(self.go_no_go["official_report_release_allowed"])
        self.assertFalse(self.go_no_go["lineage_full_check_complete"])
        self.assertNotIn("FINAL_OVERALL_REVIEW_PENDING", self.go_no_go["blocker_ids"])
        self.assertIn("ONE_TIME_GITHUB_MAIN_UPLOAD_PENDING", self.go_no_go["blocker_ids"])
        self.assertEqual(self.manifest["next_phase"], "V014_ONE_TIME_GITHUB_MAIN_UPLOAD")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_review_bundle_tampering_is_rejected(self) -> None:
        bundle = {
            "summary": copy.deepcopy(self.summary),
            "stage_results": copy.deepcopy(self.stage_results),
            "contracts": copy.deepcopy(self.contracts),
            "go_no_go": copy.deepcopy(self.go_no_go),
        }
        bad_stage = copy.deepcopy(bundle)
        bad_stage["stage_results"][0]["strict_validator_status"] = "FAIL"
        with self.assertRaises(ValueError):
            self.review.validate_review_bundle(bad_stage)

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
        self.assertEqual(self.review._read_jsonl(self.review.METADATA_STAGE_RESULTS_PATH), self.stage_results)
        self.assertEqual(self.review._read_jsonl(self.review.METADATA_CONTRACT_MATRIX_PATH), self.contracts)
        self.assertEqual(self.review._read_json(self.review.METADATA_GO_NO_GO_PATH), self.go_no_go)
        self.assertEqual(self.acceptance["check_fail_count"], 0)
        self.assertEqual(self.acceptance["check_pass_count"], self.acceptance["check_count"])
        self.assertGreaterEqual(self.acceptance["check_count"], 24)
        self.assertTrue(self.review.PRIVATE_RAW_BEFORE_PATH.is_file())
        self.assertTrue(self.review.PRIVATE_RAW_AFTER_PATH.is_file())
        self.assertTrue(self.review.PRIVATE_DIFFERENCE_REPORT_PATH.is_file())

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_private_difference_report_is_chinese_and_keeps_unresolved_state(self) -> None:
        report = self.review.PRIVATE_DIFFERENCE_REPORT_PATH.read_text(encoding="utf-8")
        self.assertIn("差异报告", report)
        self.assertIn("三项最终接受未决", report)
        self.assertIn("九项非零差异", report)
        self.assertIn("一项未完成比较", report)
        self.assertIn("未关闭", report)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_public_bundle_has_no_private_or_raw_plaintext(self) -> None:
        payload = json.dumps(
            [self.manifest, self.summary, self.stage_results, self.contracts, self.go_no_go],
            ensure_ascii=False,
        )
        for token in self.review.FORBIDDEN_PUBLIC_TEXT:
            self.assertNotIn(token, payload)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_tracked_repository_contains_no_actual_raw_filenames(self) -> None:
        raw_root = Path("/Users/linzezhang/Downloads/KMFA_MetaData")
        raw_names = {path.name.encode("utf-8") for path in raw_root.rglob("*") if path.is_file()}
        self.assertEqual(len(raw_names), 5)
        tracked = subprocess.run(
            ["git", "-c", "core.quotePath=false", "ls-files", "KMFA"],
            text=True,
            capture_output=True,
            check=True,
        ).stdout.splitlines()
        hits = [
            path
            for path_text in tracked
            if (path := Path(path_text)).is_file()
            for raw_name in raw_names
            if raw_name in path.read_bytes()
        ]
        self.assertEqual(hits, [])

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_governance_and_next_run_boundary_are_locked(self) -> None:
        for path in (
            self.review.DEVELOPMENT_EVENTS_PATH,
            self.review.STAGE_STATUS_PATH,
            self.review.TASK_STATUS_PATH,
        ):
            rows = self.review._read_jsonl(path)
            self.assertEqual(sum(row.get("phase_id") == self.review.PHASE_ID for row in rows), 1)
        event = next(
            row
            for row in self.review._read_jsonl(self.review.DEVELOPMENT_EVENTS_PATH)
            if row.get("phase_id") == self.review.PHASE_ID
        )
        changed_files = set(event["files_changed"])
        self.assertTrue(
            {path.as_posix() for path in self.review.RAW_ALIAS_REMEDIATION_PUBLIC_FILES}.issubset(changed_files)
        )
        self.assertIn(
            (self.review.HUMAN_DIR / "go_no_go_record_zh.md").as_posix(),
            changed_files,
        )
        handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn("下一步只能执行一次性 GitHub main upload", handoff)
        self.assertIn("本轮未执行 GitHub upload", handoff)
        self.assertIn("不得执行 App 重装", handoff)


if __name__ == "__main__":
    unittest.main()
