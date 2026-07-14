import copy
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import time
import unittest


ROOT = Path(__file__).resolve().parents[4]
REPO_ROOT = ROOT.parent
BASE = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
CONTRACT = BASE / "backpressure_policy" / "stage040_backpressure_runtime_contract.json"
EVIDENCE = BASE / "STAGE040_PHASE2_BACKPRESSURE_DECISION_SLICE.md"
CHECKER = ROOT / "scripts" / "check_backpressure_runtime.py"
BATCH = BASE / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"
MODEL_REGISTRY = ROOT / "docs" / "governance" / "model_registry.yaml"
FORMULA_REGISTRY = ROOT / "docs" / "governance" / "formula_registry.yaml"
PARAMETER_REGISTRY = ROOT / "docs" / "governance" / "parameter_registry.csv"

POLICY_VERSION = "ids.backpressure_policy.v0_1.stage040.p2"
CONTROL_REFS = [
    "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE040_PHASE1_BACKPRESSURE_SCOPE_BOUNDARY.md",
    "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE039_PHASE1_RETRY_DEAD_LETTER_SCOPE_BOUNDARY.md",
    "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md",
    "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE1_SCOPE_BOUNDARY.md",
]
PARAMETERS = {
    "queue_soft_pressure_threshold": 2,
    "queue_hard_capacity_threshold": 4,
    "disk_free_bytes_threshold": 1073741824,
    "disk_reserve_bytes": 536870912,
    "external_api_budget_window_seconds": 60,
    "queue_low_watermark": 1,
    "observation_ttl_seconds": 30,
    "per_job_type_concurrency_limit": 1,
    "admission_rate_limit_per_window": 4,
}
UPSTREAM_BINDINGS = {
    "phase1_policy_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/backpressure_policy/"
        "stage040_backpressure_policy_contract.json",
        "fe7110d0338de3fcb603e267ecf8995ef93e8db58f401612f322ff06166bd25a",
    ),
    "phase1_checker": (
        "KM_IDSystem/scripts/check_backpressure_policy.py",
        "debf37652e23f4b618739a7eb22ed63fd9fa5dd508dad931ec772031049298d0",
    ),
    "phase1_scope_boundary": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "STAGE040_PHASE1_BACKPRESSURE_SCOPE_BOUNDARY.md",
        "68826e3b64936568327ac5050bbff7ba8ed9960ae791a69825ed6c6d3ff3aef6",
    ),
    "stage037_state_index": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "job_state_model/stage037_job_state_model_index.json",
        "b70bf72ebe4212f45d380c13fbfe429791e1f4a5c73dccbba81211b7adc1c2d3",
    ),
    "stage038_queue_index": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "worker_queue_baseline/stage038_worker_queue_baseline_index.json",
        "68513591996a51fea90cd2ea863f42f910c0c3a45b70fd1611655bb6d95911ab",
    ),
    "stage039_runtime_contract": (
        "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
        "retry_dead_letter/stage039_retry_dead_letter_runtime_contract.json",
        "5fc9b49b0ede0fdbc87311f3280ffc69e8ec8e59f219b17a04a2ccae1e9124c0",
    ),
}


