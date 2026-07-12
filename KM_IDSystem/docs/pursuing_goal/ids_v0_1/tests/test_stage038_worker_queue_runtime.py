import asyncio
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
CHECKER = ROOT / "scripts" / "check_worker_queue_baseline.py"
INDEX = (
    PURSUE_ROOT
    / "worker_queue_baseline"
    / "stage038_worker_queue_baseline_index.json"
)
PHASE2 = PURSUE_ROOT / "STAGE038_PHASE2_ASYNC_WORKER_QUEUE_SLICE.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"
CONTROL_INPUT_REF = (
    "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
    "STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md"
)


class Stage038WorkerQueueRuntimePhase2Tests(unittest.TestCase):
    def _load_checker(self):
        self.assertTrue(CHECKER.is_file(), f"missing Phase 2 checker: {CHECKER}")
        spec = importlib.util.spec_from_file_location(
            "stage038_worker_queue_runtime", CHECKER
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_phase2_contract_binds_exact_upstream_sources_and_fails_closed(self):
        module = self._load_checker()
        self.assertTrue(INDEX.is_file(), f"missing queue index: {INDEX}")
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        report = module.build_stage038_phase2_report(index=index, execute_slice=False)

        self.assertEqual(
            "ids.stage038.worker_queue_baseline.index.v1",
            index["schema_version"],
        )
        self.assertEqual("IDS-V0_1-STAGE038-P2", index["task_id"])
        self.assertEqual("ACC-STAGE-038", index["acceptance_id"])
        self.assertTrue(report["contract_valid"], report)
        self.assertTrue(all(report["source_integrity"].values()), report)
        self.assertFalse(report["queue_runtime_performed"])
        self.assertFalse(report["worker_runtime_performed"])

        tampered = json.loads(json.dumps(index))
        tampered["worker_queue_contract"]["maximum_isolated_capacity"] = 17
        blocked = module.build_stage038_phase2_report(
            index=tampered, execute_slice=True
        )
        self.assertFalse(blocked["contract_valid"], blocked)
        self.assertFalse(blocked["slice_valid"], blocked)
        self.assertFalse(blocked["queue_runtime_performed"])
        self.assertFalse(blocked["worker_runtime_performed"])

    def test_report_runs_one_real_tracked_control_job_without_persistence(self):
        report = self._load_checker().build_stage038_phase2_report()

        self.assertTrue(report["contract_valid"], report)
        self.assertTrue(report["slice_valid"], report)
        self.assertEqual(
            "ISOLATED_NON_PRODUCTION_ASYNC_CONTROL_METADATA_SLICE",
            report["execution_mode"],
        )
        self.assertTrue(report["submission_ack_returned_before_completion"])
        self.assertTrue(report["queue_runtime_performed"])
        self.assertTrue(report["worker_runtime_performed"])
        self.assertTrue(report["isolated_control_job_created"])
        self.assertFalse(report["production_runtime_activation_performed"])
        self.assertFalse(report["claim_persistence_performed"])
        self.assertFalse(report["persistent_queue_write_performed"])
        self.assertFalse(report["database_connection_performed"])
        self.assertFalse(report["state_registry_write_performed"])
        self.assertFalse(report["runtime_output_written"])
        self.assertFalse(report["ids_business_source_read_performed"])
        self.assertFalse(report["external_api_call_performed"])
        self.assertFalse(report["raw_metadata_content_accessed"])
        self.assertFalse(report["fake_ids_business_data_used"])
        self.assertFalse(report["real_ids_business_job_created"])

        record = report["final_record"]
        self.assertEqual("SUCCEEDED", record["machine_state"])
        self.assertEqual("已完成", record["owner_status"]["label_zh"])
        self.assertEqual([CONTROL_INPUT_REF], record["input_refs"])
        self.assertEqual(1, len(record["output_refs"]))
        self.assertRegex(record["output_refs"][0], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(record["checkpoint_ref"], r"^checkpoint:sha256:[0-9a-f]{64}$")
        self.assertIsNone(record["error_ref"])
        self.assertEqual(
            ["QUEUED", "CLAIMED", "RUNNING", "SUCCEEDED"],
            record["state_history"],
        )

    def test_submit_ack_does_not_wait_for_worker_completion(self):
        module = self._load_checker()

        async def exercise():
            started = asyncio.Event()
            release = asyncio.Event()

            async def controlled_operation(envelope):
                started.set()
                await release.wait()
                return await module._hash_tracked_control_file(envelope)

            queue = module.IsolatedWorkerQueue(
                capacity=1,
                operation=controlled_operation,
            )
            await queue.start()
            envelope = module.build_control_envelope(CONTROL_INPUT_REF)
            ack = queue.submit(envelope)
            ack_before_worker_started = not started.is_set()
            await started.wait()
            running = queue.get_record(ack["queue_entry_ref"])
            release.set()
            await queue.join()
            completed = queue.get_record(ack["queue_entry_ref"])
            await queue.shutdown()
            return ack, ack_before_worker_started, running, completed

        ack, ack_before_worker_started, running, completed = asyncio.run(
            exercise()
        )
        self.assertTrue(ack["accepted"], ack)
        self.assertEqual("QUEUED", ack["machine_state"])
        self.assertTrue(ack_before_worker_started)
        self.assertEqual("RUNNING", running["machine_state"])
        self.assertEqual("处理中", running["owner_status"]["label_zh"])
        self.assertEqual("SUCCEEDED", completed["machine_state"])

    def test_duplicate_admission_returns_existing_entry_and_runs_once(self):
        module = self._load_checker()
        queue = module.IsolatedWorkerQueue(capacity=1)
        envelope = module.build_control_envelope(CONTROL_INPUT_REF)

        first = queue.submit(envelope)
        duplicate = queue.submit(envelope)

        self.assertTrue(first["accepted"], first)
        self.assertTrue(duplicate["accepted"], duplicate)
        self.assertFalse(first["duplicate"])
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(first["queue_entry_ref"], duplicate["queue_entry_ref"])
        self.assertEqual(1, queue.queue_size)
        self.assertEqual(1, queue.record_count)

        conflicting = json.loads(json.dumps(envelope))
        conflicting["priority_ref"] = "P2_SUPPORTING_ENGINEERING_DATA"
        conflict = queue.submit(conflicting)
        self.assertFalse(conflict["accepted"], conflict)
        self.assertEqual("IDEMPOTENCY_KEY_CONFLICT", conflict["result_code"])
        self.assertEqual(1, queue.record_count)

    def test_capacity_backpressure_rejects_second_distinct_entry(self):
        module = self._load_checker()
        queue = module.IsolatedWorkerQueue(capacity=1)
        first = module.build_control_envelope(CONTROL_INPUT_REF)
        second = module.build_control_envelope(
            "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
            "STAGE038_PHASE1_SOURCE_REVERIFICATION.md"
        )

        accepted = queue.submit(first)
        blocked = queue.submit(second)

        self.assertTrue(accepted["accepted"], accepted)
        self.assertFalse(blocked["accepted"], blocked)
        self.assertEqual("QUEUE_CAPACITY_REACHED", blocked["result_code"])
        self.assertEqual("已暂停", blocked["owner_status"]["label_zh"])
        self.assertTrue(blocked["owner_status"]["owner_attention_required"])
        self.assertEqual(1, queue.record_count)

    def test_raw_paths_bodies_secrets_and_untracked_refs_fail_before_queueing(self):
        module = self._load_checker()
        queue = module.IsolatedWorkerQueue(capacity=2)
        baseline = module.build_control_envelope(CONTROL_INPUT_REF)

        cases = []
        raw_path = json.loads(json.dumps(baseline))
        raw_path["input_refs"] = [
            "repo:/Users/linzezhang/Downloads/IDS_MetaData/forbidden"
        ]
        cases.append((raw_path, "FORBIDDEN_REFERENCE"))

        raw_body = json.loads(json.dumps(baseline))
        raw_body["raw_content"] = "forbidden"
        cases.append((raw_body, "INVALID_ENVELOPE_SHAPE"))

        secret = json.loads(json.dumps(baseline))
        secret["api_key"] = "forbidden"
        cases.append((secret, "INVALID_ENVELOPE_SHAPE"))

        untracked = module.build_control_envelope(
            "repo:KM_IDSystem/not-tracked.txt"
        )
        cases.append((untracked, "UNTRACKED_CONTROL_REFERENCE"))

        wrong_lock = json.loads(json.dumps(baseline))
        wrong_lock["lock_key"] = "resource:stage038:wrong-conflict-domain"
        cases.append((wrong_lock, "INVALID_ENVELOPE_IDENTITY"))

        for envelope, result_code in cases:
            with self.subTest(result_code=result_code):
                decision = queue.submit(envelope)
                self.assertFalse(decision["accepted"], decision)
                self.assertEqual(result_code, decision["result_code"])
        self.assertEqual(0, queue.queue_size)
        self.assertEqual(0, queue.record_count)

    def test_actual_worker_failure_records_bounded_error_and_terminal_state(self):
        module = self._load_checker()

        async def exercise():
            async def failing_operation(_envelope):
                raise RuntimeError("bounded control operation failed")

            queue = module.IsolatedWorkerQueue(
                capacity=1,
                operation=failing_operation,
            )
            await queue.start()
            ack = queue.submit(module.build_control_envelope(CONTROL_INPUT_REF))
            await queue.join()
            record = queue.get_record(ack["queue_entry_ref"])
            await queue.shutdown()
            return record

        record = asyncio.run(exercise())
        self.assertEqual("FAILED", record["machine_state"])
        self.assertEqual("处理失败", record["owner_status"]["label_zh"])
        self.assertEqual("error:RuntimeError", record["error_ref"])
        self.assertEqual([], record["output_refs"])
        self.assertIsNone(record["checkpoint_ref"])
        self.assertEqual(
            ["QUEUED", "CLAIMED", "RUNNING", "FAILED"],
            record["state_history"],
        )

    def test_phase2_docs_and_event_remain_valid_after_phase3_progression(self):
        self.assertTrue(PHASE2.is_file(), f"missing Phase 2 evidence: {PHASE2}")
        text = PHASE2.read_text(encoding="utf-8")
        for term in (
            "IDS-V0_1-STAGE038-P2",
            "ACC-STAGE-038",
            "ISOLATED_NON_PRODUCTION_ASYNC_CONTROL_METADATA_SLICE",
            "submission acknowledgement returns before worker completion",
            "QUEUED -> CLAIMED -> RUNNING -> SUCCEEDED",
            "input_refs",
            "output_refs",
            "error_ref",
            "checkpoint_ref",
            "STAGE-039..044 retain runtime ownership",
            "production_runtime_activation_performed=false",
            "raw_metadata_content_accessed=false",
            "fake_ids_business_data_used=false",
            "push_allowed=false",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)

        module = self._load_checker()
        batch = module._parse_yaml_text(BATCH_LOCK.read_text(encoding="utf-8"))
        roadmap = module._parse_yaml_text(ROADMAP.read_text(encoding="utf-8"))
        stage = batch["stage_progress"]["STAGE-038"]
        self.assertEqual("stage038_phase3_completed", batch["status"])
        self.assertEqual(
            ["Phase 1", "Phase 2", "Phase 3"],
            stage["completed_phases"],
        )
        self.assertEqual("IDS-V0_1-STAGE038-P3", stage["current_task_id"])
        self.assertEqual("Phase 4", stage["next_phase"])
        self.assertEqual("IDS-STAGE038-P4-GATE", stage["next_gate"])
        self.assertFalse(batch["upload_gate"]["push_allowed"])
        self.assertEqual(
            "IDS-V0_1-STAGE038-P4",
            batch["decision"]["next_allowed_task_id"],
        )

        roadmap_stage = next(
            item
            for item in roadmap["stages"]
            if item.get("stage_id") == "IDS-STAGE038"
        )
        phases = {item["phase_id"]: item for item in roadmap_stage["phases"]}
        self.assertEqual("passed_with_local_evidence", phases["IDS-STAGE038-P2"]["status"])
        self.assertEqual(
            "passed_with_local_evidence",
            phases["IDS-STAGE038-P3"]["status"],
        )
        self.assertEqual("planned", phases["IDS-STAGE038-P4"]["status"])
        self.assertEqual("IDS-STAGE038-P4-GATE", roadmap["next_gate_id"])

        events = [
            json.loads(line)
            for line in EVENTS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        matching = [
            event
            for event in events
            if event.get("event_id")
            == "EVT-IDS-V0_1-STAGE038-P2-20260713-001"
        ]
        self.assertEqual(1, len(matching), matching)
        event = matching[0]
        self.assertEqual("phase_completed", event["event_type"])
        self.assertEqual("IDS-V0_1-STAGE038-P2", event["task_id"])
        self.assertIn("queue_runtime_performed=true", event["notes"])
        self.assertIn("worker_runtime_performed=true", event["notes"])
        self.assertIn("production_runtime_activation_performed=false", event["notes"])
        self.assertIn("raw_metadata_content_accessed=false", event["notes"])
        self.assertIn("fake_ids_business_data_used=false", event["notes"])
        self.assertIn("push_allowed=false", event["notes"])

    def test_cli_emits_one_truthful_json_report_without_runtime_files(self):
        completed = subprocess.run(
            [sys.executable, "-B", str(CHECKER)],
            cwd=ROOT.parent,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr or completed.stdout)
        self.assertEqual("", completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["contract_valid"], payload)
        self.assertTrue(payload["slice_valid"], payload)
        self.assertEqual("IDS-V0_1-STAGE038-P2", payload["task_id"])
        self.assertEqual("IDS-STAGE038-P3-GATE", payload["next_gate"])
        self.assertFalse(payload["github_upload_allowed"])
        self.assertFalse(payload["app_reinstall_allowed"])


if __name__ == "__main__":
    unittest.main()
