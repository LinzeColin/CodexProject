from __future__ import annotations

import unittest
from pathlib import Path

from KMFA.tools import v014_outside_scope_authorized_source_map_extension_resumed_readiness_recheck as generator
from KMFA.tools.check_v014_outside_scope_authorized_source_map_extension_resumed_readiness_recheck import validate


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


class OutsideScopeAuthorizedSourceMapExtensionResumedReadinessRecheckTest(unittest.TestCase):
    def setUp(self) -> None:
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

    def test_resumed_blocker_counter_restarts_at_one(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["resumed_goal_turn_blocker_count"], 1)
        self.assertFalse(summary["resumed_blocked_audit_threshold_met"])
        self.assertEqual(summary["goal_status_recommendation"], "continue_waiting_for_owner_input")

    def test_template_still_has_no_valid_authorized_extensions(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["private_authorized_extension_template_item_count"], 72)
        self.assertEqual(summary["pending_authorized_extension_record_count"], 72)
        self.assertEqual(summary["valid_authorized_extension_record_count"], 0)
        self.assertEqual(summary["missing_authorized_extension_record_count"], 72)
        self.assertFalse(summary["source_map_extension_application_ready"])

    def test_downstream_gates_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["source_map_extension_written_by_this_phase"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(summary["full_reconciliation_allowed"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_raw_inbox_is_not_accessed(self) -> None:
        boundary = self.manifest["summary"]["raw_boundary"]
        self.assertTrue(boundary["raw_data_root_readonly_policy_active"])
        self.assertTrue(boundary["private_authorized_extension_template_read_by_this_phase"])
        self.assertFalse(boundary["private_template_mutated_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_hash_or_value_fingerprint_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_validator_accepts_resumed_recheck(self) -> None:
        manifest = validate(require_private_diagnostic=True)
        summary = manifest["summary"]
        self.assertEqual(summary["resumed_goal_turn_blocker_count"], 1)
        self.assertEqual(summary["valid_authorized_extension_record_count"], 0)


if __name__ == "__main__":
    unittest.main()
