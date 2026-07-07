from __future__ import annotations

import unittest
from pathlib import Path

from KMFA.tools import v014_residual_difference_raw_candidate_alignment_after_precheck as generator
from KMFA.tools.check_v014_residual_difference_raw_candidate_alignment_after_precheck import validate


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
    generator.PRIVATE_ANCHOR_DRAFT_PATH,
    generator.PRIVATE_QUESTION_LIST_PATH,
    generator.PRIVATE_RAW_SCAN_RUNTIME_PATH,
    generator.DEVELOPMENT_EVENTS_PATH,
    generator.STAGE_STATUS_PATH,
    generator.TASK_STATUS_PATH,
]
SOURCE_INPUT_PATHS = [
    generator.SOURCE_PRECHECK_SUMMARY_PATH,
    generator.SOURCE_PRECHECK_MANIFEST_PATH,
    generator.SOURCE_PRECHECK_BLOCKERS_PATH,
    generator.SOURCE_RAW_COMPARISON_INPUT_PATH,
]


class ResidualDifferenceRawCandidateAlignmentAfterPrecheckTest(unittest.TestCase):
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
        self.assertEqual(summary["source_precheck_blocker_count"], 72)
        self.assertEqual(summary["source_raw_comparison_input_record_count"], 72)
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

    def test_diagnostic_track_alignment_statuses_remain_blocked(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(
            summary["diagnostic_track_counts"],
            {
                "owner_select_one_authoritative_candidate": 24,
                "provide_authoritative_source_reference_or_owner_exclusion": 40,
                "provide_formula_or_non_numeric_mapping": 8,
            },
        )
        self.assertEqual(summary["raw_candidate_anchor_draft_item_count"], 72)
        self.assertEqual(summary["owner_review_required_item_count"], 72)
        self.assertEqual(summary["alignment_ready_count"], 0)
        self.assertEqual(summary["private_anchor_draft_ready_count"], 0)

    def test_comparison_anchors_are_not_owner_authorized(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["direct_raw_candidate_record_ref_match_count"], 0)
        self.assertEqual(summary["direct_processed_fingerprint_match_count"], 0)
        self.assertEqual(summary["owner_authorized_comparison_anchor_count"], 0)
        self.assertFalse(summary["raw_to_processed_value_comparison_ready"])
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
        self.assertEqual(checks["direct_raw_candidate_record_ref_coverage"], "FAIL")
        self.assertEqual(checks["owner_authorized_anchor_coverage"], "FAIL")
        self.assertFalse(matrix["raw_to_processed_value_comparison_ready"])
        self.assertFalse(matrix["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(matrix["business_value_consistency_verified"])

    def test_validator_accepts_private_alignment(self) -> None:
        manifest = validate(require_private_alignment=True)
        summary = manifest["summary"]
        self.assertEqual(summary["source_precheck_blocker_count"], 72)
        self.assertEqual(summary["owner_review_required_item_count"], 72)
        self.assertFalse(summary["raw_to_processed_value_comparison_ready"])


if __name__ == "__main__":
    unittest.main()
