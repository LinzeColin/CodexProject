from __future__ import annotations

import unittest
from pathlib import Path

from KMFA.tools import v014_full_raw_to_processed_comparison_precheck_after_full_materialization as generator
from KMFA.tools.check_v014_full_raw_to_processed_comparison_precheck_after_full_materialization import validate


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
    generator.PRIVATE_PRECHECK_PATH,
    generator.PRIVATE_DIAGNOSTIC_PATH,
    generator.PRIVATE_COMPARISON_RECORDS_PATH,
    generator.PRIVATE_BLOCKER_RECORDS_PATH,
    generator.PRIVATE_REPORT_PATH,
    generator.DEVELOPMENT_EVENTS_PATH,
    generator.STAGE_STATUS_PATH,
    generator.TASK_STATUS_PATH,
]
SOURCE_INPUT_PATHS = [
    generator.SOURCE_FULL_MATERIALIZATION_SUMMARY_PATH,
    generator.SOURCE_FULL_MATERIALIZATION_MANIFEST_PATH,
    generator.PRIVATE_FULL_REPLAY_PATH,
    generator.PRIVATE_FULL_MATERIALIZED_RECORDS_PATH,
    generator.PRIVATE_CANDIDATE_CATALOG_PATH,
]


class FullRawToProcessedComparisonPrecheckAfterFullMaterializationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.input_snapshot = self._snapshot_artifacts(SOURCE_INPUT_PATHS)
        snapshot = self._snapshot_artifacts(ARTIFACT_PATHS)
        self.addCleanup(self._restore_artifacts, snapshot)
        self.result = generator.generate(
            generated_at="2026-07-07T00:00:00+10:00",
            write_governance_event=False,
        )

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

    def test_full_precheck_locks_expected_blocker_counts(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["processed_target_slot_count"], 149)
        self.assertEqual(summary["full_materialized_record_count"], 149)
        self.assertEqual(summary["candidate_catalog_record_count"], 366)
        self.assertEqual(summary["full_scope_candidate_record_match_count"], 77)
        self.assertEqual(summary["full_scope_private_fingerprint_precheck_pair_count"], 77)
        self.assertEqual(summary["full_scope_exact_fingerprint_match_count"], 77)
        self.assertEqual(summary["full_scope_fingerprint_mismatch_count"], 0)
        self.assertEqual(summary["full_scope_missing_candidate_count"], 72)
        self.assertEqual(summary["full_scope_invalid_materialized_record_count"], 0)
        self.assertEqual(summary["linked_materialized_record_count"], 77)
        self.assertEqual(summary["linked_exact_fingerprint_match_count"], 77)
        self.assertEqual(summary["linked_missing_candidate_count"], 0)
        self.assertEqual(summary["outside_scope_materialized_record_count"], 72)
        self.assertEqual(summary["outside_scope_missing_candidate_count"], 72)
        self.assertEqual(summary["full_unique_source_record_ref_count"], 35)
        self.assertEqual(summary["full_unique_processed_value_fingerprint_count"], 84)

    def test_precheck_performs_only_public_safe_readiness_check(self) -> None:
        summary = self.result["summary"]
        self.assertTrue(summary["full_raw_to_processed_value_comparison_precheck_performed_by_this_phase"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_precheck_passed"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_ready"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(summary["full_reconciliation_allowed"])
        self.assertFalse(summary["business_value_consistency_verified"])

    def test_release_and_execution_gates_stay_closed(self) -> None:
        summary = self.result["summary"]
        self.assertFalse(summary["lineage_full_check_complete"])
        self.assertFalse(summary["formal_report_allowed"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_raw_inbox_is_not_accessed_and_source_inputs_are_not_mutated(self) -> None:
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["raw_data_root_readonly_policy_active"])
        self.assertTrue(boundary["private_full_materialization_summary_read_by_this_phase"])
        self.assertTrue(boundary["private_full_materialized_records_read_by_this_phase"])
        self.assertTrue(boundary["private_candidate_catalog_read_by_this_phase"])
        self.assertTrue(boundary["private_full_comparison_precheck_written_by_this_phase"])
        self.assertFalse(boundary["source_private_full_replay_mutated_by_this_phase"])
        self.assertFalse(boundary["source_private_materialized_records_mutated_by_this_phase"])
        self.assertFalse(boundary["source_private_candidate_catalog_mutated_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])
        self.assertEqual(self.input_snapshot, self._snapshot_artifacts(SOURCE_INPUT_PATHS))

    def test_public_matrix_preserves_no_go_state(self) -> None:
        matrix = self.result["matrix"]
        self.assertEqual(matrix["full_precheck_check_count"], 7)
        self.assertEqual(matrix["full_precheck_pass_count"], 5)
        self.assertEqual(matrix["full_precheck_fail_count"], 2)
        self.assertEqual(matrix["full_scope_exact_fingerprint_match_count"], 77)
        self.assertEqual(matrix["full_scope_missing_candidate_count"], 72)
        self.assertEqual(matrix["outside_scope_missing_candidate_count"], 72)
        self.assertFalse(matrix["full_raw_to_processed_value_comparison_ready"])
        self.assertFalse(matrix["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(matrix["business_value_consistency_verified"])

    def test_validator_accepts_private_precheck(self) -> None:
        manifest = validate(require_private_precheck=True)
        summary = manifest["summary"]
        self.assertEqual(summary["full_scope_exact_fingerprint_match_count"], 77)
        self.assertEqual(summary["full_scope_missing_candidate_count"], 72)
        self.assertEqual(summary["outside_scope_missing_candidate_count"], 72)
        self.assertFalse(summary["full_raw_to_processed_value_comparison_ready"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])


if __name__ == "__main__":
    unittest.main()
