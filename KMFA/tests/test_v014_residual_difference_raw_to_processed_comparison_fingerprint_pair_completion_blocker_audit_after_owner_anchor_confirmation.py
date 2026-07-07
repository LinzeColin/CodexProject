from __future__ import annotations

import json
import unittest
from pathlib import Path

from KMFA.tools import (
    v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_audit_after_owner_anchor_confirmation
    as generator,
)
from KMFA.tools.check_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_audit_after_owner_anchor_confirmation import (
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
    generator.PRIVATE_BLOCKER_AUDIT_DIAGNOSTIC_PATH,
    generator.PRIVATE_BLOCKER_AUDIT_RECORDS_PATH,
    generator.PRIVATE_BLOCKER_AUDIT_REPORT_PATH,
]

SOURCE_INPUT_PATHS = [
    generator.SOURCE_PAIR_COMPLETION_SUMMARY_PATH,
    generator.SOURCE_PAIR_COMPLETION_MANIFEST_PATH,
    generator.SOURCE_PAIR_COMPLETION_GO_NO_GO_PATH,
    generator.SOURCE_PAIR_COMPLETION_MATRIX_PATH,
    generator.SOURCE_PRIVATE_PAIR_COMPLETION_RECORDS_PATH,
    generator.SOURCE_PRIVATE_PAIR_COMPLETION_BLOCKER_RECORDS_PATH,
]


class FingerprintPairCompletionBlockerAuditAfterOwnerAnchorConfirmationTest(unittest.TestCase):
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

    def test_audit_locks_all_remaining_pair_completion_blockers(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_fingerprint_pair_completion_item_count"], 72)
        self.assertEqual(summary["source_fingerprint_pair_completed_count"], 24)
        self.assertEqual(summary["source_fingerprint_pair_completion_blocker_count"], 48)
        self.assertEqual(summary["blocker_audit_item_count"], 48)
        self.assertEqual(summary["missing_raw_candidate_fingerprint_blocker_count"], 48)
        self.assertEqual(summary["missing_raw_candidate_record_ref_hash_blocker_count"], 48)
        self.assertEqual(summary["missing_processed_fingerprint_blocker_count"], 0)
        self.assertEqual(summary["actionable_private_pair_completion_ready_count"], 0)
        self.assertEqual(summary["comparison_retry_ready_after_blocker_audit_count"], 0)
        self.assertTrue(summary["fingerprint_pair_completion_blocker_audit_performed_by_this_phase"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertEqual(summary["unresolved_difference_count"], 72)

    def test_private_audit_records_cover_only_the_48_blockers(self) -> None:
        source_blockers = self._read_jsonl(generator.SOURCE_PRIVATE_PAIR_COMPLETION_BLOCKER_RECORDS_PATH)
        audit_rows = self._read_jsonl(generator.PRIVATE_BLOCKER_AUDIT_RECORDS_PATH)
        self.assertEqual(len(source_blockers), 48)
        self.assertEqual(len(audit_rows), 48)
        self.assertEqual(
            {row[generator.PRIVATE_SLOT_KEY] for row in source_blockers},
            {row[generator.PRIVATE_SLOT_KEY] for row in audit_rows},
        )
        self.assertTrue(
            all(row["blocker_audit_status"] == "missing_raw_candidate_fingerprint_blocker_confirmed" for row in audit_rows)
        )
        self.assertTrue(all(row["public_commit_allowed"] is False for row in audit_rows))
        self.assertTrue(all(row["comparison_retry_ready_after_blocker_audit"] is False for row in audit_rows))

    def test_blocker_track_counts_are_preserved(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["owner_select_one_authoritative_candidate_blocker_count"], 0)
        self.assertEqual(summary["provide_authoritative_source_reference_or_owner_exclusion_blocker_count"], 40)
        self.assertEqual(summary["provide_formula_or_non_numeric_mapping_blocker_count"], 8)
        self.assertEqual(summary["requires_owner_or_authorized_source_reference_count"], 40)
        self.assertEqual(summary["requires_formula_or_non_numeric_mapping_count"], 8)

    def test_preserves_source_inputs_and_raw_boundary(self) -> None:
        self.assertEqual(self.source_snapshot, self._snapshot_artifacts(SOURCE_INPUT_PATHS))
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["source_public_pair_completion_summary_read_by_this_phase"])
        self.assertTrue(boundary["source_private_pair_completion_blocker_records_read_by_this_phase"])
        self.assertFalse(boundary["source_private_pair_completion_blocker_records_mutated_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_matrix_all_pass_and_validator_accepts_private_audit(self) -> None:
        matrix = self.result["matrix"]
        self.assertEqual(matrix["check_count"], 15)
        self.assertEqual(matrix["check_pass_count"], 15)
        self.assertEqual(matrix["check_fail_count"], 0)
        manifest = validate(require_private_audit=True)
        self.assertEqual(manifest["summary"]["blocker_audit_item_count"], 48)
        self.assertEqual(manifest["summary"]["missing_raw_candidate_fingerprint_blocker_count"], 48)


if __name__ == "__main__":
    unittest.main()
