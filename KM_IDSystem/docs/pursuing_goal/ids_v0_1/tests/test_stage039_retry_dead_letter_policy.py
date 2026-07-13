import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
REPO_ROOT = ROOT.parent
BASE = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
CONTRACT = BASE / "retry_dead_letter" / "stage039_retry_dead_letter_policy_contract.json"
ENTRY = BASE / "STAGE039_ENTRY_CONTRACT.md"
BOUNDARY = BASE / "STAGE039_PHASE1_RETRY_DEAD_LETTER_SCOPE_BOUNDARY.md"
BATCH = BASE / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
CHECKER = ROOT / "scripts" / "check_retry_dead_letter_policy.py"

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
        "STAGE-039_重试与死信策略.md"
    ),
    "source_member_match_count": 1,
    "source_member_integrity": "OK",
    "source_member_sha256": (
        "504caf72a6aeab67a650b4b096e728f03269f6ca8798f6e8a5c51210c8ddd7d9"
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
    "stage037_checker_ref": (
        "KM_IDSystem/scripts/check_job_state_model.py",
        "7de8746b70ca1eaba78b672deebd9973113cedeacf3edbba09d2afb90407f404",
    ),
    "stage038_queue_index_ref": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "worker_queue_baseline/stage038_worker_queue_baseline_index.json",
        "68513591996a51fea90cd2ea863f42f910c0c3a45b70fd1611655bb6d95911ab",
    ),
    "stage038_delivery_contract_ref": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "worker_queue_baseline/stage038_worker_queue_delivery_contract.json",
        "a4067c25b46340c33bee5017c286d6867d2b72e8fa208430c005d6b1a342c7e4",
    ),
    "stage038_review_checker_ref": (
        "KM_IDSystem/scripts/check_worker_queue_stage_review.py",
        "b406cb8500b22b62c2d8400b6bfcf24cf1ed1b06990313ee66483a91bf255f96",
    ),
    "stage038_review_artifact_ref": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_STAGE_REVIEW.md",
        "5bb4cb3382f97ded9228d278c4cfb34fc5f0a65b8858263ed0c9bbd6c035eb04",
    ),
}


