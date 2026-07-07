from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path

from KMFA.tools import (
    v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh
    as generator,
)
from KMFA.tools.check_v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh import (
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

SOURCE_INPUT_PATHS = [
    generator.SOURCE_INTAKE_SUMMARY_PATH,
    generator.SOURCE_INTAKE_MANIFEST_PATH,
    generator.SOURCE_INTAKE_GO_NO_GO_PATH,
    generator.SOURCE_INTAKE_MATRIX_PATH,
    generator.SOURCE_PRIVATE_ACTIVE_RECORD_PATH,
    generator.SOURCE_PRIVATE_INTAKE_QUEUE_PATH,
    generator.SOURCE_PRIVATE_DIAGNOSTIC_PATH,
    generator.SOURCE_PRIVATE_REPORT_PATH,
]


class AuthorizedSourceReferenceOrExclusionApplicationReadinessAfterRawRefreshTest(unittest.TestCase):
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

    def test_readiness_preserves_intake_counts_and_blocks_application(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(
            summary["version"],
            "0.1.4-residual-difference-authorized-source-reference-or-exclusion-application-readiness-after-raw-refresh",
        )
        self.assertEqual(
            summary["phase_id"],
            "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_APPLICATION_READINESS_AFTER_RAW_REFRESH",
        )
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(
            summary["source_phase_id"],
            "V014_RESIDUAL_DIFFERENCE_AUTHORIZED_SOURCE_REFERENCE_OR_EXCLUSION_INTAKE_AFTER_RAW_REFRESH",
        )
        self.assertEqual(summary["source_intake_item_count"], 48)
        self.assertEqual(summary["application_readiness_item_count"], 48)
        self.assertEqual(summary["application_ready_item_count"], 0)
        self.assertEqual(summary["application_blocker_item_count"], 48)
        self.assertEqual(summary["source_reference_or_owner_exclusion_application_blocker_count"], 40)
        self.assertEqual(summary["formula_or_non_numeric_mapping_application_blocker_count"], 8)
        self.assertEqual(summary["active_authoritative_decision_count"], 0)

    def test_private_blocker_queue_is_complete_and_non_applying(self) -> None:
        ready_rows = self._read_jsonl(generator.PRIVATE_READY_QUEUE_PATH)
        blocker_rows = self._read_jsonl(generator.PRIVATE_BLOCKER_QUEUE_PATH)
        self.assertEqual(len(ready_rows), 0)
        self.assertEqual(len(blocker_rows), 48)
        tracks = Counter(row["intake_track"] for row in blocker_rows)
        self.assertEqual(tracks["source_reference_or_owner_exclusion"], 40)
        self.assertEqual(tracks["formula_or_non_numeric_mapping"], 8)
        self.assertTrue(all(row["application_ready"] is False for row in blocker_rows))
        self.assertTrue(all(row["authoritative_binding_application_ready"] is False for row in blocker_rows))
        self.assertTrue(all(row["raw_to_processed_value_comparison_ready"] is False for row in blocker_rows))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in blocker_rows))

    def test_preserves_source_intake_artifacts_and_does_not_read_raw_inbox(self) -> None:
        self.assertEqual(self.source_snapshot, self._snapshot_artifacts(SOURCE_INPUT_PATHS))
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["source_intake_public_artifacts_read_by_this_phase"])
        self.assertTrue(boundary["source_private_intake_queue_read_by_this_phase"])
        self.assertFalse(boundary["source_private_intake_queue_mutated_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_downstream_gates_stay_closed(self) -> None:
        summary = self.result["summary"]
        for key in (
            "authoritative_binding_application_ready",
            "raw_candidate_fingerprint_bound_by_this_phase",
            "raw_to_processed_value_comparison_ready",
            "raw_to_processed_value_comparison_performed_by_this_phase",
            "full_raw_to_processed_value_comparison_complete",
            "business_value_consistency_verified",
            "lineage_full_check_complete",
            "formal_report_allowed",
            "github_upload_performed",
            "app_reinstall_performed",
            "business_execution_performed",
        ):
            self.assertFalse(summary[key], key)

    def test_matrix_and_validator_accept_private_readiness_blockers(self) -> None:
        matrix = self.result["matrix"]
        self.assertEqual(matrix["check_count"], 15)
        self.assertEqual(matrix["check_pass_count"], 15)
        self.assertEqual(matrix["check_fail_count"], 0)
        manifest = validate(require_private_readiness=True)
        self.assertEqual(manifest["summary"]["application_readiness_item_count"], 48)
        self.assertEqual(manifest["summary"]["application_blocker_item_count"], 48)


if __name__ == "__main__":
    unittest.main()
