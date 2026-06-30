from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
STAGE4_DIR = ROOT / "reports" / "pfi_v024" / "stage_4"
REVIEW_DIR = STAGE4_DIR / "whole_stage_review"
REQUIRED_FIELDS = {
    "metric_id",
    "value",
    "currency",
    "status",
    "source_id",
    "record_count",
    "as_of",
    "formula_id",
    "confidence",
    "blocking_reason_zh",
    "calculation_state",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestV024Stage4WholeReviewContract(unittest.TestCase):
    def test_whole_stage_review_artifacts_exist_and_scope_is_bounded(self) -> None:
        expected_files = [
            ROOT / "docs" / "pfi_v024" / "STAGE4_WHOLE_STAGE_REVIEW.md",
            REVIEW_DIR / "evidence.json",
            REVIEW_DIR / "terminal.log",
            REVIEW_DIR / "changed_files.txt",
            REVIEW_DIR / "risk_and_rollback.md",
        ]
        for path in expected_files:
            self.assertTrue(path.exists(), str(path))

        evidence = read_json(REVIEW_DIR / "evidence.json")
        self.assertEqual(evidence["schema"], "PFIV024Stage4WholeReviewEvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 4")
        self.assertEqual(evidence["review_status"], "pass")
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertTrue(evidence["stage_4_whole_review_complete"])
        self.assertEqual(evidence["current_run_unit"], "Stage 4 whole-stage review")
        self.assertTrue(evidence["current_run_only"])
        self.assertIn("GitHub main upload", evidence["explicitly_not_done"])

    def test_review_proves_all_stage4_acceptance_criteria(self) -> None:
        evidence = read_json(REVIEW_DIR / "evidence.json")
        acceptance = evidence["acceptance_review"]

        expected_checks = {
            "core_metric_fields_complete",
            "missing_real_data_no_cny_zero",
            "confirmed_zero_requires_source_time_sample_formula",
            "shared_read_model_across_surfaces",
            "no_mock_fixture_demo_financial_fallback",
        }
        self.assertEqual(set(acceptance), expected_checks)
        for check_id, item in acceptance.items():
            self.assertEqual(item["result"], "pass", check_id)
            self.assertTrue(item["evidence"], check_id)

    def test_phase_evidence_is_current_and_consistent(self) -> None:
        evidence = read_json(REVIEW_DIR / "evidence.json")
        phase41 = read_json(STAGE4_DIR / "phase_4_1" / "evidence.json")
        phase42 = read_json(STAGE4_DIR / "phase_4_2" / "evidence.json")
        phase43 = read_json(STAGE4_DIR / "phase_4_3" / "evidence.json")
        read_model = read_json(STAGE4_DIR / "phase_4_2" / "read_model_status.json")
        page_views = read_json(STAGE4_DIR / "phase_4_2" / "page_metric_states.json")
        browser = read_json(STAGE4_DIR / "phase_4_3" / "browser_validation.json")

        self.assertEqual(phase41["status"], "candidate_pass")
        self.assertEqual(phase42["status"], "candidate_pass")
        self.assertEqual(phase43["status"], "candidate_pass")
        self.assertTrue(phase43["phase_4_3_complete"])
        self.assertEqual(evidence["review_inputs"]["phase_4_1"], str(STAGE4_DIR / "phase_4_1" / "evidence.json"))
        self.assertEqual(evidence["review_inputs"]["phase_4_2"], str(STAGE4_DIR / "phase_4_2" / "evidence.json"))
        self.assertEqual(evidence["review_inputs"]["phase_4_3"], str(STAGE4_DIR / "phase_4_3" / "evidence.json"))

        metrics = {item["metric_id"]: item for item in read_model["core_metric_states"]}
        self.assertEqual(set(metrics), set(evidence["core_metric_ids"]))
        for metric in metrics.values():
            self.assertEqual(set(metric), REQUIRED_FIELDS)
            if metric["status"] not in {"ready", "confirmed_zero"}:
                self.assertIsNone(metric["value"], metric["metric_id"])

        hashes = {surface["read_model_hash"] for surface in page_views["surfaces"].values()}
        self.assertEqual(hashes, {read_model["read_model_hash"]})
        self.assertEqual(browser["status"], "pass")
        self.assertTrue(browser["no_financial_zero_when_data_missing"])
        self.assertEqual(browser["console_errors"], [])

    def test_review_findings_are_recorded_and_fixed_before_upload(self) -> None:
        evidence = read_json(REVIEW_DIR / "evidence.json")
        findings = evidence["findings"]

        self.assertGreaterEqual(len(findings), 1)
        for finding in findings:
            self.assertIn(finding["severity"], {"P1", "P2", "P3"})
            self.assertEqual(finding["status"], "fixed")
            self.assertTrue(finding["fix"])
            self.assertTrue(finding["verification"])

        self.assertFalse(evidence["github_main_uploaded"])
        self.assertIn("GitHub main upload", evidence["remaining_gates"])


if __name__ == "__main__":
    unittest.main()
