import json
import importlib.util
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE038_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md"
EXECUTION_INDEX = PURSUE_ROOT / "V0_1_STAGE_EXECUTION_INDEX.json"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"
VALIDATOR = PURSUE_ROOT / "validate_stage005_governance_regression.py"


class Stage038WorkerQueueBaselinePhase1Tests(unittest.TestCase):
    def _combined_contract(self) -> str:
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing Phase 1 boundary: {PHASE1}")
        return "\n".join(
            [ENTRY.read_text(encoding="utf-8"), PHASE1.read_text(encoding="utf-8")]
        )

    def _stage_index_entry(self) -> dict:
        payload = json.loads(EXECUTION_INDEX.read_text(encoding="utf-8"))
        stages = payload.get("stages", payload)
        self.assertIsInstance(stages, list)
        matching = [item for item in stages if item.get("stage") == "STAGE-038"]
        self.assertEqual(1, len(matching), matching)
        return matching[0]

    def _load_validator(self):
        spec = importlib.util.spec_from_file_location(
            "stage038_governance_validator", VALIDATOR
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _parsed_governance(self) -> tuple[dict, dict]:
        validator = self._load_validator()
        batch = validator._parse_yaml_text(BATCH_LOCK.read_text(encoding="utf-8"))
        roadmap = validator._parse_yaml_text(ROADMAP.read_text(encoding="utf-8"))
        self.assertIsInstance(batch, dict)
        self.assertIsInstance(roadmap, dict)
        return batch, roadmap

    def test_phase1_binds_tracked_stage_identity_without_fabricating_source_hash(self):
        index_entry = self._stage_index_entry()
        self.assertEqual("D07-S002", index_entry["local_code"])
        self.assertEqual("Worker 队列基线", index_entry["title"])
        self.assertEqual("ACC-STAGE-038", index_entry["acceptance_id"])
        self.assertEqual(
            "stages/STAGE-038_Worker队列基线.md", index_entry["taskpack_file"]
        )
        text = self._combined_contract()
        for term in (
            "STAGE-038 · Worker 队列基线",
            "IDS-V0_1-STAGE038-P1",
            "ACC-STAGE-038",
            "D07-S002",
            "D07 · 任务编排与机器控制",
            "IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-038_Worker队列基线.md",
            "Phase 1 · 范围、输入输出与边界确认",
            "P0 source verification: EXTERNAL_TASKPACK_ABSENT",
            "P0 SHA-256: UNKNOWN_UNDER_IDS-V0_1-STAGE038-P1",
            "source_reverification_required_before_phase2=true",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)
        self.assertNotRegex(text, r"P0 SHA-256:\s*`?[0-9a-f]{64}`?")
        self.assertNotIn("source_reverification_required_before_phase2=false", text)

    def test_queue_contract_reuses_stage037_envelope_and_state_authority(self):
        text = self._combined_contract()
        for term in (
            "worker_queue_contract_id=UNASSIGNED_UNTIL_SOURCE_REVERIFICATION",
            "worker_queue_contract_status=PROVISIONAL_SOURCE_LIMITED_BOUNDARY",
            "job_control_envelope_schema=ids.job_control_envelope.v1",
            "job_state_model_version=ids.job_state.v1",
            "only `QUEUED` jobs are queue-eligible",
            "queue status is not a second job lifecycle state",
            "queue entry may contain bounded metadata refs only",
            "job_id",
            "state_version",
            "priority_ref",
            "resource_gate_refs",
            "dependency_refs",
            "audit_ref",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_priority_ordering_dependency_and_idempotency_remain_source_gated(self):
        text = self._combined_contract()
        for term in (
            "P0_CRITICAL_ENGINEERING_DATA",
            "P1_HIGH_VALUE_ENGINEERING_DATA",
            "P2_SUPPORTING_ENGINEERING_DATA",
            "P3_LOW_VALUE_OR_DEFERRED_DATA",
            "owner-approved priority_ref",
            "ordering_policy=UNASSIGNED_UNTIL_SOURCE_REVERIFICATION",
            "numeric priority weights are not invented",
            "enqueue_idempotency_contract=UNASSIGNED_UNTIL_SOURCE_REVERIFICATION",
            "dependency_admission_contract=UNASSIGNED_UNTIL_SOURCE_REVERIFICATION",
            "missing dependency evidence fails closed pending source approval",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)
        for invented_term in (
            "ordering tuple: (priority_class_order_ref, admission_sequence, job_id)",
            "enqueue_idempotency_key=(job_id,state_version,queue_contract_version)",
            "duplicate enqueue returns the existing queue_entry_id",
            "all dependency_refs must be SUCCEEDED",
        ):
            with self.subTest(invented_term=invented_term):
                self.assertNotIn(invented_term, text)

    def test_claim_transport_requires_stage041_lease_lock_and_fencing_proof(self):
        text = self._combined_contract()
        for term in (
            "claim_transport_contract=UNASSIGNED_UNTIL_SOURCE_REVERIFICATION",
            "claim_atomic_sequence=UNASSIGNED_UNTIL_SOURCE_REVERIFICATION",
            "job_id",
            "expected_state=QUEUED",
            "expected_state_version",
            "lease_owner_ref",
            "lease_expires_at",
            "fencing_token",
            "lock_key",
            "STAGE-041 owns lock, lease, renewal, and fencing runtime",
            "missing or stale claim proof fails closed",
            "a stale worker cannot commit",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)
        self.assertNotIn("claim_lease_and_lock_acquired=true", text)
        self.assertNotIn("persisted=true", text)

    def test_downstream_ownership_and_runtime_non_goals_are_exact(self):
        text = self._combined_contract()
        for term in (
            "STAGE-039 owns retry scheduling and dead-letter policy",
            "STAGE-040 owns measured backpressure and fairness policy",
            "STAGE-041 owns lock/lease/fencing runtime",
            "STAGE-042 owns automatic run, pause, resume, and shutdown",
            "STAGE-043 owns worker-crash recovery",
            "STAGE-044 owns half-product cleanup",
            "NO_PHASE2",
            "NO_QUEUE_RUNTIME",
            "NO_WORKER_RUNTIME",
            "NO_CLAIM_PERSISTENCE",
            "NO_SCHEMA_CHANGE",
            "NO_POSTGRES_CONNECTION",
            "NO_RUNTIME_OUTPUT",
            "NO_STAGE039",
            "NO_GITHUB_UPLOAD",
            "NO_APP_REINSTALL",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)
        for conflicting_owner in (
            "STAGE-038 owns retry scheduling",
            "STAGE-038 owns dead-letter policy",
            "STAGE-038 owns measured backpressure",
            "STAGE-038 owns fairness policy",
            "STAGE-038 owns lock/lease/fencing runtime",
            "STAGE-038 owns automatic run",
            "STAGE-038 owns worker-crash recovery",
            "STAGE-038 owns half-product cleanup",
        ):
            with self.subTest(conflicting_owner=conflicting_owner):
                self.assertNotIn(conflicting_owner, text)

    def test_raw_real_data_and_payload_boundaries_remain_fail_closed(self):
        text = self._combined_contract()
        for term in (
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "不得使用虚构 IDS 业务数据、虚构数据库行、placeholder corpus 或伪造证据",
            "payload_size_bytes <= 1048576",
            "raw source bodies are forbidden",
            "plaintext secrets are forbidden",
            "future queue persistence may store refs, not source content",
            "source_read_performed=false",
            "database_connection_performed=false",
            "real_job_created=false",
            "fake_ids_business_data_used=false",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase2_plan_is_static_and_source_reverification_gated(self):
        _batch, roadmap = self._parsed_governance()
        stage = next(
            item for item in roadmap["stages"] if item.get("stage_id") == "IDS-STAGE038"
        )
        phases = {item["phase_id"]: item for item in stage["phases"]}
        self.assertEqual("planned", phases["IDS-STAGE038-P2"]["status"])
        self.assertIs(False, phases["IDS-STAGE038-P2"]["entry_authorized"])
        self.assertEqual(
            "source_reverification_required_before_phase2",
            phases["IDS-STAGE038-P2"]["entry_blocker"],
        )
        self.assertEqual("planned", phases["IDS-STAGE038-P3"]["status"])
        phase2 = json.dumps(phases["IDS-STAGE038-P2"], ensure_ascii=False)
        for term in (
            "machine-readable worker-queue contract/checker",
            "metadata-only deterministic queue candidate evaluation",
            "source_reverification_required_before_phase2",
            "no queue/worker runtime",
        ):
            with self.subTest(term=term):
                self.assertIn(term, phase2)
        self.assertNotIn("start worker", phase2.lower())
        self.assertNotIn("connect PostgreSQL", phase2)

    def test_batch_roadmap_and_event_track_phase1_without_upload(self):
        batch, roadmap = self._parsed_governance()
        stage = batch["stage_progress"]["STAGE-038"]
        decision = batch["decision"]
        self.assertEqual("stage038_phase1_in_progress", batch["status"])
        self.assertEqual(["Phase 1"], stage["completed_phases"])
        self.assertEqual("EXTERNAL_TASKPACK_ABSENT", stage["source_verification_status"])
        self.assertIs(False, stage["phase2_entry_authorized"])
        self.assertEqual("Phase 1 source reverification", stage["next_phase"])
        self.assertEqual("IDS-STAGE038-P1-SOURCE-REVERIFY-GATE", stage["next_gate"])
        self.assertEqual("IDS-V0_1-STAGE038-P1", stage["current_task_id"])
        self.assertEqual("ACC-STAGE-038", stage["acceptance_id"])
        self.assertEqual(
            "phase1_scope_boundary_defined_source_reverification_required",
            stage["acceptance_status"],
        )
        self.assertEqual(
            "IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY",
            decision["next_allowed_task_id"],
        )
        self.assertIs(False, decision["github_upload_allowed"])
        self.assertNotEqual("IDS-V0_1-STAGE038-P2", decision["next_allowed_task_id"])
        self.assertIs(False, batch["upload_gate"]["push_allowed"])

        self.assertEqual("IDS-STAGE038", roadmap["current_stage_id"])
        self.assertEqual("IDS-STAGE038-P1", roadmap["current_phase_id"])
        self.assertEqual("IDS-V0_1-STAGE038-P1", roadmap["current_task_id"])
        self.assertEqual(
            "IDS-STAGE038-P1-SOURCE-REVERIFY-GATE", roadmap["next_gate_id"]
        )
        roadmap_stage = next(
            item for item in roadmap["stages"] if item.get("stage_id") == "IDS-STAGE038"
        )
        phase1 = next(
            item for item in roadmap_stage["phases"]
            if item.get("phase_id") == "IDS-STAGE038-P1"
        )
        self.assertEqual("passed_with_local_evidence", phase1["status"])

        events = [
            json.loads(line)
            for line in EVENTS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        matching = [
            event
            for event in events
            if event.get("event_id") == "EVT-IDS-V0_1-STAGE038-P1-20260711-001"
        ]
        self.assertEqual(1, len(matching), matching)
        event = matching[0]
        self.assertEqual("stage_boundary", event["event_type"])
        self.assertEqual("IDS-V0_1-STAGE038-P1", event["task_id"])
        self.assertEqual(["ACC-STAGE-038"], event["acceptance_ids"])
        self.assertIn("source_verification_status=EXTERNAL_TASKPACK_ABSENT", event["notes"])
        self.assertIn("phase2_entry_authorized=false", event["notes"])
        self.assertIn("push_allowed=false", event["notes"])
        self.assertNotIn("next_gate=", event["notes"])
        self.assertNotRegex(
            event["notes"],
            re.compile(
                r"(?:live_execution_performed|queue_runtime_performed|"
                r"worker_runtime_performed|claim_persistence_performed|"
                r"retry_scheduler_performed|dead_letter_runtime_performed|"
                r"backpressure_runtime_performed|lock_runtime_performed|"
                r"automatic_lifecycle_runtime_performed|"
                r"crash_recovery_runtime_performed|cleanup_runtime_performed|"
                r"database_connection_performed|schema_change_performed|"
                r"state_registry_write_performed|source_read_performed|"
                r"runtime_output_written|real_job_created|"
                r"fake_ids_business_data_used|raw_metadata_content_accessed|"
                r"phase2_entry_authorized)=true",
                re.I,
            ),
        )
        validator = self._load_validator()
        for field in (
            "live_execution_performed",
            "queue_runtime_performed",
            "worker_runtime_performed",
            "claim_persistence_performed",
            "retry_scheduler_performed",
            "dead_letter_runtime_performed",
            "backpressure_runtime_performed",
            "lock_runtime_performed",
            "automatic_lifecycle_runtime_performed",
            "crash_recovery_runtime_performed",
            "cleanup_runtime_performed",
            "database_connection_performed",
            "schema_change_performed",
            "state_registry_write_performed",
            "source_read_performed",
            "runtime_output_written",
            "real_job_created",
            "fake_ids_business_data_used",
            "raw_metadata_content_accessed",
            "phase2_entry_authorized",
        ):
            tampered = json.loads(json.dumps(event))
            tampered["notes"] = tampered["notes"].replace(
                f"{field}=false", f"{field}=true"
            )
            self.assertNotEqual(event["notes"], tampered["notes"], field)
            with self.subTest(field=field):
                self.assertTrue(
                    validator.evaluate_required_event_semantics([tampered]),
                    field,
                )


if __name__ == "__main__":
    unittest.main()
