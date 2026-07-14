import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[4]
REPO_ROOT = ROOT.parent
BASE = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
CONTRACT = (
    BASE
    / "backpressure_policy"
    / "stage040_backpressure_delivery_contract.json"
)
EVIDENCE = BASE / "STAGE040_PHASE4_CLOSEOUT.md"
CHECKER = ROOT / "scripts" / "check_backpressure_delivery.py"
BATCH = BASE / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"

EXPECTED_STATE_HISTORY = [
    "QUEUED",
    "CLAIMED",
    "RUNNING",
    "RETRY_WAIT",
    "QUEUED",
    "CLAIMED",
    "RUNNING",
    "RETRY_WAIT",
    "QUEUED",
    "CLAIMED",
    "RUNNING",
    "RETRY_WAIT",
    "DEAD_LETTERED",
]
EXPECTED_PRESSURE_SIGNALS = {
    "QUEUE_SOFT_PRESSURE",
    "QUEUE_HARD_CAPACITY",
    "EXTERNAL_DRIVE_OFFLINE",
    "DISK_SPACE_INSUFFICIENT",
    "EXTERNAL_API_BUDGET_INSUFFICIENT",
    "JOB_TYPE_CONCURRENCY_LIMIT_REACHED",
    "SAME_SOURCE_CONFLICT",
}
EXPECTED_CLEANUP_CLASSES = {
    "TEMP_STAGING_OUTPUT",
    "INCOMPLETE_DERIVATIVE_OUTPUT",
}
EXPECTED_PROTECTED_CLASSES = {
    "FACT_SOURCE",
    "MANIFEST",
    "EVIDENCE_LEDGER",
    "REPORT_SNAPSHOT",
    "AUDIT_LOG",
}


