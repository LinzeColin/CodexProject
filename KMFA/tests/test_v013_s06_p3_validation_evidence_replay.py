import csv
import json
import unittest

from KMFA.tools.check_v013_s06_p3_validation_evidence_replay import (
    validate_v013_s06_p3_validation_evidence_replay,
)
from KMFA.tools.v013_s06_p3_validation_evidence_replay import (
    MISMATCH_OUTPUT_PATH,
    PROJECT_STATUS_OUTPUT_PATH,
    ZERO_DELTA_OUTPUT_PATH,
)


class V013S06P3ValidationEvidenceReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.validation_result = validate_v013_s06_p3_validation_evidence_replay()

    def test_replay_validator_locks_metadata_quality_output(self) -> None:
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
        zero_delta = json.loads(ZERO_DELTA_OUTPUT_PATH.read_text(encoding="utf-8"))
        statuses = [
            json.loads(line)
            for line in PROJECT_STATUS_OUTPUT_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        with MISMATCH_OUTPUT_PATH.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

        self.assertNotIn("mismatches", zero_delta)
        self.assertEqual(zero_delta["mismatch_count"], 1)
        self.assertEqual(len(statuses), 2)
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["field_path"].startswith("field_ref:sha256:"))
        combined = "\n".join(
            [
                ZERO_DELTA_OUTPUT_PATH.read_text(encoding="utf-8"),
                PROJECT_STATUS_OUTPUT_PATH.read_text(encoding="utf-8"),
                MISMATCH_OUTPUT_PATH.read_text(encoding="utf-8"),
            ]
        )
        self.assertNotIn("contract_amount_cents", combined)
        self.assertNotIn("authoritative_value_cents", combined)
        self.assertNotIn("system_value_cents", combined)
        self.assertNotIn("pdf_value_cents", combined)
        self.assertNotIn("excel_value_cents", combined)
        self.assertNotIn("10000", combined)
        self.assertNotIn("9999", combined)

    def test_phase_boundaries_remain_local_only_and_no_go(self) -> None:
        result = self.validation_result

        self.assertFalse(result["stage6_review_performed"])
        self.assertFalse(result["github_upload_performed"])
        self.assertFalse(result["raw_dir_read_performed"])
        self.assertFalse(result["raw_dir_mutation_performed"])
        self.assertFalse(result["formal_report_allowed"])
        self.assertFalse(result["business_execution_allowed"])


if __name__ == "__main__":
    unittest.main()
