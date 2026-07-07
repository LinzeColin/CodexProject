from __future__ import annotations

import json
import unittest
from pathlib import Path

from KMFA.tools import (
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_audit
    as generator,
)
from KMFA.tools.check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_audit import (
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
    generator.PRIVATE_ACTIONABILITY_BLOCKER_AUDIT_DIAGNOSTIC_PATH,
    generator.PRIVATE_ACTIONABILITY_BLOCKER_AUDIT_QUEUE_PATH,
    generator.PRIVATE_ACTIONABILITY_BLOCKER_AUDIT_REPORT_PATH,
]

SOURCE_INPUT_PATHS = [
    generator.SOURCE_PUBLIC_SUMMARY_PATH,
    generator.SOURCE_PUBLIC_MANIFEST_PATH,
    generator.SOURCE_PUBLIC_GO_NO_GO_PATH,
    generator.SOURCE_PUBLIC_MATRIX_PATH,
    generator.SOURCE_PRIVATE_ACTIONABILITY_DIAGNOSTIC_PATH,
    generator.SOURCE_PRIVATE_ACTIONABILITY_BLOCKER_QUEUE_PATH,
    generator.SOURCE_PRIVATE_ACTIONABILITY_REPORT_PATH,
]


class AuthorizedSourceReferenceOrExclusionApplicationOwnerOrAgentActionabilityBlockerAuditTest(unittest.TestCase):
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

    def test_audit_records_first_actionability_blocker_observation(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_actionability_recheck_item_count"], 48)
        self.assertEqual(summary["source_actionability_ready_count"], 0)
        self.assertEqual(summary["source_actionability_blocker_count"], 48)
        self.assertEqual(summary["source_private_actionability_blocker_queue_item_count"], 48)
        self.assertEqual(summary["prior_actionability_blocker_observation_count"], 0)
        self.assertEqual(summary["actionability_blocker_observation_count"], 1)
        self.assertFalse(summary["actionability_blocked_audit_threshold_met"])
        self.assertEqual(summary["actionability_ready_count"], 0)
        self.assertEqual(summary["actionability_blocker_count"], 48)
        self.assertEqual(summary["private_audit_queue_item_count"], 48)
        self.assertEqual(summary["valid_diagnostic_response_count"], 48)
        self.assertEqual(summary["actionable_resolution_count"], 0)
        self.assertEqual(summary["source_reference_or_owner_exclusion_actionability_blocker_count"], 40)
        self.assertEqual(summary["formula_or_non_numeric_mapping_actionability_blocker_count"], 8)
        self.assertEqual(summary["binding_ready_after_actionability_blocker_audit_count"], 0)
        self.assertEqual(summary["comparison_retry_ready_after_actionability_blocker_audit_count"], 0)
        self.assertEqual(summary["unresolved_difference_count"], 72)

    def test_private_audit_queue_contains_only_blockers(self) -> None:
        rows = self._read_jsonl(generator.PRIVATE_ACTIONABILITY_BLOCKER_AUDIT_QUEUE_PATH)
        self.assertEqual(len(rows), 48)
        self.assertTrue(
            all(
                row["actionability_audit_status"]
                == "blocked_non_actionable_generated_response_actionability_audit"
                for row in rows
            )
        )
        self.assertTrue(all(row["valid_diagnostic_response"] is True for row in rows))
        self.assertTrue(all(row["actionable_resolution_ready"] is False for row in rows))
        self.assertTrue(all(row["binding_ready_after_actionability_blocker_audit"] is False for row in rows))
        self.assertTrue(all(row["comparison_retry_ready_after_actionability_blocker_audit"] is False for row in rows))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in rows))

    def test_preserves_source_private_inputs_and_raw_boundary(self) -> None:
        self.assertEqual(self.source_snapshot, self._snapshot_artifacts(SOURCE_INPUT_PATHS))
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["source_public_actionability_summary_read_by_this_phase"])
        self.assertTrue(boundary["source_private_actionability_diagnostic_read_by_this_phase"])
        self.assertTrue(boundary["source_private_actionability_blocker_queue_read_by_this_phase"])
        self.assertFalse(boundary["source_private_actionability_diagnostic_mutated_by_this_phase"])
        self.assertFalse(boundary["source_private_actionability_blocker_queue_mutated_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_keeps_downstream_gates_closed(self) -> None:
        summary = self.result["summary"]
        for key in (
            "authoritative_binding_application_ready",
            "authoritative_binding_applied_by_this_phase",
            "raw_candidate_fingerprint_bound_by_this_phase",
            "raw_to_processed_value_comparison_ready",
            "raw_to_processed_value_comparison_performed_by_this_phase",
            "full_raw_to_processed_value_comparison_complete",
            "business_value_consistency_verified",
            "github_upload_performed",
            "app_reinstall_performed",
            "business_execution_performed",
        ):
            self.assertFalse(summary[key], key)

    def test_matrix_and_validator_accept_actionability_blocker_audit(self) -> None:
        matrix = self.result["matrix"]
        self.assertEqual(matrix["check_count"], 12)
        self.assertEqual(matrix["check_pass_count"], 12)
        self.assertEqual(matrix["check_fail_count"], 0)
        self.assertTrue(self.result["summary"]["private_actionability_blocker_audit_diagnostic_gitignored"])
        self.assertTrue(self.result["summary"]["private_actionability_blocker_audit_queue_gitignored"])
        self.assertTrue(self.result["summary"]["private_actionability_blocker_audit_report_gitignored"])
        manifest = validate(require_private_audit=True)
        self.assertEqual(manifest["summary"]["actionability_blocker_count"], 48)


if __name__ == "__main__":
    unittest.main()