class Stage040BackpressureDeliveryTests(unittest.TestCase):
    def _module(self):
        self.assertTrue(CHECKER.is_file(), f"missing Phase 4 checker: {CHECKER}")
        spec = importlib.util.spec_from_file_location(
            "stage040_backpressure_delivery", CHECKER
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _contract(self):
        self.assertTrue(CONTRACT.is_file(), f"missing Phase 4 contract: {CONTRACT}")
        return json.loads(CONTRACT.read_text(encoding="utf-8"))

    def _report(self):
        return self._module().build_stage040_phase4_delivery_report()

    def test_phase4_contract_sources_and_fail_closed_tampering(self):
        module = self._module()
        contract = self._contract()
        self.assertTrue(EVIDENCE.is_file(), f"missing Phase 4 evidence: {EVIDENCE}")
        checks = module.validate_delivery_contract(contract)
        self.assertTrue(all(checks.values()), checks)
        self.assertEqual("IDS-V0_1-STAGE040-P4", contract["task_id"])
        self.assertEqual("ACC-STAGE-040", contract["acceptance_id"])
        for binding in contract["upstream_bindings"].values():
            path = REPO_ROOT / binding["ref"]
            self.assertTrue(path.is_file(), path)
            self.assertEqual(binding["sha256"], module.sha256_file(path))

        mutations = []
        for mutate in (
            lambda value: value.update({"unknown_root": True}),
            lambda value: value.update({"delivery_contract": []}),
            lambda value: value["cleanup_allowlist"][
                "cleanup_eligible_classes"
            ].append("FACT_SOURCE"),
            lambda value: value["recovery_handling"].update(
                {"successful_automatic_recovery_cases_observed": ["FAKE_SUCCESS"]}
            ),
            lambda value: value["review_gate"].update(
                {"phase4_may_mark_stage_reviewed": True}
            ),
            lambda value: value["truth_flags"].update(
                {"production_runtime_activation_performed": True}
            ),
        ):
            candidate = copy.deepcopy(contract)
            mutate(candidate)
            mutations.append(candidate)
        for candidate in mutations:
            with self.subTest(candidate=candidate):
                blocked = module.build_stage040_phase4_delivery_report(
                    contract=candidate, execute_delivery_checks=True
                )
                self.assertFalse(blocked["contract_valid"], blocked)
                self.assertFalse(blocked["delivery_checks_performed"], blocked)
                self.assertEqual("IDS-STAGE040-P4-GATE", blocked["next_gate"])

    def test_job_state_and_backpressure_decision_graphs_are_exact(self):
        report = self._report()
        graph = report["state_decision_graph"]
        self.assertTrue(report["delivery_contract_valid"], report)
        self.assertEqual("ids.job_state.v1", graph["state_model_version"])
        self.assertEqual(8, len(graph["job_types"]))
        self.assertEqual(11, len(graph["job_states"]))
        self.assertEqual(4, len(graph["terminal_states"]))
        self.assertEqual(21, graph["allowed_transition_count"])
        self.assertEqual(EXPECTED_PRESSURE_SIGNALS, set(graph["pressure_signals"]))
        self.assertEqual(
            {
                "ADMIT",
                "THROTTLE_ADMISSION",
                "DENY_NEW_ADMISSION",
                "PAUSE_RESOURCE_GATE",
                "REQUIRE_MANUAL_REVIEW",
            },
            set(graph["decision_actions"]),
        )
        self.assertIn("stateDiagram-v2", graph["mermaid_state_diagram"])
        self.assertIn("flowchart TD", graph["mermaid_backpressure_flow"])

    def test_failure_retry_log_replays_reviewed_actual_isolated_evidence(self):
        log = self._report()["failure_retry_log"]
        self.assertEqual(
            "STAGE039_REVIEWED_PHASE4_ACTUAL_ISOLATED_CONTROL_METADATA",
            log["source"],
        )
        self.assertEqual(EXPECTED_STATE_HISTORY, log["state_history"])
        self.assertEqual(3, log["attempt_count"])
        self.assertEqual(2, log["retry_count"])
        self.assertEqual(2, log["max_retries"])
        self.assertEqual("DEAD_LETTERED", log["final_state"])
        self.assertEqual("exhausted", log["retry_disposition"])
        self.assertEqual([], log["output_refs"])
        self.assertTrue(log["checkpoint_ref"].startswith("checkpoint:sha256:"))
        self.assertTrue(log["reviewed_stage039_delivery_valid"])
        self.assertFalse(log["persisted"])

    def test_backpressure_trigger_proof_covers_required_signals(self):
        proof = self._report()["backpressure_trigger_proof"]
        self.assertEqual(EXPECTED_PRESSURE_SIGNALS, set(proof))
        self.assertEqual(
            "THROTTLE_ADMISSION",
            proof["QUEUE_SOFT_PRESSURE"]["decision_action"],
        )
        self.assertEqual(
            "DENY_NEW_ADMISSION",
            proof["QUEUE_HARD_CAPACITY"]["decision_action"],
        )
        self.assertFalse(proof["QUEUE_HARD_CAPACITY"]["job_created"])
        for signal in (
            "EXTERNAL_DRIVE_OFFLINE",
            "DISK_SPACE_INSUFFICIENT",
            "EXTERNAL_API_BUDGET_INSUFFICIENT",
        ):
            with self.subTest(signal=signal):
                self.assertEqual(
                    "PAUSE_RESOURCE_GATE", proof[signal]["decision_action"]
                )
                self.assertFalse(proof[signal]["retry_budget_consumed"])
        self.assertEqual(
            4,
            proof["JOB_TYPE_CONCURRENCY_LIMIT_REACHED"][
                "throttled_decision_count"
            ],
        )
        self.assertEqual(3, proof["SAME_SOURCE_CONFLICT"]["conflict_count"])

    def test_cleanup_allowlist_is_narrow_and_protected(self):
        cleanup = self._report()["cleanup_allowlist"]
        self.assertEqual(
            EXPECTED_CLEANUP_CLASSES, set(cleanup["cleanup_eligible_classes"])
        )
        self.assertEqual(
            EXPECTED_PROTECTED_CLASSES,
            set(cleanup["protected_artifact_classes"]),
        )
        self.assertTrue(cleanup["cleanup_manifest_required"])
        self.assertEqual(5, cleanup["protected_ref_count"])
        self.assertTrue(all(cleanup["phase3_protected_ref_checks"].values()))
        self.assertFalse(cleanup["cleanup_runtime_performed"])
        self.assertFalse(cleanup["delete_attempt_performed"])
        self.assertEqual("STAGE-044", cleanup["runtime_owner"])

    def test_automatic_and_manual_recovery_classification_is_truthful(self):
        handling = self._report()["recovery_handling"]
        self.assertTrue(handling["healthy_new_admission_observed"])
        self.assertEqual([], handling["automatic_recovery_eligible_cases"])
        self.assertEqual(
            [], handling["successful_automatic_recovery_cases_observed"]
        )
        self.assertIn(
            "UNKNOWN_OR_STALE_OBSERVATION",
            handling["manual_action_required_cases"],
        )
        self.assertIn(
            "WORKER_PROCESS_EXCEPTION",
            handling["manual_action_required_cases"],
        )
        self.assertIn(
            "RESOURCE_GATE_OWNER_REVALIDATION",
            handling["manual_action_required_cases"],
        )
        self.assertFalse(handling["automatic_resume_allowed"])
        self.assertFalse(handling["automatic_resume_performed"])
        self.assertEqual("STAGE-042", handling["automatic_resume_runtime_owner"])

    def test_safe_shutdown_recovery_and_rollback_are_explicit(self):
        report = self._report()
        shutdown = report["safe_shutdown_and_recovery"]
        self.assertTrue(shutdown["transport_orderly_shutdown_proved"])
        self.assertTrue(shutdown["transport_queue_closed"])
        self.assertTrue(shutdown["transport_resource_locks_released"])
        self.assertFalse(shutdown["persistent_backpressure_state_available_after_exit"])
        self.assertFalse(shutdown["process_termination_performed"])
        self.assertFalse(shutdown["automatic_process_recovery_performed"])
        self.assertIn("STOP_NEW_ADMISSION_DECISIONS", shutdown["shutdown_steps"])
        self.assertIn(
            "REOBSERVE_QUEUE_DISK_DRIVE_AND_API_BUDGET",
            shutdown["recovery_steps"],
        )
        self.assertGreaterEqual(len(report["rollback_steps"]), 6)
        self.assertIn(
            "DENY_NEW_ADMISSION_REQUIRE_MANUAL_REVIEW",
            report["rollback_steps"],
        )

    def test_delivery_truth_and_chinese_feedback_stop_at_review(self):
        report = self._report()
        self.assertEqual(
            "PASS_ISOLATED_CLOSEOUT_PRODUCTION_DISABLED", report["result"]
        )
        self.assertEqual("pending_next_run", report["stage_review_status"])
        self.assertEqual("IDS-STAGE040-REVIEW-GATE", report["next_gate"])
        self.assertFalse(report["execution_ready"])
        for flag in (
            "production_runtime_activation_performed",
            "persistent_queue_write_performed",
            "database_connection_performed",
            "runtime_output_written",
            "ids_business_source_read_performed",
            "raw_metadata_content_accessed",
            "fake_ids_business_data_used",
            "real_ids_business_job_created",
            "production_lock_runtime_performed",
            "automatic_resume_performed",
            "process_crash_recovery_performed",
            "cleanup_runtime_performed",
            "whole_stage_review_performed",
            "batch_review_performed",
            "github_upload_allowed",
            "app_reinstall_allowed",
        ):
            with self.subTest(flag=flag):
                self.assertFalse(report[flag])
        self.assertIn("整阶段复审", report["owner_feedback_zh"])
        self.assertIn("未观察到自动恢复成功", report["owner_feedback_zh"])
        self.assertIn("不是生产运行或生产就绪证明", report["owner_feedback_zh"])

    def test_phase4_governance_routes_only_to_whole_stage_review(self):
        self.assertTrue(EVIDENCE.is_file(), f"missing closeout: {EVIDENCE}")
        batch = BATCH.read_text(encoding="utf-8")
        roadmap = ROADMAP.read_text(encoding="utf-8")
        self.assertIn('status: "stage040_phase4_completed_review_pending"', batch)
        self.assertIn('next_gate: "IDS-STAGE040-REVIEW-GATE"', batch)
        self.assertIn(
            'next_allowed_task_id: "IDS-V0_1-STAGE040-REVIEW"', batch
        )
        self.assertIn('current_phase_id: "IDS-STAGE040-P4"', roadmap)
        self.assertIn('next_gate_id: "IDS-STAGE040-REVIEW-GATE"', roadmap)
        self.assertIn('push_allowed: false', batch)

        events = [
            json.loads(line)
            for line in EVENTS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        matching = [
            item
            for item in events
            if item.get("event_id") == "EVT-IDS-V0_1-STAGE040-P4-20260714-001"
        ]
        self.assertEqual(1, len(matching), matching)
        self.assertEqual("phase_completed", matching[0]["event_type"])
        self.assertEqual("IDS-V0_1-STAGE040-P4", matching[0]["task_id"])
        self.assertIn("whole_stage_review_performed=false", matching[0]["notes"])
        self.assertIn("batch_review_performed=false", matching[0]["notes"])
        self.assertIn("push_allowed=false", matching[0]["notes"])

    def test_cli_returns_exact_machine_report(self):
        module = self._module()
        completed = subprocess.run(
            [sys.executable, "-B", str(CHECKER)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr or completed.stdout)
        self.assertEqual("", completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["delivery_contract_valid"], payload)
        self.assertEqual("IDS-STAGE040-REVIEW-GATE", payload["next_gate"])
        self.assertEqual(module.VALID_RESULT, payload["result"])


if __name__ == "__main__":
    unittest.main()