class Stage039RetryDeadLetterPolicyTests(unittest.TestCase):
    def _contract(self):
        self.assertTrue(CONTRACT.is_file(), f"missing contract: {CONTRACT}")
        return json.loads(CONTRACT.read_text(encoding="utf-8"))

    def _checker(self):
        self.assertTrue(CHECKER.is_file(), f"missing checker: {CHECKER}")
        spec = importlib.util.spec_from_file_location(
            "stage039_retry_dead_letter_checker", CHECKER
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

    def test_state_model_inheritance_preserves_terminal_states(self):
        state = self._contract()["state_model_inheritance"]
        self.assertEqual("ids.job_state.v1", state["state_model_version"])
        self.assertEqual(
            ["SUCCEEDED", "FAILED", "DEAD_LETTERED", "CANCELLED"],
            state["terminal_states"],
        )
        self.assertFalse(state["terminal_state_mutation_allowed"])
        self.assertEqual(["RETRY_WAIT", "DEAD_LETTERED"], state["exhaustion_path"])
        self.assertEqual(["RUNNING", "FAILED"], state["permanent_failure_path"])
        self.assertFalse(state["running_to_dead_letter_allowed"])

    def test_retry_budget_and_identity_are_unambiguous(self):
        contract = self._contract()
        budget = contract["retry_budget_contract"]
        identity = contract["identity_contract"]
        inputs = contract["input_contract"]
        self.assertIn("failure_observation_ref", inputs["required_fields"])
        self.assertNotIn("failure_class", inputs["required_fields"])
        self.assertEqual("number_of_retry_attempts_after_initial_attempt", budget["max_retries_definition"])
        self.assertEqual("1 + max_retries", budget["total_attempt_limit_formula"])
        self.assertFalse(budget["reservation_increments_retry_count"])
        self.assertTrue(budget["admission_increments_retry_count"])
        self.assertFalse(budget["resource_pause_consumes_retry"])
        self.assertEqual("NO_AUTOMATIC_RETRY", budget["missing_policy_behavior"])
        self.assertEqual("stable_across_attempts", identity["job_id_scope"])
        self.assertEqual("unique_per_execution_attempt", identity["attempt_id_scope"])
        self.assertEqual("stable_for_one_logical_job", identity["idempotency_key_scope"])
        self.assertEqual("NEW_LINKED_JOB_REQUIRED", identity["terminal_manual_rerun"])
        self.assertEqual(
            ["parent_job_id", "rerun_request_id", "new_job_id", "new_idempotency_key"],
            identity["terminal_manual_rerun_required_fields"],
        )
        self.assertEqual(
            "parent_job_id_plus_owner_rerun_request_id",
            identity["terminal_rerun_idempotency_scope"],
        )

    def test_failure_classification_has_exact_fail_closed_actions(self):
        classifications = self._contract()["failure_classification"]
        expected = {
            "TRANSIENT_RETRYABLE": ("SCHEDULE_RETRY", "RETRY_WAIT", False),
            "PERMANENT_NON_RETRYABLE": ("FAIL_TERMINAL", "FAILED", False),
            "RESOURCE_CONDITION_PAUSE": ("PAUSE_RESOURCE_GATE", "PAUSED", False),
            "RETRY_EXHAUSTED": ("DEAD_LETTER", "DEAD_LETTERED", True),
            "POLICY_OR_AUTHORIZATION_BLOCK": ("REQUIRE_MANUAL_REVIEW", "FAILED", True),
            "INDETERMINATE_UNSAFE": ("REQUIRE_MANUAL_REVIEW", "FAILED", True),
        }
        self.assertEqual(set(expected), set(classifications))
        for name, (action, target, manual) in expected.items():
            with self.subTest(classification=name):
                self.assertEqual(action, classifications[name]["decision_action"])
                self.assertEqual(target, classifications[name]["target_state"])
                self.assertIs(manual, classifications[name]["manual_review_required"])
                self.assertTrue(classifications[name]["legal_transition_paths"])
        self.assertEqual(
            [["RETRY_WAIT", "DEAD_LETTERED"]],
            classifications["RETRY_EXHAUSTED"]["legal_transition_paths"],
        )
        self.assertIn(
            ["RUNNING", "PAUSE_REQUESTED", "PAUSED"],
            classifications["RESOURCE_CONDITION_PAUSE"]["legal_transition_paths"],
        )

    def test_resource_pause_and_dead_letter_preserve_evidence(self):
        contract = self._contract()
        resource = contract["resource_pause_contract"]
        dead_letter = contract["dead_letter_contract"]
        self.assertEqual(
            [
                "external_drive_offline",
                "disk_space_insufficient",
                "external_api_budget_insufficient",
            ],
            resource["pause_reason_codes"],
        )
        self.assertFalse(resource["retry_budget_consumed"])
        self.assertFalse(resource["automatic_resume_allowed"])
        self.assertEqual("STAGE-042", resource["resume_runtime_owner"])
        self.assertEqual("RETRY_WAIT", dead_letter["required_source_state"])
        self.assertEqual("RETRY_EXHAUSTED", dead_letter["required_failure_class"])
        self.assertFalse(dead_letter["raw_payload_copy_allowed"])
        self.assertFalse(dead_letter["evidence_deletion_allowed"])
        self.assertEqual(
            ["FACT_SOURCE", "MANIFEST", "EVIDENCE_LEDGER", "AUDIT_LOG", "REPORT_SNAPSHOT"],
            dead_letter["protected_artifact_classes"],
        )

    def test_checker_reports_contract_only_and_no_runtime(self):
        report = self._checker().build_stage039_phase1_report()
        self.assertTrue(report["phase1_contract_valid"], report)
        self.assertTrue(all(report["contract_checks"].values()), report["contract_checks"])
        self.assertEqual("IDS-STAGE039-P2-GATE", report["next_gate"])
        self.assertEqual("PHASE1_ENGINEERING_CONTRACT_RUNTIME_DISABLED", report["contract_state"])
        for key in (
            "retry_scheduler_performed",
            "dead_letter_runtime_performed",
            "queue_runtime_performed",
            "worker_runtime_performed",
            "database_connection_performed",
            "schema_change_performed",
            "runtime_output_written",
            "raw_metadata_content_accessed",
            "fake_ids_business_data_used",
            "github_upload_allowed",
            "app_reinstall_allowed",
        ):
            with self.subTest(flag=key):
                self.assertFalse(report[key])

    def test_checker_rejects_contract_tampering(self):
        checker = self._checker()
        original = self._contract()
        mutations = []
        for mutate in (
            lambda item: item.update({"unknown_root_field": True}),
            lambda item: item["state_model_inheritance"].update(
                {"terminal_state_mutation_allowed": True}
            ),
            lambda item: item["retry_budget_contract"].update(
                {"resource_pause_consumes_retry": True}
            ),
            lambda item: item["dead_letter_contract"].update(
                {"raw_payload_copy_allowed": True}
            ),
            lambda item: item["truth_flags"].update(
                {"retry_scheduler_performed": True}
            ),
            lambda item: item["input_contract"].update(
                {"unknown_nested_field": True}
            ),
            lambda item: item["identity_contract"].update(
                {"unknown_nested_field": True}
            ),
            lambda item: item["retry_budget_contract"].update(
                {"unknown_nested_field": True}
            ),
            lambda item: item["retry_eligibility_contract"].update(
                {"unknown_nested_field": True}
            ),
            lambda item: item["dead_letter_contract"].update(
                {"unknown_nested_field": True}
            ),
            lambda item: item["worker_boundary"].update(
                {"unknown_nested_field": True}
            ),
            lambda item: item["phase2_entry_gate"].update(
                {"unknown_nested_field": True}
            ),
            lambda item: item["failure_classification"][
                "TRANSIENT_RETRYABLE"
            ].update({"unknown_nested_field": True}),
        ):
            candidate = copy.deepcopy(original)
            mutate(candidate)
            mutations.append(candidate)
        for candidate in mutations:
            with self.subTest(candidate=candidate):
                checks = checker.evaluate_contract(candidate, ROOT)
                self.assertFalse(all(checks.values()), checks)

    def test_governance_routes_only_to_separate_phase2(self):
        entry = ENTRY.read_text(encoding="utf-8")
        boundary = BOUNDARY.read_text(encoding="utf-8")
        batch = BATCH.read_text(encoding="utf-8")
        roadmap = ROADMAP.read_text(encoding="utf-8")
        combined = "\n".join((entry, boundary))
        for term in (
            "retry_policy_contract_id=ids.retry_dead_letter.v0_1.p1",
            "NO_PHASE2",
            "NO_RETRY_RUNTIME",
            "NO_DEAD_LETTER_RUNTIME",
            "NO_POSTGRES_CONNECTION",
            "NO_RAW_METADATA_ACCESS",
            "NO_FAKE_IDS_BUSINESS_DATA",
            "NO_GITHUB_UPLOAD",
            "NO_APP_REINSTALL",
            "Phase 2 must run separately",
        ):
            with self.subTest(term=term):
                self.assertIn(term, combined)
        self.assertIn('status: "stage039_phase3_completed"', batch)
        self.assertIn('      - "Phase 1"', batch)
        self.assertIn('      - "Phase 2"', batch)
        self.assertIn('current_task_id: "IDS-V0_1-STAGE039-P3"', batch)
        self.assertIn('next_gate: "IDS-STAGE039-P4-GATE"', batch)
        self.assertIn('current_stage_id: "IDS-STAGE039"', roadmap)
        self.assertIn('current_phase_id: "IDS-STAGE039-P2"', roadmap)
        self.assertIn('current_task_id: "IDS-V0_1-STAGE039-P3"', roadmap)
        self.assertIn('next_gate_id: "IDS-STAGE039-P4-GATE"', roadmap)
        self.assertIn('push_allowed: false', batch)


if __name__ == "__main__":
    unittest.main()
