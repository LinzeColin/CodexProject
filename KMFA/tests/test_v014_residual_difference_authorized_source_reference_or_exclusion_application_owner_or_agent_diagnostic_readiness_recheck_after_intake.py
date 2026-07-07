from __future__ import annotations

import json
import unittest
from pathlib import Path

from KMFA.tools import (
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_readiness_recheck_after_intake
    as generator,
)
from KMFA.tools.check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_diagnostic_readiness_recheck_after_intake import (
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
    generator.SOURCE_PRIVATE_RESPONSE_TEMPLATE_PATH,
    generator.SOURCE_PRIVATE_PENDING_QUEUE_PATH,
    generator.SOURCE_PRIVATE_DIAGNOSTIC_PATH,
    generator.SOURCE_PRIVATE_REPORT_PATH,
]


class AuthorizedSourceReferenceOrExclusionApplicationOwnerOrAgentDiagnosticReadinessRecheckAfterIntakeTest(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_snapshot = cls._snapshot_artifacts(SOURCE_INPUT_PATHS)
        cls.artifact_snapshot = cls._snapshot_artifacts(ARTIFACT_PATHS)
        cls.result = generator.generate(
            generated_at="2026-07-08T00:00:00+10:00",
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
        self.assertEqual(summary["source_phase_id"], generator.source_intake.PHASE_ID)
        self.assertEqual(summary["source_private_response_template_item_count"], 48)
        self.assertEqual(summary["source_private_pending_queue_item_count"], 48)
        self.assertEqual(summary["source_pending_diagnostic_response_count"], 48)
        self.assertEqual(summary["source_valid_diagnostic_response_count"], 0)
        self.assertEqual(summary["source_actionable_resolution_count"], 0)

    def test_recheck_keeps_all_items_blocked(self) -> None:
        summary = self.result["summary"]
        self.assertTrue(summary["diagnostic_readiness_recheck_performed"])
        self.assertEqual(summary["diagnostic_response_ready_count"], 0)
        self.assertEqual(summary["diagnostic_response_blocker_count"], 48)
        self.assertEqual(summary["private_readiness_blocker_queue_item_count"], 48)
        self.assertEqual(summary["pending_diagnostic_response_count"], 48)
        self.assertEqual(summary["valid_diagnostic_response_count"], 0)
        self.assertEqual(summary["invalid_diagnostic_response_count"], 0)
        self.assertEqual(summary["actionable_resolution_count"], 0)
        self.assertEqual(summary["binding_ready_after_readiness_recheck_count"], 0)
        self.assertEqual(summary["comparison_retry_ready_after_readiness_recheck_count"], 0)
        self.assertEqual(summary["unresolved_difference_count"], 72)

    def test_diagnostic_kind_counts_stay_locked(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["source_reference_or_owner_exclusion_readiness_blocker_count"], 40)
        self.assertEqual(summary["formula_or_non_numeric_mapping_readiness_blocker_count"], 8)

    def test_private_blocker_queue_contains_only_pending_blockers(self) -> None:
        rows = [
            json.loads(line)
            for line in generator.PRIVATE_BLOCKER_QUEUE_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(rows), 48)
        self.assertTrue(all(row["blocker_code"] == "missing_valid_owner_or_agent_diagnostic_response" for row in rows))
        self.assertTrue(all(row["response_status"] == "pending_owner_or_external_agent" for row in rows))
        self.assertTrue(all(row["valid_diagnostic_response"] is False for row in rows))
        self.assertTrue(all(row["actionable_resolution_ready"] is False for row in rows))
        self.assertTrue(all(row["binding_ready_after_response"] is False for row in rows))
        self.assertTrue(all(row["comparison_retry_ready_after_response"] is False for row in rows))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in rows))

    def test_does_not_mutate_source_private_inputs_or_raw_inbox(self) -> None:
        self.assertEqual(self.source_snapshot, self._snapshot_artifacts(SOURCE_INPUT_PATHS))
        boundary = self.result["summary"]["raw_boundary"]
        self.assertTrue(boundary["source_private_response_template_read_by_this_phase"])
        self.assertFalse(boundary["source_private_response_template_mutated_by_this_phase"])
        self.assertFalse(boundary["source_private_pending_queue_mutated_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

    def test_keeps_downstream_gates_closed(self) -> None:
        summary = self.result["summary"]
        for key in (
            "owner_or_agent_valid_response_supplied",
            "authoritative_binding_application_ready",
            "authoritative_binding_applied_by_this_phase",
            "raw_candidate_fingerprint_bound_by_this_phase",
            "raw_to_processed_value_comparison_ready",
            "raw_to_processed_value_comparison_performed_by_this_phase",
            "full_raw_to_processed_value_comparison_complete",
            "business_value_consistency_verified",
            "github_upload_performed",
            "app_reinstall_performed",
            "business_execution_performed",
        ):
            self.assertFalse(summary[key], key)

    def test_validator_accepts_private_readiness_recheck(self) -> None:
        manifest = validate(require_private_readiness=True)
        summary = manifest["summary"]
        self.assertEqual(summary["diagnostic_response_ready_count"], 0)
        self.assertEqual(summary["diagnostic_response_blocker_count"], 48)
        self.assertEqual(summary["binding_ready_after_readiness_recheck_count"], 0)


if __name__ == "__main__":
    unittest.main()
