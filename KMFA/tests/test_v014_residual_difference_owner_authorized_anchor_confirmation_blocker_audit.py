from __future__ import annotations

import json
import unittest
from pathlib import Path

from KMFA.tools import (
    v014_residual_difference_owner_authorized_anchor_confirmation_blocker_audit as generator,
)
from KMFA.tools.check_v014_residual_difference_owner_authorized_anchor_confirmation_blocker_audit import (
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
    generator.PRIVATE_AUDIT_DIAGNOSTIC_PATH,
    generator.PRIVATE_AUDIT_QUEUE_PATH,
    generator.PRIVATE_AUDIT_REPORT_PATH,
]

SOURCE_INPUT_PATHS = [
    generator.SOURCE_SUMMARY_PATH,
    generator.SOURCE_MANIFEST_PATH,
    generator.SOURCE_GO_NO_GO_PATH,
    generator.SOURCE_MATRIX_PATH,
    generator.SOURCE_PRIVATE_DIFFERENCE_REPORT_PATH,
    generator.SOURCE_PRIVATE_DIAGNOSTIC_PATH,
    generator.SOURCE_PRIVATE_UNRESOLVED_QUEUE_PATH,
    generator.SOURCE_PRIVATE_CONFIRMATION_READY_QUEUE_PATH,
    generator.SOURCE_PRIVATE_REPORT_PATH,
]


class ResidualDifferenceOwnerAuthorizedAnchorBlockerAuditTest(unittest.TestCase):
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

    def test_records_first_owner_authorized_anchor_blocker_observation(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_difference_report_item_count"], 72)
        self.assertEqual(summary["source_unresolved_difference_count"], 72)
        self.assertEqual(summary["owner_authorized_anchor_blocker_count"], 72)
        self.assertEqual(summary["owner_authorized_anchor_blocker_observation_count"], 1)
        self.assertFalse(summary["owner_authorized_anchor_blocked_audit_threshold_met"])
        self.assertEqual(summary["goal_status_recommendation"], "continue_to_owner_authorized_anchor_blocker_threshold_recheck")
        self.assertEqual(summary["owner_authorized_anchor_confirmation_count"], 0)
        self.assertEqual(summary["unresolved_difference_count"], 72)

    def test_preserves_source_difference_report_inputs(self) -> None:
        self.assertEqual(self.source_snapshot, self._snapshot_artifacts(SOURCE_INPUT_PATHS))
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["source_private_difference_report_read_by_this_phase"])
        self.assertTrue(boundary["source_private_unresolved_queue_read_by_this_phase"])
        self.assertFalse(boundary["source_private_difference_report_mutated_by_this_phase"])
        self.assertFalse(boundary["source_private_unresolved_queue_mutated_by_this_phase"])

    def test_keeps_anchor_confirmation_and_downstream_gates_closed(self) -> None:
        summary = self.result["summary"]
        for key in (
            "anchor_confirmation_ready",
            "owner_authorized_anchor_confirmation_performed_by_this_phase",
            "raw_to_processed_value_comparison_ready",
            "raw_to_processed_value_comparison_performed_by_this_phase",
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

    def test_private_audit_queue_matches_unresolved_rows(self) -> None:
        source_rows = self._read_jsonl(generator.SOURCE_PRIVATE_UNRESOLVED_QUEUE_PATH)
        audit_rows = self._read_jsonl(generator.PRIVATE_AUDIT_QUEUE_PATH)
        self.assertEqual(len(source_rows), 72)
        self.assertEqual(len(audit_rows), 72)
        self.assertEqual({row["target_slot_id"] for row in source_rows}, {row["target_slot_id"] for row in audit_rows})
        self.assertTrue(all(row["anchor_confirmation_ready_after_audit"] is False for row in audit_rows))
        self.assertTrue(all(row["raw_to_processed_value_comparison_ready_after_audit"] is False for row in audit_rows))
        self.assertTrue(all(row["threshold_met_after_this_phase"] is False for row in audit_rows))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in audit_rows))

    def test_matrix_all_pass(self) -> None:
        matrix = self.result["matrix"]
        self.assertEqual(matrix["check_count"], 13)
        self.assertEqual(matrix["check_pass_count"], 13)
        self.assertEqual(matrix["check_fail_count"], 0)

    def test_validator_accepts_private_audit(self) -> None:
        manifest = validate(require_private_audit=True)
        summary = manifest["summary"]
        self.assertEqual(summary["owner_authorized_anchor_blocker_count"], 72)
        self.assertEqual(summary["owner_authorized_anchor_blocker_observation_count"], 1)
        self.assertFalse(summary["owner_authorized_anchor_blocked_audit_threshold_met"])


if __name__ == "__main__":
    unittest.main()
