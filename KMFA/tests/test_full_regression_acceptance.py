import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from KMFA.tools.full_regression_acceptance import (
    FullRegressionAcceptanceError,
    REQUIRED_CHECK_CATEGORIES,
    REQUIRED_STAGE_IDS,
    build_default_full_regression_acceptance_suite,
    validate_full_regression_acceptance_artifacts,
    write_full_regression_acceptance_artifacts,
)


class FullRegressionAcceptanceTests(unittest.TestCase):
    def test_default_suite_covers_s18_p2_required_scope(self) -> None:
        manifest, check_results, stage_evidence, go_no_go = build_default_full_regression_acceptance_suite(
            generated_at="2026-07-01T23:59:59+10:00"
        )
        validate_full_regression_acceptance_artifacts(manifest, check_results, stage_evidence, go_no_go)

        self.assertEqual(manifest["stage_phase"], "S18-P2")
        self.assertEqual(tuple(manifest["required_check_categories"]), REQUIRED_CHECK_CATEGORIES)
        self.assertEqual(manifest["summary"]["check_category_count"], 5)
        self.assertEqual(manifest["summary"]["stage_evidence_count"], 18)
        self.assertEqual(manifest["go_no_go"]["decision"], "NO_GO")
        self.assertFalse(manifest["go_no_go"]["delivery_allowed"])
        self.assertTrue(manifest["quality_gate"]["no_omission_check_passed"])
        self.assertTrue(manifest["quality_gate"]["zero_delta_check_ran"])
        self.assertTrue(manifest["quality_gate"]["schema_check_passed"])
        self.assertTrue(manifest["quality_gate"]["lineage_check_ran"])
        self.assertTrue(manifest["quality_gate"]["ui_check_passed"])
        self.assertFalse(manifest["quality_gate"]["lineage_full_check_complete"])
        self.assertFalse(manifest["quality_gate"]["official_report_release_allowed"])
        self.assertFalse(manifest["stage_scope"]["s18_p3_scope_included"])
        self.assertFalse(manifest["stage_scope"]["stage18_review_scope_included"])
        self.assertFalse(manifest["stage_scope"]["github_upload_scope_included"])

    def test_required_check_results_are_public_safe_and_classified(self) -> None:
        manifest, check_results, stage_evidence, go_no_go = build_default_full_regression_acceptance_suite(
            generated_at="2026-07-01T23:59:59+10:00"
        )
        validate_full_regression_acceptance_artifacts(manifest, check_results, stage_evidence, go_no_go)

        checks_by_category = {row["check_category"]: row for row in check_results}
        self.assertEqual(set(checks_by_category), set(REQUIRED_CHECK_CATEGORIES))
        self.assertEqual(checks_by_category["no_omission"]["result"], "passed")
        self.assertEqual(checks_by_category["zero_delta"]["result"], "passed_with_report_grade_block")
        self.assertEqual(checks_by_category["schema"]["result"], "passed")
        self.assertEqual(checks_by_category["lineage"]["result"], "blocked_not_complete")
        self.assertEqual(checks_by_category["ui"]["result"], "passed")
        for row in check_results:
            self.assertEqual(row["record_type"], "s18_p2_regression_check_result")
            self.assertEqual(row["stage_phase"], "S18-P2")
            self.assertEqual(row["execution_mode"], "public_safe_local_validation")
            self.assertFalse(row["raw_business_data_used"])
            self.assertFalse(row["external_service_called"])
            self.assertFalse(row["github_upload_performed"])

    def test_stage_evidence_index_confirms_all_18_stages(self) -> None:
        manifest, check_results, stage_evidence, go_no_go = build_default_full_regression_acceptance_suite(
            generated_at="2026-07-01T23:59:59+10:00"
        )
        validate_full_regression_acceptance_artifacts(manifest, check_results, stage_evidence, go_no_go)

        evidence_by_stage = {row["stage_id"]: row for row in stage_evidence}
        self.assertEqual(set(evidence_by_stage), set(REQUIRED_STAGE_IDS))
        for stage_id in REQUIRED_STAGE_IDS[:17]:
            self.assertIn(evidence_by_stage[stage_id]["status"], {"uploaded_to_github_main", "completed"})
            self.assertTrue(evidence_by_stage[stage_id]["review_or_phase_evidence_ref"])
        self.assertEqual(evidence_by_stage["S18"]["status"], "in_progress_s18p2_local_acceptance")
        self.assertIn("S18-P1", evidence_by_stage["S18"]["completed_phase_ids"])
        self.assertIn("S18-P2", evidence_by_stage["S18"]["completed_phase_ids"])
        self.assertNotIn("S18-P3", evidence_by_stage["S18"]["completed_phase_ids"])

    def test_go_no_go_blocks_delivery_when_lineage_and_report_gates_are_incomplete(self) -> None:
        manifest, check_results, stage_evidence, go_no_go = build_default_full_regression_acceptance_suite(
            generated_at="2026-07-01T23:59:59+10:00"
        )
        validate_full_regression_acceptance_artifacts(manifest, check_results, stage_evidence, go_no_go)

        self.assertEqual(go_no_go["decision"], "NO_GO")
        self.assertIn("LINEAGE_FULL_CHECK_NOT_COMPLETE", go_no_go["blocker_ids"])
        self.assertIn("OFFICIAL_REPORT_RELEASE_NOT_ALLOWED", go_no_go["blocker_ids"])
        self.assertIn("S09_PENDING_RECONCILIATION_12", go_no_go["blocker_ids"])
        self.assertFalse(go_no_go["delivery_allowed"])
        self.assertFalse(go_no_go["business_decision_basis_allowed"])
        self.assertFalse(go_no_go["github_upload_allowed"])

    def test_public_payload_has_no_raw_private_or_secret_material(self) -> None:
        manifest, check_results, stage_evidence, go_no_go = build_default_full_regression_acceptance_suite(
            generated_at="2026-07-01T23:59:59+10:00"
        )
        payload = json.dumps([manifest, check_results, stage_evidence, go_no_go], ensure_ascii=False, sort_keys=True)

        for forbidden_text in (
            "raw_value",
            "normalized_value",
            "plaintext_value",
            "source_header_text",
            "original_filename",
            "private://",
            "private_ref://",
            "bank_statement",
            "contract_full_text",
            "salary_detail",
            "tax_filing",
            "recipient_email",
            "smtp",
            "sk-",
            "-----BEGIN",
        ):
            self.assertNotIn(forbidden_text, payload)

    def test_validator_rejects_missing_check_stage_or_bad_go_decision(self) -> None:
        manifest, check_results, stage_evidence, go_no_go = build_default_full_regression_acceptance_suite(
            generated_at="2026-07-01T23:59:59+10:00"
        )

        broken_checks = [row for row in check_results if row["check_category"] != "lineage"]
        with self.assertRaises(FullRegressionAcceptanceError):
            validate_full_regression_acceptance_artifacts(manifest, broken_checks, stage_evidence, go_no_go)

        broken_evidence = [row for row in stage_evidence if row["stage_id"] != "S11"]
        with self.assertRaises(FullRegressionAcceptanceError):
            validate_full_regression_acceptance_artifacts(manifest, check_results, broken_evidence, go_no_go)

        broken_go = copy.deepcopy(go_no_go)
        broken_go["decision"] = "GO"
        with self.assertRaises(FullRegressionAcceptanceError):
            validate_full_regression_acceptance_artifacts(manifest, check_results, stage_evidence, broken_go)

        broken_manifest = copy.deepcopy(manifest)
        broken_manifest["stage_scope"]["github_upload_scope_included"] = True
        with self.assertRaises(FullRegressionAcceptanceError):
            validate_full_regression_acceptance_artifacts(broken_manifest, check_results, stage_evidence, go_no_go)

    def test_cli_validator_accepts_generated_public_safe_artifacts(self) -> None:
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            manifest_path = tmp_root / "full_regression_acceptance_manifest.json"
            checks_path = tmp_root / "full_regression_check_results.jsonl"
            stage_evidence_path = tmp_root / "stage_acceptance_evidence_index.jsonl"
            go_no_go_path = tmp_root / "go_no_go_report.json"
            stage_manifest_path = tmp_root / "s18_p2_manifest.json"
            write_full_regression_acceptance_artifacts(
                generated_at="2026-07-01T23:59:59+10:00",
                manifest_path=manifest_path,
                checks_path=checks_path,
                stage_evidence_path=stage_evidence_path,
                go_no_go_path=go_no_go_path,
                stage_manifest_path=stage_manifest_path,
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "KMFA/tools/check_s18_p2_full_regression_acceptance.py",
                    "--manifest",
                    str(manifest_path),
                    "--checks",
                    str(checks_path),
                    "--stage-evidence",
                    str(stage_evidence_path),
                    "--go-no-go",
                    str(go_no_go_path),
                ],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS: KMFA S18-P2 full regression acceptance check passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
