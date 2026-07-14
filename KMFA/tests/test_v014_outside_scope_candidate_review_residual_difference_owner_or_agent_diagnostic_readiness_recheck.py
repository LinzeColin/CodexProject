from __future__ import annotations

import json
import unittest
from pathlib import Path

from KMFA.tools import (
    v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck as generator,
)
from KMFA.tools.check_v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_readiness_recheck import (
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
    generator.PRIVATE_READINESS_DIAGNOSTIC_PATH,
    generator.PRIVATE_BLOCKER_QUEUE_PATH,
    generator.PRIVATE_READINESS_REPORT_PATH,
]

SOURCE_INPUT_PATHS = [
    generator.SOURCE_PRIVATE_TEMPLATE_PATH,
    generator.SOURCE_PRIVATE_PENDING_QUEUE_PATH,
    generator.SOURCE_PRIVATE_DIAGNOSTIC_PATH,
    generator.SOURCE_PRIVATE_REPORT_PATH,
]


class OutsideScopeCandidateReviewResidualDifferenceOwnerOrAgentDiagnosticReadinessRecheckTest(unittest.TestCase):
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

    def test_recheck_preserves_source_intake_counts(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(
            summary["source_phase_id"],
            "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_INTAKE",
        )
        self.assertEqual(summary["source_private_diagnostic_response_template_item_count"], 72)
        self.assertEqual(summary["source_private_diagnostic_pending_queue_item_count"], 72)
        self.assertEqual(summary["source_pending_diagnostic_response_count"], 72)
        self.assertEqual(summary["source_valid_diagnostic_response_count"], 0)
        self.assertEqual(summary["source_actionable_resolution_count"], 0)

    def test_recheck_keeps_all_items_blocked(self) -> None:
        summary = self.result["summary"]
        self.assertTrue(summary["diagnostic_readiness_recheck_performed"])
        self.assertEqual(summary["diagnostic_response_ready_count"], 0)
        self.assertEqual(summary["diagnostic_response_blocker_count"], 72)
        self.assertEqual(summary["private_readiness_blocker_queue_item_count"], 72)
        self.assertEqual(summary["pending_diagnostic_response_count"], 72)
        self.assertEqual(summary["valid_diagnostic_response_count"], 0)
        self.assertEqual(summary["invalid_diagnostic_response_count"], 0)
        self.assertEqual(summary["actionable_resolution_count"], 0)
        self.assertEqual(summary["open_residual_difference_count"], 72)
        self.assertEqual(summary["closed_discrepancy_count"], 0)
        self.assertEqual(summary["safe_auto_resolution_count"], 0)

    def test_track_counts_stay_locked(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["owner_select_one_authoritative_candidate_count"], 24)
        self.assertEqual(summary["provide_authoritative_source_reference_or_owner_exclusion_count"], 40)
        self.assertEqual(summary["provide_formula_or_non_numeric_mapping_count"], 8)

    def test_private_blocker_queue_contains_only_pending_blockers(self) -> None:
        rows = [
            json.loads(line)
            for line in generator.PRIVATE_BLOCKER_QUEUE_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(rows), 72)
        self.assertTrue(all(row["blocker_code"] == "missing_valid_owner_or_agent_diagnostic_response" for row in rows))
        self.assertTrue(all(row["response_status"] == "pending_owner_or_external_agent" for row in rows))
        self.assertTrue(all(row["valid_diagnostic_response"] is False for row in rows))
        self.assertTrue(all(row["actionable_resolution_ready"] is False for row in rows))
        self.assertTrue(all(row["source_map_correction_ready_after_recheck"] is False for row in rows))
        self.assertTrue(all(row["discrepancy_closed_by_this_phase"] is False for row in rows))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in rows))

    def test_does_not_mutate_source_private_inputs(self) -> None:
        self.assertEqual(self.source_snapshot, self._snapshot_artifacts(SOURCE_INPUT_PATHS))
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["source_private_diagnostic_response_template_read_by_this_phase"])
        self.assertFalse(boundary["source_private_diagnostic_response_template_mutated_by_this_phase"])
        self.assertFalse(boundary["source_private_diagnostic_pending_queue_mutated_by_this_phase"])

    def test_keeps_raw_and_downstream_gates_closed(self) -> None:
        summary = self.result["summary"]
        boundary = summary["raw_boundary"]
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])
        self.assertFalse(summary["owner_or_agent_valid_response_supplied"])
        self.assertFalse(summary["source_map_correction_ready"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_validator_accepts_private_readiness_recheck(self) -> None:
        manifest = validate(require_private_readiness=True)
        summary = manifest["summary"]
        self.assertEqual(summary["diagnostic_response_ready_count"], 0)
        self.assertEqual(summary["diagnostic_response_blocker_count"], 72)
        self.assertEqual(summary["closed_discrepancy_count"], 0)


if __name__ == "__main__":
    unittest.main()
