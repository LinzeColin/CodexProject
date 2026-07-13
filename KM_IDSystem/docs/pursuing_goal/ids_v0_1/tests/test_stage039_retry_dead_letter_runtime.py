import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
CONTRACT = BASE / "retry_dead_letter" / "stage039_retry_dead_letter_runtime_contract.json"
EVIDENCE = BASE / "STAGE039_PHASE2_RETRY_DEAD_LETTER_SLICE.md"
CHECKER = ROOT / "scripts" / "check_retry_dead_letter_runtime.py"
CONTROL_INPUT_REF = (
    "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
    "STAGE039_PHASE1_RETRY_DEAD_LETTER_SCOPE_BOUNDARY.md"
)
POLICY_VERSION = "ids.retry_policy.v0_1.stage039.p2"


class Stage039RetryDeadLetterRuntimeTests(unittest.TestCase):
    def _module(self):
        self.assertTrue(CHECKER.is_file(), f"missing Phase 2 checker: {CHECKER}")
        spec = importlib.util.spec_from_file_location(
            "stage039_retry_dead_letter_runtime", CHECKER
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _contract(self):
        self.assertTrue(CONTRACT.is_file(), f"missing Phase 2 contract: {CONTRACT}")
        return json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_phase2_artifacts_and_versioned_policy_are_explicit(self):
        module = self._module()
        contract = self._contract()
        self.assertTrue(EVIDENCE.is_file(), f"missing Phase 2 evidence: {EVIDENCE}")
        self.assertTrue(all(module.validate_runtime_contract(contract).values()))
        self.assertEqual("IDS-V0_1-STAGE039-P2", contract["task_id"])
        self.assertEqual("ACC-STAGE-039", contract["acceptance_id"])
        self.assertEqual(POLICY_VERSION, contract["policy"]["policy_version"])
        self.assertEqual(2, contract["policy"]["max_retries"])
        self.assertEqual([5, 30], contract["policy"]["backoff_schedule_seconds"])
        self.assertEqual(
            "DETERMINISTIC_BOUNDED_HASH_JITTER_V1",
            contract["policy"]["jitter_policy"],
        )
        self.assertEqual(
            [
                "TRANSIENT_DEPENDENCY_UNAVAILABLE",
                "TRANSIENT_OPERATION_TIMEOUT",
            ],
            contract["policy"]["retryable_safe_error_codes"],
        )
        self.assertEqual("PROPOSED", contract["policy"]["fact_level"])
        self.assertFalse(contract["policy"]["production_calibrated"])
        self.assertEqual("NO_AUTOMATIC_RETRY", contract["policy"]["unknown_code_behavior"])

    def test_policy_tampering_fails_closed_before_execution(self):
        module = self._module()
        baseline = self._contract()
        mutations = []
        for mutate in (
            lambda value: value.update({"unknown_root": True}),
            lambda value: value["policy"].update({"max_retries": -1}),
            lambda value: value["policy"].update({"backoff_schedule_seconds": [0, 30]}),
            lambda value: value["policy"].update({"backoff_schedule_seconds": [5]}),
            lambda value: value["policy"].update({"retryable_safe_error_codes": ["UNKNOWN"]}),
            lambda value: value["runtime_boundary"].update({"database_allowed": True}),
            lambda value: value["truth_flags"].update({"fake_ids_business_data_used": True}),
        ):
            candidate = copy.deepcopy(baseline)
            mutate(candidate)
            mutations.append(candidate)
        for candidate in mutations:
            with self.subTest(candidate=candidate):
                self.assertFalse(all(module.validate_runtime_contract(candidate).values()))
                report = module.build_stage039_phase2_report(
                    contract=candidate, execute_slice=True
                )
                self.assertFalse(report["contract_valid"], report)
                self.assertFalse(report["slice_executed"], report)

    def test_jitter_is_deterministic_bounded_and_never_immediate(self):
        module = self._module()
        policy = self._contract()["policy"]
        for retry_ordinal, ceiling in enumerate(
            policy["backoff_schedule_seconds"], start=1
        ):
            first = module.deterministic_delay_seconds(
                "control:stage039:bounded", retry_ordinal, policy
            )
            second = module.deterministic_delay_seconds(
                "control:stage039:bounded", retry_ordinal, policy
            )
            self.assertEqual(first, second)
            self.assertGreaterEqual(first, max(1, (ceiling + 1) // 2))
            self.assertLessEqual(first, ceiling)

    def test_stage038_admission_and_running_snapshot_use_tracked_control_metadata(self):
        module = self._module()
        context = module.build_running_control_context(self._contract())
        self.assertTrue(context["admission"]["accepted"], context)
        self.assertFalse(context["admission"]["duplicate"])
        self.assertEqual(CONTROL_INPUT_REF, context["snapshot"]["input_refs"][0])
        self.assertNotEqual(
            context["stage038_record"]["job_id"], context["snapshot"]["job_id"]
        )
        self.assertTrue(context["snapshot"]["job_id"].startswith("control:stage039:"))
        self.assertFalse(context["identity_bridge"]["same_logical_job"])
        self.assertTrue(
            context["identity_bridge"]["max_retries_bound_at_stage039_job_creation"]
        )
        self.assertEqual("RUNNING", context["snapshot"]["job_state"])
        self.assertEqual(2, context["snapshot"]["max_retries"])
        self.assertEqual(["QUEUED", "CLAIMED", "RUNNING"], context["state_history"])
        self.assertEqual("处理中", context["owner_status"]["label_zh"])

    def test_transient_failure_reserves_without_consuming_retry_budget(self):
        module = self._module()
        contract = self._contract()
        context = module.build_running_control_context(contract)
        snapshot = context["snapshot"]
        observation = module.build_failure_observation(
            snapshot,
            safe_error_code="TRANSIENT_OPERATION_TIMEOUT",
            observed_at_epoch_seconds=1_720_000_000,
        )
        prior_results = {}
        result = module.evaluate_failure(
            snapshot,
            observation,
            contract=contract,
            prior_results=prior_results,
        )
        next_snapshot = result["next_snapshot"]

        self.assertTrue(result["accepted"], result)
        self.assertEqual("SCHEDULE_RETRY", result["decision_action"])
        self.assertEqual("RETRY_WAIT", next_snapshot["job_state"])
        self.assertEqual(0, next_snapshot["retry_count"])
        self.assertTrue(next_snapshot["retry_pending"])
        self.assertEqual("eligible", next_snapshot["retry_disposition"])
        self.assertRegex(next_snapshot["next_eligible_at"], r"^epoch:[0-9]+$")
        self.assertEqual(snapshot["input_refs"], next_snapshot["input_refs"])
        self.assertEqual([], next_snapshot["output_refs"])
        self.assertEqual(observation["error_ref"], next_snapshot["error_ref"])
        self.assertEqual(observation["checkpoint_ref"], next_snapshot["checkpoint_ref"])
        self.assertEqual("等待重试", result["owner_status"]["label_zh"])

        replay = module.evaluate_failure(
            snapshot,
            observation,
            contract=contract,
            prior_results=prior_results,
        )
        self.assertTrue(replay["accepted"], replay)
        self.assertTrue(replay["idempotent_replay"])
        self.assertEqual(next_snapshot, replay["next_snapshot"])
        self.assertEqual(0, replay["next_snapshot"]["retry_count"])

    def test_retry_admission_is_due_gated_atomic_and_idempotent(self):
        module = self._module()
        contract = self._contract()
        context = module.build_running_control_context(contract)
        observation = module.build_failure_observation(
            context["snapshot"],
            safe_error_code="TRANSIENT_DEPENDENCY_UNAVAILABLE",
            observed_at_epoch_seconds=1_720_000_000,
        )
        reserved = module.evaluate_failure(
            context["snapshot"], observation, contract=contract
        )
        waiting = reserved["next_snapshot"]
        due_at = int(waiting["next_eligible_at"].split(":", 1)[1])

        early = module.admit_due_retry(
            waiting,
            observed_at_epoch_seconds=due_at - 1,
            transition_request_id="acceptance:ACC-STAGE-039:retry-admission-1",
            contract=contract,
        )
        self.assertFalse(early["accepted"], early)
        self.assertEqual("RETRY_NOT_YET_ELIGIBLE", early["result_code"])
        self.assertEqual(0, early["next_snapshot"]["retry_count"])

        prior_results = {}
        admitted = module.admit_due_retry(
            waiting,
            observed_at_epoch_seconds=due_at,
            transition_request_id="acceptance:ACC-STAGE-039:retry-admission-1",
            contract=contract,
            prior_results=prior_results,
        )
        self.assertTrue(admitted["accepted"], admitted)
        self.assertEqual("QUEUED", admitted["next_snapshot"]["job_state"])
        self.assertEqual(1, admitted["next_snapshot"]["retry_count"])
        self.assertFalse(admitted["next_snapshot"]["retry_pending"])

        replay = module.admit_due_retry(
            waiting,
            observed_at_epoch_seconds=due_at,
            transition_request_id="acceptance:ACC-STAGE-039:retry-admission-1",
            contract=contract,
            prior_results=prior_results,
        )
        self.assertTrue(replay["accepted"], replay)
        self.assertTrue(replay["idempotent_replay"])
        self.assertEqual(1, replay["next_snapshot"]["retry_count"])

    def test_resource_pause_does_not_consume_pending_retry(self):
        module = self._module()
        contract = self._contract()
        context = module.build_running_control_context(contract)
        observation = module.build_failure_observation(
            context["snapshot"],
            safe_error_code="TRANSIENT_OPERATION_TIMEOUT",
            observed_at_epoch_seconds=1_720_000_000,
        )
        waiting = module.evaluate_failure(
            context["snapshot"], observation, contract=contract
        )["next_snapshot"]
        blocked = module.pause_pending_retry(
            waiting,
            pause_reason_code="disk_space_insufficient",
            transition_request_id="acceptance:ACC-STAGE-039:resource-pause-1",
            contract=contract,
        )
        paused = blocked["next_snapshot"]
        self.assertTrue(blocked["accepted"], blocked)
        self.assertEqual("PAUSED", paused["job_state"])
        self.assertEqual(0, paused["retry_count"])
        self.assertTrue(paused["retry_pending"])
        self.assertEqual("eligible", paused["retry_disposition"])
        self.assertEqual("disk_space_insufficient", paused["pause_reason_code"])
        self.assertEqual("已暂停", blocked["owner_status"]["label_zh"])

    def test_exhaustion_dead_letters_without_reopening_terminal_state(self):
        module = self._module()
        contract = self._contract()
        context = module.build_running_control_context(contract, retry_count=2)
        observation = module.build_failure_observation(
            context["snapshot"],
            safe_error_code="TRANSIENT_OPERATION_TIMEOUT",
            observed_at_epoch_seconds=1_720_000_000,
        )
        exhausted = module.evaluate_failure(
            context["snapshot"], observation, contract=contract
        )
        final_snapshot = exhausted["next_snapshot"]
        self.assertTrue(exhausted["accepted"], exhausted)
        self.assertEqual("DEAD_LETTER", exhausted["decision_action"])
        self.assertEqual("DEAD_LETTERED", final_snapshot["job_state"])
        self.assertEqual(2, final_snapshot["retry_count"])
        self.assertFalse(final_snapshot["retry_pending"])
        self.assertEqual("exhausted", final_snapshot["retry_disposition"])
        self.assertEqual("需要人工处理", exhausted["owner_status"]["label_zh"])
        self.assertEqual(
            ["RUNNING", "RETRY_WAIT", "DEAD_LETTERED"],
            exhausted["state_history"],
        )

        terminal_retry = module.evaluate_failure(
            final_snapshot, observation, contract=contract
        )
        self.assertFalse(terminal_retry["accepted"], terminal_retry)
        self.assertEqual("TERMINAL_STATE_IMMUTABLE", terminal_retry["result_code"])

    def test_unknown_error_fails_closed_to_manual_review(self):
        module = self._module()
        contract = self._contract()
        context = module.build_running_control_context(contract)
        observation = module.build_failure_observation(
            context["snapshot"],
            safe_error_code="UNRECOGNIZED_SAFE_CODE",
            observed_at_epoch_seconds=1_720_000_000,
        )
        result = module.evaluate_failure(
            context["snapshot"], observation, contract=contract
        )
        self.assertTrue(result["accepted"], result)
        self.assertEqual("REQUIRE_MANUAL_REVIEW", result["decision_action"])
        self.assertEqual("FAILED", result["next_snapshot"]["job_state"])
        self.assertEqual(0, result["next_snapshot"]["retry_count"])
        self.assertEqual("处理失败", result["owner_status"]["label_zh"])

    def test_report_executes_only_bounded_nonproduction_metadata_slice(self):
        module = self._module()
        report = module.build_stage039_phase2_report()
        self.assertTrue(report["contract_valid"], report)
        self.assertTrue(report["slice_valid"], report)
        self.assertTrue(report["slice_executed"])
        self.assertTrue(report["stage038_isolated_admission_performed"])
        self.assertTrue(report["retry_reservation_performed"])
        self.assertTrue(report["retry_admission_performed"])
        self.assertTrue(report["dead_letter_metadata_transition_performed"])
        self.assertEqual("DEAD_LETTERED", report["final_record"]["machine_state"])
        self.assertEqual(2, report["final_record"]["retry_count"])
        self.assertEqual(CONTROL_INPUT_REF, report["final_record"]["input_refs"][0])
        self.assertNotEqual(
            report["final_record"]["stage038_admission_job_id"],
            report["final_record"]["job_id"],
        )
        self.assertRegex(
            report["final_record"]["stage038_queue_entry_ref"],
            r"^queue-entry:stage038:[0-9a-f]{64}$",
        )
        self.assertEqual([], report["final_record"]["output_refs"])
        self.assertRegex(report["final_record"]["error_ref"], r"^error:[A-Z0-9_]+$")
        self.assertRegex(
            report["final_record"]["checkpoint_ref"],
            r"^checkpoint:sha256:[0-9a-f]{64}$",
        )
        for flag in (
            "production_runtime_activation_performed",
            "database_connection_performed",
            "persistent_queue_write_performed",
            "runtime_output_written",
            "ids_business_source_read_performed",
            "raw_metadata_content_accessed",
            "fake_ids_business_data_used",
            "real_ids_business_job_created",
            "external_api_call_performed",
            "github_upload_allowed",
            "app_reinstall_allowed",
        ):
            with self.subTest(flag=flag):
                self.assertFalse(report[flag])


if __name__ == "__main__":
    unittest.main()
