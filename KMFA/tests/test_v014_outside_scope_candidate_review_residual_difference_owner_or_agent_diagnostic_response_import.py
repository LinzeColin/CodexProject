from __future__ import annotations

import json
import unittest
from pathlib import Path

from KMFA.tools import (
    v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import as generator,
)
from KMFA.tools.check_v014_outside_scope_candidate_review_residual_difference_owner_or_agent_diagnostic_response_import import (
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
    generator.PRIVATE_RESPONSE_RECORD_PATH,
    generator.PRIVATE_RESPONSE_ITEMS_PATH,
    generator.PRIVATE_NON_ACTIONABLE_QUEUE_PATH,
    generator.PRIVATE_REPORT_PATH,
]

SOURCE_INPUT_PATHS = [
    generator.SOURCE_THRESHOLD_SUMMARY_PATH,
    generator.SOURCE_THRESHOLD_MANIFEST_PATH,
    generator.SOURCE_TEMPLATE_PATH,
    generator.SOURCE_PENDING_QUEUE_PATH,
    generator.SOURCE_OWNER_AUTHORIZED_REPORT_PATH,
]


class ResidualDifferenceOwnerAgentDiagnosticResponseImportTest(unittest.TestCase):
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

    @staticmethod
    def _read_jsonl(path: Path) -> list[dict[str, object]]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_imports_all_valid_diagnostic_responses_without_closure(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_diagnostic_blocker_observation_count"], 3)
        self.assertTrue(summary["source_diagnostic_blocked_audit_threshold_met"])
        self.assertEqual(summary["source_template_item_count"], 72)
        self.assertEqual(summary["source_owner_authorized_report_item_count"], 72)
        self.assertEqual(summary["valid_diagnostic_response_imported_count"], 72)
        self.assertEqual(summary["valid_diagnostic_response_count"], 72)
        self.assertEqual(summary["pending_diagnostic_response_count"], 0)
        self.assertEqual(summary["diagnostic_response_blocker_count"], 0)
        self.assertEqual(summary["non_actionable_diagnostic_response_count"], 72)
        self.assertEqual(summary["open_residual_difference_count"], 72)
        self.assertEqual(summary["closed_discrepancy_count"], 0)

    def test_preserves_source_inputs(self) -> None:
        self.assertEqual(self.source_snapshot, self._snapshot_artifacts(SOURCE_INPUT_PATHS))
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["source_private_response_template_read_by_this_phase"])
        self.assertTrue(boundary["source_private_pending_queue_read_by_this_phase"])
        self.assertTrue(boundary["source_owner_authorized_discrepancy_report_read_by_this_phase"])
        self.assertFalse(boundary["source_private_response_template_mutated_by_this_phase"])
        self.assertFalse(boundary["source_private_pending_queue_mutated_by_this_phase"])
        self.assertFalse(boundary["source_owner_authorized_discrepancy_report_mutated_by_this_phase"])

    def test_keeps_downstream_gates_closed(self) -> None:
        summary = self.result["summary"]
        for key in (
            "source_map_correction_ready",
            "source_map_correction_written_by_this_phase",
            "raw_to_processed_value_comparison_performed_by_this_phase",
            "full_raw_to_processed_value_comparison_ready",
            "full_raw_to_processed_value_comparison_complete",
            "processed_consistency_verified",
            "business_value_consistency_verified",
            "full_reconciliation_allowed",
            "lineage_full_check_complete",
            "formal_report_allowed",
            "github_upload_performed",
            "app_reinstall_performed",
            "business_execution_performed",
        ):
            self.assertFalse(summary[key], key)

    def test_raw_inbox_is_not_accessed(self) -> None:
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["raw_data_root_readonly_policy_active"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_stat_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_private_response_rows_are_non_actionable(self) -> None:
        rows = self._read_jsonl(generator.PRIVATE_RESPONSE_ITEMS_PATH)
        non_actionable = self._read_jsonl(generator.PRIVATE_NON_ACTIONABLE_QUEUE_PATH)
        self.assertEqual(len(rows), 72)
        self.assertEqual(len(non_actionable), 72)
        self.assertTrue(all(row["valid_diagnostic_response"] is True for row in rows))
        self.assertTrue(all(row["discrepancy_report_response"] is True for row in rows))
        self.assertTrue(all(row["actionable_resolution_ready"] is False for row in rows))
        self.assertTrue(all(row["source_map_correction_ready_after_import"] is False for row in rows))
        self.assertTrue(all(row["discrepancy_closed_by_this_phase"] is False for row in rows))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in rows))

    def test_validator_accepts_private_import(self) -> None:
        manifest = validate(require_private_import=True)
        summary = manifest["summary"]
        self.assertEqual(summary["valid_diagnostic_response_count"], 72)
        self.assertEqual(summary["non_actionable_diagnostic_response_count"], 72)
        self.assertEqual(summary["closed_discrepancy_count"], 0)


if __name__ == "__main__":
    unittest.main()
