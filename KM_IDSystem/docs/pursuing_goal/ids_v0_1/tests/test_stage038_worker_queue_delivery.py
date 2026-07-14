import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
CHECKER = ROOT / "scripts" / "check_worker_queue_delivery.py"
INDEX = (
    PURSUE_ROOT
    / "worker_queue_baseline"
    / "stage038_worker_queue_delivery_contract.json"
)
PHASE4 = PURSUE_ROOT / "STAGE038_PHASE4_CLOSEOUT.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage038WorkerQueuePhase4DeliveryTests(unittest.TestCase):
    def _load_checker(self):
        self.assertTrue(CHECKER.is_file(), f"missing Phase 4 checker: {CHECKER}")
        spec = importlib.util.spec_from_file_location(
            "stage038_worker_queue_delivery", CHECKER
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_delivery_contract_binds_exact_phase2_phase3_and_state_sources(self):
        self.assertTrue(INDEX.is_file(), f"missing delivery index: {INDEX}")
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        module = self._load_checker()
        report = module.build_stage038_phase4_delivery_report(
            index=index,
            execute_delivery_checks=False,
        )

        self.assertEqual(
            "ids.stage038.worker_queue_baseline.phase4.index.v1",
            index["schema_version"],
        )
        self.assertEqual("IDS-V0_1-STAGE038-P4", index["task_id"])
        self.assertEqual("ACC-STAGE-038", index["acceptance_id"])
        self.assertTrue(report["contract_valid"], report)
        self.assertTrue(all(report["source_integrity"].values()), report)
        self.assertFalse(report["delivery_checks_performed"])
        self.assertEqual(
            "blocked_delivery_checks_not_executed",
            report["stage_review_status"],
        )
        self.assertEqual("IDS-STAGE038-P4-GATE", report["next_gate"])

        tampered = json.loads(json.dumps(index))
        tampered["cleanup_allowlist"]["eligible_artifact_classes"].append(
            "FACT_SOURCE"
        )
        blocked = module.build_stage038_phase4_delivery_report(
            index=tampered,
            execute_delivery_checks=True,
        )
        self.assertFalse(blocked["contract_valid"], blocked)
        self.assertFalse(blocked["delivery_contract_valid"], blocked)
        self.assertFalse(blocked["delivery_checks_performed"])
        self.assertEqual(
            "blocked_invalid_delivery_contract",
            blocked["stage_review_status"],
        )
        self.assertEqual("IDS-STAGE038-P4-GATE", blocked["next_gate"])

        for mutation in ("root", "nested"):
            injected = json.loads(json.dumps(index))
            if mutation == "root":
                injected["production_runtime_activation_allowed"] = True
            else:
                injected["recovery_boundary"][
                    "same_operation_resubmission_available"
                ] = True
            with self.subTest(mutation=mutation):
                rejected = module.build_stage038_phase4_delivery_report(
                    index=injected,
                    execute_delivery_checks=False,
                )
                self.assertFalse(rejected["contract_valid"], rejected)
                self.assertFalse(rejected["delivery_contract_valid"], rejected)

    def test_job_state_graph_is_exact_and_has_renderable_mermaid(self):
        report = self._load_checker().build_stage038_phase4_delivery_report()
        graph = report["job_state_graph"]

        self.assertTrue(report["delivery_contract_valid"], report)
        self.assertEqual("ids.job_state.v1", graph["state_model_version"])
        self.assertEqual(8, len(graph["job_types"]))
        self.assertEqual(11, len(graph["job_states"]))
        self.assertEqual(
            ["SUCCEEDED", "FAILED", "DEAD_LETTERED", "CANCELLED"],
            graph["terminal_states"],
        )
        self.assertEqual(21, graph["allowed_transition_count"])
        self.assertEqual(21, len(graph["allowed_transitions_flat"]))
        self.assertIn("stateDiagram-v2", graph["mermaid_state_diagram"])
        self.assertIn("QUEUED --> CLAIMED", graph["mermaid_state_diagram"])
        self.assertIn("RUNNING --> FAILED", graph["mermaid_state_diagram"])

    def test_failure_retry_log_is_actual_bounded_and_not_fake_retry_runtime(self):
        report = self._load_checker().build_stage038_phase4_delivery_report()
        log = report["failure_retry_log"]

        self.assertTrue(log["actual_isolated_worker_exception_observed"])
        self.assertEqual(
            ["QUEUED", "CLAIMED", "RUNNING", "FAILED"],
            log["state_history"],
        )
        self.assertEqual("error:RuntimeError", log["error_ref"])
        self.assertEqual([], log["output_refs"])
        self.assertIsNone(log["checkpoint_ref"])
        self.assertGreaterEqual(len(log["transition_audit"]), 3)
        self.assertEqual(0, log["baseline_max_retries"])
        self.assertEqual(
            "NOT_AVAILABLE_BASELINE_MAX_RETRIES_ZERO_STAGE039_OWNED",
            log["retry_disposition"],
        )
        self.assertEqual(
            "REVIEW_ERROR_NO_SAME_OPERATION_RESUBMISSION_UNTIL_STAGE039",
            log["owner_action"],
        )
        self.assertFalse(log["same_operation_resubmission_available"])
        self.assertEqual(
            "EXISTING_QUEUE_ENTRY",
            log["same_operation_resubmission_result"],
        )
        self.assertFalse(log["automatic_retry_performed"])
        self.assertFalse(log["retry_scheduler_performed"])
        self.assertFalse(log["dead_letter_runtime_performed"])

    def test_backpressure_proof_covers_capacity_resource_and_lock_signals(self):
        report = self._load_checker().build_stage038_phase4_delivery_report()
        proof = report["backpressure_trigger_proof"]

        capacity = proof["capacity"]
        self.assertTrue(capacity["first_admission_accepted"])
        self.assertEqual("QUEUE_CAPACITY_REACHED", capacity["result_code"])
        self.assertEqual("已暂停", capacity["owner_status"]["label_zh"])
        self.assertEqual(1, capacity["queue_record_count"])
        self.assertFalse(capacity["worker_started"])

        self.assertEqual(
            "PAUSED_EXTERNAL_DRIVE_OFFLINE",
            proof["external_drive_offline"]["result_code"],
        )
        self.assertEqual("PAUSED_LOW_DISK", proof["low_disk"]["result_code"])
        self.assertEqual(
            "PAUSED_EXTERNAL_API_BUDGET_INSUFFICIENT",
            proof["external_api_budget_insufficient"]["result_code"],
        )
        self.assertEqual(
            "RESOURCE_CONFLICT_ACTIVE",
            proof["same_source_conflict"]["result_code"],
        )
        self.assertFalse(proof["measured_backpressure_runtime_performed"])
        self.assertFalse(proof["automatic_resume_performed"])

    def test_cleanup_allowlist_is_narrow_and_protected_surfaces_remain_denied(self):
        report = self._load_checker().build_stage038_phase4_delivery_report()
        cleanup = report["cleanup_allowlist"]

        self.assertEqual(
            ["TEMPORARY_PARTIAL_OUTPUT", "REBUILDABLE_CACHE"],
            cleanup["eligible_artifact_classes"],
        )
        self.assertTrue(cleanup["cleanup_manifest_required"])
        self.assertEqual(
            {
                "ORIGINAL_RAW_DATA",
                "FACT_SOURCE",
                "MANIFEST",
                "EVIDENCE_LEDGER",
                "REPORT_SNAPSHOT",
                "AUDIT_LOG",
                "ACTIVE_INDEX",
                "REQUIRED_CHECKPOINT",
            },
            set(cleanup["protected_artifact_classes"]),
        )
        self.assertTrue(all(cleanup["phase3_protected_ref_checks"].values()))
        self.assertFalse(cleanup["cleanup_runtime_performed"])
        self.assertFalse(cleanup["delete_attempt_performed"])
        self.assertEqual("STAGE-044", cleanup["runtime_owner"])

    def test_recovery_boundary_and_orderly_shutdown_are_explicit(self):
        report = self._load_checker().build_stage038_phase4_delivery_report()
        handling = report["recovery_handling"]
        shutdown = report["safe_shutdown"]

        self.assertEqual([], handling["automatic_recovery_cases"])
        self.assertEqual(
            {
                "WORKER_EXCEPTION",
                "EXTERNAL_DRIVE_OFFLINE",
                "LOW_DISK",
                "QUEUE_CAPACITY_REACHED",
                "SAME_SOURCE_CONFLICT",
                "PROCESS_RESTART",
            },
            set(handling["manual_action_required_cases"]),
        )
        self.assertFalse(handling["crash_recovery_runtime_performed"])
        self.assertFalse(handling["persistent_recovery_available"])
        self.assertFalse(handling["same_operation_resubmission_available"])
        self.assertEqual(
            "STAGE-039",
            handling["same_operation_resubmission_owner"],
        )

        self.assertEqual(
            [
                "STOP_NEW_ADMISSION",
                "DRAIN_ACCEPTED_CONTROL_WORK",
                "VERIFY_TERMINAL_STATE_AND_RELEASED_LOCKS",
                "STOP_ISOLATED_WORKER",
            ],
            shutdown["steps"],
        )
        self.assertEqual("SUCCEEDED", shutdown["final_record"]["machine_state"])
        self.assertTrue(shutdown["queue_closed"])
        self.assertTrue(shutdown["all_resource_locks_released"])
        self.assertEqual(
            "QUEUE_CLOSED",
            shutdown["post_shutdown_submission"]["result_code"],
        )
        self.assertFalse(shutdown["active_work_cancelled"])
        self.assertFalse(shutdown["automatic_shutdown_runtime_performed"])

    def test_delivery_truth_rollback_and_chinese_feedback_are_fail_closed(self):
        report = self._load_checker().build_stage038_phase4_delivery_report()

        self.assertEqual("PASS_ISOLATED_CLOSEOUT_PRODUCTION_DISABLED", report["result"])
        self.assertEqual("pending_next_run", report["stage_review_status"])
        self.assertEqual("IDS-STAGE038-REVIEW-GATE", report["next_gate"])
        self.assertFalse(report["execution_ready"])
        self.assertFalse(report["production_runtime_activation_performed"])
        self.assertFalse(report["persistent_queue_write_performed"])
        self.assertFalse(report["retry_scheduler_performed"])
        self.assertFalse(report["measured_backpressure_runtime_performed"])
        self.assertFalse(report["production_lock_runtime_performed"])
        self.assertFalse(report["automatic_lifecycle_runtime_performed"])
        self.assertFalse(report["crash_recovery_runtime_performed"])
        self.assertFalse(report["cleanup_runtime_performed"])
        self.assertFalse(report["raw_metadata_content_accessed"])
        self.assertFalse(report["fake_ids_business_data_used"])
        self.assertFalse(report["github_upload_allowed"])
        self.assertFalse(report["app_reinstall_allowed"])
        self.assertGreaterEqual(len(report["rollback_steps"]), 4)
        self.assertIn("整阶段复审", report["owner_feedback_zh"])

    def test_phase4_docs_governance_event_and_cli_stop_at_review_gate(self):
        self.assertTrue(PHASE4.is_file(), f"missing closeout: {PHASE4}")
        text = PHASE4.read_text(encoding="utf-8")
        for term in (
            "IDS-V0_1-STAGE038-P4",
            "ACC-STAGE-038",
            "stateDiagram-v2",
            "failure_retry_log",
            "QUEUE_CAPACITY_REACHED",
            "PAUSED_EXTERNAL_API_BUDGET_INSUFFICIENT",
            "TEMPORARY_PARTIAL_OUTPUT",
            "automatic_recovery_cases=[]",
            "STOP_NEW_ADMISSION",
            "PASS_ISOLATED_CLOSEOUT_PRODUCTION_DISABLED",
            "stage_review_status=pending_next_run",
            "push_allowed=false",
            "NO_STAGE_REVIEW_THIS_RUN",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)

        module = self._load_checker()
        batch = module._parse_yaml_text(BATCH_LOCK.read_text(encoding="utf-8"))
        roadmap = module._parse_yaml_text(ROADMAP.read_text(encoding="utf-8"))
        stage = batch["stage_progress"]["STAGE-038"]
        self.assertTrue(
            batch["status"] == "stage038_completed_reviewed_local"
            or batch["status"].startswith("stage039_")
            or batch["status"].startswith("stage040_"),
            batch["status"],
        )
        self.assertEqual(
            ["Phase 1", "Phase 2", "Phase 3", "Phase 4"],
            stage["completed_phases"],
        )
        self.assertEqual("passed", stage["review_status"])
        self.assertEqual("STAGE-039", stage["next_stage"])
        self.assertEqual("IDS-STAGE039-P1-GATE", stage["next_gate"])
        self.assertEqual("IDS-V0_1-STAGE038-REVIEW", stage["current_task_id"])
        self.assertFalse(batch["upload_gate"]["push_allowed"])
        self.assertFalse(batch["decision"]["github_upload_allowed"])

        roadmap_stage = next(
            item for item in roadmap["stages"] if item.get("stage_id") == "IDS-STAGE038"
        )
        phases = {item["phase_id"]: item for item in roadmap_stage["phases"]}
        self.assertEqual(
            "passed_with_local_evidence",
            phases["IDS-STAGE038-P4"]["status"],
        )
        self.assertTrue(
            roadmap["next_gate_id"].startswith("IDS-STAGE039-")
            or roadmap["next_gate_id"].startswith("IDS-STAGE040-")
            or roadmap["next_gate_id"]
            == "IDS-V0_1-BATCH-031-040-REVIEW-GATE"
        )

        events = [
            json.loads(line)
            for line in EVENTS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        matching = [
            item
            for item in events
            if item.get("event_id") == "EVT-IDS-V0_1-STAGE038-P4-20260713-001"
        ]
        self.assertEqual(1, len(matching), matching)
        self.assertEqual("phase_completed", matching[0]["event_type"])
        self.assertEqual("IDS-V0_1-STAGE038-P4", matching[0]["task_id"])
        self.assertIn("delivery_contract_valid=true", matching[0]["notes"])
        self.assertIn("push_allowed=false", matching[0]["notes"])

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
        self.assertTrue(payload["delivery_contract_valid"], payload)
        self.assertEqual("IDS-STAGE038-REVIEW-GATE", payload["next_gate"])


if __name__ == "__main__":
    unittest.main()
