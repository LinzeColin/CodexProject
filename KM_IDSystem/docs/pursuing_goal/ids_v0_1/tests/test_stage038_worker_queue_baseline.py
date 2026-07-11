import importlib.util
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE038_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE038_PHASE1_WORKER_QUEUE_SCOPE_BOUNDARY.md"
SOURCE_REVERIFICATION = PURSUE_ROOT / "STAGE038_PHASE1_SOURCE_REVERIFICATION.md"
SOURCE_REVIEW = PURSUE_ROOT / "STAGE038_PHASE1_SOURCE_REVERIFICATION_REVIEW.md"
EXECUTION_INDEX = PURSUE_ROOT / "V0_1_STAGE_EXECUTION_INDEX.json"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"
VALIDATOR = PURSUE_ROOT / "validate_stage005_governance_regression.py"


class Stage038WorkerQueueBaselinePhase1Tests(unittest.TestCase):
    def _combined_contract(self) -> str:
        for path in (ENTRY, PHASE1, SOURCE_REVERIFICATION, SOURCE_REVIEW):
            self.assertTrue(path.is_file(), f"missing Stage038 evidence: {path}")
        return "\n".join(
            path.read_text(encoding="utf-8")
            for path in (ENTRY, PHASE1, SOURCE_REVERIFICATION, SOURCE_REVIEW)
        )

    def _normalized_contract(self) -> str:
        return " ".join(self._combined_contract().split())

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

    def _source_reverification_checks(self) -> dict[str, bool]:
        validator = self._load_validator()
        return validator.evaluate_stage038_source_reverification(
            BATCH_LOCK.read_text(encoding="utf-8"),
            ROADMAP.read_text(encoding="utf-8"),
            ENTRY.read_text(encoding="utf-8"),
            PHASE1.read_text(encoding="utf-8"),
            SOURCE_REVERIFICATION.read_text(encoding="utf-8"),
            SOURCE_REVIEW.read_text(encoding="utf-8"),
        )

    def test_phase1_binds_unique_verified_source_and_truthful_hashes(self):
        index_entry = self._stage_index_entry()
        self.assertEqual("D07-S002", index_entry["local_code"])
        self.assertEqual("Worker 队列基线", index_entry["title"])
        self.assertEqual("ACC-STAGE-038", index_entry["acceptance_id"])
        self.assertEqual(
            "stages/STAGE-038_Worker队列基线.md", index_entry["taskpack_file"]
        )

        text = self._normalized_contract()
        for term in (
            "STAGE-038 · Worker 队列基线",
            "IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY",
            "ACC-STAGE-038",
            "D07-S002",
            "D07 · 任务编排与机器控制",
            "IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-038_Worker队列基线.md",
            "/Users/linzezhang/Downloads/IDS_Taskpack_v0_1_only_中文修订版.zip",
            "Phase 1 · 范围、输入输出与边界确认",
            "P0 source verification: SOURCE_VERIFIED",
            "P0 SHA-256: 613acde3cc8f9b8fdc267eb1b0f3076fbce6e858a0d00c3840a2bd730faa7634",
            "source_archive_sha256=55b782e338610aab6361b7945bb5e290ba60038a06cc765c7c2da801734db6d3",
            "roadmap_sha256=a193fd2c44c51d634bf7887a1a6baf7e5199d9a8535e4211e35e97588e2e21a6",
            "instructions_sha256=ce456e06136d5ecc56cd7c9dc926abb5894817dda87bf7667588bf85211794f8",
            "source_member_match_count=1",
            "source_reverification_required_before_phase2=false",
            "independent_review_status=passed",
            "phase2_entry_authorized=true",
            "建立异步 worker 队列，避免长任务阻塞前端和 API。",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)
        self.assertNotIn("EXTERNAL_TASKPACK_ABSENT", text)
        self.assertNotIn("UNKNOWN_UNDER_IDS-V0_1-STAGE038-P1", text)
        self.assertNotIn("source_reverification_required_before_phase2=true", text)
        checks = self._source_reverification_checks()
        self.assertTrue(all(checks.values()), checks)

    def test_queue_contract_reuses_stage037_envelope_and_state_authority(self):
        text = self._normalized_contract()
        for term in (
            "worker_queue_contract_id=ids.worker_queue_baseline.v0_1.p1",
            "worker_queue_contract_status=SOURCE_RECONCILED_PHASE1_CONTRACT",
            "job_control_envelope_schema=ids.job_control_envelope.v1",
            "job_state_model_version=ids.job_state.v1",
            "Only `QUEUED` jobs are queue-eligible",
            "Queue status is not a second job lifecycle state",
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

    def test_priority_ordering_dependency_and_idempotency_are_source_reconciled(self):
        text = self._normalized_contract()
        for term in (
            "P0_CRITICAL_ENGINEERING_DATA",
            "P1_HIGH_VALUE_ENGINEERING_DATA",
            "P2_SUPPORTING_ENGINEERING_DATA",
            "P3_LOW_VALUE_OR_DEFERRED_DATA",
            "owner-approved priority_ref",
            "ordering_policy=DEFERRED_TO_PHASE2_NO_NUMERIC_POLICY_IN_P1",
            "numeric priority weights are not invented",
            "enqueue_idempotency_contract=REQUIRE_ENVELOPE_IDEMPOTENCY_KEY_NO_DUPLICATE_ENTRY",
            "idempotency_key is required",
            "duplicate admission must return the existing queue-entry reference",
            "dependency_admission_contract=PHASE2_DEFINITION_REQUIRED_FAIL_CLOSED",
            "missing dependency evidence fails closed",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)
        for invented_term in (
            "ordering tuple: (priority_class_order_ref, admission_sequence, job_id)",
            "idempotency_key=sha256(raw_source_body)",
            "all dependency_refs must be SUCCEEDED",
        ):
            with self.subTest(invented_term=invented_term):
                self.assertNotIn(invented_term, text)

    def test_claim_transport_requires_stage041_lease_lock_and_fencing_proof(self):
        text = self._normalized_contract()
        for term in (
            "claim_transport_contract=PHASE2_DEFINITION_REQUIRED_STAGE041_RUNTIME",
            "claim_atomic_sequence=PHASE2_DEFINITION_REQUIRED_STAGE041_RUNTIME",
            "job_id",
            "expected_state=QUEUED",
            "expected_state_version",
            "lease_owner_ref",
            "lease_expires_at",
            "fencing_token",
            "lock_key",
            "lock_granularity=RESOURCE_CONFLICT_DOMAIN_NOT_GLOBAL_QUEUE",
            "STAGE-041 owns lock, lease, renewal, and fencing runtime",
            "Missing or stale claim proof fails closed",
            "a stale worker cannot commit",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)
        self.assertNotIn("claim_lease_and_lock_acquired=true", text)
        self.assertNotIn("persisted=true", text)

    def test_stage038_baseline_and_downstream_runtime_ownership_are_both_explicit(self):
        text = self._normalized_contract()
        for term in (
            "STAGE-038 defines retry/dead-letter interface",
            "STAGE-038 defines resource-gate backpressure interface",
            "STAGE-038 defines lock granularity and claim-proof requirements",
            "STAGE-038 defines automatic lifecycle interface",
            "STAGE-038 defines crash-recovery checkpoint boundary",
            "STAGE-038 defines cleanup allowlist boundary",
            "STAGE-039 owns retry scheduling and dead-letter runtime",
            "STAGE-040 owns measured backpressure and fairness runtime",
            "STAGE-041 owns lock/lease/fencing runtime",
            "STAGE-042 owns automatic run, pause, resume, and shutdown runtime",
            "STAGE-043 owns worker-crash recovery runtime",
            "STAGE-044 owns half-product cleanup runtime",
            "external_drive_offline",
            "disk_space_insufficient",
            "external_api_budget_insufficient",
            "cleanup_manifest_ref",
            "Facts, manifests, evidence ledgers, audit logs, and report snapshots are protected",
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
            "STAGE-038 owns retry scheduling runtime",
            "STAGE-038 owns dead-letter runtime",
            "STAGE-038 owns measured backpressure runtime",
            "STAGE-038 owns fairness runtime",
            "STAGE-038 owns lock/lease/fencing runtime",
            "STAGE-038 owns automatic lifecycle runtime",
            "STAGE-038 owns worker-crash recovery runtime",
            "STAGE-038 owns half-product cleanup runtime",
        ):
            with self.subTest(conflicting_owner=conflicting_owner):
                self.assertNotIn(conflicting_owner, text)

    def test_raw_real_data_and_payload_boundaries_remain_fail_closed(self):
        text = self._normalized_contract()
        for term in (
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "不得使用虚构 IDS 业务数据、虚构数据库行、placeholder corpus 或伪造证据",
            "payload_size_bytes <= 1048576",
            "raw source bodies are forbidden",
            "plaintext secrets are forbidden",
            "future queue persistence may store refs, not source content",
            "taskpack_source_read_performed=true",
            "ids_business_source_read_performed=false",
            "raw_metadata_content_accessed=false",
            "database_connection_performed=false",
            "real_job_created=false",
            "fake_ids_business_data_used=false",
        ):
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase2_and_phase3_plans_match_verified_source(self):
        _batch, roadmap = self._parsed_governance()
        stage = next(
            item for item in roadmap["stages"] if item.get("stage_id") == "IDS-STAGE038"
        )
        phases = {item["phase_id"]: item for item in stage["phases"]}
        self.assertEqual("planned", phases["IDS-STAGE038-P2"]["status"])
        self.assertIs(
            True,
            phases["IDS-STAGE038-P2"]["isolated_non_production_runtime_allowed"],
        )
        self.assertIs(
            False,
            phases["IDS-STAGE038-P2"]["production_runtime_activation_allowed"],
        )
        self.assertEqual("planned", phases["IDS-STAGE038-P3"]["status"])
        phase2 = json.dumps(phases["IDS-STAGE038-P2"], ensure_ascii=False)
        for term in (
            "minimal asynchronous worker queue slice",
            "long tasks do not block frontend or API request lifecycles",
            "machine state to restrained Chinese owner status",
            "input/output/error/checkpoint refs",
            "state transitions",
            "at least one retry, backpressure, or automatic-run slice",
            "STAGE-039..044 retain runtime ownership",
            "no raw metadata access or fake IDS business data",
        ):
            with self.subTest(term=term):
                self.assertIn(term, phase2)
        self.assertNotIn("start worker", phase2.lower())
        self.assertNotIn("connect PostgreSQL", phase2)
        self.assertNotIn("Implementation would enqueue, claim, run a worker", phase2)

        phase3 = json.dumps(phases["IDS-STAGE038-P3"], ensure_ascii=False)
        for term in (
            "duplicate clicks",
            "worker crash",
            "external drive removal",
            "low disk",
            "concurrent processing of the same file",
            "locks prevent duplicate processing, extraction, indexing, and reports",
            "cleanup preserves facts, evidence ledgers, audit logs, and report snapshots",
        ):
            with self.subTest(term=term):
                self.assertIn(term, phase3)
        self.assertNotIn("static contract", phase3)

    def test_batch_roadmap_and_event_track_source_reverification_without_upload(self):
        batch, roadmap = self._parsed_governance()
        stage = batch["stage_progress"]["STAGE-038"]
        decision = batch["decision"]
        self.assertEqual("stage038_phase1_source_reverified", batch["status"])
        self.assertEqual(["Phase 1"], stage["completed_phases"])
        self.assertEqual("SOURCE_VERIFIED", stage["source_verification_status"])
        self.assertEqual("passed", stage["source_reverification_gate_status"])
        self.assertIs(True, stage["phase2_entry_authorized"])
        self.assertEqual("Phase 2", stage["next_phase"])
        self.assertEqual("IDS-STAGE038-P2-GATE", stage["next_gate"])
        self.assertEqual(
            "IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY", stage["current_task_id"]
        )
        self.assertEqual("ACC-STAGE-038", stage["acceptance_id"])
        self.assertEqual(
            "phase1_source_reverified_phase2_authorized",
            stage["acceptance_status"],
        )
        self.assertEqual("IDS-V0_1-STAGE038-P2", decision["next_allowed_task_id"])
        self.assertIs(False, decision["github_upload_allowed"])
        self.assertIs(False, batch["upload_gate"]["push_allowed"])

        self.assertEqual("IDS-STAGE038", roadmap["current_stage_id"])
        self.assertEqual("IDS-STAGE038-P1", roadmap["current_phase_id"])
        self.assertEqual(
            "IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY", roadmap["current_task_id"]
        )
        self.assertEqual("IDS-STAGE038-P2-GATE", roadmap["next_gate_id"])
        roadmap_stage = next(
            item for item in roadmap["stages"] if item.get("stage_id") == "IDS-STAGE038"
        )
        phase1 = next(
            item
            for item in roadmap_stage["phases"]
            if item.get("phase_id") == "IDS-STAGE038-P1"
        )
        self.assertEqual("passed_with_local_evidence", phase1["status"])
        tasks = {item["task_id"]: item for item in phase1["tasks"]}
        self.assertEqual(
            "completed",
            tasks["IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY"]["status"],
        )

        events = [
            json.loads(line)
            for line in EVENTS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        matching = [
            event
            for event in events
            if event.get("event_id")
            == "EVT-IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY-20260711-001"
        ]
        self.assertEqual(1, len(matching), matching)
        event = matching[0]
        self.assertEqual("source_reverification", event["event_type"])
        self.assertEqual("IDS-V0_1-STAGE038-P1-SOURCE-REVERIFY", event["task_id"])
        self.assertEqual(["ACC-STAGE-038"], event["acceptance_ids"])
        self.assertIn("source_verification_status=SOURCE_VERIFIED", event["notes"])
        self.assertIn("source_member_match_count=1", event["notes"])
        self.assertIn("phase2_entry_authorized=true", event["notes"])
        self.assertIn("taskpack_source_read_performed=true", event["notes"])
        self.assertIn("raw_metadata_content_accessed=false", event["notes"])
        self.assertIn("push_allowed=false", event["notes"])
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
                r"state_registry_write_performed|ids_business_source_read_performed|"
                r"runtime_output_written|real_job_created|"
                r"fake_ids_business_data_used|raw_metadata_content_accessed)=true",
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
            "ids_business_source_read_performed",
            "runtime_output_written",
            "real_job_created",
            "fake_ids_business_data_used",
            "raw_metadata_content_accessed",
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
