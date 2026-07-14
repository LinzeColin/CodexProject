from __future__ import annotations

import json
import unittest
from pathlib import Path

from KMFA.tools import (
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_actionability_blocker_final_threshold_recheck
    as source_final_threshold,
)
from KMFA.tools import (
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_blocked_handoff_after_final_threshold
    as generator,
)
from KMFA.tools.check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_generated_diagnostic_response_blocked_handoff_after_final_threshold import (
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
    generator.PRIVATE_BLOCKED_HANDOFF_DIAGNOSTIC_PATH,
    generator.PRIVATE_BLOCKED_HANDOFF_RECORDS_PATH,
    generator.PRIVATE_OWNER_ACTION_QUEUE_PATH,
    generator.PRIVATE_BLOCKED_HANDOFF_REPORT_PATH,
]

SOURCE_INPUT_PATHS = [
    generator.SOURCE_FINAL_THRESHOLD_SUMMARY_PATH,
    generator.SOURCE_FINAL_THRESHOLD_MANIFEST_PATH,
    generator.SOURCE_FINAL_THRESHOLD_GO_NO_GO_PATH,
    generator.SOURCE_FINAL_THRESHOLD_MATRIX_PATH,
    generator.SOURCE_PRIVATE_ACTIONABILITY_FINAL_THRESHOLD_DIAGNOSTIC_PATH,
    generator.SOURCE_PRIVATE_ACTIONABILITY_FINAL_THRESHOLD_RECORDS_PATH,
    generator.SOURCE_PRIVATE_ACTIONABILITY_FINAL_THRESHOLD_REPORT_PATH,
]


class AuthorizedSourceReferenceOrExclusionApplicationOwnerOrAgentBlockedHandoffAfterFinalThresholdTest(
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

    def test_blocked_handoff_counts_are_public_safe_and_locked(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_phase_id"], source_final_threshold.PHASE_ID)
        self.assertEqual(summary["source_actionability_blocker_final_threshold_recheck_item_count"], 48)
        self.assertEqual(summary["source_actionability_blocker_count"], 48)
        self.assertEqual(summary["source_private_actionability_final_threshold_records_item_count"], 48)
        self.assertEqual(summary["blocked_handoff_item_count"], 48)
        self.assertEqual(summary["owner_action_item_count"], 48)
        self.assertEqual(summary["goal_status_recommendation"], "blocked")
        self.assertTrue(summary["actionability_blocked_audit_threshold_met"])
        self.assertEqual(summary["actionability_ready_count"], 0)
        self.assertEqual(summary["actionability_blocker_count"], 48)
        self.assertEqual(summary["valid_diagnostic_response_count"], 48)
        self.assertEqual(summary["actionable_resolution_count"], 0)
        self.assertEqual(summary["source_reference_or_owner_exclusion_owner_action_count"], 40)
        self.assertEqual(summary["formula_or_non_numeric_mapping_owner_action_count"], 8)
        self.assertEqual(summary["binding_ready_after_blocked_handoff_count"], 0)
        self.assertEqual(summary["comparison_retry_ready_after_blocked_handoff_count"], 0)
        self.assertEqual(summary["unresolved_difference_count"], 72)

    def test_private_handoff_and_owner_action_queue_remain_blocked(self) -> None:
        handoff_rows = self._read_jsonl(generator.PRIVATE_BLOCKED_HANDOFF_RECORDS_PATH)
        owner_action_rows = self._read_jsonl(generator.PRIVATE_OWNER_ACTION_QUEUE_PATH)
        self.assertEqual(len(handoff_rows), 48)
        self.assertEqual(len(owner_action_rows), 48)
        self.assertTrue(
            all(
                row["blocked_handoff_status"]
                == "blocked_after_final_threshold_requires_owner_or_authorized_agent_action"
                for row in handoff_rows
            )
        )
        self.assertTrue(
            all(row["owner_action_status"] == "required_before_binding_or_value_comparison" for row in owner_action_rows)
        )
        self.assertTrue(all(row["owner_action_required"] is True for row in handoff_rows))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in handoff_rows))
        self.assertTrue(all(row["binding_ready_after_blocked_handoff"] is False for row in handoff_rows))
        self.assertTrue(all(row["comparison_retry_ready_after_blocked_handoff"] is False for row in handoff_rows))

    def test_preserves_sources_and_raw_boundary(self) -> None:
        self.assertEqual(self.source_snapshot, self._snapshot_artifacts(SOURCE_INPUT_PATHS))
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["source_final_threshold_public_artifacts_read_by_this_phase"])
        self.assertTrue(boundary["source_private_actionability_final_threshold_records_read_by_this_phase"])
        self.assertTrue(boundary["private_blocked_handoff_records_written_by_this_phase"])
        self.assertTrue(boundary["private_owner_action_queue_written_by_this_phase"])
        self.assertFalse(boundary["source_private_actionability_final_threshold_records_mutated_by_this_phase"])
        self.assertFalse(boundary["authoritative_binding_applied_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_downstream_gates_stay_closed(self) -> None:
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
            "github_upload_performed",
            "app_reinstall_performed",
            "business_execution_performed",
        ):
            self.assertFalse(summary[key], key)

    def test_matrix_and_validator_accept_blocked_handoff_after_final_threshold(self) -> None:
        matrix = self.result["matrix"]
        self.assertEqual(matrix["check_count"], 12)
        self.assertEqual(matrix["check_pass_count"], 12)
        self.assertEqual(matrix["check_fail_count"], 0)
        self.assertTrue(self.result["summary"]["private_blocked_handoff_records_gitignored"])
        self.assertTrue(self.result["summary"]["private_owner_action_queue_gitignored"])
        manifest = validate(require_private_blocked_handoff=True)
        self.assertEqual(manifest["summary"]["blocked_handoff_item_count"], 48)
        self.assertEqual(manifest["summary"]["owner_action_item_count"], 48)
        self.assertEqual(manifest["summary"]["goal_status_recommendation"], "blocked")


if __name__ == "__main__":
    unittest.main()
