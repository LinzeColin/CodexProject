import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
REPO_ROOT = ROOT.parent
BASE = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
CONTRACT = BASE / "backpressure_policy" / "stage040_backpressure_policy_contract.json"
ENTRY = BASE / "STAGE040_ENTRY_CONTRACT.md"
BOUNDARY = BASE / "STAGE040_PHASE1_BACKPRESSURE_SCOPE_BOUNDARY.md"
BATCH = BASE / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"
CHECKER = ROOT / "scripts" / "check_backpressure_policy.py"

SOURCE_BINDING = {
    "source_archive_path": (
        "/Users/linzezhang/Downloads/"
        "IDS_Taskpack_v0_1_only_中文修订版.zip"
    ),
    "source_archive_sha256": (
        "55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3"
    ),
    "source_member": (
        "IDS_v0_1_Final_Chinese_Revised/stages/"
        "STAGE-040_反压策略.md"
    ),
    "source_member_match_count": 1,
    "source_member_integrity": "OK",
    "source_member_sha256": (
        "f0ef128467300d7541796f8d51caca673f838cac2552eba2e415a94a07af614d"
    ),
    "roadmap_sha256": (
        "a193fd2c44c51d634bf7887a1a6baf7e5199d9a8535e4211e35e97588e2e21a6"
    ),
    "instructions_sha256": (
        "ce456e06136d5ecc56cd7c9dc926abb5894817dda87bf7667588bf85211794f8"
    ),
    "source_verification_status": "SOURCE_VERIFIED",
}

UPSTREAM_BINDINGS = {
    "stage037_state_index_ref": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "job_state_model/stage037_job_state_model_index.json",
        "b70bf72ebe4212f45d380c13fbfe429791e1f4a5c73dccbba81211b7adc1c2d3",
    ),
    "stage038_delivery_contract_ref": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "worker_queue_baseline/stage038_worker_queue_delivery_contract.json",
        "a4067c25b46340c33bee5017c286d6867d2b72e8fa208430c005d6b1a342c7e4",
    ),
    "stage039_delivery_contract_ref": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "retry_dead_letter/stage039_retry_dead_letter_delivery_contract.json",
        "c4aad64a9283de683067aff07026d723c708285c57eef8a0eac4ee1b13f5cb96",
    ),
    "stage039_review_checker_ref": (
        "KM_IDSystem/scripts/check_retry_dead_letter_stage_review.py",
        "c49f654ff7a1a27e36a79749582066bb348b9e856b716f8411bb3cf2039ae81a",
    ),
    "stage039_review_artifact_ref": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_STAGE_REVIEW.md",
        "32e621db9d7d4ad87ff4f6788e1de22d7ada9c0f57ce756a76a9608a864c4b9b",
    ),
}


