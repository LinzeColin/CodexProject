from __future__ import annotations

import json
import unittest
from pathlib import Path

from KMFA.tools import v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold as generator
from KMFA.tools.check_v014_residual_difference_raw_candidate_fingerprint_evidence_refresh_after_final_threshold import (
    validate,
)
from KMFA.tools.v014_s05_p1_a0_file_registration import RAW_INBOX, stat_snapshot


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
    generator.PRIVATE_REFRESH_DIAGNOSTIC_PATH,
    generator.PRIVATE_REFRESH_RECORDS_PATH,
    generator.PRIVATE_RAW_INDEX_PATH,
    generator.PRIVATE_REFRESH_REPORT_PATH,
]

SOURCE_INPUT_PATHS = [
    generator.SOURCE_RESOLUTION_SUMMARY_PATH,
    generator.SOURCE_RESOLUTION_MANIFEST_PATH,
    generator.SOURCE_RESOLUTION_GO_NO_GO_PATH,
    generator.SOURCE_RESOLUTION_MATRIX_PATH,
    generator.SOURCE_PRIVATE_RESOLUTION_RECORDS_PATH,
]


class RawCandidateFingerprintEvidenceRefreshAfterFinalThresholdTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_snapshot = cls._snapshot_artifacts(SOURCE_INPUT_PATHS)
        cls.artifact_snapshot = cls._snapshot_artifacts(ARTIFACT_PATHS)
        cls.raw_root_before = stat_snapshot(RAW_INBOX) if RAW_INBOX.exists() else {}
        cls.result = generator.generate(
            generated_at="2026-07-07T00:00:00+10:00",
            write_governance_event=False,
        )
        cls.raw_root_after = stat_snapshot(RAW_INBOX) if RAW_INBOX.exists() else {}

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

    def test_refresh_reads_raw_inbox_readonly_and_keeps_public_counts(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_still_blocked_raw_candidate_fingerprint_count"], 48)
        self.assertEqual(summary["refresh_item_count"], 48)
        self.assertGreater(summary["raw_numeric_candidate_count"], 0)
        self.assertGreater(summary["raw_unique_numeric_fingerprint_count"], 0)
        self.assertTrue(summary["raw_value_fingerprints_generated"])
        self.assertEqual(summary["deterministic_raw_candidate_fingerprint_match_count"], 0)
        self.assertEqual(summary["still_blocked_after_raw_refresh_count"], 48)
        self.assertEqual(summary["comparison_retry_ready_after_raw_refresh_count"], 0)

    def test_private_refresh_records_remain_blocked_without_public_values(self) -> None:
        records = self._read_jsonl(generator.PRIVATE_REFRESH_RECORDS_PATH)
        self.assertEqual(len(records), 48)
        self.assertTrue(all(row["raw_refresh_status"] == "blocked_missing_authoritative_fingerprint_pair_after_raw_refresh" for row in records))
        self.assertTrue(all(row["comparison_retry_ready_after_raw_refresh"] is False for row in records))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in records))

    def test_preserves_sources_and_raw_root_stat(self) -> None:
        self.assertEqual(self.source_snapshot, self._snapshot_artifacts(SOURCE_INPUT_PATHS))
        self.assertEqual(self.raw_root_before, self.raw_root_after)
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["user_authorized_raw_data_read_for_this_phase"])
        self.assertTrue(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertTrue(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_write_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_delete_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])
        self.assertTrue(boundary["raw_root_stat_unchanged_after_phase"])

    def test_downstream_gates_stay_closed(self) -> None:
        summary = self.result["summary"]
        for key in (
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

    def test_matrix_and_validator_accept_private_refresh(self) -> None:
        matrix = self.result["matrix"]
        self.assertEqual(matrix["check_count"], 15)
        self.assertEqual(matrix["check_pass_count"], 15)
        self.assertEqual(matrix["check_fail_count"], 0)
        manifest = validate(require_private_refresh=True)
        self.assertEqual(manifest["summary"]["still_blocked_after_raw_refresh_count"], 48)
        self.assertEqual(manifest["summary"]["comparison_retry_ready_after_raw_refresh_count"], 0)


if __name__ == "__main__":
    unittest.main()
