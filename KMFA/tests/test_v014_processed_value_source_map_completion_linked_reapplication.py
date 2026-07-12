from __future__ import annotations

import unittest
from pathlib import Path

from KMFA.tools import v014_processed_value_source_map_completion_linked_reapplication as generator
from KMFA.tools.check_v014_processed_value_source_map_completion_linked_reapplication import validate


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
    generator.PRIVATE_DIAGNOSTIC_PATH,
    generator.PRIVATE_RESULT_PATH,
    generator.PRIVATE_APPLIED_RECORDS_PATH,
    generator.PRIVATE_SOURCE_MAP_PATH,
    generator.PRIVATE_MATERIALIZATION_SOURCE_MAP_PATH,
    generator.PRIVATE_REPORT_PATH,
    generator.DEVELOPMENT_EVENTS_PATH,
]


class LinkedSourceMapReapplicationTest(unittest.TestCase):
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

    def test_linked_reapplication_locks_15_groups_and_77_records(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["linked_reapplication_candidate_group_count"], 15)
        self.assertEqual(summary["linked_reapplication_candidate_record_count"], 77)
        self.assertEqual(summary["linked_reapplication_applied_group_count"], 15)
        self.assertEqual(summary["linked_reapplication_applied_record_count"], 77)
        self.assertEqual(summary["linked_reapplication_blocked_record_count"], 0)
        self.assertEqual(summary["source_map_records_applied_count"], 77)

    def test_private_materialization_input_is_staged_without_replay(self) -> None:
        summary = self.result["summary"]
        self.assertTrue(summary["private_processed_value_source_map_written"])
        self.assertTrue(summary["private_processed_value_source_map_gitignored"])
        self.assertTrue(summary["private_materialization_source_map_staged"])
        self.assertTrue(summary["private_materialization_source_map_gitignored"])
        self.assertEqual(summary["private_materialization_source_map_record_count"], 77)
        self.assertTrue(summary["processed_value_materialization_replay_ready"])
        self.assertFalse(summary["processed_value_materialization_replay_performed"])

    def test_downstream_gates_stay_closed(self) -> None:
        summary = self.result["summary"]
        self.assertFalse(summary["raw_to_processed_value_comparison_ready"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_reconciliation_allowed"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["lineage_full_check_complete"])
        self.assertFalse(summary["formal_report_allowed"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_public_matrix_is_aggregate_only(self) -> None:
        matrix = self.result["matrix"]
        self.assertEqual(matrix["linked_reapplication_check_count"], 9)
        self.assertEqual(matrix["linked_reapplication_pass_count"], 9)
        self.assertEqual(matrix["linked_reapplication_fail_count"], 0)
        self.assertEqual(matrix["linked_reapplication_candidate_group_count"], 15)
        self.assertEqual(matrix["linked_reapplication_candidate_record_count"], 77)
        self.assertEqual(matrix["source_map_records_applied_count"], 77)
        self.assertEqual(matrix["private_materialization_source_map_record_count"], 77)

    def test_raw_boundary_excludes_raw_inbox_access(self) -> None:
        boundary = self.result["summary"]["raw_boundary"]
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])
        self.assertTrue(boundary["private_post_resolution_candidate_queue_read_by_this_phase"])
        self.assertTrue(boundary["private_partial_value_source_fill_read_by_this_phase"])

    def test_validator_accepts_private_reapplication(self) -> None:
        manifest = validate(require_private_reapplication=True)
        self.assertEqual(manifest["summary"]["linked_reapplication_applied_record_count"], 77)
        self.assertEqual(manifest["summary"]["private_materialization_source_map_record_count"], 77)
        self.assertFalse(manifest["summary"]["raw_to_processed_value_comparison_performed_by_this_phase"])


if __name__ == "__main__":
    unittest.main()
