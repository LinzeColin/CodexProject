import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from KMFA.tools.precision_stress_validation import (
    PrecisionStressError,
    REQUIRED_SCENARIO_TYPES,
    build_default_precision_stress_suite,
    validate_precision_stress_artifacts,
    write_precision_stress_artifacts,
)


class PrecisionStressValidationTests(unittest.TestCase):
    def test_default_suite_covers_s18_p1_required_scope(self) -> None:
        manifest, scenarios, import_runs, error_reports = build_default_precision_stress_suite(
            generated_at="2026-07-01T23:59:59+10:00"
        )
        validate_precision_stress_artifacts(manifest, scenarios, import_runs, error_reports)

        self.assertEqual(manifest["stage_phase"], "S18-P1")
        self.assertEqual(tuple(manifest["required_scenario_types"]), REQUIRED_SCENARIO_TYPES)
        self.assertEqual(manifest["summary"]["scenario_count"], 5)
        self.assertEqual(manifest["summary"]["consecutive_import_run_count"], 3)
        self.assertEqual(manifest["summary"]["large_batch_file_count"], 1200)
        self.assertEqual(manifest["summary"]["error_report_count"], 2)
        self.assertTrue(manifest["quality_gate"]["amount_precision_extreme_test_passed"])
        self.assertTrue(manifest["quality_gate"]["zero_delta_extreme_test_passed"])
        self.assertTrue(manifest["quality_gate"]["duplicate_import_idempotency_passed"])
        self.assertTrue(manifest["quality_gate"]["bad_file_error_report_passed"])
        self.assertTrue(manifest["quality_gate"]["missing_field_error_report_passed"])
        self.assertTrue(manifest["quality_gate"]["three_consecutive_imports_consistent"])
        self.assertTrue(manifest["quality_gate"]["large_batch_performance_within_budget"])
        self.assertTrue(manifest["quality_gate"]["html_samples_read_for_s18_acceptance"])
        self.assertFalse(manifest["quality_gate"]["s18_p2_scope_included"])
        self.assertFalse(manifest["quality_gate"]["s18_p3_scope_included"])
        self.assertFalse(manifest["quality_gate"]["github_upload_allowed"])

    def test_scenarios_cover_precision_zero_delta_duplicate_bad_file_and_missing_field(self) -> None:
        manifest, scenarios, import_runs, error_reports = build_default_precision_stress_suite(
            generated_at="2026-07-01T23:59:59+10:00"
        )
        validate_precision_stress_artifacts(manifest, scenarios, import_runs, error_reports)

        scenarios_by_type = {row["scenario_type"]: row for row in scenarios}
        self.assertEqual(set(scenarios_by_type), set(REQUIRED_SCENARIO_TYPES))
        self.assertEqual(scenarios_by_type["amount_precision"]["minimum_fail_difference_cents"], 1)
        self.assertEqual(scenarios_by_type["zero_delta"]["zero_delta_result"], "passed")
        self.assertEqual(scenarios_by_type["duplicate_import"]["idempotency_result"], "passed")
        self.assertEqual(scenarios_by_type["bad_file"]["error_report_ref"], "precision_stress_error_report_bad_file")
        self.assertEqual(
            scenarios_by_type["missing_field"]["error_report_ref"],
            "precision_stress_error_report_missing_field",
        )
        for row in scenarios:
            self.assertEqual(row["record_type"], "precision_stress_scenario")
            self.assertEqual(row["stage_phase"], "S18-P1")
            self.assertEqual(row["fixture_mode"], "public_safe_synthetic")
            self.assertFalse(row["raw_business_data_used"])
            self.assertFalse(row["true_money_used"])

    def test_three_consecutive_import_runs_have_identical_result_hashes(self) -> None:
        manifest, scenarios, import_runs, error_reports = build_default_precision_stress_suite(
            generated_at="2026-07-01T23:59:59+10:00"
        )
        validate_precision_stress_artifacts(manifest, scenarios, import_runs, error_reports)

        self.assertEqual([row["run_sequence"] for row in import_runs], [1, 2, 3])
        result_hashes = {row["result_hash"] for row in import_runs}
        scenario_hashes = {row["scenario_set_hash"] for row in import_runs}
        self.assertEqual(len(result_hashes), 1)
        self.assertEqual(len(scenario_hashes), 1)
        for row in import_runs:
            self.assertEqual(row["record_type"], "precision_stress_import_run")
            self.assertEqual(row["status"], "passed")
            self.assertEqual(row["input_mode"], "public_safe_synthetic_metadata_only")
            self.assertFalse(row["raw_file_committed"])

    def test_large_batch_performance_budget_and_error_reports_are_public_safe(self) -> None:
        manifest, scenarios, import_runs, error_reports = build_default_precision_stress_suite(
            generated_at="2026-07-01T23:59:59+10:00"
        )
        validate_precision_stress_artifacts(manifest, scenarios, import_runs, error_reports)

        self.assertLessEqual(
            manifest["large_batch"]["elapsed_ms"],
            manifest["large_batch"]["performance_budget_ms"],
        )
        self.assertEqual(manifest["large_batch"]["synthetic_file_count"], 1200)
        self.assertEqual(manifest["large_batch"]["failed_file_count"], 2)
        reports_by_type = {row["error_type"]: row for row in error_reports}
        self.assertEqual(set(reports_by_type), {"bad_file", "missing_field"})
        for row in error_reports:
            self.assertEqual(row["record_type"], "precision_stress_error_report")
            self.assertEqual(row["stage_phase"], "S18-P1")
            self.assertEqual(row["severity"], "blocking")
            self.assertTrue(row["error_code"])
            self.assertTrue(row["impact_ref"])
            self.assertFalse(row["raw_excerpt_committed"])
            self.assertFalse(row["private_file_path_committed"])

    def test_public_payload_has_no_raw_values_private_refs_credentials_or_real_business_names(self) -> None:
        manifest, scenarios, import_runs, error_reports = build_default_precision_stress_suite(
            generated_at="2026-07-01T23:59:59+10:00"
        )
        payload = json.dumps([manifest, scenarios, import_runs, error_reports], ensure_ascii=False, sort_keys=True)

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

    def test_validator_rejects_missing_scope_or_performance_regression(self) -> None:
        manifest, scenarios, import_runs, error_reports = build_default_precision_stress_suite(
            generated_at="2026-07-01T23:59:59+10:00"
        )

        broken_scenarios = [row for row in scenarios if row["scenario_type"] != "bad_file"]
        with self.assertRaises(PrecisionStressError):
            validate_precision_stress_artifacts(manifest, broken_scenarios, import_runs, error_reports)

        broken_runs = copy.deepcopy(import_runs)
        broken_runs[2]["result_hash"] = "sha256:" + "0" * 64
        with self.assertRaises(PrecisionStressError):
            validate_precision_stress_artifacts(manifest, scenarios, broken_runs, error_reports)

        broken_manifest = copy.deepcopy(manifest)
        broken_manifest["large_batch"]["elapsed_ms"] = broken_manifest["large_batch"]["performance_budget_ms"] + 1
        with self.assertRaises(PrecisionStressError):
            validate_precision_stress_artifacts(broken_manifest, scenarios, import_runs, error_reports)

        broken_manifest = copy.deepcopy(manifest)
        broken_manifest["quality_gate"]["github_upload_allowed"] = True
        with self.assertRaises(PrecisionStressError):
            validate_precision_stress_artifacts(broken_manifest, scenarios, import_runs, error_reports)

    def test_cli_validator_accepts_generated_public_safe_artifacts(self) -> None:
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            manifest_path = tmp_root / "precision_stress_manifest.json"
            scenarios_path = tmp_root / "precision_stress_scenarios.jsonl"
            import_runs_path = tmp_root / "precision_stress_import_runs.jsonl"
            error_reports_path = tmp_root / "precision_stress_error_reports.jsonl"
            stage_manifest_path = tmp_root / "s18_p1_manifest.json"
            write_precision_stress_artifacts(
                generated_at="2026-07-01T23:59:59+10:00",
                manifest_path=manifest_path,
                scenarios_path=scenarios_path,
                import_runs_path=import_runs_path,
                error_reports_path=error_reports_path,
                stage_manifest_path=stage_manifest_path,
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "KMFA/tools/check_s18_p1_precision_stress.py",
                    "--manifest",
                    str(manifest_path),
                    "--scenarios",
                    str(scenarios_path),
                    "--import-runs",
                    str(import_runs_path),
                    "--error-reports",
                    str(error_reports_path),
                ],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS: KMFA S18-P1 precision stress check passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
