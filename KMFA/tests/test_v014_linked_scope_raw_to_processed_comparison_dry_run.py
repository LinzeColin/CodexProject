from __future__ import annotations

import unittest
from pathlib import Path

from KMFA.tools import v014_linked_scope_raw_to_processed_comparison_dry_run as generator
from KMFA.tools.check_v014_linked_scope_raw_to_processed_comparison_dry_run import validate


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
    generator.PRIVATE_DRY_RUN_PATH,
    generator.PRIVATE_DIAGNOSTIC_PATH,
    generator.PRIVATE_DRY_RUN_RECORDS_PATH,
    generator.PRIVATE_REPORT_PATH,
    generator.DEVELOPMENT_EVENTS_PATH,
]


class LinkedScopeRawToProcessedComparisonDryRunTest(unittest.TestCase):
    def setUp(self) -> None:
        snapshot = self._snapshot_artifacts()
        self.addCleanup(self._restore_artifacts, snapshot)
        self.result = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    @staticmethod
    def _snapshot_artifacts() -> dict[Path, bytes | None]:
        snapshot: dict[Path, bytes | None] = {}
        for path in ARTIFACT_PATHS:
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

    def test_linked_scope_dry_run_counts(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["processed_target_slot_count"], 149)
        self.assertEqual(summary["linked_materialized_record_count"], 77)
        self.assertEqual(summary["candidate_catalog_record_count"], 366)
        self.assertEqual(summary["linked_scope_private_fingerprint_precheck_pair_count"], 77)
        self.assertEqual(summary["linked_scope_dry_run_pair_count"], 77)
        self.assertEqual(summary["linked_scope_dry_run_exact_match_count"], 77)
        self.assertEqual(summary["linked_scope_dry_run_mismatch_count"], 0)
        self.assertEqual(summary["linked_scope_dry_run_invalid_record_count"], 0)
        self.assertEqual(summary["linked_unique_source_record_ref_count"], 15)
        self.assertEqual(summary["linked_unique_processed_value_fingerprint_count"], 12)
        self.assertEqual(summary["processed_target_slot_outside_linked_replay_scope_count"], 72)

    def test_dry_run_passes_but_full_comparison_stays_closed(self) -> None:
        summary = self.result["summary"]
        self.assertTrue(summary["linked_scope_raw_to_processed_value_comparison_dry_run_performed_by_this_phase"])
        self.assertTrue(summary["linked_scope_raw_to_processed_value_comparison_dry_run_passed"])
        self.assertTrue(summary["linked_scope_private_fingerprint_consistency_dry_run_verified"])
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

    def test_raw_inbox_is_not_accessed(self) -> None:
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["raw_data_root_readonly_policy_active"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_hash_or_value_fingerprint_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_public_matrix_is_aggregate_only(self) -> None:
        matrix = self.result["matrix"]
        self.assertEqual(matrix["linked_scope_dry_run_check_count"], 8)
        self.assertEqual(matrix["linked_scope_dry_run_check_pass_count"], 8)
        self.assertEqual(matrix["linked_scope_dry_run_check_fail_count"], 0)
        self.assertEqual(matrix["linked_scope_dry_run_exact_match_count"], 77)
        self.assertEqual(matrix["linked_scope_dry_run_mismatch_count"], 0)
        self.assertFalse(matrix["full_raw_to_processed_value_comparison_complete"])

    def test_validator_accepts_private_dry_run(self) -> None:
        manifest = validate(require_private_dry_run=True)
        summary = manifest["summary"]
        self.assertEqual(summary["linked_scope_dry_run_exact_match_count"], 77)
        self.assertEqual(summary["linked_scope_dry_run_mismatch_count"], 0)
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])


if __name__ == "__main__":
    unittest.main()
