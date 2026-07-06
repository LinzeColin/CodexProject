from __future__ import annotations

import unittest
from pathlib import Path

from KMFA.tools import v014_processed_target_outside_linked_scope_resolution as generator
from KMFA.tools.check_v014_processed_target_outside_linked_scope_resolution import validate


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
    generator.PRIVATE_RESOLUTION_PATH,
    generator.PRIVATE_DIAGNOSTIC_PATH,
    generator.PRIVATE_QUEUE_PATH,
    generator.PRIVATE_REPORT_PATH,
    generator.DEVELOPMENT_EVENTS_PATH,
]


class ProcessedTargetOutsideLinkedScopeResolutionTest(unittest.TestCase):
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

    def test_outside_scope_counts(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertTrue(summary["source_dry_run_passed"])
        self.assertEqual(summary["processed_target_slot_count"], 149)
        self.assertEqual(summary["linked_scope_resolved_target_slot_count"], 77)
        self.assertEqual(summary["outside_linked_scope_target_slot_count"], 72)
        self.assertEqual(summary["outside_scope_resolution_queue_record_count"], 72)
        self.assertEqual(summary["outside_scope_verified_against_staging_count"], 72)
        self.assertEqual(summary["outside_scope_already_has_source_map_count"], 0)

    def test_resolution_requires_authorized_source_map_extension(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["outside_scope_auto_resolvable_count"], 0)
        self.assertEqual(summary["outside_scope_authorized_source_map_required_count"], 72)
        self.assertEqual(summary["outside_scope_resolution_applied_count"], 0)
        self.assertEqual(summary["outside_scope_resolution_pending_count"], 72)
        self.assertFalse(summary["source_map_extension_written_by_this_phase"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])
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
        self.assertEqual(matrix["outside_scope_resolution_check_count"], 8)
        self.assertEqual(matrix["outside_scope_resolution_check_pass_count"], 8)
        self.assertEqual(matrix["outside_scope_resolution_check_fail_count"], 0)
        self.assertEqual(matrix["outside_scope_authorized_source_map_required_count"], 72)
        self.assertFalse(matrix["full_raw_to_processed_value_comparison_complete"])

    def test_validator_accepts_private_resolution(self) -> None:
        manifest = validate(require_private_resolution=True)
        summary = manifest["summary"]
        self.assertEqual(summary["outside_linked_scope_target_slot_count"], 72)
        self.assertEqual(summary["outside_scope_authorized_source_map_required_count"], 72)
        self.assertFalse(summary["source_map_extension_written_by_this_phase"])


if __name__ == "__main__":
    unittest.main()
