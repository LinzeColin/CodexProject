from __future__ import annotations

import importlib
import json
import unittest
from pathlib import Path
from types import ModuleType

from KMFA.tools import (
    v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_github_upload
    as source_github_upload,
)


GENERATOR_MODULE = (
    "KMFA.tools."
    "v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "external_action_required_before_app_reinstall"
)
VALIDATOR_MODULE = (
    "KMFA.tools."
    "check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_"
    "external_action_required_before_app_reinstall"
)


class OwnerOrAuthorizedAgentExternalActionRequiredBeforeAppReinstallTest(unittest.TestCase):
    artifact_snapshot: dict[Path, bytes | None] = {}

    def _load_modules(self) -> tuple[ModuleType, ModuleType]:
        try:
            generator = importlib.import_module(GENERATOR_MODULE)
        except ModuleNotFoundError as exc:
            self.fail(f"missing app reinstall requirement generator: {exc.name}")
        try:
            validator = importlib.import_module(VALIDATOR_MODULE)
        except ModuleNotFoundError as exc:
            self.fail(f"missing app reinstall requirement validator: {exc.name}")
        return generator, validator

    @staticmethod
    def _snapshot_artifacts(paths: list[Path]) -> dict[Path, bytes | None]:
        return {path: path.read_bytes() if path.exists() else None for path in paths}

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

    def tearDown(self) -> None:
        self._restore_artifacts(self.artifact_snapshot)

    def test_external_action_required_before_app_reinstall_remains_blocked(self) -> None:
        generator, validator = self._load_modules()
        source_paths = [
            generator.SOURCE_GITHUB_UPLOAD_SUMMARY_PATH,
            generator.SOURCE_GITHUB_UPLOAD_MANIFEST_PATH,
            generator.SOURCE_GITHUB_UPLOAD_GO_NO_GO_PATH,
            generator.SOURCE_GITHUB_UPLOAD_MATRIX_PATH,
            generator.SOURCE_PRIVATE_GITHUB_UPLOAD_REQUIREMENT_DIAGNOSTIC_PATH,
            generator.SOURCE_PRIVATE_GITHUB_UPLOAD_REQUIREMENT_QUEUE_PATH,
            generator.SOURCE_PRIVATE_GITHUB_UPLOAD_REQUIREMENT_REPORT_PATH,
        ]
        artifact_paths = [
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
            generator.PRIVATE_APP_REINSTALL_REQUIREMENT_DIAGNOSTIC_PATH,
            generator.PRIVATE_APP_REINSTALL_REQUIREMENT_QUEUE_PATH,
            generator.PRIVATE_APP_REINSTALL_REQUIREMENT_REPORT_PATH,
        ]
        source_snapshot = self._snapshot_artifacts(source_paths)
        self.artifact_snapshot = self._snapshot_artifacts(artifact_paths)

        result = generator.generate(generated_at="2026-07-08T00:00:00+10:00", write_governance_event=False)
        summary = result["summary"]

        self.assertEqual(source_snapshot, self._snapshot_artifacts(source_paths))
        self.assertEqual(summary["decision"], "NO_GO")
        self.assertEqual(summary["source_phase_id"], source_github_upload.PHASE_ID)
        self.assertEqual(summary["source_github_upload_requirement_ready_count"], 0)
        self.assertEqual(summary["source_github_upload_requirement_blocker_count"], 48)
        self.assertEqual(summary["source_github_upload_requirement_required_count"], 48)
        self.assertEqual(summary["source_private_github_upload_requirement_queue_item_count"], 48)
        self.assertEqual(summary["goal_status_recommendation"], "blocked")
        self.assertEqual(summary["app_reinstall_requirement_ready_count"], 0)
        self.assertEqual(summary["app_reinstall_requirement_blocker_count"], 48)
        self.assertEqual(summary["app_reinstall_requirement_required_count"], 48)
        self.assertEqual(summary["actionable_owner_resolution_count"], 0)
        self.assertEqual(summary["source_reference_or_owner_exclusion_app_reinstall_requirement_count"], 40)
        self.assertEqual(summary["formula_or_non_numeric_mapping_app_reinstall_requirement_count"], 8)
        self.assertEqual(summary["authoritative_binding_application_ready_count"], 0)
        self.assertEqual(summary["raw_to_processed_value_comparison_ready_count"], 0)
        self.assertEqual(summary["processed_data_reconciliation_ready_count"], 0)
        self.assertEqual(summary["business_value_consistency_ready_count"], 0)
        self.assertEqual(summary["lineage_full_check_ready_count"], 0)
        self.assertEqual(summary["app_reinstall_ready_count"], 0)
        self.assertEqual(summary["unresolved_difference_count"], 72)

        rows = self._read_jsonl(generator.PRIVATE_APP_REINSTALL_REQUIREMENT_QUEUE_PATH)
        self.assertEqual(len(rows), 48)
        self.assertTrue(
            all(
                row["app_reinstall_requirement_status"]
                == "blocked_owner_or_authorized_agent_external_action_required_before_app_reinstall"
                for row in rows
            )
        )
        self.assertTrue(all(row["app_reinstall_requirement_required"] is True for row in rows))
        self.assertTrue(all(row["app_reinstall_ready"] is False for row in rows))
        self.assertTrue(all(row["app_reinstall_allowed"] is False for row in rows))
        self.assertTrue(all(row["lineage_full_check_ready"] is False for row in rows))
        self.assertTrue(all(row["lineage_full_check_performed_by_this_phase"] is False for row in rows))
        self.assertTrue(all(row["business_value_consistency_ready"] is False for row in rows))
        self.assertTrue(all(row["processed_data_reconciliation_ready"] is False for row in rows))
        self.assertTrue(all(row["raw_to_processed_value_comparison_ready"] is False for row in rows))
        self.assertTrue(all(row["public_commit_allowed"] is False for row in rows))
        self.assertIn(
            "owner/授权代理 external action required before app reinstall 队列",
            generator.PRIVATE_APP_REINSTALL_REQUIREMENT_REPORT_PATH.read_text(encoding="utf-8"),
        )

        boundary = summary["raw_boundary"]
        self.assertTrue(boundary["source_github_upload_public_artifacts_read_by_this_phase"])
        self.assertTrue(boundary["source_private_github_upload_requirement_queue_read_by_this_phase"])
        self.assertTrue(boundary["private_app_reinstall_requirement_queue_written_by_this_phase"])
        self.assertFalse(boundary["owner_or_agent_external_action_completed_by_this_phase"])
        self.assertFalse(boundary["authoritative_binding_applied_by_this_phase"])
        self.assertFalse(boundary["raw_to_processed_value_comparison_performed_by_this_phase"])
        self.assertFalse(boundary["processed_data_reconciliation_performed_by_this_phase"])
        self.assertFalse(boundary["business_value_consistency_verified_by_this_phase"])
        self.assertFalse(boundary["lineage_full_check_performed_by_this_phase"])
        self.assertFalse(boundary["app_reinstall_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_read_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_list_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_parse_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_value_extraction_performed_by_this_phase"])
        self.assertFalse(boundary["raw_inbox_mutated_by_this_phase"])

        for key in (
            "authoritative_binding_application_ready",
            "authoritative_binding_applied_by_this_phase",
            "raw_candidate_fingerprint_bound_by_this_phase",
            "raw_to_processed_value_comparison_ready",
            "raw_to_processed_value_comparison_performed_by_this_phase",
            "full_raw_to_processed_value_comparison_complete",
            "processed_data_reconciliation_ready",
            "processed_data_reconciliation_performed_by_this_phase",
            "business_value_consistency_ready",
            "business_value_consistency_verified",
            "business_value_consistency_verified_by_this_phase",
            "lineage_full_check_ready",
            "lineage_full_check_complete",
            "lineage_full_check_performed_by_this_phase",
            "app_reinstall_ready",
            "app_reinstall_allowed",
            "github_upload_performed",
            "app_reinstall_performed",
            "business_execution_performed",
        ):
            self.assertFalse(summary[key], key)

        self.assertEqual(result["matrix"]["check_count"], 12)
        self.assertEqual(result["matrix"]["check_fail_count"], 0)
        self.assertTrue(summary["private_app_reinstall_requirement_diagnostic_gitignored"])
        self.assertTrue(summary["private_app_reinstall_requirement_queue_gitignored"])
        self.assertTrue(summary["private_app_reinstall_requirement_report_gitignored"])

        manifest = validator.validate(require_private_app_reinstall_requirement=True)
        self.assertEqual(manifest["summary"]["app_reinstall_requirement_blocker_count"], 48)
        self.assertEqual(manifest["summary"]["goal_status_recommendation"], "blocked")


if __name__ == "__main__":
    unittest.main()
