from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


GENERATOR_MODULE = "KMFA.tools.v014_s18_p3_post_remediation_integration_preparation"
CHECKER_MODULE = "KMFA.tools.check_v014_s18_p3_post_remediation_integration_preparation"
IMPLEMENTATION_EXISTS = (
    importlib.util.find_spec(GENERATOR_MODULE) is not None
    and importlib.util.find_spec(CHECKER_MODULE) is not None
)


class V014S18P3PostRemediationIntegrationPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not IMPLEMENTATION_EXISTS:
            return
        from KMFA.tools import v014_s18_p3_post_remediation_integration_preparation as phase
        from KMFA.tools.check_v014_s18_p3_post_remediation_integration_preparation import (
            validate_v014_s18_p3_post_remediation_integration_preparation,
        )

        cls.phase = phase
        cls.manifest = validate_v014_s18_p3_post_remediation_integration_preparation(
            require_private_evidence=True,
            require_final_evidence=True,
        )
        cls.summary = cls.manifest["summary"]
        cls.connectors = phase._read_jsonl(phase.CONNECTOR_PLAN_PATH)
        cls.opme = phase._read_json(phase.OPME_PLAN_PATH)
        cls.backlog = phase._read_jsonl(phase.BACKLOG_PATH)
        cls.acceptance = phase._read_json(phase.ACCEPTANCE_MATRIX_PATH)
        cls.go_no_go = phase._read_json(phase.GO_NO_GO_PATH)

    def test_implementation_exists(self) -> None:
        self.assertTrue(IMPLEMENTATION_EXISTS, "current S18-P3 generator/checker not written yet")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_current_s18_p2_dependency_and_historical_s18_p3_are_quarantined(self) -> None:
        dependency = self.manifest["s18_p2_dependency"]
        self.assertEqual(
            dependency["phase_id"],
            "V014_S18_P2_POST_REMEDIATION_FULL_REGRESSION_ACCEPTANCE",
        )
        self.assertTrue(dependency["validated"])
        self.assertEqual(dependency["decision"], "NO_GO")
        self.assertTrue(self.manifest["historical_s18_p3_structural_baseline_validated"])
        self.assertFalse(self.manifest["historical_s18_p3_dynamic_state_authoritative"])
        self.assertEqual(self.manifest["taskpack_contract"]["roadmap_phase_id"], "S18-P3")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_three_future_connectors_are_read_only_proposals(self) -> None:
        self.assertEqual(
            [row["connector_id"] for row in self.connectors],
            list(self.phase.REQUIRED_CONNECTOR_IDS),
        )
        self.assertEqual(len(self.connectors), 3)
        for row in self.connectors:
            self.assertEqual(row["integration_mode"], "read_only_future_connector")
            self.assertEqual(row["lifecycle_state"], "proposal_only_not_authorized")
            self.assertEqual(row["authorization_state"], "not_requested_in_this_phase")
            self.assertEqual(row["connection_state"], "not_connected")
            for key in (
                "owner_authorization_required",
                "private_runtime_only",
                "hash_manifest_required",
                "schema_contract_required",
                "idempotency_key_required",
                "rollback_required",
            ):
                self.assertTrue(row[key], f"{row['connector_id']}.{key}")
            for key in (
                "polling_enabled",
                "source_mutation_allowed",
                "writeback_allowed",
                "auto_write_allowed",
                "credential_required_now",
                "credential_material_present",
                "live_connector_called",
                "external_service_called",
                "raw_business_data_used",
                "raw_business_data_committed",
                "field_plaintext_committed",
                "github_upload_allowed",
                "business_execution_allowed",
            ):
                self.assertFalse(row[key], f"{row['connector_id']}.{key}")

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_opme_plan_is_light_entry_and_public_safe_status_only(self) -> None:
        self.assertEqual(self.opme["integration_mode"], "entry_link_and_status_index_only")
        self.assertEqual(self.opme["coupling_level"], "light_entry_only")
        self.assertEqual(
            tuple(self.opme["entry_surfaces"]),
            self.phase.REQUIRED_OPME_ENTRY_SURFACES,
        )
        self.assertEqual(
            tuple(self.opme["allowed_exchange_refs"]),
            self.phase.REQUIRED_OPME_EXCHANGE_REFS,
        )
        for key in (
            "deep_coupling_allowed",
            "shared_database_allowed",
            "shared_runtime_logic_allowed",
            "sensitive_data_mixing_allowed",
            "opme_controls_kmfa_business_logic",
            "kmfa_controls_opme_service_logic",
            "raw_business_data_exposed",
            "field_plaintext_exposed",
            "credential_material_present",
            "external_service_called",
            "github_upload_allowed",
            "business_execution_allowed",
        ):
            self.assertFalse(self.opme[key], key)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_next_stage_backlog_is_ordered_and_not_started(self) -> None:
        self.assertEqual(
            [row["backlog_id"] for row in self.backlog],
            list(self.phase.REQUIRED_BACKLOG_IDS),
        )
        self.assertEqual([row["priority"] for row in self.backlog], list(range(1, 7)))
        for row in self.backlog:
            self.assertEqual(row["status"], "backlog_proposed_not_started")
            for key in (
                "started",
                "external_connector_allowed",
                "persistent_write_allowed",
                "business_execution_allowed",
                "github_upload_allowed",
                "app_reinstall_allowed",
                "raw_business_data_required_in_public_repo",
            ):
                self.assertFalse(row[key], f"{row['backlog_id']}.{key}")
        self.assertEqual(
            self.manifest["completion_gate_sequence"],
            [
                "S18_STAGE_REVIEW_AND_FINDING_FIX",
                "V014_FINAL_OVERALL_REVIEW_AND_FINDING_FIX",
                "ONE_TIME_GITHUB_MAIN_UPLOAD",
                "APP_ENTRY_REINSTALL_AND_PARITY_VERIFICATION",
            ],
        )

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_current_go_no_go_keeps_all_delivery_gates_closed(self) -> None:
        self.assertEqual(self.go_no_go["decision"], "NO_GO")
        self.assertEqual(self.go_no_go["maximum_report_grade"], "D")
        for blocker in (
            "LINEAGE_FULL_CHECK_NOT_COMPLETE",
            "OPEN_RECONCILIATION_REMAINS",
            "OFFICIAL_REPORT_RELEASE_NOT_ALLOWED",
            "STAGE18_REVIEW_PENDING",
            "FINAL_OVERALL_REVIEW_PENDING",
            "GITHUB_MAIN_UPLOAD_DEFERRED",
            "APP_REINSTALL_DEFERRED",
        ):
            self.assertIn(blocker, self.go_no_go["blocker_ids"])
        self.assertNotIn("S18_P3_PENDING", self.go_no_go["blocker_ids"])
        for key, value in self.go_no_go.items():
            if key.endswith("_allowed") or key.endswith("_performed"):
                self.assertFalse(value, key)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_raw_snapshot_and_reconciliation_truth_remain_unchanged(self) -> None:
        self.assertEqual(self.summary["raw_source_file_count"], 5)
        self.assertTrue(self.summary["raw_snapshot_exact_match"])
        self.assertTrue(self.summary["raw_cross_phase_snapshot_exact_match"])
        self.assertFalse(self.summary["raw_business_content_used_for_integration_plan"])
        self.assertEqual(self.summary["open_final_difference_accepted_count"], 3)
        self.assertEqual(self.summary["nonzero_delta_reconciliation_count"], 9)
        self.assertEqual(self.summary["zero_delta_reconciliation_count"], 2)
        self.assertEqual(self.summary["incomplete_reconciliation_count"], 1)
        self.assertEqual(self.summary["current_data_quality_grade"], "Q4")
        self.assertEqual(self.summary["current_report_grade"], "D")
        self.assertEqual(self.summary["decision"], "NO_GO")
        self.assertTrue(self.summary["s18_p3_performed"])
        self.assertFalse(self.summary["stage18_review_performed"])

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_tampering_with_readonly_or_phase_boundaries_is_rejected(self) -> None:
        bundle = {
            "summary": copy.deepcopy(self.summary),
            "connectors": copy.deepcopy(self.connectors),
            "opme": copy.deepcopy(self.opme),
            "backlog": copy.deepcopy(self.backlog),
            "go_no_go": copy.deepcopy(self.go_no_go),
        }
        bad_connector = copy.deepcopy(bundle)
        bad_connector["connectors"][0]["writeback_allowed"] = True
        with self.assertRaises(ValueError):
            self.phase.validate_integration_bundle(bad_connector)

        bad_opme = copy.deepcopy(bundle)
        bad_opme["opme"]["shared_database_allowed"] = True
        with self.assertRaises(ValueError):
            self.phase.validate_integration_bundle(bad_opme)

        bad_backlog = copy.deepcopy(bundle)
        bad_backlog["backlog"][0]["started"] = True
        with self.assertRaises(ValueError):
            self.phase.validate_integration_bundle(bad_backlog)

        bad_scope = copy.deepcopy(bundle)
        bad_scope["summary"]["stage18_review_performed"] = True
        with self.assertRaises(ValueError):
            self.phase.validate_integration_bundle(bad_scope)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_public_mirrors_acceptance_and_private_evidence_are_complete(self) -> None:
        self.assertEqual(self.phase._read_json(self.phase.METADATA_MANIFEST_PATH), self.manifest)
        self.assertEqual(self.phase._read_jsonl(self.phase.METADATA_CONNECTOR_PLAN_PATH), self.connectors)
        self.assertEqual(self.phase._read_json(self.phase.METADATA_OPME_PLAN_PATH), self.opme)
        self.assertEqual(self.phase._read_jsonl(self.phase.METADATA_BACKLOG_PATH), self.backlog)
        self.assertEqual(self.phase._read_json(self.phase.METADATA_GO_NO_GO_PATH), self.go_no_go)
        self.assertEqual(self.acceptance["check_fail_count"], 0)
        self.assertEqual(self.acceptance["check_pass_count"], self.acceptance["check_count"])
        self.assertGreaterEqual(self.acceptance["check_count"], 24)
        self.assertTrue(self.phase.PRIVATE_RAW_BEFORE_PATH.is_file())
        self.assertTrue(self.phase.PRIVATE_RAW_AFTER_PATH.is_file())
        payload = json.dumps(
            [self.manifest, self.connectors, self.opme, self.backlog, self.go_no_go],
            ensure_ascii=False,
        )
        for token in self.phase.FORBIDDEN_PUBLIC_TEXT:
            self.assertNotIn(token, payload)

    @unittest.skipUnless(IMPLEMENTATION_EXISTS, "implementation not written yet")
    def test_governance_history_and_next_run_boundary_are_locked(self) -> None:
        for path in (
            self.phase.DEVELOPMENT_EVENTS_PATH,
            self.phase.STAGE_STATUS_PATH,
            self.phase.TASK_STATUS_PATH,
        ):
            rows = self.phase._read_jsonl(path)
            self.assertEqual(sum(row.get("phase_id") == self.phase.PHASE_ID for row in rows), 1)
            self.assertEqual(sum(row.get("phase_id") == self.phase.s18_p2.PHASE_ID for row in rows), 1)
        version_matrix = Path("KMFA/docs/governance/VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        if f'current_phase: "{self.phase.PHASE_ID}"' in version_matrix:
            handoff = Path("KMFA/HANDOFF.md").read_text(encoding="utf-8")
            self.assertIn("下一步只能执行 Stage 18 整体复审", handoff)
            self.assertIn("不得执行最终整体复审", handoff)
            self.assertIn("不得执行 GitHub upload", handoff)
        self.assertEqual(self.manifest["next_phase"], "S18_STAGE_REVIEW")


if __name__ == "__main__":
    unittest.main()
