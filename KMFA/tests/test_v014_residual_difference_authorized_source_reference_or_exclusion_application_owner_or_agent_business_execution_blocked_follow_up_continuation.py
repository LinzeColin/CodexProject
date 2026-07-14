from __future__ import annotations

import importlib
import json
import unittest
from pathlib import Path
from types import ModuleType

from KMFA.tools import (
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_business_execution_blocked_follow_up_after_blocked_handoff
    as source_blocked_follow_up,
)


GENERATOR_MODULE = (
    "KMFA.tools."
    "v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "business_execution_blocked_follow_up_continuation"
)
VALIDATOR_MODULE = (
    "KMFA.tools."
    "check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "business_execution_blocked_follow_up_continuation"
)


class OwnerOrAuthorizedAgentBusinessExecutionBlockedFollowUpContinuationTest(
    unittest.TestCase
):
    artifact_snapshot: dict[Path, bytes | None] = {}

    def _load_modules(self) -> tuple[ModuleType, ModuleType]:
        try:
            generator = importlib.import_module(GENERATOR_MODULE)
        except ModuleNotFoundError as exc:
            self.fail(f"missing business execution blocked follow-up continuation generator: {exc.name}")
        try:
            validator = importlib.import_module(VALIDATOR_MODULE)
        except ModuleNotFoundError as exc:
            self.fail(f"missing business execution blocked follow-up continuation validator: {exc.name}")
        return generator, validator

    @staticmethod
    def _snapshot_artifacts(paths: list[Path]) -> dict[Path, bytes | None]:
        return {path: path.read_bytes() if path.exists() else None for path in paths}

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

    def test_blocked_follow_up_continuation_preserves_no_go_and_source_immutability(self) -> None:
        generator, validator = self._load_modules()
        source_paths = [
            generator.SOURCE_BUSINESS_EXECUTION_BLOCKED_FOLLOW_UP_SUMMARY_PATH,
            generator.SOURCE_BUSINESS_EXECUTION_BLOCKED_FOLLOW_UP_MANIFEST_PATH,
            generator.SOURCE_BUSINESS_EXECUTION_BLOCKED_FOLLOW_UP_GO_NO_GO_PATH,
            generator.SOURCE_BUSINESS_EXECUTION_BLOCKED_FOLLOW_UP_MATRIX_PATH,
            generator.SOURCE_PRIVATE_BUSINESS_EXECUTION_BLOCKED_FOLLOW_UP_DIAGNOSTIC_PATH,
            generator.SOURCE_PRIVATE_BUSINESS_EXECUTION_BLOCKED_FOLLOW_UP_QUEUE_PATH,
            generator.SOURCE_PRIVATE_BUSINESS_EXECUTION_BLOCKED_FOLLOW_UP_REPORT_PATH,
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
            generator.PRIVATE_BUSINESS_EXECUTION_BLOCKED_FOLLOW_UP_CONTINUATION_DIAGNOSTIC_PATH,
            generator.PRIVATE_BUSINESS_EXECUTION_BLOCKED_FOLLOW_UP_CONTINUATION_QUEUE_PATH,
            generator.PRIVATE_BUSINESS_EXECUTION_BLOCKED_FOLLOW_UP_CONTINUATION_REPORT_PATH,
        ]
        source_snapshot = self._snapshot_artifacts(source_paths)
        self.artifact_snapshot = self._snapshot_artifacts(artifact_paths)

        result = generator.generate(generated_at="2026-07-08T00:00:00+10:00", write_governance_event=False)
        summary = result["summary"]

        self.assertEqual(source_snapshot, self._snapshot_artifacts(source_paths))
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_phase_id"], source_blocked_follow_up.PHASE_ID)
        self.assertEqual(summary["source_business_execution_blocked_follow_up_ready_count"], 0)
        self.assertEqual(summary["source_business_execution_blocked_follow_up_blocker_count"], 48)
        self.assertEqual(summary["source_business_execution_blocked_follow_up_item_count"], 48)
        self.assertEqual(summary["source_private_business_execution_blocked_follow_up_queue_item_count"], 48)
        self.assertEqual(summary["goal_status_recommendation"], "blocked")
        self.assertEqual(summary["business_execution_blocked_follow_up_continuation_ready_count"], 0)
        self.assertEqual(summary["business_execution_blocked_follow_up_continuation_blocker_count"], 48)
        self.assertEqual(summary["business_execution_blocked_follow_up_continuation_item_count"], 48)
        self.assertEqual(summary["business_execution_blocked_follow_up_continuation_required_count"], 48)
        self.assertEqual(summary["owner_or_authorized_agent_resolution_count"], 0)
        self.assertEqual(summary["source_reference_or_owner_exclusion_business_execution_blocked_follow_up_continuation_count"], 40)
        self.assertEqual(summary["formula_or_non_numeric_mapping_business_execution_blocked_follow_up_continuation_count"], 8)
        self.assertEqual(summary["business_execution_ready_count"], 0)
        self.assertEqual(summary["unresolved_difference_count"], 72)

        rows = self._read_jsonl(generator.PRIVATE_BUSINESS_EXECUTION_BLOCKED_FOLLOW_UP_CONTINUATION_QUEUE_PATH)
        self.assertEqual(len(rows), 48)
        self.assertTrue(
            all(
                row["business_execution_blocked_follow_up_continuation_status"]
                == "blocked_owner_or_authorized_agent_business_execution_blocked_follow_up_continuation"
                for row in rows
            )
        )
        self.assertTrue(all(row["business_execution_blocked_follow_up_continuation_ready"] is False for row in rows))
        self.assertTrue(all(row["business_execution_blocked_follow_up_continuation_blocker"] is True for row in rows))
        self.assertTrue(all(row["business_execution_ready"] is False for row in rows))
        self.assertTrue(all(row["business_execution_allowed"] is False for row in rows))
        self.assertTrue(all(row["business_execution_performed_by_this_phase"] is False for row in rows))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in rows))
        self.assertIn(
            "owner/授权代理 business execution blocked follow-up continuation 队列",
            generator.PRIVATE_BUSINESS_EXECUTION_BLOCKED_FOLLOW_UP_CONTINUATION_REPORT_PATH.read_text(encoding="utf-8"),
        )

        boundary = summary["raw_boundary"]
        self.assertTrue(boundary["source_business_execution_blocked_follow_up_public_artifacts_read_by_this_phase"])
        self.assertTrue(boundary["source_private_business_execution_blocked_follow_up_queue_read_by_this_phase"])
        self.assertTrue(boundary["private_business_execution_blocked_follow_up_continuation_queue_written_by_this_phase"])
        self.assertFalse(boundary["owner_or_agent_actionable_resolution_completed_by_this_phase"])
        self.assertFalse(boundary["business_execution_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

        for key in (
            "owner_or_agent_actionable_resolution_completed_by_this_phase",
            "authoritative_binding_application_ready",
            "raw_to_processed_value_comparison_ready",
            "processed_data_reconciliation_ready",
            "business_value_consistency_ready",
            "lineage_full_check_ready",
            "github_upload_performed",
            "app_reinstall_performed",
            "business_execution_ready",
            "business_execution_allowed",
            "business_execution_performed_by_this_phase",
            "business_execution_performed",
        ):
            self.assertFalse(summary[key], key)

        self.assertEqual(result["matrix"]["check_count"], 12)
        self.assertEqual(result["matrix"]["check_fail_count"], 0)
        self.assertTrue(summary["private_business_execution_blocked_follow_up_continuation_diagnostic_gitignored"])
        self.assertTrue(summary["private_business_execution_blocked_follow_up_continuation_queue_gitignored"])
        self.assertTrue(summary["private_business_execution_blocked_follow_up_continuation_report_gitignored"])

        manifest = validator.validate(require_private_business_execution_blocked_follow_up_continuation=True)
        self.assertEqual(manifest["summary"]["business_execution_blocked_follow_up_continuation_blocker_count"], 48)
        self.assertEqual(manifest["summary"]["goal_status_recommendation"], "blocked")


if __name__ == "__main__":
    unittest.main()
