from __future__ import annotations

import unittest
from pathlib import Path

from KMFA.tools import v014_outside_scope_candidate_review_residual_difference_report as generator
from KMFA.tools.check_v014_outside_scope_candidate_review_residual_difference_report import validate


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
    generator.PRIVATE_RESIDUAL_DIFFERENCE_QUEUE_PATH,
    generator.PRIVATE_RESIDUAL_DIFFERENCE_REPORT_PATH,
]

SOURCE_INPUT_PATHS = [
    generator.SOURCE_SUMMARY_PATH,
    generator.SOURCE_MANIFEST_PATH,
    generator.SOURCE_PRIVATE_RESIDUAL_QUEUE_PATH,
    generator.SOURCE_PRIVATE_RESIDUAL_REPORT_PATH,
]


class OutsideScopeCandidateReviewResidualDifferenceReportTest(unittest.TestCase):
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

    def test_report_preserves_source_closure_counts(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_phase_id"], "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_DISCREPANCY_CLOSURE_BLOCKER_AUDIT")
        self.assertEqual(summary["source_open_closure_blocker_count"], 72)
        self.assertEqual(summary["source_closed_discrepancy_count"], 0)
        self.assertEqual(summary["source_newly_actionable_closure_count"], 0)
        self.assertEqual(summary["source_safe_auto_closure_count"], 0)

    def test_writes_residual_difference_report_without_closing_discrepancies(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["source_private_residual_queue_item_count"], 72)
        self.assertEqual(summary["residual_difference_report_item_count"], 72)
        self.assertEqual(summary["open_residual_difference_count"], 72)
        self.assertEqual(summary["closed_discrepancy_count"], 0)
        self.assertEqual(summary["safe_auto_closure_count"], 0)
        self.assertEqual(summary["newly_actionable_closure_count"], 0)
        self.assertFalse(summary["discrepancy_closure_complete"])
        self.assertTrue(summary["private_diagnostic_handoff_ready"])

    def test_bucket_counts_stay_public_safe_and_aggregate_only(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["ambiguous_selection_required_count"], 24)
        self.assertEqual(summary["authoritative_source_reference_required_count"], 40)
        self.assertEqual(summary["formula_or_non_numeric_mapping_required_count"], 8)
        self.assertEqual(summary["unsupported_manual_triage_required_count"], 0)
        self.assertEqual(summary["mandatory_owner_or_authorized_delegate_resolution_count"], 72)

    def test_does_not_mutate_source_private_inputs(self) -> None:
        self.assertEqual(self.source_snapshot, self._snapshot_artifacts(SOURCE_INPUT_PATHS))
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["source_private_residual_queue_read_by_this_phase"])
        self.assertFalse(boundary["source_private_residual_queue_mutated_by_this_phase"])
        self.assertFalse(boundary["source_private_residual_report_mutated_by_this_phase"])

    def test_keeps_raw_and_downstream_gates_closed(self) -> None:
        summary = self.result["summary"]
        boundary = summary["raw_boundary"]
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])
        self.assertFalse(summary["source_map_correction_ready"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_validator_accepts_private_report(self) -> None:
        manifest = validate(require_private_report=True)
        summary = manifest["summary"]
        self.assertEqual(summary["open_residual_difference_count"], 72)
        self.assertEqual(summary["closed_discrepancy_count"], 0)


if __name__ == "__main__":
    unittest.main()
