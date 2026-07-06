from __future__ import annotations

import unittest
from pathlib import Path

from KMFA.tools import v014_outside_scope_raw_candidate_alignment_after_full_precheck as generator
from KMFA.tools.check_v014_outside_scope_raw_candidate_alignment_after_full_precheck import validate


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
    generator.PRIVATE_ALIGNMENT_PATH,
    generator.PRIVATE_DIAGNOSTIC_PATH,
    generator.PRIVATE_ALIGNMENT_ITEMS_PATH,
    generator.PRIVATE_QUESTION_LIST_PATH,
    generator.DEVELOPMENT_EVENTS_PATH,
    generator.STAGE_STATUS_PATH,
    generator.TASK_STATUS_PATH,
]
SOURCE_INPUT_PATHS = [
    generator.SOURCE_PRECHECK_SUMMARY_PATH,
    generator.SOURCE_PRECHECK_MANIFEST_PATH,
    generator.SOURCE_PRECHECK_BLOCKERS_PATH,
    generator.SOURCE_FULL_MATERIALIZED_RECORDS_PATH,
    generator.SOURCE_PROCESSED_STAGING_PATH,
]


class OutsideScopeRawCandidateAlignmentAfterFullPrecheckTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.input_snapshot = cls._snapshot_artifacts(SOURCE_INPUT_PATHS)
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

    def test_alignment_locks_expected_public_safe_counts(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_precheck_missing_candidate_count"], 72)
        self.assertEqual(summary["outside_scope_blocker_count"], 72)
        self.assertEqual(summary["outside_scope_materialized_record_count"], 72)
        self.assertEqual(summary["processed_staging_slot_count"], 149)
        self.assertEqual(summary["raw_root_file_count"], 5)
        self.assertEqual(summary["raw_archive_member_count"], 18)
        self.assertEqual(summary["raw_archive_workbook_member_count"], 5)
        self.assertEqual(summary["raw_archive_pdf_member_count"], 7)
        self.assertEqual(summary["raw_openable_workbook_count"], 1)
        self.assertEqual(summary["raw_openable_pdf_count"], 7)
        self.assertEqual(summary["raw_workbook_parse_error_count"], 3)
        self.assertEqual(summary["raw_pdf_parse_error_count"], 0)
        self.assertEqual(summary["raw_numeric_candidate_count"], 351453)
        self.assertEqual(summary["raw_unique_numeric_fingerprint_count"], 22453)
        self.assertEqual(summary["outside_scope_context_group_count"], 10)

    def test_candidate_alignment_statuses_require_owner_review(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(
            summary["candidate_status_counts"],
            {
                "auto_ambiguous_multiple_candidates_requires_owner_review": 24,
                "auto_unmatched_requires_owner_review": 40,
                "requires_non_numeric_owner_mapping": 8,
            },
        )
        self.assertEqual(summary["auto_unique_candidate_item_count"], 0)
        self.assertEqual(summary["auto_ambiguous_candidate_item_count"], 24)
        self.assertEqual(summary["auto_unmatched_item_count"], 40)
        self.assertEqual(summary["non_numeric_or_calculation_context_item_count"], 8)
        self.assertEqual(summary["owner_review_required_item_count"], 72)
        self.assertEqual(summary["alignment_ready_count"], 0)

    def test_direct_coverage_is_still_blocked(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["direct_source_record_ref_match_count"], 0)
        self.assertEqual(summary["direct_processed_fingerprint_match_count"], 0)
        self.assertEqual(summary["processed_replay_fingerprint_matches_private_processed_ref_hash_count"], 72)
        self.assertFalse(summary["source_map_correction_ready"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_ready"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(summary["business_value_consistency_verified"])

    def test_raw_boundary_is_read_only_and_sources_are_not_mutated(self) -> None:
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["user_authorized_raw_data_read_for_this_phase"])
        self.assertTrue(boundary["raw_data_root_readonly_policy_active"])
        self.assertTrue(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertTrue(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertTrue(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertTrue(boundary["raw_inbox_hash_or_value_fingerprint_performed_by_this_phase"])
        self.assertTrue(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertTrue(boundary["raw_inbox_field_or_header_read_performed_by_this_phase"])
        self.assertTrue(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertTrue(boundary["raw_root_stat_unchanged_after_phase"])
        self.assertFalse(boundary["raw_inbox_write_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_delete_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_move_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_rename_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_overwrite_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_copy_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_normalize_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])
        self.assertEqual(self.input_snapshot, self._snapshot_artifacts(SOURCE_INPUT_PATHS))

    def test_public_matrix_preserves_no_go_state(self) -> None:
        matrix = self.result["matrix"]
        self.assertEqual(matrix["check_count"], 8)
        self.assertEqual(matrix["pass_count"], 6)
        self.assertEqual(matrix["fail_count"], 2)
        checks = {row["check_code"]: row["status"] for row in matrix["checks"]}
        self.assertEqual(checks["direct_source_ref_coverage"], "FAIL")
        self.assertEqual(checks["direct_processed_fingerprint_coverage"], "FAIL")
        self.assertFalse(matrix["full_raw_to_processed_value_comparison_ready"])
        self.assertFalse(matrix["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(matrix["business_value_consistency_verified"])

    def test_validator_accepts_private_alignment(self) -> None:
        manifest = validate(require_private_alignment=True)
        summary = manifest["summary"]
        self.assertEqual(summary["outside_scope_blocker_count"], 72)
        self.assertEqual(summary["owner_review_required_item_count"], 72)
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])


if __name__ == "__main__":
    unittest.main()
