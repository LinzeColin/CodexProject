from __future__ import annotations

import unittest
from pathlib import Path

from KMFA.tools import v014_outside_scope_candidate_review_intake_readiness_recheck as generator
from KMFA.tools.check_v014_outside_scope_candidate_review_intake_readiness_recheck import validate


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
]

SOURCE_INPUT_PATHS = [
    generator.SOURCE_SUMMARY_PATH,
    generator.SOURCE_MANIFEST_PATH,
    generator.SOURCE_PRIVATE_RESPONSE_RECORD_PATH,
    generator.SOURCE_PRIVATE_RESPONSE_ITEMS_PATH,
    generator.SOURCE_PRIVATE_DIAGNOSTIC_PATH,
]


class OutsideScopeCandidateReviewIntakeReadinessRecheckTest(unittest.TestCase):
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

    def test_recheck_preserves_expected_counts(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_phase_id"], "V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_AFTER_PACKET")
        self.assertEqual(summary["delegated_decision_record_count"], 72)
        self.assertEqual(summary["delegated_keep_pending_response_count"], 72)
        self.assertEqual(summary["selected_private_candidate_count"], 0)
        self.assertEqual(summary["corrected_source_map_reference_count"], 0)
        self.assertEqual(summary["source_map_actionable_response_count"], 0)

    def test_does_not_mutate_prior_private_response(self) -> None:
        self.assertEqual(self.source_snapshot, self._snapshot_artifacts(SOURCE_INPUT_PATHS))
        boundary = self.result["summary"]["raw_boundary"]
        self.assertFalse(boundary["source_private_delegated_response_record_mutated_by_this_phase"])
        self.assertFalse(boundary["source_private_delegated_response_items_mutated_by_this_phase"])
        self.assertFalse(boundary["source_private_delegated_response_diagnostic_mutated_by_this_phase"])

    def test_keeps_source_map_and_downstream_gates_closed(self) -> None:
        summary = self.result["summary"]
        self.assertFalse(summary["source_map_correction_ready"])
        self.assertFalse(summary["source_map_correction_feasible_after_intake"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_ready"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_blocked_threshold_not_met_on_first_recheck(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["review_intake_blocker_observation_count"], 1)
        self.assertFalse(summary["review_intake_blocked_audit_threshold_met"])
        self.assertEqual(summary["goal_status_recommendation"], "continue_waiting_for_actionable_source_map_response")

    def test_raw_inbox_is_not_accessed(self) -> None:
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["raw_data_root_readonly_policy_active"])
        self.assertTrue(boundary["source_private_delegated_response_record_read_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_hash_or_value_fingerprint_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_validator_accepts_private_diagnostic(self) -> None:
        manifest = validate(require_private_diagnostic=True)
        summary = manifest["summary"]
        self.assertEqual(summary["delegated_keep_pending_response_count"], 72)
        self.assertFalse(summary["source_map_correction_ready"])


if __name__ == "__main__":
    unittest.main()
