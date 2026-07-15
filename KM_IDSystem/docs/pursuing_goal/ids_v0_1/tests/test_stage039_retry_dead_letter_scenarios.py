import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
REPO_ROOT = ROOT.parent
BASE = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
CONTRACT = BASE / "retry_dead_letter" / "stage039_retry_dead_letter_scenarios.json"
EVIDENCE = BASE / "STAGE039_PHASE3_SCENARIO_VALIDATION.md"
CHECKER = ROOT / "scripts" / "check_retry_dead_letter_scenarios.py"
BATCH = BASE / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
POLICY_VERSION = "ids.retry_policy.v0_1.stage039.p2"
CONTROL_EPOCH = 1_720_000_000
EXPECTED_SCENARIOS = [
    "duplicate_retry_reservation_and_admission",
    "worker_exception_crash_boundary",
    "external_drive_offline_pending_retry_pause",
    "actual_low_disk_pending_retry_pause_without_allocation",
    "external_api_budget_pending_retry_pause",
    "same_source_cross_operation_lock",
    "retry_exhaustion_dead_letter",
    "terminal_replay_blocked",
    "manual_rerun_lineage_idempotent",
    "protected_cleanup_denied",
]


class Stage039RetryDeadLetterScenarioTests(unittest.TestCase):
    def _module(self):
        self.assertTrue(CHECKER.is_file(), f"missing Phase 3 checker: {CHECKER}")
        spec = importlib.util.spec_from_file_location(
            "stage039_retry_dead_letter_scenarios", CHECKER
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _contract(self):
        self.assertTrue(CONTRACT.is_file(), f"missing Phase 3 contract: {CONTRACT}")
        return json.loads(CONTRACT.read_text(encoding="utf-8"))

    def _report(self):
        return self._module().build_stage039_phase3_report()

    def test_phase3_artifacts_source_and_upstream_bindings_are_exact(self):
        module = self._module()
        contract = self._contract()
        self.assertTrue(EVIDENCE.is_file(), f"missing Phase 3 evidence: {EVIDENCE}")
        checks = module.validate_scenario_contract(contract)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual("IDS-V0_1-STAGE039-P3", contract["task_id"])
        self.assertEqual("ACC-STAGE-039", contract["acceptance_id"])
        self.assertEqual(POLICY_VERSION, contract["policy_version"])
        self.assertEqual(EXPECTED_SCENARIOS, contract["scenario_catalog"])
        for binding in contract["upstream_bindings"].values():
            path = REPO_ROOT / binding["ref"]
            self.assertTrue(path.is_file(), path)
            self.assertEqual(binding["sha256"], module.sha256_file(path))

    def test_contract_tampering_fails_closed_without_scenario_execution(self):
        module = self._module()
        baseline = self._contract()
        mutations = []
        for mutate in (
            lambda value: value.update({"unknown_root": True}),
            lambda value: value["scenario_catalog"].append("unknown_scenario"),
            lambda value: value["physical_action_boundary"].update(
                {"process_termination_allowed": True}
            ),
            lambda value: value["protected_artifact_contract"].update(
                {"delete_attempt_allowed": True}
            ),
            lambda value: value["truth_flags"].update(
                {"fake_ids_business_data_used": True}
            ),
        ):
            candidate = copy.deepcopy(baseline)
            mutate(candidate)
            mutations.append(candidate)
        for candidate in mutations:
            with self.subTest(candidate=candidate):
                self.assertFalse(all(module.validate_scenario_contract(candidate).values()))
                report = module.build_stage039_phase3_report(
                    contract=candidate, execute_scenarios=True
                )
                self.assertFalse(report["contract_valid"], report)
                self.assertFalse(report["scenario_runtime_performed"], report)

    def test_duplicate_retry_requests_replay_without_double_budget(self):
        scenario = self._report()["scenario_results"][
            "duplicate_retry_reservation_and_admission"
        ]
        self.assertEqual("PASS", scenario["status"], scenario)
        self.assertTrue(scenario["failure_replay_idempotent"])
        self.assertTrue(scenario["admission_replay_idempotent"])
        self.assertEqual(0, scenario["retry_count_after_reservation_replay"])
        self.assertEqual(1, scenario["retry_count_after_admission_replay"])
        self.assertEqual(2, scenario["idempotency_ledger_entry_count"])

    def test_worker_exception_is_real_but_process_crash_recovery_stays_blocked(self):
        scenario = self._report()["scenario_results"][
            "worker_exception_crash_boundary"
        ]
        self.assertEqual("PASS", scenario["status"], scenario)
        self.assertTrue(scenario["actual_worker_exception_performed"])
        self.assertFalse(scenario["process_termination_performed"])
        self.assertFalse(scenario["crash_recovery_runtime_performed"])
        self.assertEqual("STAGE-043", scenario["crash_recovery_owner"])
        self.assertEqual("REQUIRE_MANUAL_REVIEW", scenario["stage039_decision_action"])
        self.assertEqual("FAILED", scenario["stage039_machine_state"])
        self.assertEqual(0, scenario["retry_count"])

    def test_three_resource_pauses_preserve_retry_budget(self):
        report = self._report()["scenario_results"]
        expected = {
            "external_drive_offline_pending_retry_pause": "external_drive_offline",
            "actual_low_disk_pending_retry_pause_without_allocation": "disk_space_insufficient",
            "external_api_budget_pending_retry_pause": "external_api_budget_insufficient",
        }
        for scenario_id, reason in expected.items():
            with self.subTest(scenario_id=scenario_id):
                scenario = report[scenario_id]
                self.assertEqual("PASS", scenario["status"], scenario)
                self.assertEqual("PAUSED", scenario["machine_state"])
                self.assertEqual(reason, scenario["pause_reason_code"])
                self.assertEqual(0, scenario["retry_count"])
                self.assertTrue(scenario["retry_pending"])
                self.assertEqual("eligible", scenario["retry_disposition"])
                self.assertFalse(scenario["physical_action_performed"])

    def test_same_source_lock_blocks_duplicate_operations(self):
        scenario = self._report()["scenario_results"][
            "same_source_cross_operation_lock"
        ]
        self.assertEqual("PASS", scenario["status"], scenario)
        self.assertEqual(["ARCHIVE", "PARSE", "INDEX", "REPORT"], scenario["job_types"])
        self.assertEqual(1, scenario["shared_lock_key_count"])
        self.assertEqual(1, scenario["record_count"])
        self.assertEqual(1, scenario["operation_invocations"])
        self.assertEqual(3, scenario["resource_conflict_count"])
        self.assertFalse(scenario["production_lock_runtime_performed"])

    def test_exhaustion_dead_letters_and_terminal_replay_cannot_reopen(self):
        report = self._report()["scenario_results"]
        exhausted = report["retry_exhaustion_dead_letter"]
        terminal = report["terminal_replay_blocked"]
        self.assertEqual("PASS", exhausted["status"], exhausted)
        self.assertEqual("DEAD_LETTERED", exhausted["machine_state"])
        self.assertEqual(2, exhausted["retry_count"])
        self.assertFalse(exhausted["retry_pending"])
        self.assertEqual("PASS", terminal["status"], terminal)
        self.assertEqual("TERMINAL_STATE_IMMUTABLE", terminal["result_code"])
        self.assertEqual("DEAD_LETTERED", terminal["preserved_state"])
        self.assertFalse(terminal["new_job_created"])

    def test_manual_rerun_candidate_requires_new_lineage_and_is_idempotent(self):
        scenario = self._report()["scenario_results"][
            "manual_rerun_lineage_idempotent"
        ]
        self.assertEqual("PASS", scenario["status"], scenario)
        self.assertEqual("RERUN_CANDIDATE_ACCEPTED", scenario["first_result_code"])
        self.assertEqual("EXISTING_RERUN_CANDIDATE", scenario["replay_result_code"])
        self.assertTrue(scenario["replay_idempotent"])
        self.assertEqual("RERUN_REQUEST_CONFLICT", scenario["conflict_result_code"])
        self.assertEqual("OWNER_AUTHORIZATION_REQUIRED", scenario["unauthorized_result_code"])
        self.assertNotEqual(scenario["parent_job_id"], scenario["new_job_id"])
        self.assertTrue(scenario["candidate_only"])
        self.assertEqual("CREATED", scenario["proposed_initial_state"])
        self.assertFalse(scenario["persisted"])
        self.assertFalse(scenario["job_created"])
        self.assertFalse(scenario["database_write_performed"])

    def test_protected_cleanup_denies_every_protected_class(self):
        scenario = self._report()["scenario_results"]["protected_cleanup_denied"]
        self.assertEqual("PASS", scenario["status"], scenario)
        self.assertEqual(
            ["AUDIT_LOG", "EVIDENCE_LEDGER", "FACT_SOURCE", "MANIFEST", "REPORT_SNAPSHOT"],
            sorted(scenario["artifact_results"]),
        )
        for artifact in scenario["artifact_results"].values():
            self.assertTrue(artifact["git_tracked"], artifact)
            self.assertEqual("PROTECTED_ARTIFACT", artifact["result_code"])
            self.assertFalse(artifact["delete_allowed"])
            self.assertFalse(artifact["delete_attempted"])
        self.assertEqual(0, scenario["delete_attempt_count"])

    def test_report_has_exact_ten_passes_and_no_forbidden_side_effects(self):
        report = self._report()
        self.assertTrue(report["contract_valid"], report)
        self.assertTrue(report["scenario_validation_valid"], report)
        self.assertTrue(report["scenario_runtime_performed"])
        self.assertEqual(EXPECTED_SCENARIOS, list(report["scenario_results"]))
        self.assertEqual(10, report["scenario_count"])
        self.assertEqual(10, report["passed_scenario_count"])
        for scenario in report["scenario_results"].values():
            self.assertEqual("PASS", scenario["status"], scenario)
        self.assertTrue(report["stage038_isolated_queue_runtime_performed"])
        self.assertTrue(report["actual_worker_exception_performed"])
        for flag in (
            "process_termination_performed",
            "physical_drive_removal_performed",
            "disk_allocation_performed",
            "external_api_call_performed",
            "cleanup_runtime_performed",
            "protected_ref_delete_performed",
            "production_runtime_activation_performed",
            "persistent_queue_write_performed",
            "database_connection_performed",
            "runtime_output_written",
            "ids_business_source_read_performed",
            "raw_metadata_content_accessed",
            "fake_ids_business_data_used",
            "real_ids_business_job_created",
            "github_upload_allowed",
            "app_reinstall_allowed",
        ):
            with self.subTest(flag=flag):
                self.assertFalse(report[flag])
        self.assertEqual("IDS-STAGE039-P4-GATE", report["next_gate"])

    def test_governance_preserves_phase3_and_routes_only_to_review(self):
        batch = BATCH.read_text(encoding="utf-8")
        roadmap = ROADMAP.read_text(encoding="utf-8")
        pending_review = (
            'status: "stage039_phase4_completed_review_pending"' in batch
            and 'next_gate: "IDS-STAGE039-REVIEW-GATE"' in batch
            and 'next_allowed_task_id: "IDS-V0_1-STAGE039-REVIEW"' in batch
        )
        completed_review = (
            'status: "stage039_completed_reviewed_local"' in batch
            and 'next_gate: "IDS-STAGE040-P1-GATE"' in batch
            and 'current_phase_id: "IDS-STAGE039-REVIEW"' in roadmap
            and 'next_gate_id: "IDS-STAGE040-P1-GATE"' in roadmap
        )
        self.assertTrue(pending_review or completed_review)
        self.assertIn('push_allowed: false', batch)


if __name__ == "__main__":
    unittest.main()
