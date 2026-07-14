from __future__ import annotations

import json
import unittest
from pathlib import Path

from KMFA.tools import (
    v014_residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold
    as generator,
)
from KMFA.tools.check_v014_residual_difference_authorized_source_reference_or_exclusion_application_resolution_attempt_after_final_threshold import (
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
    generator.PRIVATE_RESOLUTION_DIAGNOSTIC_PATH,
    generator.PRIVATE_RESOLUTION_RECORDS_PATH,
    generator.PRIVATE_RESOLUTION_REPORT_PATH,
]

SOURCE_INPUT_PATHS = [
    generator.SOURCE_APPLICATION_BLOCKER_FINAL_THRESHOLD_SUMMARY_PATH,
    generator.SOURCE_APPLICATION_BLOCKER_FINAL_THRESHOLD_MANIFEST_PATH,
    generator.SOURCE_APPLICATION_BLOCKER_FINAL_THRESHOLD_GO_NO_GO_PATH,
    generator.SOURCE_APPLICATION_BLOCKER_FINAL_THRESHOLD_MATRIX_PATH,
    generator.SOURCE_PRIVATE_APPLICATION_BLOCKER_FINAL_THRESHOLD_DIAGNOSTIC_PATH,
    generator.SOURCE_PRIVATE_APPLICATION_BLOCKER_FINAL_THRESHOLD_RECORDS_PATH,
    generator.SOURCE_PRIVATE_APPLICATION_BLOCKER_FINAL_THRESHOLD_REPORT_PATH,
]


class AuthorizedSourceReferenceOrExclusionApplicationResolutionAttemptAfterFinalThresholdTest(unittest.TestCase):
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

    def test_records_public_safe_application_resolution_attempt_counts(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_application_blocker_final_threshold_recheck_item_count"], 48)
        self.assertTrue(summary["source_application_blocked_audit_threshold_met"])
        self.assertEqual(summary["resolution_attempt_item_count"], 48)
        self.assertEqual(summary["active_authoritative_resolution_application_count"], 0)
        self.assertEqual(summary["auto_applied_authorized_resolution_count"], 0)
        self.assertEqual(summary["still_blocked_authorized_resolution_application_count"], 48)
        self.assertEqual(summary["source_reference_or_owner_exclusion_application_blocker_count"], 40)
        self.assertEqual(summary["formula_or_non_numeric_mapping_application_blocker_count"], 8)
        self.assertEqual(summary["binding_ready_after_resolution_attempt_count"], 0)
        self.assertEqual(summary["comparison_retry_ready_after_resolution_attempt_count"], 0)
        self.assertEqual(summary["unresolved_difference_count"], 72)

    def test_private_resolution_records_remain_blocked_without_public_values(self) -> None:
        records = self._read_jsonl(generator.PRIVATE_RESOLUTION_RECORDS_PATH)
        self.assertEqual(len(records), 48)
        self.assertTrue(
            all(row["resolution_attempt_status"] == "still_blocked_missing_authorized_resolution_application" for row in records)
        )
        self.assertTrue(all(row["active_authoritative_resolution_application_available"] is False for row in records))
        self.assertTrue(all(row["auto_applied_authorized_resolution"] is False for row in records))
        self.assertTrue(all(row["binding_ready_after_resolution_attempt"] is False for row in records))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in records))

    def test_preserves_sources_and_raw_boundary(self) -> None:
        self.assertEqual(self.source_snapshot, self._snapshot_artifacts(SOURCE_INPUT_PATHS))
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["source_application_blocker_final_threshold_public_artifacts_read_by_this_phase"])
        self.assertTrue(boundary["source_private_application_blocker_final_threshold_records_read_by_this_phase"])
        self.assertFalse(boundary["authoritative_binding_applied_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_downstream_gates_stay_closed(self) -> None:
        summary = self.result["summary"]
        for key in (
            "raw_candidate_fingerprint_bound_by_this_phase",
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

    def test_matrix_and_validator_accept_private_resolution_attempt(self) -> None:
        matrix = self.result["matrix"]
        self.assertEqual(matrix["check_count"], 15)
        self.assertEqual(matrix["check_pass_count"], 15)
        self.assertEqual(matrix["check_fail_count"], 0)
        manifest = validate(require_private_resolution=True)
        self.assertEqual(manifest["summary"]["still_blocked_authorized_resolution_application_count"], 48)
        self.assertEqual(manifest["summary"]["auto_applied_authorized_resolution_count"], 0)


if __name__ == "__main__":
    unittest.main()
