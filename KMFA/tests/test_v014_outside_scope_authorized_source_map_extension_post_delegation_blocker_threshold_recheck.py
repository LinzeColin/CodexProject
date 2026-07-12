from __future__ import annotations

import unittest
from pathlib import Path

from KMFA.tools import v014_outside_scope_authorized_source_map_extension_post_delegation_blocker_threshold_recheck as generator
from KMFA.tools.check_v014_outside_scope_authorized_source_map_extension_post_delegation_blocker_threshold_recheck import (
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
    generator.DEVELOPMENT_EVENTS_PATH,
]


class OutsideScopePostDelegationBlockerThresholdRecheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.prior_private_diagnostic_before = generator.PRIOR_PRIVATE_DIAGNOSTIC_PATH.read_bytes()
        snapshot = self._snapshot_artifacts()
        self.addCleanup(self._restore_artifacts, snapshot)
        self.manifest = generator.generate(
            generated_at="2026-07-06T00:00:00+10:00",
            write_governance_event=False,
        )

    @staticmethod
    def _snapshot_artifacts() -> dict[Path, bytes | None]:
        snapshot: dict[Path, bytes | None] = {}
        for path in ARTIFACT_PATHS:
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

    def test_records_third_post_delegation_observation(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["prior_post_delegation_blocker_observation_count"], 2)
        self.assertEqual(summary["post_delegation_blocker_observation_count"], 3)
        self.assertTrue(summary["post_delegation_blocked_audit_threshold_met"])
        self.assertEqual(summary["goal_status_recommendation"], "blocked")

    def test_delegated_keep_pending_remains_non_authorizing(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["delegated_decision_record_count"], 72)
        self.assertEqual(summary["delegated_keep_pending_decision_count"], 72)
        self.assertEqual(summary["delegated_authorize_source_map_extension_count"], 0)
        self.assertEqual(summary["delegated_application_allowed_count"], 0)
        self.assertEqual(summary["valid_authorized_extension_record_count"], 0)

    def test_downstream_gates_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["source_map_extension_application_ready"])
        self.assertFalse(summary["source_map_extension_application_feasible_after_delegated_decision"])
        self.assertFalse(summary["source_map_extension_written_by_this_phase"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(summary["processed_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_prior_private_diagnostic_is_not_mutated(self) -> None:
        self.assertEqual(generator.PRIOR_PRIVATE_DIAGNOSTIC_PATH.read_bytes(), self.prior_private_diagnostic_before)
        boundary = self.manifest["summary"]["raw_boundary"]
        self.assertTrue(boundary["prior_private_diagnostic_read_by_this_phase"])
        self.assertFalse(boundary["prior_private_diagnostic_mutated_by_this_phase"])

    def test_raw_inbox_is_not_accessed(self) -> None:
        boundary = self.manifest["summary"]["raw_boundary"]
        self.assertTrue(boundary["raw_data_root_readonly_policy_active"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_hash_or_value_fingerprint_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_validator_accepts_private_diagnostic(self) -> None:
        manifest = validate(require_private_diagnostic=True)
        summary = manifest["summary"]
        self.assertEqual(summary["post_delegation_blocker_observation_count"], 3)
        self.assertTrue(summary["post_delegation_blocked_audit_threshold_met"])


if __name__ == "__main__":
    unittest.main()