class Stage040BackpressurePolicyTests(unittest.TestCase):
    def _contract(self):
        self.assertTrue(CONTRACT.is_file(), f"missing contract: {CONTRACT}")
        return json.loads(CONTRACT.read_text(encoding="utf-8"))

    def _checker(self):
        self.assertTrue(CHECKER.is_file(), f"missing checker: {CHECKER}")
        spec = importlib.util.spec_from_file_location(
            "stage040_backpressure_policy_checker", CHECKER
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_phase1_artifacts_exist(self):
        for path in (CONTRACT, ENTRY, BOUNDARY, CHECKER):
            with self.subTest(path=path):
                self.assertTrue(path.is_file(), f"missing Phase 1 artifact: {path}")

    def test_source_binding_is_exact_and_unique(self):
        contract = self._contract()
        self.assertEqual(SOURCE_BINDING, contract["source_binding"])
        self.assertTrue(contract["truth_flags"]["taskpack_source_read_performed"])
        self.assertFalse(contract["truth_flags"]["ids_business_source_read_performed"])
        self.assertFalse(contract["truth_flags"]["raw_metadata_content_accessed"])

    def test_upstream_bindings_match_tracked_sources(self):
        contract = self._contract()
        self.assertEqual(set(UPSTREAM_BINDINGS), set(contract["upstream_bindings"]))
        for key, (relative, expected_sha) in UPSTREAM_BINDINGS.items():
            with self.subTest(binding=key):
                binding = contract["upstream_bindings"][key]
                self.assertEqual(relative, binding["ref"])
                self.assertEqual(expected_sha, binding["sha256"])
                observed = hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest()
                self.assertEqual(expected_sha, observed)

    def test_pressure_observation_and_input_contract_are_metadata_only(self):
        contract = self._contract()
        inputs = contract["input_contract"]
        observation = contract["pressure_observation_contract"]
        self.assertEqual(
            [
                "job_id",
                "job_type",
                "job_state",
                "state_version",
                "idempotency_key",
                "priority_ref",
                "pressure_observation_refs",
                "claim_lock_refs",
                "retry_refs",
                "checkpoint_ref",
                "input_ref",
                "output_ref",
                "error_ref",
                "audit_ref",
                "policy_version",
                "observation_time",
            ],
            inputs["required_fields"],
        )
        self.assertFalse(inputs["raw_payload_allowed"])
        self.assertEqual(
            [
                "signal_code",
                "observed_value_ref",
                "unit",
                "observed_at",
                "source_ref",
                "policy_version",
                "validity_status",
            ],
            observation["required_fields"],
        )
        self.assertFalse(observation["raw_source_body_allowed"])
        self.assertEqual("REQUIRE_MANUAL_REVIEW", observation["unknown_or_stale_action"])

    def test_decision_matrix_is_exact_and_fail_closed(self):
        decisions = self._contract()["decision_matrix"]
        expected = {
            "HEALTHY": ("ADMIT", "NO_POLICY_STATE_MUTATION", False),
            "QUEUE_SOFT_PRESSURE": (
                "THROTTLE_ADMISSION",
                "NO_LIFECYCLE_MUTATION",
                False,
            ),
            "QUEUE_HARD_CAPACITY": (
                "DENY_NEW_ADMISSION",
                "NO_QUEUE_RECORD_CREATED",
                False,
            ),
            "EXTERNAL_DRIVE_OFFLINE": (
                "PAUSE_RESOURCE_GATE",
                "LEGAL_PAUSE_PATH_REQUIRED",
                False,
            ),
            "DISK_SPACE_INSUFFICIENT": (
                "PAUSE_RESOURCE_GATE",
                "LEGAL_PAUSE_PATH_REQUIRED",
                False,
            ),
            "EXTERNAL_API_BUDGET_INSUFFICIENT": (
                "PAUSE_RESOURCE_GATE",
                "LEGAL_PAUSE_PATH_REQUIRED",
                False,
            ),
            "UNKNOWN_OR_STALE_PRESSURE": (
                "REQUIRE_MANUAL_REVIEW",
                "NO_NEW_ADMISSION",
                True,
            ),
        }
        self.assertEqual(set(expected), set(decisions))
        for signal, (action, effect, manual_review) in expected.items():
            with self.subTest(signal=signal):
                self.assertEqual(action, decisions[signal]["decision_action"])
                self.assertEqual(effect, decisions[signal]["state_effect"])
                self.assertIs(
                    manual_review,
                    decisions[signal]["manual_review_required"],
                )
        pause_paths = decisions["EXTERNAL_DRIVE_OFFLINE"]["legal_transition_paths"]
        self.assertIn(["QUEUED", "PAUSED"], pause_paths)
        self.assertIn(["RUNNING", "PAUSE_REQUESTED", "PAUSED"], pause_paths)
        self.assertEqual([], decisions["QUEUE_HARD_CAPACITY"]["legal_transition_paths"])

    def test_state_retry_and_fairness_invariants_are_preserved(self):
        contract = self._contract()
        state = contract["state_model_inheritance"]
        budget = contract["retry_budget_invariants"]
        fairness = contract["fairness_contract"]
        self.assertEqual("ids.job_state.v1", state["state_model_version"])
        self.assertEqual(
            ["SUCCEEDED", "FAILED", "DEAD_LETTERED", "CANCELLED"],
            state["terminal_states"],
        )
        self.assertFalse(state["terminal_state_mutation_allowed"])
        self.assertFalse(budget["throttle_consumes_retry"])
        self.assertFalse(budget["resource_pause_consumes_retry"])
        self.assertFalse(budget["admission_denial_consumes_retry"])
        self.assertFalse(budget["automatic_resume_allowed"])
        self.assertEqual("STAGE-042", budget["automatic_resume_runtime_owner"])
        self.assertTrue(fairness["priority_cannot_bypass_safety_gate"])
        self.assertFalse(fairness["starvation_allowed"])
        self.assertEqual("STAGE-022", fairness["priority_vocabulary_owner"])
        self.assertEqual("DEFERRED_TO_PHASE2", fairness["scheduler_algorithm"])

    def test_parameters_lock_and_cleanup_are_deferred_to_owners(self):
        contract = self._contract()
        parameters = contract["policy_parameter_contract"]
        locking = contract["lock_boundary"]
        cleanup = contract["partial_output_cleanup_boundary"]
        self.assertFalse(parameters["numeric_values_assigned"])
        self.assertEqual(
            [
                "queue_soft_pressure_threshold",
                "queue_hard_capacity_threshold",
                "disk_free_bytes_threshold",
                "disk_reserve_bytes",
                "external_api_budget_window",
                "high_low_watermarks",
                "observation_ttl",
                "per_job_type_concurrency",
                "admission_rate_limit",
            ],
            parameters["deferred_parameters"],
        )
        self.assertEqual("STAGE-041", locking["runtime_owner"])
        self.assertFalse(locking["lock_runtime_performed"])
        self.assertEqual("STAGE-044", cleanup["runtime_owner"])
        self.assertFalse(cleanup["cleanup_runtime_performed"])
        self.assertFalse(cleanup["protected_artifact_delete_allowed"])
        self.assertEqual(
            ["FACT_SOURCE", "MANIFEST", "EVIDENCE_LEDGER", "AUDIT_LOG", "REPORT_SNAPSHOT"],
            cleanup["protected_artifact_classes"],
        )

    def test_ownership_matrix_does_not_absorb_later_stages(self):
        ownership = self._contract()["ownership_matrix"]
        self.assertEqual("STAGE-040", ownership["backpressure_decision_policy"])
        self.assertEqual("STAGE-038", ownership["queue_and_worker_transport"])
        self.assertEqual("STAGE-039", ownership["retry_and_dead_letter_policy"])
        self.assertEqual("STAGE-041", ownership["lock_lease_and_fencing_runtime"])
        self.assertEqual("STAGE-042", ownership["automatic_resume_runtime"])
        self.assertEqual("STAGE-043", ownership["crash_recovery_runtime"])
        self.assertEqual("STAGE-044", ownership["cleanup_execution_runtime"])

    def test_checker_reports_contract_only_and_rejects_tampering(self):
        checker = self._checker()
        report = checker.build_stage040_phase1_report()
        self.assertTrue(report["phase1_contract_valid"], report)
        self.assertTrue(all(report["contract_checks"].values()), report)
        self.assertEqual("IDS-STAGE040-P2-GATE", report["next_gate"])
        self.assertEqual(
            "PHASE1_ENGINEERING_CONTRACT_RUNTIME_DISABLED",
            report["contract_state"],
        )
        for key in (
            "backpressure_runtime_performed",
            "queue_runtime_performed",
            "worker_runtime_performed",
            "lock_runtime_performed",
            "automatic_resume_performed",
            "cleanup_runtime_performed",
            "database_connection_performed",
            "runtime_output_written",
            "raw_metadata_content_accessed",
            "fake_ids_business_data_used",
            "github_upload_allowed",
            "app_reinstall_allowed",
        ):
            with self.subTest(flag=key):
                self.assertFalse(report[key])

        original = self._contract()
        mutations = []
        for mutate in (
            lambda item: item.update({"unknown_root_field": True}),
            lambda item: item["decision_matrix"]["UNKNOWN_OR_STALE_PRESSURE"].update(
                {"decision_action": "ADMIT"}
            ),
            lambda item: item["policy_parameter_contract"].update(
                {"numeric_values_assigned": True}
            ),
            lambda item: item["retry_budget_invariants"].update(
                {"resource_pause_consumes_retry": True}
            ),
            lambda item: item["lock_boundary"].update(
                {"lock_runtime_performed": True}
            ),
            lambda item: item["truth_flags"].update(
                {"raw_metadata_content_accessed": True}
            ),
        ):
            candidate = copy.deepcopy(original)
            mutate(candidate)
            mutations.append(candidate)
        for candidate in mutations:
            with self.subTest(candidate=candidate):
                checks = checker.evaluate_contract(candidate)
                self.assertFalse(all(checks.values()), checks)

    def test_docs_governance_and_event_stop_at_phase1(self):
        entry = ENTRY.read_text(encoding="utf-8")
        boundary = BOUNDARY.read_text(encoding="utf-8")
        batch = BATCH.read_text(encoding="utf-8")
        roadmap = ROADMAP.read_text(encoding="utf-8")
        events = [
            json.loads(line)
            for line in EVENTS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for marker in (
            "Phase 2 must run separately",
            "NO_PHASE2",
            "NO_BACKPRESSURE_RUNTIME",
            "NO_RAW_METADATA_ACCESS",
            "NO_FAKE_IDS_BUSINESS_DATA",
            "NO_GITHUB_UPLOAD",
            "NO_APP_REINSTALL",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, entry + boundary)
        self.assertIn('status: "stage040_phase1_completed"', batch)
        self.assertIn('next_allowed_task_id: "IDS-V0_1-STAGE040-P2"', batch)
        self.assertIn('current_stage_id: "IDS-STAGE040"', roadmap)
        self.assertIn('current_phase_id: "IDS-STAGE040-P1"', roadmap)
        self.assertIn('next_gate_id: "IDS-STAGE040-P2-GATE"', roadmap)
        matching = [
            item
            for item in events
            if item.get("event_id") == "EVT-IDS-V0_1-STAGE040-P1-20260713-001"
        ]
        self.assertEqual(1, len(matching))
        self.assertEqual("IDS-V0_1-STAGE040-P1", matching[0]["task_id"])
        self.assertEqual(["ACC-STAGE-040"], matching[0]["acceptance_ids"])


if __name__ == "__main__":
    unittest.main()
