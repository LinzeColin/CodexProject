from __future__ import annotations

import unittest
from pathlib import Path

from KMFA.tools import (
    v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry as generator,
)
from KMFA.tools.check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry import (
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
    generator.PRIVATE_RETRY_TEMPLATE_PATH,
    generator.PRIVATE_RETRY_QUEUE_PATH,
    generator.PRIVATE_RETRY_DIAGNOSTIC_PATH,
    generator.PRIVATE_RETRY_REPORT_PATH,
    generator.DEVELOPMENT_EVENTS_PATH,
]


class CorrectedSourceOrOwnerExclusionInputRetryTest(unittest.TestCase):
    def setUp(self) -> None:
        snapshot = self._snapshot_artifacts()
        self.addCleanup(self._restore_artifacts, snapshot)
        self.manifest = generator.generate(generated_at="2026-07-06T00:00:00+10:00")

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

    def test_retry_input_prepared_from_no_match_blockers(self) -> None:
        summary = self.manifest["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertTrue(summary["delegated_default_decision_applied"])
        self.assertEqual(summary["private_retry_item_count"], 36)
        self.assertEqual(summary["owner_exclusion_retry_item_count"], 36)
        self.assertEqual(summary["corrected_source_retry_item_count"], 0)
        self.assertEqual(summary["no_raw_index_fingerprint_match_count"], 36)

    def test_retry_allows_next_readiness_but_not_application(self) -> None:
        summary = self.manifest["summary"]
        self.assertTrue(summary["resolution_application_readiness_allowed_next_phase"])
        self.assertFalse(summary["resolution_application_allowed"])
        self.assertFalse(summary["resolution_application_performed_by_this_phase"])
        self.assertFalse(summary["source_map_mutation_performed_by_this_phase"])
        self.assertEqual(summary["source_map_records_applied_count"], 0)
        self.assertFalse(summary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(summary["full_reconciliation_allowed"])

    def test_retry_matrix_passes_only_retry_checks(self) -> None:
        matrix = self.manifest["matrix"]
        self.assertEqual(matrix["retry_check_count"], 6)
        self.assertEqual(matrix["retry_check_pass_count"], 6)
        self.assertEqual(matrix["retry_check_fail_count"], 0)
        self.assertTrue(matrix["all_retry_inputs_valid"])
        self.assertFalse(matrix["resolution_application_performed_by_this_phase"])
        self.assertFalse(matrix["github_upload_performed"])

    def test_raw_boundary_excludes_raw_inbox_access(self) -> None:
        boundary = self.manifest["summary"]["raw_boundary"]
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])
        self.assertTrue(boundary["private_prior_raw_matching_dry_run_read_by_this_phase"])

    def test_validator_accepts_private_retry(self) -> None:
        manifest = validate(require_private_retry=True)
        self.assertEqual(manifest["summary"]["private_retry_item_count"], 36)
        self.assertTrue(manifest["summary"]["resolution_application_readiness_allowed_next_phase"])


if __name__ == "__main__":
    unittest.main()