class Stage040BackpressureRuntimeTests(unittest.TestCase):
    def _module(self):
        self.assertTrue(CHECKER.is_file(), f"missing checker: {CHECKER}")
        spec = importlib.util.spec_from_file_location(
            "stage040_backpressure_runtime", CHECKER
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _contract(self):
        self.assertTrue(CONTRACT.is_file(), f"missing contract: {CONTRACT}")
        return json.loads(CONTRACT.read_text(encoding="utf-8"))

    def _job(self, *, state="QUEUED", job_type="PARSE", ref=CONTROL_REFS[0]):
        return self._module().build_control_job(
            ref,
            job_type=job_type,
            job_state=state,
        )

    def _observation(self, **updates):
        value = {
            "observed_at_epoch_seconds": int(time.time()),
            "queue_depth": 0,
            "queued_input_refs": [],
            "active_job_type_count": 0,
            "admissions_in_window": 0,
            "disk_free_bytes": PARAMETERS["disk_free_bytes_threshold"]
            + PARAMETERS["disk_reserve_bytes"],
            "external_drive_required": False,
            "external_drive_available": None,
            "external_api_units_required": 0,
            "external_api_budget_remaining_units": 0,
            "external_api_budget_window_seconds": 60,
            "previous_queue_throttled": False,
            "validity_status": "VALID",
            "source_refs": [CONTROL_REFS[0]],
            "policy_version": POLICY_VERSION,
        }
        value.update(updates)
        return value

    def test_phase2_artifacts_and_identity_exist(self):
        for path in (CONTRACT, EVIDENCE, CHECKER):
            with self.subTest(path=path):
                self.assertTrue(path.is_file(), f"missing Phase 2 artifact: {path}")
        contract = self._contract()
        self.assertEqual("ids.stage040.backpressure.phase2.v1", contract["schema_version"])
        self.assertEqual("STAGE-040", contract["stage"])
        self.assertEqual("Phase 2", contract["phase"])
        self.assertEqual("IDS-V0_1-STAGE040-P2", contract["task_id"])
        self.assertEqual("ACC-STAGE-040", contract["acceptance_id"])
        self.assertEqual(POLICY_VERSION, contract["policy_contract_id"])
        self.assertEqual("IDS-STAGE040-P3-GATE", contract["next_gate"])

    def test_upstream_bindings_are_current_and_exact(self):
        bindings = self._contract()["upstream_bindings"]
        self.assertEqual(set(UPSTREAM_BINDINGS), set(bindings))
        for key, (relative, expected_sha) in UPSTREAM_BINDINGS.items():
            with self.subTest(binding=key):
                self.assertEqual(relative, bindings[key]["ref"])
                self.assertEqual(expected_sha, bindings[key]["sha256"])
                self.assertEqual(
                    expected_sha,
                    hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest(),
                )

    def test_policy_parameters_are_exact_bounded_and_not_production_calibrated(self):
        policy = self._contract()["policy"]
        self.assertEqual(POLICY_VERSION, policy["policy_version"])
        self.assertEqual(PARAMETERS, policy["parameters"])
        self.assertEqual(
            "queue_soft_pressure_threshold",
            policy["queue_high_watermark_alias"],
        )
        self.assertEqual("PROPOSED", policy["fact_level"])
        self.assertFalse(policy["production_calibrated"])
        self.assertTrue(policy["production_calibration_required"])
        self.assertLess(
            PARAMETERS["queue_low_watermark"],
            PARAMETERS["queue_soft_pressure_threshold"],
        )
        self.assertLess(
            PARAMETERS["queue_soft_pressure_threshold"],
            PARAMETERS["queue_hard_capacity_threshold"],
        )
        self.assertLessEqual(PARAMETERS["queue_hard_capacity_threshold"], 16)
        self.assertLess(
            PARAMETERS["disk_reserve_bytes"],
            PARAMETERS["disk_free_bytes_threshold"],
        )
        self.assertLess(
            PARAMETERS["observation_ttl_seconds"],
            PARAMETERS["external_api_budget_window_seconds"],
        )

    def test_control_refs_are_real_tracked_files_and_raw_data_is_excluded(self):
        contract = self._contract()
        self.assertEqual(CONTROL_REFS, contract["control_metadata_contract"]["input_refs"])
        for ref in CONTROL_REFS:
            with self.subTest(ref=ref):
                relative = ref.removeprefix("repo:")
                self.assertTrue((REPO_ROOT / relative).is_file())
                self.assertNotIn("/Users/linzezhang/Downloads/IDS_MetaData", ref)
        self.assertFalse(contract["control_metadata_contract"]["raw_body_allowed"])
        self.assertFalse(contract["runtime_boundary"]["ids_business_job_allowed"])
        self.assertFalse(contract["runtime_boundary"]["fake_ids_business_data_allowed"])

    def test_queue_soft_hard_rate_and_concurrency_decisions(self):
        module = self._module()
        contract = self._contract()
        job = self._job()
        healthy = module.evaluate_backpressure(
            job,
            self._observation(),
            contract=contract,
        )
        self.assertEqual("ADMIT", healthy["decision_action"])
        self.assertEqual("可接收", healthy["human_status"]["label_zh"])

        soft = module.evaluate_backpressure(
            job,
            self._observation(
                queue_depth=2,
                queued_input_refs=CONTROL_REFS[:2],
            ),
            contract=contract,
        )
        self.assertEqual("QUEUE_SOFT_PRESSURE", soft["signal_code"])
        self.assertEqual("THROTTLE_ADMISSION", soft["decision_action"])
        self.assertEqual("限流中", soft["human_status"]["label_zh"])
        self.assertFalse(soft["retry_budget_consumed"])

        hard = module.evaluate_backpressure(
            job,
            self._observation(
                queue_depth=4,
                queued_input_refs=CONTROL_REFS,
            ),
            contract=contract,
        )
        self.assertEqual("QUEUE_HARD_CAPACITY", hard["signal_code"])
        self.assertEqual("DENY_NEW_ADMISSION", hard["decision_action"])
        self.assertFalse(hard["job_created"])

        rate = module.evaluate_backpressure(
            job,
            self._observation(admissions_in_window=4),
            contract=contract,
        )
        self.assertEqual("QUEUE_SOFT_PRESSURE", rate["signal_code"])
        self.assertEqual("ADMISSION_RATE_LIMIT_REACHED", rate["reason_code"])

        concurrency = module.evaluate_backpressure(
            job,
            self._observation(active_job_type_count=1),
            contract=contract,
        )
        self.assertEqual("QUEUE_SOFT_PRESSURE", concurrency["signal_code"])
        self.assertEqual("JOB_TYPE_CONCURRENCY_LIMIT_REACHED", concurrency["reason_code"])

    def test_hysteresis_requires_low_watermark_before_release(self):
        module = self._module()
        job = self._job()
        throttled = module.evaluate_backpressure(
            job,
            self._observation(
                queue_depth=2,
                queued_input_refs=CONTROL_REFS[:2],
            ),
            contract=self._contract(),
        )
        self.assertEqual("THROTTLE_ADMISSION", throttled["decision_action"])
        held = module.evaluate_backpressure(
            job,
            self._observation(
                queue_depth=2 - 1,
                queued_input_refs=CONTROL_REFS[:1],
                previous_queue_throttled=True,
            ),
            contract=self._contract(),
        )
        self.assertEqual("ADMIT", held["decision_action"])
        above_low = module.evaluate_backpressure(
            job,
            self._observation(
                queue_depth=2,
                queued_input_refs=CONTROL_REFS[:2],
                previous_queue_throttled=True,
            ),
            contract=self._contract(),
        )
        self.assertEqual("THROTTLE_ADMISSION", above_low["decision_action"])

    def test_resource_pressure_uses_only_legal_pause_candidates(self):
        module = self._module()
        contract = self._contract()
        queued = self._job(state="QUEUED")
        drive = module.evaluate_backpressure(
            queued,
            self._observation(
                external_drive_required=True,
                external_drive_available=False,
            ),
            contract=contract,
        )
        self.assertEqual("EXTERNAL_DRIVE_OFFLINE", drive["signal_code"])
        self.assertEqual(["QUEUED", "PAUSED"], drive["state_path"])
        self.assertEqual("PAUSED", drive["requested_state"])

        disk = module.evaluate_backpressure(
            queued,
            self._observation(
                disk_free_bytes=PARAMETERS["disk_free_bytes_threshold"]
                + PARAMETERS["disk_reserve_bytes"]
                - 1,
            ),
            contract=contract,
        )
        self.assertEqual("DISK_SPACE_INSUFFICIENT", disk["signal_code"])
        self.assertEqual(["QUEUED", "PAUSED"], disk["state_path"])

        running = self._job(state="RUNNING")
        api = module.evaluate_backpressure(
            running,
            self._observation(
                external_api_units_required=1,
                external_api_budget_remaining_units=0,
            ),
            contract=contract,
        )
        self.assertEqual("EXTERNAL_API_BUDGET_INSUFFICIENT", api["signal_code"])
        self.assertEqual(["RUNNING", "PAUSE_REQUESTED", "PAUSED"], api["state_path"])
        self.assertEqual("PAUSE_REQUESTED", api["requested_state"])
        self.assertEqual("暂停中", api["human_status"]["label_zh"])
        self.assertFalse(api["retry_budget_consumed"])
        self.assertFalse(api["automatic_resume_allowed"])

    def test_stale_unknown_and_terminal_inputs_fail_closed(self):
        module = self._module()
        contract = self._contract()
        job = self._job()
        stale = module.evaluate_backpressure(
            job,
            self._observation(
                observed_at_epoch_seconds=int(time.time()) - 31,
            ),
            contract=contract,
        )
        self.assertEqual("UNKNOWN_OR_STALE_PRESSURE", stale["signal_code"])
        self.assertEqual("REQUIRE_MANUAL_REVIEW", stale["decision_action"])
        self.assertEqual("等待人工复核", stale["human_status"]["label_zh"])

        malformed = self._observation()
        malformed.pop("disk_free_bytes")
        blocked = module.evaluate_backpressure(job, malformed, contract=contract)
        self.assertEqual("INVALID_PRESSURE_OBSERVATION", blocked["reason_code"])
        self.assertEqual("REQUIRE_MANUAL_REVIEW", blocked["decision_action"])

        terminal = module.evaluate_backpressure(
            self._job(state="SUCCEEDED"),
            self._observation(
                external_api_units_required=1,
                external_api_budget_remaining_units=0,
            ),
            contract=contract,
        )
        self.assertEqual("TERMINAL_STATE_IMMUTABLE", terminal["reason_code"])
        self.assertIsNone(terminal["requested_state"])
        self.assertIsNone(terminal["candidate_state_version"])

    def test_malformed_control_metadata_is_structured_and_redacted(self):
        module = self._module()
        contract = self._contract()
        valid_job = self._job()

        invalid_observation = module.evaluate_backpressure(
            valid_job,
            {"unexpected": object()},
            contract=contract,
            now_epoch_seconds=1,
        )
        self.assertEqual(
            "INVALID_PRESSURE_OBSERVATION", invalid_observation["reason_code"]
        )
        self.assertIsNone(invalid_observation["observed_at_epoch_seconds"])
        json.dumps(invalid_observation)

        for invalid_refs in (
            [{"private_payload": "SENTINEL"}],
            ["PRIVATE_SENTINEL_NOT_A_REF"],
        ):
            with self.subTest(invalid_refs=invalid_refs):
                invalid_job = copy.deepcopy(valid_job)
                invalid_job["input_refs"] = invalid_refs
                result = module.evaluate_backpressure(
                    invalid_job,
                    {},
                    contract=contract,
                    now_epoch_seconds=1,
                )
                self.assertEqual("INVALID_CONTRACT_OR_JOB", result["reason_code"])
                self.assertEqual([], result["input_refs"])
                self.assertNotIn("SENTINEL", json.dumps(result))

    def test_idempotent_replay_and_checkpoint_are_deterministic(self):
        module = self._module()
        contract = self._contract()
        ledger = module.IsolatedDecisionLedger()
        job = self._job()
        observation = self._observation(
            queue_depth=2,
            queued_input_refs=CONTROL_REFS[:2],
        )
        first = module.evaluate_backpressure(
            job,
            observation,
            contract=contract,
            ledger=ledger,
        )
        replay = module.evaluate_backpressure(
            job,
            copy.deepcopy(observation),
            contract=contract,
            ledger=ledger,
        )
        changed = module.evaluate_backpressure(
            job,
            self._observation(),
            contract=contract,
            ledger=ledger,
        )
        self.assertFalse(first["idempotent_replay"])
        self.assertTrue(replay["idempotent_replay"])
        self.assertEqual(first["decision_key"], replay["decision_key"])
        self.assertEqual(first["checkpoint_ref"], replay["checkpoint_ref"])
        self.assertNotEqual(first["decision_key"], changed["decision_key"])
        self.assertEqual(2, ledger.entry_count)

    def test_untracked_absolute_and_raw_metadata_refs_are_rejected(self):
        module = self._module()
        for ref in (
            "repo:KM_IDSystem/docs/not-tracked-stage040-control.md",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "repo:KM_IDSystem/../outside.md",
        ):
            with self.subTest(ref=ref):
                with self.assertRaises(ValueError):
                    module.build_control_job(ref)

    def test_checker_executes_truthful_actual_control_slice(self):
        report = self._module().build_stage040_phase2_report()
        self.assertTrue(report["contract_valid"], report)
        self.assertTrue(report["slice_valid"], report)
        self.assertTrue(all(report["contract_checks"].values()), report)
        self.assertTrue(all(report["slice_checks"].values()), report)
        self.assertEqual(POLICY_VERSION, report["policy_version"])
        self.assertEqual("IDS-STAGE040-P3-GATE", report["next_gate"])
        self.assertEqual(4, report["tracked_control_ref_count"])
        self.assertGreater(report["actual_disk_free_bytes"], 0)
        self.assertTrue(report["actual_disk_observation_performed"])
        self.assertEqual("THROTTLE_ADMISSION", report["soft_pressure_result"])
        self.assertEqual("DENY_NEW_ADMISSION", report["hard_capacity_result"])
        self.assertEqual("PAUSE_REQUESTED", report["api_budget_pause_requested_state"])
        self.assertTrue(report["idempotent_replay_proved"])
        for key in (
            "queue_runtime_performed",
            "worker_runtime_performed",
            "retry_scheduler_performed",
            "lock_runtime_performed",
            "automatic_resume_performed",
            "cleanup_runtime_performed",
            "database_connection_performed",
            "persistent_queue_write_performed",
            "runtime_output_written",
            "external_api_call_performed",
            "raw_metadata_content_accessed",
            "fake_ids_business_data_used",
            "real_ids_business_job_created",
            "production_runtime_activation_performed",
            "github_upload_allowed",
            "app_reinstall_allowed",
        ):
            with self.subTest(flag=key):
                self.assertFalse(report[key])

    def test_checker_rejects_parameter_or_boundary_tampering(self):
        module = self._module()
        original = self._contract()
        mutations = []
        for mutate in (
            lambda item: item["policy"]["parameters"].update(
                {"queue_hard_capacity_threshold": 1}
            ),
            lambda item: item["policy"].update({"production_calibrated": True}),
            lambda item: item["runtime_boundary"].update(
                {"database_allowed": True}
            ),
            lambda item: item["truth_flags"].update(
                {"raw_metadata_content_accessed": True}
            ),
            lambda item: item["state_transition_contract"].update(
                {"terminal_state_mutation_allowed": True}
            ),
        ):
            candidate = copy.deepcopy(original)
            mutate(candidate)
            mutations.append(candidate)
        for candidate in mutations:
            with self.subTest(candidate=candidate):
                checks = module.evaluate_contract(candidate)
                self.assertFalse(all(checks.values()), checks)

    def test_registry_entries_are_planned_proposed_and_task_linked(self):
        models = MODEL_REGISTRY.read_text(encoding="utf-8")
        formulas = FORMULA_REGISTRY.read_text(encoding="utf-8")
        rows = list(
            csv.DictReader(
                io.StringIO(PARAMETER_REGISTRY.read_text(encoding="utf-8"))
            )
        )
        self.assertIn('model_id: "MOD-009"', models)
        self.assertIn('model_version: "ids.backpressure_policy.v0_1.stage040.p2"', models)
        self.assertIn('formula_id: "FORM-009"', formulas)
        selected = [row for row in rows if row["model_id"] == "MOD-009"]
        self.assertEqual(9, len(selected))
        self.assertEqual(
            {f"PARAM-{number:03d}" for number in range(56, 65)},
            {row["parameter_id"] for row in selected},
        )
        self.assertTrue(all(row["status"] == "planned" for row in selected))
        self.assertTrue(all(row["fact_level"] == "PROPOSED" for row in selected))
        self.assertTrue(
            all(row["unknown_task_ids"] == "TASK-OPME-B-001" for row in selected)
        )

    def test_governance_routes_only_to_phase3_and_records_one_event(self):
        batch = BATCH.read_text(encoding="utf-8")
        roadmap = ROADMAP.read_text(encoding="utf-8")
        events = [
            json.loads(line)
            for line in EVENTS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertIn('status: "stage040_phase2_completed"', batch)
        self.assertIn('next_allowed_task_id: "IDS-V0_1-STAGE040-P3"', batch)
        self.assertIn('current_phase_id: "IDS-STAGE040-P2"', roadmap)
        self.assertIn('next_gate_id: "IDS-STAGE040-P3-GATE"', roadmap)
        matching = [
            event
            for event in events
            if event.get("event_id") == "EVT-IDS-V0_1-STAGE040-P2-20260713-001"
        ]
        self.assertEqual(1, len(matching), matching)
        self.assertEqual("phase_completed", matching[0]["event_type"])
        self.assertEqual("IDS-V0_1-STAGE040-P2", matching[0]["task_id"])
        self.assertEqual(["ACC-STAGE-040"], matching[0]["acceptance_ids"])

    def test_phase2_evidence_stops_before_phase3_and_later_runtime(self):
        text = EVIDENCE.read_text(encoding="utf-8")
        for term in (
            "Phase 3 must run separately",
            "NO_PHASE3",
            "NO_QUEUE_RUNTIME",
            "NO_WORKER_RUNTIME",
            "NO_LOCK_RUNTIME",
            "NO_AUTOMATIC_RESUME",
            "NO_CLEANUP_RUNTIME",
            "NO_RAW_METADATA_ACCESS",
            "NO_FAKE_IDS_BUSINESS_DATA",
            "NO_GITHUB_UPLOAD",
            "NO_APP_REINSTALL",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
