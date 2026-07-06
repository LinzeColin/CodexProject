from __future__ import annotations

import unittest
from pathlib import Path

from KMFA.tools import v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision as generator
from KMFA.tools.check_v014_outside_scope_authorized_source_map_extension_delegated_keep_pending_decision import validate


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
    generator.PRIVATE_DECISION_RECORD_PATH,
    generator.PRIVATE_DECISION_QUEUE_PATH,
    generator.PRIVATE_DIAGNOSTIC_PATH,
    generator.DEVELOPMENT_EVENTS_PATH,
]


class OutsideScopeDelegatedKeepPendingDecisionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.template_before = generator.SOURCE_TEMPLATE_PATH.read_bytes()
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

    def test_records_delegated_keep_pending_decisions(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertTrue(summary["delegated_default_decision_applied_by_this_phase"])
        self.assertEqual(summary["delegated_decision_record_count"], 72)
        self.assertEqual(summary["delegated_keep_pending_decision_count"], 72)
        self.assertEqual(summary["delegated_authorize_source_map_extension_count"], 0)

    def test_does_not_mutate_original_private_template(self) -> None:
        self.assertEqual(generator.SOURCE_TEMPLATE_PATH.read_bytes(), self.template_before)
        summary = self.manifest["summary"]
        self.assertFalse(summary["raw_boundary"]["private_template_mutated_by_this_phase"])

    def test_no_exact_candidate_match_unlocks_source_map(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["exact_source_record_ref_match_count"], 0)
        self.assertEqual(summary["exact_processed_ref_match_count"], 0)
        self.assertEqual(summary["valid_authorized_extension_record_count"], 0)
        self.assertFalse(summary["source_map_extension_application_ready"])

    def test_downstream_gates_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["source_map_extension_written_by_this_phase"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(summary["full_reconciliation_allowed"])
        self.assertFalse(summary["processed_consistency_verified"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_raw_inbox_is_not_accessed(self) -> None:
        boundary = self.manifest["summary"]["raw_boundary"]
        self.assertTrue(boundary["raw_data_root_readonly_policy_active"])
        self.assertTrue(boundary["private_authorized_extension_template_read_by_this_phase"])
        self.assertTrue(boundary["private_candidate_catalog_read_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_hash_or_value_fingerprint_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_validator_accepts_private_decision(self) -> None:
        manifest = validate(require_private_decision=True)
        summary = manifest["summary"]
        self.assertEqual(summary["delegated_decision_record_count"], 72)
        self.assertEqual(summary["delegated_keep_pending_decision_count"], 72)


if __name__ == "__main__":
    unittest.main()
