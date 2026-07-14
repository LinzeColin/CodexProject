import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
REPO_ROOT = ROOT.parent
CONTRACT = (
    ROOT
    / "docs"
    / "pursuing_goal"
    / "ids_v0_1"
    / "backpressure_policy"
    / "stage040_backpressure_scenarios.json"
)
CHECKER = ROOT / "scripts" / "check_backpressure_scenarios.py"
EVIDENCE = (
    ROOT
    / "docs"
    / "pursuing_goal"
    / "ids_v0_1"
    / "STAGE040_PHASE3_SCENARIO_VALIDATION.md"
)
BATCH = (
    ROOT
    / "docs"
    / "pursuing_goal"
    / "ids_v0_1"
    / "BATCH031_040_UPLOAD_LOCK.yaml"
)
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"

SCENARIOS = [
    "duplicate_click_decision_replay",
    "worker_exception_crash_boundary",
    "external_drive_offline_pause_candidate",
    "actual_disk_observation_and_low_disk_boundary",
    "external_api_budget_pause_candidate",
    "same_source_cross_operation_concurrency_throttle",
    "reviewed_lock_conflict_proof",
    "protected_cleanup_denied",
]
EXPECTED_HASHES = {
    "stage040_phase2_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/"
        "stage040_backpressure_runtime_contract.json",
        "3db2409b082b9f788e061dfbb3a8e33ad8459c8e56a863e21fe0faeca8581b5c",
    ),
    "stage040_phase2_checker": (
        "KM_IDSystem/scripts/check_backpressure_runtime.py",
        "c28493586d2d0982948ce5e968ff756ddf069228382328078c5516c6348c15ad",
    ),
    "stage040_phase2_evidence": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "STAGE040_PHASE2_BACKPRESSURE_DECISION_SLICE.md",
        "3a01138928e4fa9c526ab392617464675b30ae42d290e91de942e887b91132b3",
    ),
    "stage039_scenario_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/retry_dead_letter/"
        "stage039_retry_dead_letter_scenarios.json",
        "045cc67295c4918996b8439e0b2ea857edf2f998e836fbc7b4bbcbbedd660b3e",
    ),
    "stage039_scenario_checker": (
        "KM_IDSystem/scripts/check_retry_dead_letter_scenarios.py",
        "2502d8fde4016be717c72ad079ec338c80e1ed8fec9a9c27f5494dfb34eef862",
    ),
    "stage038_scenario_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/worker_queue_baseline/"
        "stage038_worker_queue_scenarios.json",
        "0ec9f1a0de6ec24d64d4108214ea426f9171b15eebdd6c3c60693fade62f2961",
    ),
    "stage038_scenario_checker": (
        "KM_IDSystem/scripts/check_worker_queue_scenarios.py",
        "b7e335039ecf65e4fe91df39e91cddd296296852bd3be8923237b8616db9517c",
    ),
}


