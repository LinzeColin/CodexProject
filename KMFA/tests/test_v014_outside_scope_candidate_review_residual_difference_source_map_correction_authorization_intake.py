from __future__ import annotations

import json
import unittest
from pathlib import Path

from KMFA.tools import (
    v014_outside_scope_candidate_review_residual_difference_source_map_correction_authorization_intake as generator,
)
from KMFA.tools.check_v014_outside_scope_candidate_review_residual_difference_source_map_correction_authorization_intake import (
    validate,
)


ARTIFACT_PATHS = [
    generator.SUMMARY_PATH,
    generator.MANIFEST_PATH,
    generator.GO_NO_GO_PATH,
    generator.MATRIX_PATH,
    generator.REPORT_PATH,
    generator.GO_NO_GO_RECORD_PATH,
    generator.TEST_RESULTS_PATH,
    generator.RISK_REGISTER_PATH,
    generator.ROLLBACK_PATH,
    generator.METADATA_SUMMARY_PATH,
    generator.METADATA_MANIFEST_PATH,
    generator.METADATA_GO_NO_GO_PATH,
    generator.METADATA_MATRIX_PATH,
    generator.PRIVATE_ACTIVE_RECORD_PATH,
    generator.PRIVATE_AUTHORIZATION_QUEUE_PATH,
    generator.PRIVATE_DIAGNOSTIC_PATH,
    generator.PRIVATE_REPORT_PATH,
]

SOURCE_INPUT_PATHS = [
    generator.SOURCE_SUMMARY_PATH,
    generator.SOURCE_MANIFEST_PATH,
    generator.SOURCE_GO_NO_GO_PATH,
    generator.SOURCE_MATRIX_PATH,
    generator.SOURCE_PRIVATE_FINAL_THRESHOLD_DIAGNOSTIC_PATH,
    generator.SOURCE_PRIVATE_FINAL_THRESHOLD_QUEUE_PATH,
    generator.SOURCE_PRIVATE_FINAL_THRESHOLD_REPORT_PATH,
]


class ResidualDifferenceSourceMapCorrectionAuthorizationIntakeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_snapshot = cls._snapshot_artifacts(SOURCE_INPUT_PATHS)
        cls.artifact_snapshot = cls._snapshot_artifacts(ARTIFACT_PATHS)
        cls.result = generator.generate(
            generated_at="2026-07-07T00:00:00+10:00",
            write_governance_event=False,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._restore_artifacts(cls.artifact_snapshot)

    @staticmethod
    def _snapshot_artifacts(paths: list[Path]) -> dict[Path, bytes | None]:
        snapshot: dict[Path, bytes | None] = {}
        for path in paths:
            snapshot[path] = path.read_bytes() if path.exists() else None
        return snapshot

    @staticmethod
    def _restore_artifacts(snapshot: dict[Path, bytes | None]) -> None:
        for path, data in snapshot.items():
            if data is None:
                if path.exists():
                    path.unlink()
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, object]]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_records_owner_authorization_without_application(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["authorization_item_count"], 72)
        self.assertTrue(summary["owner_authorization_intaken"])
        self.assertTrue(summary["private_resolution_preparation_allowed_next_phase"])
        self.assertTrue(summary["source_map_correction_application_readiness_allowed_next_phase"])
        self.assertFalse(summary["source_map_correction_ready"])
        self.assertFalse(summary["source_map_correction_written_by_this_phase"])
        self.assertFalse(summary["authoritative_value_resolution_written_by_this_phase"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])

    def test_preserves_final_threshold_inputs(self) -> None:
        self.assertEqual(self.source_snapshot, self._snapshot_artifacts(SOURCE_INPUT_PATHS))
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["source_private_final_threshold_queue_read_by_this_phase"])
        self.assertFalse(boundary["source_private_final_threshold_queue_mutated_by_this_phase"])

    def test_private_authorization_queue_matches_source_queue(self) -> None:
        source_rows = self._read_jsonl(generator.SOURCE_PRIVATE_FINAL_THRESHOLD_QUEUE_PATH)
        auth_rows = self._read_jsonl(generator.PRIVATE_AUTHORIZATION_QUEUE_PATH)
        self.assertEqual(len(source_rows), 72)
        self.assertEqual(len(auth_rows), 72)
        self.assertEqual(
            {row[generator.PRIVATE_SLOT_KEY] for row in source_rows},
            {row[generator.PRIVATE_SLOT_KEY] for row in auth_rows},
        )
        self.assertTrue(
            all(row["owner_authorization_decision_code"] == "AUTHORIZE_CODEX_PREPARE_PRIVATE_RESOLUTION" for row in auth_rows)
        )
        self.assertTrue(all(row["private_resolution_preparation_allowed_next_phase"] is True for row in auth_rows))
        self.assertTrue(all(row["source_map_correction_application_allowed_by_this_phase"] is False for row in auth_rows))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in auth_rows))

    def test_track_counts_are_public_safe(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["owner_select_one_authoritative_candidate_count"], 24)
        self.assertEqual(summary["provide_authoritative_source_reference_or_owner_exclusion_count"], 40)
        self.assertEqual(summary["provide_formula_or_non_numeric_mapping_count"], 8)

    def test_raw_inbox_is_not_accessed(self) -> None:
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["raw_data_root_readonly_policy_active"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_matrix_all_pass(self) -> None:
        matrix = self.result["matrix"]
        self.assertEqual(matrix["check_count"], 15)
        self.assertEqual(matrix["check_pass_count"], 15)
        self.assertEqual(matrix["check_fail_count"], 0)

    def test_validator_accepts_private_authorization(self) -> None:
        manifest = validate(require_private_authorization=True)
        summary = manifest["summary"]
        self.assertEqual(summary["authorization_item_count"], 72)
        self.assertTrue(summary["owner_authorization_intaken"])
        self.assertFalse(summary["source_map_correction_written_by_this_phase"])


if __name__ == "__main__":
    unittest.main()
