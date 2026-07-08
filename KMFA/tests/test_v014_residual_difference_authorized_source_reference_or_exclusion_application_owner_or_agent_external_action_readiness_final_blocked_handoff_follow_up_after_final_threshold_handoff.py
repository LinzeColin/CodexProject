from __future__ import annotations

import importlib
import json
import unittest
from pathlib import Path
from types import ModuleType

from KMFA.tools import (
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_final_threshold_blocked_handoff_action_readiness_after_final_threshold_handoff
    as source_readiness,
)


GENERATOR_MODULE = (
    "KMFA.tools."
    "v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "external_action_readiness_final_blocked_handoff_follow_up_after_final_threshold_handoff"
)
VALIDATOR_MODULE = (
    "KMFA.tools."
    "check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "external_action_readiness_final_blocked_handoff_follow_up_after_final_threshold_handoff"
)


class AuthorizedSourceReferenceOrExclusionApplicationOwnerOrAgentExternalActionReadinessFinalBlockedHandoffFollowUpAfterFinalThresholdHandoffTest(
    unittest.TestCase
):
    artifact_snapshot: dict[Path, bytes | None] = {}

    def _load_modules(self) -> tuple[ModuleType, ModuleType]:
        try:
            generator = importlib.import_module(GENERATOR_MODULE)
        except ModuleNotFoundError as exc:
            self.fail(f"missing external action follow-up generator: {exc.name}")
        try:
            validator = importlib.import_module(VALIDATOR_MODULE)
        except ModuleNotFoundError as exc:
            self.fail(f"missing external action follow-up validator: {exc.name}")
        return generator, validator

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

    def tearDown(self) -> None:
        self._restore_artifacts(self.artifact_snapshot)

    def test_external_action_follow_up_remains_blocked_without_owner_or_agent_actions(self) -> None:
        generator, validator = self._load_modules()
        source_paths = [
            generator.SOURCE_READINESS_SUMMARY_PATH,
            generator.SOURCE_READINESS_MANIFEST_PATH,
            generator.SOURCE_READINESS_GO_NO_GO_PATH,
            generator.SOURCE_READINESS_MATRIX_PATH,
            generator.SOURCE_PRIVATE_EXTERNAL_ACTION_READINESS_DIAGNOSTIC_PATH,
            generator.SOURCE_PRIVATE_EXTERNAL_ACTION_READINESS_BLOCKER_RECORDS_PATH,
            generator.SOURCE_PRIVATE_EXTERNAL_ACTION_READINESS_QUESTION_LIST_PATH,
        ]
        artifact_paths = [
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
            generator.PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_DIAGNOSTIC_PATH,
            generator.PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_QUEUE_PATH,
            generator.PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_REPORT_PATH,
        ]
        source_snapshot = self._snapshot_artifacts(source_paths)
        self.artifact_snapshot = self._snapshot_artifacts(artifact_paths)

        result = generator.generate(generated_at="2026-07-08T00:00:00+10:00", write_governance_event=False)
        summary = result["summary"]

        self.assertEqual(source_snapshot, self._snapshot_artifacts(source_paths))
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_phase_id"], source_readiness.PHASE_ID)
        self.assertEqual(summary["source_external_owner_action_ready_count"], 0)
        self.assertEqual(summary["source_external_owner_action_blocker_count"], 48)
        self.assertEqual(summary["source_private_external_action_readiness_blocker_records_item_count"], 48)
        self.assertEqual(summary["source_goal_status_recommendation"], "blocked")
        self.assertEqual(summary["external_action_follow_up_ready_count"], 0)
        self.assertEqual(summary["external_action_follow_up_blocker_count"], 48)
        self.assertEqual(summary["external_action_follow_up_required_count"], 48)
        self.assertEqual(summary["actionable_owner_resolution_count"], 0)
        self.assertEqual(summary["source_reference_or_owner_exclusion_follow_up_count"], 40)
        self.assertEqual(summary["formula_or_non_numeric_mapping_follow_up_count"], 8)
        self.assertEqual(summary["binding_ready_after_external_action_follow_up_count"], 0)
        self.assertEqual(summary["comparison_retry_ready_after_external_action_follow_up_count"], 0)
        self.assertEqual(summary["unresolved_difference_count"], 72)

        follow_up_rows = self._read_jsonl(generator.PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_QUEUE_PATH)
        self.assertEqual(len(follow_up_rows), 48)
        self.assertTrue(
            all(
                row["external_action_follow_up_status"]
                == "blocked_follow_up_waiting_for_owner_or_authorized_agent_external_action_after_final_threshold_handoff"
                for row in follow_up_rows
            )
        )
        self.assertTrue(all(row["external_action_follow_up_required"] is True for row in follow_up_rows))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in follow_up_rows))
        self.assertIn(
            "owner/授权代理 external action follow-up 队列",
            generator.PRIVATE_EXTERNAL_ACTION_FOLLOW_UP_REPORT_PATH.read_text(encoding="utf-8"),
        )

        boundary = summary["raw_boundary"]
        self.assertTrue(boundary["source_readiness_public_artifacts_read_by_this_phase"])
        self.assertTrue(boundary["source_private_readiness_blocker_records_read_by_this_phase"])
        self.assertFalse(boundary["owner_or_agent_external_action_completed_by_this_phase"])
        self.assertFalse(boundary["authoritative_binding_applied_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

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

        self.assertEqual(result["matrix"]["check_count"], 12)
        self.assertEqual(result["matrix"]["check_fail_count"], 0)
        self.assertTrue(summary["private_external_action_follow_up_diagnostic_gitignored"])
        self.assertTrue(summary["private_external_action_follow_up_queue_gitignored"])
        self.assertTrue(summary["private_external_action_follow_up_report_gitignored"])

        manifest = validator.validate(require_private_external_action_follow_up=True)
        self.assertEqual(manifest["summary"]["external_action_follow_up_blocker_count"], 48)
        self.assertEqual(manifest["summary"]["goal_status_recommendation"], "blocked")


if __name__ == "__main__":
    unittest.main()
