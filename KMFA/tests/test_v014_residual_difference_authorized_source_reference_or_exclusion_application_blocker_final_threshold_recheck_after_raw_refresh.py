from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path

from KMFA.tools import (
    v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh
    as generator,
)
from KMFA.tools.check_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh import (
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
    generator.PRIVATE_FINAL_THRESHOLD_DIAGNOSTIC_PATH,
    generator.PRIVATE_FINAL_THRESHOLD_RECORDS_PATH,
    generator.PRIVATE_FINAL_THRESHOLD_REPORT_PATH,
]

SOURCE_INPUT_PATHS = [
    generator.SOURCE_APPLICATION_BLOCKER_THRESHOLD_SUMMARY_PATH,
    generator.SOURCE_APPLICATION_BLOCKER_THRESHOLD_MANIFEST_PATH,
    generator.SOURCE_APPLICATION_BLOCKER_THRESHOLD_GO_NO_GO_PATH,
    generator.SOURCE_APPLICATION_BLOCKER_THRESHOLD_MATRIX_PATH,
    generator.SOURCE_PRIVATE_APPLICATION_BLOCKER_THRESHOLD_DIAGNOSTIC_PATH,
    generator.SOURCE_PRIVATE_APPLICATION_BLOCKER_THRESHOLD_RECORDS_PATH,
    generator.SOURCE_PRIVATE_APPLICATION_BLOCKER_THRESHOLD_REPORT_PATH,
]


class AuthorizedSourceReferenceOrExclusionApplicationBlockerFinalThresholdRecheckAfterRawRefreshTest(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_snapshot = cls._snapshot_artifacts(SOURCE_INPUT_PATHS)
        cls.artifact_snapshot = cls._snapshot_artifacts(ARTIFACT_PATHS)
        cls.result = generator.generate(
            generated_at="2026-07-08T00:00:00+10:00",
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

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, object]]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_records_third_application_blocker_observation_and_blocks_goal(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_application_blocker_threshold_recheck_item_count"], 48)
        self.assertEqual(summary["source_application_blocker_observation_count"], 2)
        self.assertFalse(summary["source_application_blocked_audit_threshold_met"])
        self.assertEqual(summary["source_private_application_blocker_threshold_record_count"], 48)
        self.assertEqual(summary["prior_application_blocker_observation_count"], 2)
        self.assertEqual(summary["application_blocker_observation_count"], 3)
        self.assertTrue(summary["application_blocked_audit_threshold_met"])
        self.assertEqual(summary["goal_status_recommendation"], "blocked")
        self.assertEqual(summary["application_blocker_final_threshold_recheck_item_count"], 48)
        self.assertEqual(summary["source_reference_or_owner_exclusion_final_threshold_blocker_count"], 40)
        self.assertEqual(summary["formula_or_non_numeric_mapping_final_threshold_blocker_count"], 8)
        self.assertEqual(summary["binding_ready_after_final_threshold_recheck_count"], 0)
        self.assertEqual(summary["comparison_retry_ready_after_final_threshold_recheck_count"], 0)
        self.assertEqual(summary["unresolved_difference_count"], 72)

    def test_private_final_threshold_records_match_source_threshold_records(self) -> None:
        source_rows = self._read_jsonl(generator.SOURCE_PRIVATE_APPLICATION_BLOCKER_THRESHOLD_RECORDS_PATH)
        final_rows = self._read_jsonl(generator.PRIVATE_FINAL_THRESHOLD_RECORDS_PATH)
        self.assertEqual(len(source_rows), 48)
        self.assertEqual(len(final_rows), 48)
        self.assertEqual(
            {row[generator.PRIVATE_SLOT_KEY] for row in source_rows},
            {row[generator.PRIVATE_SLOT_KEY] for row in final_rows},
        )
        tracks = Counter(row["intake_track"] for row in final_rows)
        self.assertEqual(tracks[generator.SOURCE_REFERENCE_INTAKE_TRACK], 40)
        self.assertEqual(tracks[generator.FORMULA_MAPPING_INTAKE_TRACK], 8)
        self.assertTrue(
            all(
                row["final_threshold_recheck_status"]
                == "application_blocker_observation_3_strict_threshold_met_missing_authorized_resolution_application"
                for row in final_rows
            )
        )
        self.assertTrue(all(row["application_blocked_audit_threshold_met"] is True for row in final_rows))
        self.assertTrue(all(row["authoritative_resolution_application_available"] is False for row in final_rows))
        self.assertTrue(all(row["binding_ready_after_final_threshold_recheck"] is False for row in final_rows))
        self.assertTrue(all(row["comparison_retry_ready_after_final_threshold_recheck"] is False for row in final_rows))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in final_rows))

    def test_preserves_source_threshold_inputs_and_raw_boundary(self) -> None:
        self.assertEqual(self.source_snapshot, self._snapshot_artifacts(SOURCE_INPUT_PATHS))
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["source_private_application_blocker_threshold_records_read_by_this_phase"])
        self.assertFalse(boundary["source_private_application_blocker_threshold_records_mutated_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_keeps_authoritative_application_and_downstream_gates_closed(self) -> None:
        summary = self.result["summary"]
        for key in (
            "authoritative_binding_application_ready",
            "authoritative_binding_applied_by_this_phase",
            "raw_candidate_fingerprint_bound_by_this_phase",
            "raw_to_processed_value_comparison_ready",
            "raw_to_processed_value_comparison_performed_by_this_phase",
            "full_raw_to_processed_value_comparison_complete",
            "processed_consistency_verified",
            "business_value_consistency_verified",
            "full_reconciliation_allowed",
            "lineage_full_check_complete",
            "formal_report_allowed",
            "github_upload_performed",
            "app_reinstall_performed",
            "business_execution_performed",
        ):
            self.assertFalse(summary[key], key)

    def test_matrix_all_pass_and_validator_accepts_private_final_threshold(self) -> None:
        matrix = self.result["matrix"]
        self.assertEqual(matrix["check_count"], 14)
        self.assertEqual(matrix["check_pass_count"], 14)
        self.assertEqual(matrix["check_fail_count"], 0)
        manifest = validate(require_private_final_threshold=True)
        self.assertEqual(manifest["summary"]["application_blocker_final_threshold_recheck_item_count"], 48)
        self.assertEqual(manifest["summary"]["application_blocker_observation_count"], 3)
        self.assertTrue(manifest["summary"]["application_blocked_audit_threshold_met"])


if __name__ == "__main__":
    unittest.main()
