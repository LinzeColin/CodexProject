from __future__ import annotations

import unittest
from pathlib import Path

from KMFA.tools import v014_residual_difference_raw_to_processed_comparison_precheck as generator
from KMFA.tools.check_v014_residual_difference_raw_to_processed_comparison_precheck import validate


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
    generator.PRIVATE_READY_RECORDS_PATH,
    generator.PRIVATE_BLOCKER_RECORDS_PATH,
    generator.PRIVATE_REPORT_PATH,
    generator.DEVELOPMENT_EVENTS_PATH,
    generator.STAGE_STATUS_PATH,
    generator.TASK_STATUS_PATH,
]
SOURCE_PATHS = [
    generator.SOURCE_MATERIALIZATION_SUMMARY_PATH,
    generator.SOURCE_MATERIALIZATION_GO_NO_GO_PATH,
    generator.SOURCE_MATERIALIZATION_MATRIX_PATH,
    generator.SOURCE_PRIVATE_DIAGNOSTIC_PATH,
    generator.SOURCE_PRIVATE_RESULT_PATH,
    generator.SOURCE_PRIVATE_MATERIALIZED_RECORDS_PATH,
    generator.SOURCE_PRIVATE_RAW_COMPARISON_INPUT_PATH,
]


class ResidualDifferenceRawToProcessedComparisonPrecheckTest(unittest.TestCase):
    def setUp(self) -> None:
        snapshot = self._snapshot_artifacts()
        self.addCleanup(self._restore_artifacts, snapshot)
        self.result = generator.generate(
            generated_at="2026-07-07T00:00:00+10:00",
            write_governance_event=False,
        )

    @staticmethod
    def _snapshot_artifacts() -> dict[Path, bytes | None]:
        snapshot: dict[Path, bytes | None] = {}
        for path in ARTIFACT_PATHS + SOURCE_PATHS:
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

    def test_precheck_blocks_formal_comparison_without_private_anchors(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_private_materialized_record_count"], 72)
        self.assertEqual(summary["source_raw_comparison_input_record_count"], 72)
        self.assertTrue(summary["raw_to_processed_value_comparison_precheck_performed_by_this_phase"])
        self.assertFalse(summary["raw_to_processed_value_comparison_precheck_passed"])
        self.assertEqual(summary["comparison_ready_record_count"], 0)
        self.assertEqual(summary["comparison_blocker_record_count"], 72)
        self.assertEqual(summary["missing_private_comparison_anchor_count"], 72)

    def test_track_counts_are_preserved(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["owner_select_one_authoritative_candidate_count"], 24)
        self.assertEqual(summary["provide_authoritative_source_reference_or_owner_exclusion_count"], 40)
        self.assertEqual(summary["provide_formula_or_non_numeric_mapping_count"], 8)
        self.assertEqual(summary["diagnostic_track_counts"], generator.EXPECTED_TRACK_COUNTS)

    def test_downstream_value_consistency_gates_remain_closed(self) -> None:
        summary = self.result["summary"]
        self.assertFalse(summary["raw_to_processed_value_comparison_ready"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(summary["full_reconciliation_allowed"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_raw_boundary_excludes_raw_inbox_access(self) -> None:
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["source_public_materialization_summary_read_by_this_phase"])
        self.assertTrue(boundary["source_private_raw_comparison_input_read_by_this_phase"])
        self.assertTrue(boundary["private_precheck_blocker_records_written_by_this_phase"])
        self.assertFalse(boundary["source_private_materialization_outputs_mutated_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_source_private_materialization_inputs_are_not_mutated(self) -> None:
        before = {path: path.read_bytes() for path in SOURCE_PATHS}
        generator.generate(generated_at="2026-07-07T00:00:00+10:00", write_governance_event=False)
        after = {path: path.read_bytes() for path in SOURCE_PATHS}
        self.assertEqual(after, before)

    def test_validator_accepts_private_precheck(self) -> None:
        manifest = validate(require_private_precheck=True)
        summary = manifest["summary"]
        self.assertEqual(summary["comparison_blocker_record_count"], 72)
        self.assertEqual(summary["comparison_ready_record_count"], 0)
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])


if __name__ == "__main__":
    unittest.main()
