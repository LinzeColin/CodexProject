from __future__ import annotations

import unittest
from pathlib import Path

from KMFA.tools import (
    v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness as generator,
)
from KMFA.tools.check_v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness import (
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
    generator.PRIVATE_DIAGNOSTIC_PATH,
    generator.PRIVATE_READY_QUEUE_PATH,
    generator.PRIVATE_BLOCKER_QUEUE_PATH,
    generator.PRIVATE_REPORT_PATH,
]


class ResidualDifferenceSourceMapCorrectionApplicationReadinessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source_active_before = generator.SOURCE_PRIVATE_ACTIVE_RECORD_PATH.read_bytes()
        self.source_queue_before = generator.SOURCE_PRIVATE_AUTHORIZATION_QUEUE_PATH.read_bytes()
        snapshot = self._snapshot_artifacts()
        self.addCleanup(self._restore_artifacts, snapshot)
        self.manifest = generator.generate(
            generated_at="2026-07-07T00:00:00+10:00",
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

    def test_application_readiness_passes_for_authorized_private_resolution_rows(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_authorization_item_count"], 72)
        self.assertEqual(summary["private_active_authorization_record_count"], 72)
        self.assertEqual(summary["private_authorization_queue_count"], 72)
        self.assertEqual(summary["application_ready_record_count"], 72)
        self.assertEqual(summary["application_blocker_count"], 0)
        self.assertTrue(summary["private_resolution_application_ready"])
        self.assertTrue(summary["source_map_correction_application_allowed_next_phase"])
        self.assertTrue(summary["authoritative_value_resolution_application_allowed_next_phase"])

    def test_source_private_authorization_is_not_mutated(self) -> None:
        self.assertEqual(generator.SOURCE_PRIVATE_ACTIVE_RECORD_PATH.read_bytes(), self.source_active_before)
        self.assertEqual(generator.SOURCE_PRIVATE_AUTHORIZATION_QUEUE_PATH.read_bytes(), self.source_queue_before)
        boundary = self.manifest["summary"]["raw_boundary"]
        self.assertFalse(boundary["source_private_authorization_queue_mutated_by_this_phase"])

    def test_track_counts_remain_public_safe_aggregate_only(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["owner_select_one_authoritative_candidate_count"], 24)
        self.assertEqual(summary["provide_authoritative_source_reference_or_owner_exclusion_count"], 40)
        self.assertEqual(summary["provide_formula_or_non_numeric_mapping_count"], 8)
        self.assertEqual(summary["diagnostic_track_counts"]["owner_select_one_authoritative_candidate"], 24)

    def test_downstream_gates_stay_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["private_resolution_application_performed_by_this_phase"])
        self.assertFalse(summary["source_map_correction_written_by_this_phase"])
        self.assertEqual(summary["source_map_correction_applied_count"], 0)
        self.assertFalse(summary["authoritative_value_resolution_written_by_this_phase"])
        self.assertEqual(summary["authoritative_value_resolution_applied_count"], 0)
        self.assertFalse(summary["discrepancy_closure_written_by_this_phase"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_raw_inbox_is_not_accessed(self) -> None:
        boundary = self.manifest["summary"]["raw_boundary"]
        self.assertTrue(boundary["raw_data_root_readonly_policy_active"])
        self.assertTrue(boundary["source_private_authorization_queue_read_by_this_phase"])
        self.assertTrue(boundary["private_application_ready_queue_written_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_file_content_hash_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_validator_accepts_private_readiness(self) -> None:
        manifest = validate(require_private_readiness=True)
        summary = manifest["summary"]
        self.assertEqual(summary["application_ready_record_count"], 72)
        self.assertEqual(summary["application_blocker_count"], 0)
        self.assertTrue(summary["private_resolution_application_ready"])


if __name__ == "__main__":
    unittest.main()
