from __future__ import annotations

import unittest
from pathlib import Path

from KMFA.tools import v014_outside_scope_candidate_review_packet_after_alignment as generator
from KMFA.tools.check_v014_outside_scope_candidate_review_packet_after_alignment import validate


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
    generator.PRIVATE_PACKET_PATH,
    generator.PRIVATE_PACKET_ITEMS_PATH,
    generator.PRIVATE_PACKET_MARKDOWN_PATH,
    generator.PRIVATE_DIAGNOSTIC_PATH,
]

SOURCE_INPUT_PATHS = [
    generator.SOURCE_ALIGNMENT_SUMMARY_PATH,
    generator.SOURCE_ALIGNMENT_MANIFEST_PATH,
    generator.SOURCE_PRIVATE_ALIGNMENT_PATH,
    generator.SOURCE_PRIVATE_ALIGNMENT_ITEMS_PATH,
]


class OutsideScopeCandidateReviewPacketAfterAlignmentTest(unittest.TestCase):
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

    def test_review_packet_locks_expected_public_safe_counts(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_alignment_phase_id"], "V014_OUTSIDE_SCOPE_RAW_CANDIDATE_ALIGNMENT_AFTER_FULL_PRECHECK")
        self.assertEqual(summary["source_alignment_item_count"], 72)
        self.assertEqual(summary["review_packet_item_count"], 72)
        self.assertEqual(summary["review_group_count"], 10)
        self.assertEqual(summary["ambiguous_review_item_count"], 24)
        self.assertEqual(summary["unmatched_review_item_count"], 40)
        self.assertEqual(summary["non_numeric_or_calculation_review_item_count"], 8)
        self.assertEqual(summary["private_candidate_option_excerpt_count"], 240)
        self.assertEqual(summary["candidate_record_observation_count"], 56748)
        self.assertEqual(summary["candidate_unique_fingerprint_observation_count"], 19292)
        self.assertEqual(summary["owner_review_required_item_count"], 72)

    def test_review_packet_preserves_owner_review_no_go_state(self) -> None:
        summary = self.result["summary"]
        self.assertTrue(summary["review_packet_ready"])
        self.assertFalse(summary["owner_review_response_supplied"])
        self.assertEqual(summary["selected_private_candidate_count"], 0)
        self.assertEqual(summary["corrected_source_map_reference_count"], 0)
        self.assertEqual(summary["authoritative_non_numeric_or_calculation_mapping_count"], 0)
        self.assertEqual(summary["keep_pending_response_count"], 0)
        self.assertFalse(summary["source_map_correction_ready"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_ready"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(summary["business_value_consistency_verified"])

    def test_candidate_statuses_match_source_alignment(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(
            summary["candidate_status_counts"],
            {
                "auto_ambiguous_multiple_candidates_requires_owner_review": 24,
                "auto_unmatched_requires_owner_review": 40,
                "requires_non_numeric_owner_mapping": 8,
            },
        )
        self.assertEqual(
            summary["alignment_status_counts"],
            {
                "ambiguous_raw_candidates_require_owner_review": 24,
                "no_context_raw_candidate_requires_source_mapping_review": 40,
                "non_numeric_or_calculation_context_requires_manual_authority": 8,
            },
        )

    def test_raw_boundary_does_not_reopen_raw_inbox(self) -> None:
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["user_declared_raw_data_immutable"])
        self.assertTrue(boundary["raw_data_root_readonly_policy_active"])
        self.assertTrue(boundary["source_private_alignment_read_performed_by_this_phase"])
        self.assertTrue(boundary["private_review_packet_written_by_this_phase"])
        self.assertFalse(boundary["source_private_alignment_mutated_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_hash_or_value_fingerprint_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_field_or_header_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_write_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_delete_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_move_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_rename_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_overwrite_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_copy_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_normalize_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])
        self.assertEqual(self.input_snapshot, self._snapshot_artifacts(SOURCE_INPUT_PATHS))

    def test_public_matrix_preserves_downstream_blockers(self) -> None:
        matrix = self.result["matrix"]
        self.assertEqual(matrix["check_count"], 8)
        self.assertEqual(matrix["pass_count"], 6)
        self.assertEqual(matrix["fail_count"], 2)
        checks = {row["check_code"]: row["status"] for row in matrix["checks"]}
        self.assertEqual(checks["direct_source_ref_coverage"], "FAIL")
        self.assertEqual(checks["direct_processed_fingerprint_coverage"], "FAIL")
        self.assertFalse(matrix["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(matrix["business_value_consistency_verified"])

    def test_private_packet_is_generated_but_not_committable(self) -> None:
        summary = self.result["summary"]
        self.assertTrue(summary["private_review_packet_written"])
        self.assertTrue(summary["private_review_packet_gitignored"])
        self.assertTrue(summary["private_review_packet_items_written"])
        self.assertTrue(summary["private_review_packet_items_gitignored"])
        self.assertTrue(summary["private_review_packet_markdown_written"])
        self.assertTrue(summary["private_review_packet_markdown_gitignored"])
        self.assertTrue(summary["private_diagnostic_written"])
        self.assertTrue(summary["private_diagnostic_gitignored"])

    def test_validator_accepts_private_packet(self) -> None:
        manifest = validate(require_private_packet=True)
        summary = manifest["summary"]
        self.assertEqual(summary["review_packet_item_count"], 72)
        self.assertEqual(summary["owner_review_required_item_count"], 72)
        self.assertFalse(summary["owner_review_response_supplied"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])


if __name__ == "__main__":
    unittest.main()
