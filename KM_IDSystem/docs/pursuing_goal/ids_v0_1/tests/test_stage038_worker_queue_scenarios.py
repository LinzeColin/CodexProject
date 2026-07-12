import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
BASELINE_CHECKER = ROOT / "scripts" / "check_worker_queue_baseline.py"
SCENARIO_CHECKER = ROOT / "scripts" / "check_worker_queue_scenarios.py"
SCENARIO_INDEX = (
    PURSUE_ROOT
    / "worker_queue_baseline"
    / "stage038_worker_queue_scenarios.json"
)
PHASE3 = PURSUE_ROOT / "STAGE038_PHASE3_WORKER_QUEUE_SCENARIOS.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"
CONTROL_INPUT_REF = (
    "repo:KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
    "STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md"
)


def _load_module(path: Path, name: str):
    if not path.is_file():
        raise AssertionError(f"missing module: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Stage038WorkerQueuePhase3ScenarioTests(unittest.TestCase):
    def _baseline(self):
        return _load_module(BASELINE_CHECKER, "stage038_phase2_for_phase3_tests")

    def _scenarios(self):
        return _load_module(SCENARIO_CHECKER, "stage038_phase3_scenarios")

    def test_same_source_lock_key_is_independent_of_operation_type(self):
        module = self._baseline()
        envelopes = [
            module.build_control_envelope(CONTROL_INPUT_REF, job_type=job_type)
            for job_type in ("ARCHIVE", "PARSE", "INDEX", "REPORT")
        ]

        self.assertEqual(4, len({item["job_id"] for item in envelopes}))
        self.assertEqual(4, len({item["idempotency_key"] for item in envelopes}))
        self.assertEqual(1, len({item["lock_key"] for item in envelopes}))

    def test_active_same_source_operations_are_blocked_before_queueing(self):
        module = self._baseline()
        queue = module.IsolatedWorkerQueue(capacity=4)
        decisions = [
            queue.submit(
                module.build_control_envelope(CONTROL_INPUT_REF, job_type=job_type)
            )
            for job_type in ("ARCHIVE", "PARSE", "INDEX", "REPORT")
        ]

        self.assertTrue(decisions[0]["accepted"], decisions)
        self.assertEqual(
            ["RESOURCE_CONFLICT_ACTIVE"] * 3,
            [item["result_code"] for item in decisions[1:]],
        )
        self.assertTrue(all(not item["accepted"] for item in decisions[1:]))
        self.assertEqual(1, queue.queue_size)
        self.assertEqual(1, queue.record_count)

    def test_phase3_machine_contract_binds_repaired_phase2_sources(self):
        self.assertTrue(SCENARIO_INDEX.is_file(), f"missing index: {SCENARIO_INDEX}")
        index = json.loads(SCENARIO_INDEX.read_text(encoding="utf-8"))
        report = self._scenarios().build_stage038_phase3_report(
            index=index,
            execute_scenarios=False,
        )

        self.assertEqual(
            "ids.stage038.worker_queue_baseline.phase3.index.v1",
            index["schema_version"],
        )
        self.assertEqual("IDS-V0_1-STAGE038-P3", index["task_id"])
        self.assertEqual("ACC-STAGE-038", index["acceptance_id"])
        self.assertTrue(report["contract_valid"], report)
        self.assertTrue(all(report["source_integrity"].values()), report)
        self.assertFalse(report["scenario_runtime_performed"])

        tampered = json.loads(json.dumps(index))
        tampered["lock_contract"]["resource_conflict_result"] = "ALLOW"
        blocked = self._scenarios().build_stage038_phase3_report(
            index=tampered,
            execute_scenarios=True,
        )
        self.assertFalse(blocked["contract_valid"], blocked)
        self.assertFalse(blocked["scenario_validation_valid"], blocked)
        self.assertFalse(blocked["scenario_runtime_performed"])

    def test_six_required_scenarios_pass_with_truthful_side_effect_flags(self):
        report = self._scenarios().build_stage038_phase3_report()
        expected = (
            "duplicate_click_one_execution",
            "worker_crash_exception_and_lock_release",
            "external_drive_offline_pause_before_queue",
            "actual_low_disk_boundary_pause_without_allocation",
            "same_source_cross_operation_lock",
            "protected_cleanup_denied",
        )

        self.assertTrue(report["contract_valid"], report)
        self.assertTrue(report["scenario_validation_valid"], report)
        self.assertEqual(expected, tuple(report["scenario_results"]))
        self.assertTrue(
            all(item["status"] == "PASS" for item in report["scenario_results"].values())
        )
        self.assertTrue(report["scenario_runtime_performed"])
        self.assertTrue(report["isolated_queue_runtime_performed"])
        self.assertTrue(report["actual_worker_exception_performed"])
        self.assertTrue(report["actual_disk_observation_performed"])
        self.assertFalse(report["physical_drive_removal_performed"])
        self.assertFalse(report["disk_allocation_performed"])
        self.assertFalse(report["cleanup_runtime_performed"])
        self.assertFalse(report["protected_ref_delete_performed"])
        self.assertFalse(report["production_runtime_activation_performed"])
        self.assertFalse(report["ids_business_source_read_performed"])
        self.assertFalse(report["raw_metadata_content_accessed"])
        self.assertFalse(report["fake_ids_business_data_used"])
        self.assertFalse(report["github_upload_allowed"])
        self.assertFalse(report["app_reinstall_allowed"])

    def test_worker_exception_is_terminal_and_same_source_lock_is_reusable(self):
        result = self._scenarios().build_stage038_phase3_report()[
            "scenario_results"
        ]["worker_crash_exception_and_lock_release"]

        self.assertEqual("FAILED", result["failed_record"]["machine_state"])
        self.assertEqual("处理失败", result["failed_record"]["owner_status"]["label_zh"])
        self.assertEqual([], result["failed_record"]["output_refs"])
        self.assertIsNone(result["failed_record"]["checkpoint_ref"])
        self.assertEqual("error:RuntimeError", result["failed_record"]["error_ref"])
        self.assertTrue(result["lock_released_after_failure"])
        self.assertTrue(result["followup_same_source_admitted"])
        self.assertEqual("SUCCEEDED", result["followup_record"]["machine_state"])
        self.assertFalse(result["process_termination_performed"])

    def test_resource_pause_scenarios_stop_before_queue_or_allocation(self):
        report = self._scenarios().build_stage038_phase3_report()
        offline = report["scenario_results"][
            "external_drive_offline_pause_before_queue"
        ]
        low_disk = report["scenario_results"][
            "actual_low_disk_boundary_pause_without_allocation"
        ]

        self.assertEqual("PAUSED_EXTERNAL_DRIVE_OFFLINE", offline["result_code"])
        self.assertEqual("已暂停", offline["owner_status"]["label_zh"])
        self.assertEqual(0, offline["queue_records_created"])
        self.assertFalse(offline["physical_drive_event_observed"])
        self.assertEqual("CONTROL_GATE_INPUT_ONLY", offline["scenario_mode"])

        self.assertGreater(low_disk["observed_free_bytes"], 0)
        self.assertEqual(
            low_disk["observed_free_bytes"] + 1,
            low_disk["required_bytes"],
        )
        self.assertEqual("PAUSED_LOW_DISK", low_disk["result_code"])
        self.assertEqual(0, low_disk["queue_records_created"])
        self.assertFalse(low_disk["allocation_performed"])

    def test_cleanup_evaluator_denies_every_protected_artifact_class(self):
        result = self._scenarios().build_stage038_phase3_report()[
            "scenario_results"
        ]["protected_cleanup_denied"]
        self.assertEqual(
            {"FACT_SOURCE", "EVIDENCE_LEDGER", "REPORT_SNAPSHOT", "AUDIT_LOG"},
            set(result["artifact_results"]),
        )
        for artifact_class, decision in result["artifact_results"].items():
            with self.subTest(artifact_class=artifact_class):
                self.assertFalse(decision["delete_allowed"])
                self.assertEqual("PROTECTED_ARTIFACT", decision["result_code"])
                self.assertTrue(decision["git_tracked"])
        self.assertEqual(0, result["delete_attempt_count"])
        self.assertEqual(0, result["deleted_ref_count"])

    def test_phase3_docs_governance_event_and_cli_advance_only_to_phase4(self):
        self.assertTrue(PHASE3.is_file(), f"missing evidence: {PHASE3}")
        text = PHASE3.read_text(encoding="utf-8")
        for term in (
            "IDS-V0_1-STAGE038-P3",
            "ACC-STAGE-038",
            "six required scenarios",
            "RESOURCE_CONFLICT_ACTIVE",
            "physical_drive_removal_performed=false",
            "cleanup_runtime_performed=false",
            "raw_metadata_content_accessed=false",
            "fake_ids_business_data_used=false",
            "push_allowed=false",
            "NO_PHASE4",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)

        scenarios = self._scenarios()
        batch = scenarios._parse_yaml_text(BATCH_LOCK.read_text(encoding="utf-8"))
        roadmap = scenarios._parse_yaml_text(ROADMAP.read_text(encoding="utf-8"))
        stage = batch["stage_progress"]["STAGE-038"]
        self.assertEqual("stage038_phase3_completed", batch["status"])
        self.assertEqual(["Phase 1", "Phase 2", "Phase 3"], stage["completed_phases"])
        self.assertEqual("IDS-V0_1-STAGE038-P3", stage["current_task_id"])
        self.assertEqual("Phase 4", stage["next_phase"])
        self.assertEqual("IDS-STAGE038-P4-GATE", stage["next_gate"])
        self.assertFalse(batch["upload_gate"]["push_allowed"])
        self.assertEqual("IDS-V0_1-STAGE038-P4", batch["decision"]["next_allowed_task_id"])

        roadmap_stage = next(
            item for item in roadmap["stages"] if item.get("stage_id") == "IDS-STAGE038"
        )
        phases = {item["phase_id"]: item for item in roadmap_stage["phases"]}
        self.assertEqual("passed_with_local_evidence", phases["IDS-STAGE038-P3"]["status"])
        self.assertEqual("planned", phases["IDS-STAGE038-P4"]["status"])
        self.assertEqual("IDS-STAGE038-P4-GATE", roadmap["next_gate_id"])

        events = [
            json.loads(line)
            for line in EVENTS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        matching = [
            item
            for item in events
            if item.get("event_id") == "EVT-IDS-V0_1-STAGE038-P3-20260713-001"
        ]
        self.assertEqual(1, len(matching), matching)
        self.assertEqual("validation", matching[0]["event_type"])
        self.assertEqual("IDS-V0_1-STAGE038-P3", matching[0]["task_id"])
        self.assertIn("scenario_validation_valid=true", matching[0]["notes"])
        self.assertIn("cleanup_runtime_performed=false", matching[0]["notes"])
        self.assertIn("push_allowed=false", matching[0]["notes"])

        completed = subprocess.run(
            [sys.executable, "-B", str(SCENARIO_CHECKER)],
            cwd=ROOT.parent,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr or completed.stdout)
        self.assertEqual("", completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["scenario_validation_valid"], payload)
        self.assertEqual("IDS-STAGE038-P4-GATE", payload["next_gate"])


if __name__ == "__main__":
    unittest.main()
