from __future__ import annotations

import json
import unittest
from pathlib import Path

from KMFA.tools import (
    v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation
    as generator,
)
from KMFA.tools.check_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_after_owner_anchor_confirmation import (
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
    generator.PRIVATE_PAIR_COMPLETION_DIAGNOSTIC_PATH,
    generator.PRIVATE_PAIR_COMPLETION_RECORDS_PATH,
    generator.PRIVATE_PAIR_COMPLETION_BLOCKER_RECORDS_PATH,
    generator.PRIVATE_PAIR_COMPLETION_REPORT_PATH,
]

SOURCE_INPUT_PATHS = [
    generator.SOURCE_COMPARISON_SUMMARY_PATH,
    generator.SOURCE_COMPARISON_MANIFEST_PATH,
    generator.SOURCE_COMPARISON_GO_NO_GO_PATH,
    generator.SOURCE_COMPARISON_MATRIX_PATH,
    generator.SOURCE_PRIVATE_COMPARISON_BLOCKER_RECORDS_PATH,
    generator.SOURCE_PRIVATE_ANCHOR_DRAFT_PATH,
    generator.SOURCE_PRIVATE_FULL_MATERIALIZED_RECORDS_PATH,
]


class ResidualDifferenceFingerprintPairCompletionAfterOwnerAnchorConfirmationTest(unittest.TestCase):
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

    def test_pair_completion_attempt_completes_only_evidence_supported_pairs(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_formal_comparison_blocker_count"], 72)
        self.assertEqual(summary["source_missing_private_fingerprint_pair_count"], 72)
        self.assertEqual(summary["fingerprint_pair_completion_item_count"], 72)
        self.assertEqual(summary["processed_fingerprint_available_count"], 72)
        self.assertEqual(summary["raw_candidate_fingerprint_available_count"], 24)
        self.assertEqual(summary["fingerprint_pair_completed_count"], 24)
        self.assertEqual(summary["fingerprint_pair_completion_blocker_count"], 48)
        self.assertEqual(summary["missing_raw_candidate_fingerprint_count"], 48)
        self.assertEqual(summary["missing_processed_fingerprint_count"], 0)
        self.assertTrue(summary["fingerprint_pair_completion_attempted_by_this_phase"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertEqual(summary["unresolved_difference_count"], 72)

    def test_private_completion_outputs_preserve_slot_coverage_without_public_commit(self) -> None:
        source_blockers = self._read_jsonl(generator.SOURCE_PRIVATE_COMPARISON_BLOCKER_RECORDS_PATH)
        completion_rows = self._read_jsonl(generator.PRIVATE_PAIR_COMPLETION_RECORDS_PATH)
        blocker_rows = self._read_jsonl(generator.PRIVATE_PAIR_COMPLETION_BLOCKER_RECORDS_PATH)
        self.assertEqual(len(source_blockers), 72)
        self.assertEqual(len(completion_rows), 24)
        self.assertEqual(len(blocker_rows), 48)
        self.assertEqual(
            {row[generator.PRIVATE_SLOT_KEY] for row in source_blockers},
            {row[generator.PRIVATE_SLOT_KEY] for row in completion_rows}
            | {row[generator.PRIVATE_SLOT_KEY] for row in blocker_rows},
        )
        self.assertTrue(all(row["fingerprint_pair_completion_status"] == "completed_private_pair" for row in completion_rows))
        self.assertTrue(
            all(
                row["fingerprint_pair_completion_status"] == "missing_raw_candidate_fingerprint_for_pair_completion"
                for row in blocker_rows
            )
        )
        self.assertTrue(all(row["public_commit_allowed"] is False for row in completion_rows + blocker_rows))

    def test_preserves_source_inputs_and_raw_boundary(self) -> None:
        self.assertEqual(self.source_snapshot, self._snapshot_artifacts(SOURCE_INPUT_PATHS))
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["source_private_comparison_blocker_records_read_by_this_phase"])
        self.assertTrue(boundary["source_private_full_materialized_records_read_by_this_phase"])
        self.assertFalse(boundary["source_private_comparison_blocker_records_mutated_by_this_phase"])
        self.assertFalse(boundary["source_private_anchor_draft_mutated_by_this_phase"])
        self.assertFalse(boundary["source_private_full_materialized_records_mutated_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_track_counts_are_preserved(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["owner_select_one_authoritative_candidate_count"], 24)
        self.assertEqual(summary["provide_authoritative_source_reference_or_owner_exclusion_count"], 40)
        self.assertEqual(summary["provide_formula_or_non_numeric_mapping_count"], 8)

    def test_matrix_all_pass(self) -> None:
        matrix = self.result["matrix"]
        self.assertEqual(matrix["check_count"], 15)
        self.assertEqual(matrix["check_pass_count"], 15)
        self.assertEqual(matrix["check_fail_count"], 0)

    def test_validator_accepts_pair_completion_blockers(self) -> None:
        manifest = validate(require_private_completion=True)
        summary = manifest["summary"]
        self.assertEqual(summary["fingerprint_pair_completed_count"], 24)
        self.assertEqual(summary["fingerprint_pair_completion_blocker_count"], 48)
        self.assertTrue(summary["fingerprint_pair_completion_attempted_by_this_phase"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])


if __name__ == "__main__":
    unittest.main()