class Stage040BackpressureScenarioTests(unittest.TestCase):
    def _load_checker(self):
        self.assertTrue(CHECKER.is_file(), f"missing checker: {CHECKER}")
        spec = importlib.util.spec_from_file_location(
            "stage040_backpressure_scenarios", CHECKER
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _contract(self):
        self.assertTrue(CONTRACT.is_file(), f"missing contract: {CONTRACT}")
        return json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_contract_identity_source_commit_and_upstream_bindings(self):
        contract = self._contract()
        self.assertEqual("ids.stage040.backpressure.phase3.scenarios.v1", contract["schema_version"])
        self.assertEqual("STAGE-040", contract["stage"])
        self.assertEqual("Phase 3", contract["phase"])
        self.assertEqual("IDS-V0_1-STAGE040-P3", contract["task_id"])
        self.assertEqual("ACC-STAGE-040", contract["acceptance_id"])
        self.assertEqual(
            "ISOLATED_NON_PRODUCTION_BACKPRESSURE_SCENARIOS",
            contract["execution_mode"],
        )
        self.assertEqual(
            "PHASE3_SCENARIOS_ENABLED_PRODUCTION_DISABLED",
            contract["contract_state"],
        )
        self.assertEqual("IDS-STAGE040-P4-GATE", contract["next_gate"])
        self.assertEqual(
            "647445f9e0bb5cfcbfbfaa0f8180df872c3ece5f",
            contract["phase2_commit_binding"]["commit"],
        )
        self.assertTrue(contract["phase2_commit_binding"]["required_ancestor_of_head"])
        source = contract["source_binding"]
        self.assertEqual("SOURCE_VERIFIED", source["source_verification_status"])
        self.assertEqual(1, source["source_member_match_count"])
        self.assertEqual(
            "f0ef128467300d7541796f8d51caca673f838cac2552eba2e415a94a07af614d",
            source["source_member_sha256"],
        )
        self.assertEqual(set(EXPECTED_HASHES), set(contract["upstream_bindings"]))
        for name, (relative, expected_sha) in EXPECTED_HASHES.items():
            with self.subTest(binding=name):
                self.assertEqual(
                    {"ref": relative, "sha256": expected_sha},
                    contract["upstream_bindings"][name],
                )
                self.assertEqual(
                    expected_sha,
                    self._load_checker().sha256_file(REPO_ROOT / relative),
                )

    def test_scenario_catalog_and_safety_boundaries_are_exact(self):
        contract = self._contract()
        self.assertEqual(SCENARIOS, contract["scenario_catalog"])
        self.assertEqual(set(SCENARIOS), set(contract["scenario_expectations"]))
        self.assertEqual(
            {
                "process_termination_allowed": False,
                "physical_drive_removal_allowed": False,
                "disk_allocation_allowed": False,
                "external_api_call_allowed": False,
                "cleanup_delete_allowed": False,
                "production_runtime_allowed": False,
                "stage040_queue_worker_runtime_allowed": False,
                "stage038_isolated_worker_exception_replay_allowed": True,
                "actual_project_disk_observation_allowed": True,
            },
            contract["physical_action_boundary"],
        )
        self.assertEqual(
            {
                "production_lock_lease_and_fencing": "STAGE-041",
                "automatic_resume_and_lifecycle": "STAGE-042",
                "process_crash_recovery": "STAGE-043",
                "cleanup_execution": "STAGE-044",
                "phase3_may_take_downstream_runtime_ownership": False,
            },
            contract["downstream_ownership"],
        )

    def test_checker_validates_contract_and_all_eight_scenarios(self):
        report = self._load_checker().build_stage040_phase3_report()
        self.assertTrue(report["contract_valid"], report)
        self.assertTrue(report["scenario_validation_valid"], report)
        self.assertEqual(8, report["scenario_count"])
        self.assertEqual(8, report["passed_scenario_count"])
        self.assertEqual(SCENARIOS, list(report["scenario_results"]))
        self.assertTrue(all(item["status"] == "PASS" for item in report["scenario_results"].values()))
        self.assertEqual("IDS-STAGE040-P4-GATE", report["next_gate"])

    def test_duplicate_click_replays_one_decision_without_job_or_write(self):
        result = self._load_checker().build_stage040_phase3_report()["scenario_results"][
            "duplicate_click_decision_replay"
        ]
        self.assertEqual("PASS", result["status"])
        self.assertFalse(result["first_idempotent_replay"])
        self.assertTrue(result["second_idempotent_replay"])
        self.assertEqual(result["first_decision_key"], result["second_decision_key"])
        self.assertEqual(1, result["ledger_entry_count"])
        self.assertFalse(result["job_created"])
        self.assertFalse(result["persistent_write_performed"])

    def test_actual_worker_exception_is_bounded_and_crash_recovery_is_deferred(self):
        result = self._load_checker().build_stage040_phase3_report()["scenario_results"][
            "worker_exception_crash_boundary"
        ]
        self.assertEqual("PASS", result["status"])
        self.assertTrue(result["actual_isolated_worker_exception_performed"])
        self.assertEqual("error:RuntimeError", result["worker_error_ref"])
        self.assertEqual("REQUIRE_MANUAL_REVIEW", result["backpressure_decision_action"])
        self.assertEqual("TERMINAL_STATE_IMMUTABLE", result["backpressure_reason_code"])
        self.assertFalse(result["process_termination_performed"])
        self.assertFalse(result["crash_recovery_runtime_performed"])
        self.assertEqual("STAGE-043", result["crash_recovery_owner"])

    def test_drive_disk_and_api_pressure_use_legal_pause_candidates(self):
        results = self._load_checker().build_stage040_phase3_report()["scenario_results"]
        drive = results["external_drive_offline_pause_candidate"]
        self.assertEqual("EXTERNAL_DRIVE_OFFLINE", drive["signal_code"])
        self.assertEqual("PAUSE_RESOURCE_GATE", drive["decision_action"])
        self.assertEqual("PAUSED", drive["requested_state"])
        self.assertEqual(["QUEUED", "PAUSED"], drive["state_path"])
        self.assertFalse(drive["physical_drive_removal_performed"])

        disk = results["actual_disk_observation_and_low_disk_boundary"]
        self.assertGreater(disk["actual_disk_free_bytes"], 0)
        self.assertTrue(disk["actual_disk_decision_matches_formula"])
        self.assertEqual("DISK_SPACE_INSUFFICIENT", disk["boundary_signal_code"])
        self.assertEqual("PAUSE_RESOURCE_GATE", disk["boundary_decision_action"])
        self.assertFalse(disk["disk_allocation_performed"])

        api = results["external_api_budget_pause_candidate"]
        self.assertEqual("EXTERNAL_API_BUDGET_INSUFFICIENT", api["signal_code"])
        self.assertEqual("PAUSE_REQUESTED", api["requested_state"])
        self.assertEqual(["RUNNING", "PAUSE_REQUESTED", "PAUSED"], api["state_path"])
        self.assertFalse(api["external_api_call_performed"])

    def test_same_source_concurrency_and_reviewed_lock_proof_are_bounded(self):
        results = self._load_checker().build_stage040_phase3_report()["scenario_results"]
        concurrency = results["same_source_cross_operation_concurrency_throttle"]
        self.assertEqual(["ARCHIVE", "PARSE", "INDEX", "REPORT"], concurrency["job_types"])
        self.assertEqual(4, concurrency["throttled_decision_count"])
        self.assertEqual(0, concurrency["created_job_count"])
        self.assertFalse(concurrency["production_lock_runtime_performed"])

        lock = results["reviewed_lock_conflict_proof"]
        self.assertEqual(1, lock["shared_lock_key_count"])
        self.assertEqual(1, lock["record_count"])
        self.assertEqual(1, lock["operation_invocations"])
        self.assertEqual(3, lock["resource_conflict_count"])
        self.assertFalse(lock["production_lock_runtime_performed"])
        self.assertEqual("STAGE-041", lock["lock_runtime_owner"])

    def test_protected_artifacts_are_git_tracked_and_never_deleted(self):
        result = self._load_checker().build_stage040_phase3_report()["scenario_results"][
            "protected_cleanup_denied"
        ]
        self.assertEqual("PASS", result["status"])
        self.assertEqual(5, len(result["artifact_results"]))
        self.assertTrue(all(item["git_tracked"] for item in result["artifact_results"].values()))
        self.assertTrue(
            all(
                item["result_code"] == "PROTECTED_ARTIFACT"
                and item["delete_allowed"] is False
                and item["delete_attempted"] is False
                for item in result["artifact_results"].values()
            )
        )
        self.assertEqual(0, result["delete_attempt_count"])
        self.assertEqual(0, result["deleted_ref_count"])
        self.assertFalse(result["cleanup_runtime_performed"])
        self.assertEqual("STAGE-044", result["runtime_owner"])

    def test_truth_flags_do_not_overclaim_physical_or_production_actions(self):
        report = self._load_checker().build_stage040_phase3_report()
        self.assertTrue(report["actual_isolated_worker_exception_performed"])
        self.assertTrue(report["stage038_isolated_worker_exception_replayed"])
        self.assertTrue(report["actual_disk_observation_performed"])
        self.assertTrue(report["isolated_control_metadata_evaluated"])
        self.assertTrue(report["reviewed_control_lock_proof_replayed"])
        self.assertTrue(report["taskpack_source_read_performed"])
        for field in (
            "process_termination_performed",
            "physical_drive_removal_performed",
            "disk_allocation_performed",
            "external_api_call_performed",
            "cleanup_runtime_performed",
            "protected_ref_delete_performed",
            "stage040_queue_runtime_performed",
            "stage040_worker_runtime_performed",
            "production_lock_runtime_performed",
            "crash_recovery_runtime_performed",
            "production_runtime_activation_performed",
            "persistent_queue_write_performed",
            "database_connection_performed",
            "runtime_output_written",
            "raw_metadata_content_accessed",
            "fake_ids_business_data_used",
            "real_ids_business_job_created",
            "github_upload_allowed",
            "app_reinstall_allowed",
        ):
            with self.subTest(field=field):
                self.assertFalse(report[field])

    def test_contract_tampering_fails_closed(self):
        module = self._load_checker()
        original = self._contract()
        mutations = []
        for mutate in (
            lambda value: value.update({"next_gate": "IDS-STAGE040-REVIEW-GATE"}),
            lambda value: value["scenario_catalog"].append("production_probe"),
            lambda value: value["physical_action_boundary"].update(
                {"physical_drive_removal_allowed": True}
            ),
            lambda value: value["phase2_commit_binding"].update(
                {"commit": "0" * 40}
            ),
            lambda value: value["protected_artifact_contract"].update(
                {"delete_attempt_allowed": True}
            ),
            lambda value: value["truth_flags"].update(
                {"external_api_call_performed": True}
            ),
        ):
            candidate = copy.deepcopy(original)
            mutate(candidate)
            mutations.append(candidate)
        for candidate in mutations:
            with self.subTest(candidate=candidate):
                checks = module.validate_scenario_contract(candidate)
                self.assertFalse(all(checks.values()), checks)

    def test_evidence_and_governance_route_only_to_phase4(self):
        self.assertTrue(EVIDENCE.is_file(), f"missing evidence: {EVIDENCE}")
        evidence = EVIDENCE.read_text(encoding="utf-8")
        for term in (
            "IDS-V0_1-STAGE040-P3",
            "IDS-STAGE040-P4-GATE",
            "actual isolated worker exception",
            "actual project-filesystem free-space observation",
            "no physical drive removal",
            "no disk allocation",
            "no external API call",
            "no cleanup or delete",
            "push_allowed=false",
        ):
            with self.subTest(term=term):
                self.assertIn(term, evidence)

        batch = BATCH.read_text(encoding="utf-8")
        roadmap = ROADMAP.read_text(encoding="utf-8")
        phase3_active = (
            'status: "stage040_phase3_completed"' in batch
            and 'next_allowed_task_id: "IDS-V0_1-STAGE040-P4"' in batch
            and 'current_phase_id: "IDS-STAGE040-P3"' in roadmap
            and 'next_gate_id: "IDS-STAGE040-P4-GATE"' in roadmap
        )
        phase4_review_pending = (
            'status: "stage040_phase4_completed_review_pending"' in batch
            and 'next_allowed_task_id: "IDS-V0_1-STAGE040-REVIEW"' in batch
            and 'current_phase_id: "IDS-STAGE040-P4"' in roadmap
            and 'next_gate_id: "IDS-STAGE040-REVIEW-GATE"' in roadmap
        )
        self.assertTrue(
            phase3_active or phase4_review_pending,
            {"phase3_active": phase3_active, "phase4_review_pending": phase4_review_pending},
        )
        events = [
            json.loads(line)
            for line in EVENTS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        matching = [
            event
            for event in events
            if event.get("event_id") == "EVT-IDS-V0_1-STAGE040-P3-20260713-001"
        ]
        self.assertEqual(1, len(matching))
        self.assertEqual("IDS-V0_1-STAGE040-P3", matching[0]["task_id"])
        self.assertFalse(matching[0]["notes"].count("next_gate="))


if __name__ == "__main__":
    unittest.main()
