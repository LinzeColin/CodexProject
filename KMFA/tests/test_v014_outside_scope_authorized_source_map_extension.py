from __future__ import annotations

import unittest
from pathlib import Path

from KMFA.tools import v014_outside_scope_authorized_source_map_extension as generator
from KMFA.tools.check_v014_outside_scope_authorized_source_map_extension import validate


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
    generator.PRIVATE_TEMPLATE_PATH,
    generator.PRIVATE_PENDING_QUEUE_PATH,
    generator.PRIVATE_DIAGNOSTIC_PATH,
    generator.PRIVATE_REPORT_PATH,
    generator.DEVELOPMENT_EVENTS_PATH,
]


class OutsideScopeAuthorizedSourceMapExtensionTest(unittest.TestCase):
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

    def test_template_counts(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_outside_scope_resolution_queue_count"], 72)
        self.assertEqual(summary["outside_scope_authorized_source_map_required_count"], 72)
        self.assertEqual(summary["private_authorized_extension_template_item_count"], 72)
        self.assertEqual(summary["private_authorized_extension_pending_queue_count"], 72)

    def test_authorized_input_is_not_supplied(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["owner_authorized_extension_input_present"])
        self.assertEqual(summary["owner_authorized_extension_record_count"], 0)
        self.assertEqual(summary["valid_authorized_extension_record_count"], 0)
        self.assertEqual(summary["invalid_authorized_extension_record_count"], 0)
        self.assertEqual(summary["missing_authorized_extension_record_count"], 72)
        self.assertEqual(summary["source_map_extension_applied_count"], 0)
        self.assertEqual(summary["source_map_extension_pending_count"], 72)

    def test_downstream_gates_remain_closed(self) -> None:
        summary = self.manifest["summary"]
        self.assertFalse(summary["source_map_extension_written_by_this_phase"])
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_raw_to_processed_value_comparison_complete"])
        self.assertFalse(summary["full_reconciliation_allowed"])
        self.assertFalse(summary["business_value_consistency_verified"])
        self.assertFalse(summary["lineage_full_check_complete"])
        self.assertFalse(summary["formal_report_allowed"])
        self.assertFalse(summary["github_upload_performed"])
        self.assertFalse(summary["app_reinstall_performed"])
        self.assertFalse(summary["business_execution_performed"])

    def test_raw_inbox_is_not_accessed(self) -> None:
        boundary = self.manifest["summary"]["raw_boundary"]
        self.assertTrue(boundary["raw_data_root_readonly_policy_active"])
        self.assertTrue(boundary["private_outside_scope_resolution_queue_read_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_hash_or_value_fingerprint_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_validator_accepts_private_template(self) -> None:
        manifest = validate(require_private_template=True)
        summary = manifest["summary"]
        self.assertEqual(summary["private_authorized_extension_template_item_count"], 72)
        self.assertEqual(summary["valid_authorized_extension_record_count"], 0)


if __name__ == "__main__":
    unittest.main()
