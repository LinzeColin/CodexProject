import csv
import importlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GENERATOR_PATH = ROOT / "KMFA" / "tools" / "v014_s06_p3_validation_evidence.py"
VALIDATOR_PATH = ROOT / "KMFA" / "tools" / "check_v014_s06_p3_validation_evidence.py"


class V014S06P3ValidationEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not GENERATOR_PATH.is_file() or not VALIDATOR_PATH.is_file():
            cls.validation_result = None
            cls.generator = None
            return
        generator = importlib.import_module("KMFA.tools.v014_s06_p3_validation_evidence")
        checker = importlib.import_module("KMFA.tools.check_v014_s06_p3_validation_evidence")
        generator.main()
        cls.validation_result = checker.validate_v014_s06_p3_validation_evidence()
        cls.generator = generator

    def test_phase_modules_exist(self) -> None:
        self.assertTrue(GENERATOR_PATH.is_file(), "KMFA.tools.v014_s06_p3_validation_evidence must exist")
        self.assertTrue(VALIDATOR_PATH.is_file(), "KMFA.tools.check_v014_s06_p3_validation_evidence must exist")

    def test_phase_writes_validation_evidence_and_metadata_quality(self) -> None:
        self.assertIsNotNone(self.validation_result, "S06-P3 validation result must be available")
        result = self.validation_result

        self.assertEqual(result["phase_id"], "S06-P3")
        self.assertTrue(result["s06_p1_dependency_validated"])
        self.assertTrue(result["s06_p2_dependency_validated"])
        self.assertTrue(result["metadata_quality_written"])
        self.assertEqual(result["metadata_zero_delta_records_written"], 1)
        self.assertEqual(result["metadata_data_quality_records_written"], 2)
        self.assertEqual(result["metadata_source_difference_records_written"], 1)
        self.assertEqual(result["metadata_mismatch_rows_written"], 1)
        self.assertEqual(result["project_status_count"], 2)
        self.assertEqual(result["blocked_project_status_count"], 2)
        self.assertEqual(result["q5_allowed_count"], 0)
        self.assertEqual(result["report_grade_a_allowed_count"], 0)

    def test_stage_outputs_are_sanitized_and_do_not_inline_source_values(self) -> None:
        self.assertIsNotNone(self.generator, "S06-P3 generator must be available")
        zero_delta = json.loads(self.generator.ZERO_DELTA_OUTPUT_PATH.read_text(encoding="utf-8"))
        statuses = [
            json.loads(line)
            for line in self.generator.PROJECT_STATUS_OUTPUT_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        with self.generator.MISMATCH_OUTPUT_PATH.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

        self.assertNotIn("mismatches", zero_delta)
        self.assertEqual(zero_delta["mismatch_count"], 1)
        self.assertEqual(len(statuses), 2)
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["field_path"].startswith("field_ref:sha256:"))
        combined = "\n".join(
            [
                self.generator.ZERO_DELTA_OUTPUT_PATH.read_text(encoding="utf-8"),
                self.generator.PROJECT_STATUS_OUTPUT_PATH.read_text(encoding="utf-8"),
                self.generator.MISMATCH_OUTPUT_PATH.read_text(encoding="utf-8"),
            ]
        )
        forbidden_keys = tuple(
            "_".join(parts)
            for parts in (
                ("contract", "amount", "cents"),
                ("authoritative", "value", "cents"),
                ("system", "value", "cents"),
                ("pdf", "value", "cents"),
                ("excel", "value", "cents"),
            )
        )
        for forbidden in (
            *forbidden_keys,
            "10000",
            "9999",
        ):
            self.assertNotIn(forbidden, combined)

    def test_phase_boundaries_remain_local_only_and_no_go(self) -> None:
        self.assertIsNotNone(self.validation_result, "S06-P3 validation result must be available")
        result = self.validation_result

        self.assertFalse(result["stage6_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["raw_inbox_read_performed"])
        self.assertFalse(result["raw_inbox_mutation_performed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["business_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
