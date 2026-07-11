import copy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE037_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE037_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE037_PHASE2_JOB_STATE_MODEL_SLICE.md"
PHASE3 = PURSUE_ROOT / "STAGE037_PHASE3_ADVERSARIAL_SCENARIOS.md"
PHASE4 = PURSUE_ROOT / "STAGE037_PHASE4_CLOSEOUT.md"
MODEL_ROOT = PURSUE_ROOT / "job_state_model"
MODEL_INDEX = MODEL_ROOT / "stage037_job_state_model_index.json"
CHECKER = ROOT / "scripts" / "check_job_state_model.py"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage037JobStateModelPhase1Tests(unittest.TestCase):
    def _combined_contract(self) -> str:
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing Phase 1 boundary: {PHASE1}")
        return "\n".join(
            [ENTRY.read_text(encoding="utf-8"), PHASE1.read_text(encoding="utf-8")]
        )

    def _transition_contract(self) -> tuple[dict[str, set[str]], dict[str, str]]:
        text = PHASE1.read_text(encoding="utf-8")
        section = text.split("## Allowed Transition Matrix", 1)[1].split(
            "## Job Control Envelope", 1
        )[0]
        transitions: dict[str, set[str]] = {}
        guards: dict[str, str] = {}
        for line in section.splitlines():
            if not line.startswith("| `"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) != 3:
                continue
            source_match = re.fullmatch(r"`([A-Z_]+)`", cells[0])
            if source_match is None:
                continue
            source = source_match.group(1)
            transitions[source] = set(re.findall(r"`([A-Z_]+)`", cells[1]))
            guards[source] = cells[2]
        return transitions, guards

    def test_phase1_contracts_exist_and_bind_taskpack_identity(self):
        combined = self._combined_contract()
        required_terms = [
            "STAGE-037 · 任务状态模型",
            "IDS-V0_1-STAGE037-P1",
            "ACC-STAGE-037",
            "D07-S001",
            "D07 · 任务编排与机器控制",
            "IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-037_任务状态模型.md",
            "ab1296ab690e445f2ae915ff508d68e9fac40c888cd9ce851bfcc0cf5ce77dc2",
            "定义 import、archive、parse、ocr、chunk、embed、index、report 的统一 job 状态机",
            "Phase 1 · 范围、输入输出与边界确认",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_exact_job_types_states_and_transition_contract(self):
        text = self._combined_contract()
        type_match = re.search(r"Canonical job types:\s*`([^`]+)`", text)
        state_match = re.search(r"Canonical job states:\s*`([^`]+)`", text)
        self.assertIsNotNone(type_match, "missing canonical job type declaration")
        self.assertIsNotNone(state_match, "missing canonical job state declaration")
        job_types = {item.strip() for item in type_match.group(1).split(",")}
        job_states = {item.strip() for item in state_match.group(1).split(",")}

        self.assertEqual(
            {"IMPORT", "ARCHIVE", "PARSE", "OCR", "CHUNK", "EMBED", "INDEX", "REPORT"},
            job_types,
        )
        self.assertEqual(
            {
                "CREATED",
                "QUEUED",
                "CLAIMED",
                "RUNNING",
                "PAUSE_REQUESTED",
                "PAUSED",
                "RETRY_WAIT",
                "SUCCEEDED",
                "FAILED",
                "DEAD_LETTERED",
                "CANCELLED",
            },
            job_states,
        )

        transitions, guards = self._transition_contract()
        self.assertEqual(
            {
                "CREATED": {"QUEUED", "CANCELLED"},
                "QUEUED": {"CLAIMED", "PAUSED", "CANCELLED"},
                "CLAIMED": {"RUNNING", "PAUSE_REQUESTED", "RETRY_WAIT"},
                "RUNNING": {"SUCCEEDED", "PAUSE_REQUESTED", "RETRY_WAIT", "FAILED"},
                "PAUSE_REQUESTED": {"PAUSED", "CANCELLED", "RETRY_WAIT"},
                "PAUSED": {"QUEUED", "CANCELLED"},
                "RETRY_WAIT": {"QUEUED", "PAUSED", "DEAD_LETTERED", "CANCELLED"},
            },
            transitions,
        )
        self.assertIn("claim lease", guards["CLAIMED"])
        self.assertIn("fencing_token", guards["RUNNING"])
        self.assertIn("revoke", guards["PAUSE_REQUESTED"])
        self.assertIn("fencing", guards["PAUSE_REQUESTED"])
        self.assertIn("retry_count", guards["RETRY_WAIT"])
        self.assertIn("resource gates", guards["RETRY_WAIT"])
        for term in [
            "terminal states: SUCCEEDED, FAILED, DEAD_LETTERED, CANCELLED",
            "compare-and-set",
            "expected_state",
            "state_version",
            "append-only transition audit",
        ]:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_cancel_retry_and_resource_pause_semantics_are_unambiguous(self):
        text = self._combined_contract()
        required_terms = [
            "RUNNING never transitions directly to CANCELLED",
            "PAUSE_REQUESTED -> CANCELLED",
            "atomically revokes the claim lease and lock",
            "increments the fencing token",
            "stale worker commit fails",
            "transition_request_id",
            "state_namespace=job_state",
            "state_model_version=ids.job_state.v1",
            "max_retries is the number of retry attempts after the initial attempt",
            "retry_count=0",
            "total_attempt_limit = 1 + max_retries",
            "RETRY_WAIT -> QUEUED increments retry_count atomically",
            "retry_count < max_retries",
            "retry_count == max_retries",
            "worker loss consumes one retry opportunity",
            "duplicate lease-expiry event",
            "RETRY_WAIT -> PAUSED",
            "resource gate remains blocked",
            "active execution states: CLAIMED, RUNNING, PAUSE_REQUESTED",
            "deactivation transaction",
            "leaves active execution",
            "atomically records the destination state",
            "revokes the claim lease and lock",
            "retry_pending=true",
            "RETRY_WAIT -> PAUSED preserves retry_pending=true",
            "PAUSED -> QUEUED with retry_pending=true increments retry_count atomically",
            "clears retry_pending",
            "cannot bypass total_attempt_limit",
            "retry_count == max_retries enters RETRY_WAIT with retry_pending=false",
            "retry_disposition=exhausted",
            "only legal next transition is RETRY_WAIT -> DEAD_LETTERED",
            "resource gates cannot pause an exhausted retry",
            "RUNNING -> DEAD_LETTERED remains forbidden",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_cleanup_contract_blocks_symlink_and_toctou_escape(self):
        text = self._combined_contract()
        required_terms = [
            "approved_root_id",
            "canonical approved-root identity",
            "root-relative path",
            "lstat identity",
            "st_dev",
            "st_ino",
            "file_type",
            "symlink",
            "O_NOFOLLOW",
            "dirfd",
            "openat",
            "unlinkat",
            "revalidate immediately before deletion",
            "TOCTOU",
            "identity mismatch blocks deletion",
            "exclusive cleanup namespace lock",
            "writer quiescence",
            "no creation, rename, replacement, or deletion",
            "lock remains held through unlinkat",
            "cannot prove writer quiescence blocks cleanup",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase2_plan_keeps_stage039_040_042_runtime_ownership(self):
        roadmap = ROADMAP.read_text(encoding="utf-8")
        phase2 = roadmap.split(
            '        phase_id: "IDS-STAGE037-P2"', 1
        )[1].split(
            '        phase_id: "IDS-STAGE037-P3"', 1
        )[0]
        self.assertIn("deterministic state-transition engine", phase2)
        self.assertIn("machine-readable contract/checker", phase2)
        self.assertIn("no queue/worker runtime", phase2)
        self.assertNotIn("失败重试/反压或自动运行切片", phase2)
        self.assertNotIn("retry scheduler", phase2)
        self.assertNotIn("backpressure actuator", phase2)
        self.assertNotIn("automatic lifecycle runtime", phase2)

    def test_phase1_defines_worker_retry_backpressure_lock_and_lifecycle_boundaries(self):
        text = self._combined_contract()
        required_terms = [
            "job_state_model_contract_id",
            "job_control_envelope",
            "job_transition_event",
            "job_checkpoint_payload",
            "job_error_payload",
            "job_cleanup_manifest",
            "human_status_projection",
            "phase2_ready_contract",
            "claim lease",
            "fencing_token",
            "lease_expires_at",
            "stale worker",
            "retry_count",
            "max_retries",
            "next_eligible_at",
            "retryable",
            "permanent failure",
            "dead-letter",
            "pause_reason_code",
            "pause reason is not a job state",
            "SAFE_MODE_DRIVE_OFFLINE",
            "SAFE_MODE_STORAGE_BLOCKED",
            "SAFE_MODE_API_BUDGET_EXCEEDED",
            "BUDGET_BLOCKED_LOW_FREE",
            "EXTERNAL_ROOT_NOT_READY",
            "auto_resume=false",
            "owner revalidation",
            "idempotency_key",
            "ids-import-file-sha256-{sha256}",
            "operation_contract_version",
            "normalized_parameters_sha256",
            "lock_key",
            "lock granularity",
            "attempt_id",
            "checkpoint_ref",
            "input_refs",
            "output_refs",
            "error_ref",
            "audit_ref",
            "POLICY_VALUE_DEFERRED_TO_STAGE039_040_041",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_cleanup_and_source_boundaries_fail_closed(self):
        combined = self._combined_contract()
        required_terms = [
            "cleanup allowlist",
            "attempt-owned temporary artifacts",
            "cleanup_manifest_ref",
            "00_ORIGINAL_RAW_DATA",
            "manifest",
            "evidence ledger",
            "audit log",
            "report snapshot",
            "active index",
            "NO_PHASE2",
            "NO_QUEUE_IMPLEMENTATION",
            "NO_WORKER_EXECUTION",
            "NO_STATE_REGISTRY_WRITE",
            "NO_SCHEMA_CHANGE",
            "NO_POSTGRES_CONNECTION",
            "NO_RUNTIME_OUTPUT",
            "NO_FAKE_DATA",
            "NO_STAGE038",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据、虚构数据库行、placeholder corpus 或伪造证据",
            "STAGE-038",
            "STAGE-039",
            "STAGE-040",
            "STAGE-041",
            "STAGE-042",
            "STAGE-043",
            "STAGE-044",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch_lock_roadmap_and_event_track_stage037_phase1_without_upload(self):
        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events = [
            json.loads(line)
            for line in EVENTS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        lock_terms = [
            "STAGE-037:",
            'completed_phases:',
            '      - "Phase 1"',
            'acceptance_id: "ACC-STAGE-037"',
            'push_allowed: false',
            'github_upload_allowed: false',
        ]
        allowed_current_states = [
            [
                'status: "stage037_phase1_in_progress"',
                'next_phase: "Phase 2"',
                'next_gate: "IDS-STAGE037-P2-GATE"',
                'current_task_id: "IDS-V0_1-STAGE037-P1"',
                'acceptance_status: "phase1_scope_boundary_defined"',
                'next_allowed_task_id: "IDS-V0_1-STAGE037-P2"',
            ],
            [
                'status: "stage037_phase2_in_progress"',
                'next_phase: "Phase 3"',
                'next_gate: "IDS-STAGE037-P3-GATE"',
                'current_task_id: "IDS-V0_1-STAGE037-P2"',
                'acceptance_status: "phase2_deterministic_engine_passed"',
                'next_allowed_task_id: "IDS-V0_1-STAGE037-P3"',
            ],
            [
                'status: "stage037_phase3_in_progress"',
                'next_phase: "Phase 4"',
                'next_gate: "IDS-STAGE037-P4-GATE"',
                'current_task_id: "IDS-V0_1-STAGE037-P3"',
                'acceptance_status: "phase3_adversarial_scenarios_passed"',
                'next_allowed_task_id: "IDS-V0_1-STAGE037-P4"',
            ],
            [
                'status: "stage037_phase4_completed_review_pending"',
                'next_phase: "stage_review"',
                'next_gate: "IDS-STAGE037-REVIEW-GATE"',
                'current_task_id: "IDS-V0_1-STAGE037-P4"',
                'acceptance_status: "phase4_closeout_passed_review_pending"',
                'next_allowed_task_id: "IDS-V0_1-STAGE037-REVIEW"',
            ],
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE037"',
            'current_phase_id: "IDS-STAGE037-P1"',
            'current_task_id: "IDS-V0_1-STAGE037-P1"',
            'next_gate_id: "IDS-STAGE037-P2-GATE"',
            'stage_id: "IDS-STAGE037"',
            'phase_id: "IDS-STAGE037-P1"',
            'task_id: "IDS-V0_1-STAGE037-P1"',
            'status: "passed_with_local_evidence"',
        ]
        self.assertTrue(
            any(
                all(term in lock_text for term in state)
                for state in allowed_current_states
            ),
            allowed_current_states,
        )
        for terms, text in ((lock_terms, lock_text), (roadmap_terms, roadmap_text)):
            for term in terms:
                with self.subTest(term=term):
                    self.assertIn(term, text)

        matching = [
            event
            for event in events
            if event.get("event_id") == "EVT-IDS-V0_1-STAGE037-P1-20260711-001"
        ]
        self.assertEqual(1, len(matching), matching)
        event = matching[0]
        self.assertEqual("stage_boundary", event["event_type"])
        self.assertEqual("IDS-V0_1-STAGE037-P1", event["task_id"])
        self.assertEqual(["ACC-STAGE-037"], event["acceptance_ids"])
        self.assertIn(
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE1_SCOPE_BOUNDARY.md",
            event["changed_files"],
        )
        refs = {item["ref"] for item in event["evidence_refs"]}
        self.assertIn(
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE1_SCOPE_BOUNDARY.md",
            refs,
        )
        self.assertIn("push_allowed=false", event["notes"])
        self.assertNotIn("next_gate=", event["notes"])
        self.assertNotIn("live_migration_result=", event["notes"])


class Stage037JobStateModelPhase2Tests(unittest.TestCase):
    maxDiff = None

    @staticmethod
    def _load_checker():
        if not CHECKER.is_file():
            raise AssertionError(f"missing Phase 2 checker: {CHECKER}")
        spec = importlib.util.spec_from_file_location(
            "stage037_job_state_model_checker", CHECKER
        )
        if spec is None or spec.loader is None:
            raise AssertionError("unable to load Stage037 checker module")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def _load_index() -> dict:
        if not MODEL_INDEX.is_file():
            raise AssertionError(f"missing Phase 2 model index: {MODEL_INDEX}")
        return json.loads(MODEL_INDEX.read_text(encoding="utf-8"))

    @staticmethod
    def _snapshot(state: str = "CREATED", **overrides) -> dict:
        active = state in {"CLAIMED", "RUNNING", "PAUSE_REQUESTED"}
        snapshot = {
            "evaluation_mode": "STATIC_CONTRACT_EVALUATION_ONLY",
            "job_id": "contract:IDS-V0_1-STAGE037-P2",
            "job_type": "IMPORT",
            "job_state": state,
            "state_version": 0,
            "retry_count": 0,
            "max_retries": 2,
            "retry_pending": False,
            "retry_disposition": "none",
            "lease_active": active,
            "lock_active": active,
            "fencing_token": 7 if active else 0,
            "attempt_id": "acceptance:ACC-STAGE-037" if active else None,
            "lease_owner_ref": "task:IDS-V0_1-STAGE037-P2" if active else None,
            "lease_expires_at": (
                "policy:POLICY_VALUE_DEFERRED_TO_STAGE039_040_041"
                if active
                else None
            ),
            "lock_key": "contract:stage037:p2" if active else None,
            "pause_reason_code": None,
            "input_refs": [
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
                "STAGE037_PHASE1_SCOPE_BOUNDARY.md#Job-Control-Envelope"
            ],
            "output_refs": [],
            "checkpoint_ref": None,
            "quarantine_ref": None,
            "error_ref": None,
        }
        snapshot.update(overrides)
        return snapshot

    @staticmethod
    def _request(
        source: str,
        target: str,
        state_version: int = 0,
        **overrides,
    ) -> dict:
        request = {
            "job_id": "contract:IDS-V0_1-STAGE037-P2",
            "transition_request_id": (
                "acceptance:ACC-STAGE-037:static-transition-evaluation"
            ),
            "expected_state": source,
            "expected_state_version": state_version,
            "target_state": target,
            "actor_ref": "task:IDS-V0_1-STAGE037-P2",
            "reason_code": "PHASE2_STATIC_CONTRACT_EVALUATION",
            "audit_ref": (
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
                "STAGE037_PHASE2_JOB_STATE_MODEL_SLICE.md#Truthful-Result"
            ),
            "guard_facts": {},
            "input_refs": [],
            "output_refs": [],
            "checkpoint_ref": None,
            "quarantine_ref": None,
            "error_ref": None,
            "resource_gate_refs": [],
            "pause_reason_code": None,
            "fencing_token": None,
            "candidate_claim": None,
        }
        request.update(overrides)
        return request

    def test_phase2_artifacts_bind_exact_machine_contract_and_sources(self):
        self.assertTrue(PHASE2.is_file(), f"missing Phase 2 evidence: {PHASE2}")
        self.assertTrue(MODEL_INDEX.is_file(), f"missing model index: {MODEL_INDEX}")
        self.assertTrue(CHECKER.is_file(), f"missing checker: {CHECKER}")
        index = self._load_index()

        self.assertEqual("ids.stage037.job_state_model.index.v1", index["schema_version"])
        self.assertEqual("STAGE-037", index["stage"])
        self.assertEqual("Phase 2", index["phase"])
        self.assertEqual("IDS-V0_1-STAGE037-P2", index["task_id"])
        self.assertEqual("ACC-STAGE-037", index["acceptance_id"])
        self.assertEqual(
            "ids_stage037_job_state_model_static_slice",
            index["job_state_model_contract_id"],
        )
        self.assertEqual(
            "METADATA_ONLY_DETERMINISTIC_CONTRACT_EVALUATION",
            index["execution_mode"],
        )
        self.assertFalse(index["execution_ready"])
        self.assertEqual(
            "STATIC_JOB_STATE_CONTRACT_VALID_RUNTIME_DISABLED",
            index["contract_state"],
        )

        model = index["state_model"]
        self.assertEqual(
            ["IMPORT", "ARCHIVE", "PARSE", "OCR", "CHUNK", "EMBED", "INDEX", "REPORT"],
            model["job_types"],
        )
        self.assertEqual(
            [
                "CREATED",
                "QUEUED",
                "CLAIMED",
                "RUNNING",
                "PAUSE_REQUESTED",
                "PAUSED",
                "RETRY_WAIT",
                "SUCCEEDED",
                "FAILED",
                "DEAD_LETTERED",
                "CANCELLED",
            ],
            model["job_states"],
        )
        self.assertEqual(
            {
                "CREATED": ["QUEUED", "CANCELLED"],
                "QUEUED": ["CLAIMED", "PAUSED", "CANCELLED"],
                "CLAIMED": ["RUNNING", "PAUSE_REQUESTED", "RETRY_WAIT"],
                "RUNNING": ["SUCCEEDED", "PAUSE_REQUESTED", "RETRY_WAIT", "FAILED"],
                "PAUSE_REQUESTED": ["PAUSED", "CANCELLED", "RETRY_WAIT"],
                "PAUSED": ["QUEUED", "CANCELLED"],
                "RETRY_WAIT": ["QUEUED", "PAUSED", "DEAD_LETTERED", "CANCELLED"],
            },
            model["allowed_transitions"],
        )
        self.assertEqual(
            ["SUCCEEDED", "FAILED", "DEAD_LETTERED", "CANCELLED"],
            model["terminal_states"],
        )
        self.assertEqual(
            ["CLAIMED", "RUNNING", "PAUSE_REQUESTED"],
            model["active_execution_states"],
        )
        self.assertEqual("job_state", model["state_namespace"])
        self.assertEqual("ids.job_state.v1", model["state_model_version"])
        transition_contract = index["transition_contract"]
        self.assertIn(
            "transition_request_required_fields", transition_contract
        )
        self.assertIn("snapshot_required_fields", transition_contract)
        self.assertIn(
            "job_id", transition_contract["transition_request_required_fields"]
        )
        self.assertEqual(
            sorted(self._request("CREATED", "QUEUED")),
            sorted(transition_contract["transition_request_required_fields"]),
        )
        self.assertEqual(
            sorted(self._snapshot()),
            sorted(transition_contract["snapshot_required_fields"]),
        )

        hashes = index["dependency_contract"]["source_sha256"]
        self.assertGreaterEqual(len(hashes), 9)
        for source_name, digest in hashes.items():
            with self.subTest(source_name=source_name):
                self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_phase2_checker_reports_one_truthful_stdout_only_result(self):
        module = self._load_checker()
        report = module.build_stage037_job_state_report()
        self.assertTrue(report["contract_valid"], report)
        self.assertFalse(report["execution_ready"])
        self.assertEqual(
            "STATIC_JOB_STATE_CONTRACT_VALID_RUNTIME_DISABLED",
            report["execution_state"],
        )
        self.assertEqual("IDS-STAGE037-P3-GATE", report["next_gate"])
        self.assertFalse(report["github_upload_allowed"])
        self.assertFalse(report["app_reinstall_allowed"])
        self.assertTrue(all(not value for value in report["runtime_actions"].values()))
        self.assertTrue(all(report["checks"].values()), report["checks"])

        result = subprocess.run(
            [sys.executable, "-B", str(CHECKER)],
            cwd=ROOT.parent,
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr or result.stdout)
        self.assertEqual("", result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("Phase 4", payload["phase"])
        self.assertEqual("IDS-V0_1-STAGE037-P4", payload["task_id"])
        self.assertEqual(report, payload["phase2_report"])

    def test_deterministic_engine_enforces_cas_and_idempotent_replay(self):
        module = self._load_checker()
        contract = self._load_index()
        snapshot = self._snapshot()
        request = self._request(
            "CREATED",
            "QUEUED",
            guard_facts={
                "identity_idempotency_valid": True,
                "admission_gates_passed": True,
                "no_active_claim_or_lock": True,
            },
        )

        accepted = module.evaluate_transition(
            snapshot, request, contract=contract
        )
        self.assertTrue(accepted["accepted"], accepted)
        self.assertEqual("TRANSITION_ACCEPTED", accepted["result_code"])
        self.assertEqual("QUEUED", accepted["next_snapshot"]["job_state"])
        self.assertEqual(1, accepted["next_snapshot"]["state_version"])
        self.assertFalse(accepted["runtime_transition_performed"])
        self.assertEqual(
            "STATIC_CONTRACT_EVALUATION_ONLY", accepted["fact_level"]
        )
        self.assertRegex(accepted["request_fingerprint_sha256"], r"^[0-9a-f]{64}$")

        replay = module.evaluate_transition(
            snapshot,
            request,
            contract=contract,
            prior_results={request["transition_request_id"]: accepted},
        )
        self.assertTrue(replay["accepted"], replay)
        self.assertTrue(replay["idempotent_replay"])
        self.assertEqual(accepted["next_snapshot"], replay["next_snapshot"])

        conflict_request = copy.deepcopy(request)
        conflict_request["target_state"] = "CANCELLED"
        conflict = module.evaluate_transition(
            snapshot,
            conflict_request,
            contract=contract,
            prior_results={request["transition_request_id"]: accepted},
        )
        self.assertFalse(conflict["accepted"], conflict)
        self.assertEqual("TRANSITION_REQUEST_CONFLICT", conflict["result_code"])

        stale_request = copy.deepcopy(request)
        stale_request["expected_state_version"] = 1
        stale = module.evaluate_transition(snapshot, stale_request, contract=contract)
        self.assertFalse(stale["accepted"], stale)
        self.assertEqual("COMPARE_AND_SET_MISMATCH", stale["result_code"])

        other_snapshot = self._snapshot(
            job_id="contract:ACC-STAGE-037:other-record"
        )
        cross_job = module.evaluate_transition(
            other_snapshot,
            request,
            contract=contract,
            prior_results={request["transition_request_id"]: accepted},
        )
        self.assertFalse(cross_job["accepted"], cross_job)
        self.assertEqual("COMPARE_AND_SET_MISMATCH", cross_job["result_code"])

        tampered_prior = copy.deepcopy(accepted)
        tampered_prior["next_snapshot"]["job_id"] = (
            "contract:ACC-STAGE-037:other-record"
        )
        invalid_prior = module.evaluate_transition(
            snapshot,
            request,
            contract=contract,
            prior_results={request["transition_request_id"]: tampered_prior},
        )
        self.assertFalse(invalid_prior["accepted"], invalid_prior)
        self.assertEqual("INVALID_PRIOR_RESULT", invalid_prior["result_code"])

    def test_claim_and_active_deactivation_are_fenced_and_fail_closed(self):
        module = self._load_checker()
        contract = self._load_index()
        queued = self._snapshot("QUEUED")
        claim_request = self._request(
            "QUEUED",
            "CLAIMED",
            guard_facts={
                "admission_gates_passed": True,
                "claim_lease_and_lock_acquired": True,
            },
            candidate_claim={
                "attempt_id": "acceptance:ACC-STAGE-037",
                "lease_owner_ref": "task:IDS-V0_1-STAGE037-P2",
                "lease_expires_at": (
                    "policy:POLICY_VALUE_DEFERRED_TO_STAGE039_040_041"
                ),
                "fencing_token": 1,
                "lock_key": "contract:stage037:p2",
            },
        )
        claimed = module.evaluate_transition(queued, claim_request, contract=contract)
        self.assertTrue(claimed["accepted"], claimed)
        self.assertTrue(claimed["next_snapshot"]["lease_active"])
        self.assertTrue(claimed["next_snapshot"]["lock_active"])
        self.assertEqual(1, claimed["next_snapshot"]["fencing_token"])

        running = self._snapshot("RUNNING", state_version=4)
        succeed_request = self._request(
            "RUNNING",
            "SUCCEEDED",
            state_version=4,
            fencing_token=7,
            output_refs=[
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
                "STAGE037_PHASE2_JOB_STATE_MODEL_SLICE.md#Truthful-Result"
            ],
            guard_facts={
                "live_lease_valid": True,
                "fencing_token_matches": True,
                "output_validated": True,
            },
        )
        succeeded = module.evaluate_transition(
            running, succeed_request, contract=contract
        )
        self.assertTrue(succeeded["accepted"], succeeded)
        self.assertFalse(succeeded["next_snapshot"]["lease_active"])
        self.assertFalse(succeeded["next_snapshot"]["lock_active"])
        self.assertEqual(8, succeeded["next_snapshot"]["fencing_token"])
        self.assertIsNone(succeeded["next_snapshot"]["lease_owner_ref"])
        self.assertIsNone(succeeded["next_snapshot"]["lock_key"])

        expired_success = copy.deepcopy(succeed_request)
        expired_success["guard_facts"].pop("live_lease_valid")
        expired_success["guard_facts"]["lease_valid_or_expiry_evidence"] = True
        expired_result = module.evaluate_transition(
            running, expired_success, contract=contract
        )
        self.assertFalse(expired_result["accepted"], expired_result)
        self.assertEqual(
            "MISSING_TRANSITION_GUARD", expired_result["result_code"]
        )

        stale_fence = copy.deepcopy(succeed_request)
        stale_fence["fencing_token"] = 6
        rejected = module.evaluate_transition(running, stale_fence, contract=contract)
        self.assertFalse(rejected["accepted"], rejected)
        self.assertEqual("FENCING_TOKEN_MISMATCH", rejected["result_code"])

    def test_retry_pause_resume_and_exhaustion_preserve_budget(self):
        module = self._load_checker()
        contract = self._load_index()
        running = self._snapshot("RUNNING", state_version=3)
        retry_request = self._request(
            "RUNNING",
            "RETRY_WAIT",
            state_version=3,
            fencing_token=7,
            error_ref=(
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
                "STAGE037_PHASE2_JOB_STATE_MODEL_SLICE.md#Error-Reference-Boundary"
            ),
            guard_facts={
                "lease_valid_or_expiry_evidence": True,
                "fencing_token_matches": True,
                "retryable_failure_recorded": True,
                "error_evidence_present": True,
            },
        )
        waiting = module.evaluate_transition(running, retry_request, contract=contract)
        self.assertTrue(waiting["accepted"], waiting)
        retry_snapshot = waiting["next_snapshot"]
        self.assertEqual("RETRY_WAIT", retry_snapshot["job_state"])
        self.assertEqual(0, retry_snapshot["retry_count"])
        self.assertTrue(retry_snapshot["retry_pending"])
        self.assertEqual("eligible", retry_snapshot["retry_disposition"])

        pause_request = self._request(
            "RETRY_WAIT",
            "PAUSED",
            state_version=retry_snapshot["state_version"],
            pause_reason_code="SAFE_MODE_STORAGE_BLOCKED",
            resource_gate_refs=[
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
                "STAGE009_PHASE2_STORAGE_BUDGET_BASELINE.md"
            ],
            guard_facts={
                "resource_gate_blocked": True,
                "no_active_claim_or_lock": True,
            },
        )
        paused = module.evaluate_transition(
            retry_snapshot, pause_request, contract=contract
        )
        self.assertTrue(paused["accepted"], paused)
        self.assertTrue(paused["next_snapshot"]["retry_pending"])
        self.assertEqual(0, paused["next_snapshot"]["retry_count"])

        resume_request = self._request(
            "PAUSED",
            "QUEUED",
            state_version=paused["next_snapshot"]["state_version"],
            guard_facts={
                "owner_revalidated": True,
                "resource_gates_passed": True,
                "no_active_claim_or_lock": True,
            },
        )
        resumed = module.evaluate_transition(
            paused["next_snapshot"], resume_request, contract=contract
        )
        self.assertTrue(resumed["accepted"], resumed)
        self.assertEqual(1, resumed["next_snapshot"]["retry_count"])
        self.assertFalse(resumed["next_snapshot"]["retry_pending"])
        self.assertEqual("none", resumed["next_snapshot"]["retry_disposition"])

        exhausted_running = self._snapshot(
            "RUNNING", state_version=8, retry_count=2, max_retries=2
        )
        exhausted_request = copy.deepcopy(retry_request)
        exhausted_request["expected_state_version"] = 8
        exhausted = module.evaluate_transition(
            exhausted_running, exhausted_request, contract=contract
        )
        self.assertTrue(exhausted["accepted"], exhausted)
        exhausted_snapshot = exhausted["next_snapshot"]
        self.assertFalse(exhausted_snapshot["retry_pending"])
        self.assertEqual("exhausted", exhausted_snapshot["retry_disposition"])

        blocked_pause = self._request(
            "RETRY_WAIT",
            "PAUSED",
            state_version=exhausted_snapshot["state_version"],
            pause_reason_code="SAFE_MODE_STORAGE_BLOCKED",
            guard_facts={
                "resource_gate_blocked": True,
                "no_active_claim_or_lock": True,
            },
        )
        pause_rejected = module.evaluate_transition(
            exhausted_snapshot, blocked_pause, contract=contract
        )
        self.assertFalse(pause_rejected["accepted"], pause_rejected)
        self.assertEqual(
            "EXHAUSTED_RETRY_MUST_DEAD_LETTER",
            pause_rejected["result_code"],
        )

        dead_letter_request = self._request(
            "RETRY_WAIT",
            "DEAD_LETTERED",
            state_version=exhausted_snapshot["state_version"],
            guard_facts={
                "retry_exhaustion_confirmed": True,
                "no_active_claim_or_lock": True,
            },
        )
        dead_lettered = module.evaluate_transition(
            exhausted_snapshot, dead_letter_request, contract=contract
        )
        self.assertTrue(dead_lettered["accepted"], dead_lettered)
        self.assertEqual(
            "DEAD_LETTERED", dead_lettered["next_snapshot"]["job_state"]
        )

    def test_engine_rejects_illegal_terminal_raw_secret_and_unbounded_inputs(self):
        module = self._load_checker()
        contract = self._load_index()

        terminal = self._snapshot(
            "SUCCEEDED",
            output_refs=[
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
                "STAGE037_PHASE2_JOB_STATE_MODEL_SLICE.md#Truthful-Result"
            ],
        )
        terminal_request = self._request("SUCCEEDED", "QUEUED")
        terminal_result = module.evaluate_transition(
            terminal, terminal_request, contract=contract
        )
        self.assertFalse(terminal_result["accepted"], terminal_result)
        self.assertEqual("TERMINAL_STATE_IMMUTABLE", terminal_result["result_code"])

        running = self._snapshot("RUNNING")
        direct_cancel = self._request(
            "RUNNING",
            "CANCELLED",
            fencing_token=7,
            guard_facts={
                "lease_valid_or_expiry_evidence": True,
                "fencing_token_matches": True,
            },
        )
        cancel_result = module.evaluate_transition(
            running, direct_cancel, contract=contract
        )
        self.assertFalse(cancel_result["accepted"], cancel_result)
        self.assertEqual("TRANSITION_NOT_ALLOWED", cancel_result["result_code"])

        raw_ref = self._request(
            "CREATED",
            "QUEUED",
            input_refs=["/Users/linzezhang/Downloads/IDS_MetaData/raw.bin"],
            guard_facts={
                "identity_idempotency_valid": True,
                "admission_gates_passed": True,
                "no_active_claim_or_lock": True,
            },
        )
        raw_result = module.evaluate_transition(
            self._snapshot(), raw_ref, contract=contract
        )
        self.assertFalse(raw_result["accepted"], raw_result)
        self.assertEqual("FORBIDDEN_REFERENCE", raw_result["result_code"])

        forbidden_ref_variants = [
            "FILE:///Users/linzezhang/Downloads/IDS_MetaData/raw.bin",
            "C:\\Users\\linzezhang\\Downloads\\IDS_MetaData\\raw.bin",
            "contract:stage037\\..\\raw",
            "contract:stage037/%2e%2e/raw",
        ]
        for ref in forbidden_ref_variants:
            with self.subTest(ref=ref):
                variant = self._request(
                    "CREATED",
                    "QUEUED",
                    input_refs=[ref],
                    guard_facts={
                        "identity_idempotency_valid": True,
                        "admission_gates_passed": True,
                        "no_active_claim_or_lock": True,
                    },
                )
                result = module.evaluate_transition(
                    self._snapshot(), variant, contract=contract
                )
                self.assertFalse(result["accepted"], result)
                self.assertEqual("FORBIDDEN_REFERENCE", result["result_code"])

        secret_request = self._request(
            "CREATED",
            "QUEUED",
            guard_facts={
                "identity_idempotency_valid": True,
                "admission_gates_passed": True,
                "no_active_claim_or_lock": True,
            },
        )
        secret_request["api_key"] = "forbidden"
        secret_result = module.evaluate_transition(
            self._snapshot(), secret_request, contract=contract
        )
        self.assertFalse(secret_result["accepted"], secret_result)
        self.assertEqual("INVALID_REQUEST_SHAPE", secret_result["result_code"])

        unbounded = copy.deepcopy(secret_request)
        unbounded.pop("api_key")
        unbounded["reason_code"] = "X" * 513
        unbounded_result = module.evaluate_transition(
            self._snapshot(), unbounded, contract=contract
        )
        self.assertFalse(unbounded_result["accepted"], unbounded_result)
        self.assertEqual("UNBOUNDED_METADATA", unbounded_result["result_code"])

        zero_fence_active = self._snapshot("RUNNING", fencing_token=0)
        zero_fence_request = self._request(
            "RUNNING",
            "SUCCEEDED",
            fencing_token=0,
            output_refs=[
                "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
                "STAGE037_PHASE2_JOB_STATE_MODEL_SLICE.md#Truthful-Result"
            ],
            guard_facts={
                "live_lease_valid": True,
                "fencing_token_matches": True,
                "output_validated": True,
            },
        )
        zero_fence_result = module.evaluate_transition(
            zero_fence_active, zero_fence_request, contract=contract
        )
        self.assertFalse(zero_fence_result["accepted"], zero_fence_result)
        self.assertEqual(
            "INVALID_SNAPSHOT_SHAPE", zero_fence_result["result_code"]
        )

    def test_contract_mutations_fail_closed_and_downstream_runtime_stays_deferred(self):
        module = self._load_checker()
        index = self._load_index()
        mutations = {}

        changed_transition = copy.deepcopy(index)
        changed_transition["state_model"]["allowed_transitions"]["RUNNING"].append(
            "CANCELLED"
        )
        mutations["direct_running_cancel"] = changed_transition

        enabled_runtime = copy.deepcopy(index)
        enabled_runtime["runtime_policy"]["queue_runtime_allowed"] = True
        mutations["queue_enabled"] = enabled_runtime

        missing_state = copy.deepcopy(index)
        missing_state["state_model"]["job_states"].remove("PAUSE_REQUESTED")
        mutations["missing_state"] = missing_state

        invalid_hash = copy.deepcopy(index)
        first_hash = next(iter(invalid_hash["dependency_contract"]["source_sha256"]))
        invalid_hash["dependency_contract"]["source_sha256"][first_hash] = "0" * 64
        mutations["source_hash_changed"] = invalid_hash

        wrong_projection = copy.deepcopy(index)
        wrong_projection["human_status_projection"]["DEAD_LETTERED"]["label_zh"] = (
            "已完成"
        )
        mutations["wrong_owner_projection"] = wrong_projection

        missing_success_output_ref = copy.deepcopy(index)
        missing_success_output_ref["transition_contract"][
            "edge_reference_requirements"
        ]["RUNNING->SUCCEEDED"].remove("output_refs")
        mutations["missing_success_output_ref"] = missing_success_output_ref

        missing_secret_guard = copy.deepcopy(index)
        missing_secret_guard["reference_policy"]["forbidden_key_tokens"].remove(
            "api_key"
        )
        mutations["missing_secret_guard"] = missing_secret_guard

        unknown_runtime_switch = copy.deepcopy(index)
        unknown_runtime_switch["runtime_enabled"] = True
        mutations["unknown_runtime_switch"] = unknown_runtime_switch

        changed_source_ref = copy.deepcopy(index)
        changed_source_ref["source_refs"]["phase1_scope_ref"] = (
            "../STAGE037_ENTRY_CONTRACT.md"
        )
        mutations["changed_source_ref"] = changed_source_ref

        missing_truth_field = copy.deepcopy(index)
        missing_truth_field["truth_contract"].pop("fake_database_row_used")
        mutations["missing_truth_field"] = missing_truth_field

        stale_worker_enabled = copy.deepcopy(index)
        stale_worker_enabled["deactivation_contract"][
            "stale_worker_commit_allowed"
        ] = True
        mutations["stale_worker_enabled"] = stale_worker_enabled

        exhausted_pause_enabled = copy.deepcopy(index)
        exhausted_pause_enabled["retry_contract"][
            "resource_gate_can_pause_exhausted_retry"
        ] = True
        mutations["exhausted_pause_enabled"] = exhausted_pause_enabled

        for mutation_name, mutated in mutations.items():
            with self.subTest(mutation_name=mutation_name):
                report = module.build_stage037_job_state_report(index=mutated)
                self.assertFalse(report["contract_valid"], report)
                self.assertEqual(
                    "BLOCKED_INVALID_JOB_STATE_CONTRACT",
                    report["execution_state"],
                )
                self.assertFalse(report["execution_ready"])

        ownership = index["downstream_ownership"]
        self.assertEqual("STAGE-038", ownership["queue_and_claim_transport"])
        self.assertEqual("STAGE-039", ownership["retry_and_dead_letter_policy"])
        self.assertEqual("STAGE-040", ownership["backpressure_runtime"])
        self.assertEqual("STAGE-041", ownership["lock_lease_and_fencing_runtime"])
        self.assertEqual("STAGE-042", ownership["automatic_lifecycle_runtime"])
        self.assertEqual("STAGE-043", ownership["worker_crash_recovery"])
        self.assertEqual("STAGE-044", ownership["half_product_cleanup_runtime"])

    def test_phase2_governance_advances_only_to_phase3_gate_without_upload(self):
        self.assertTrue(PHASE2.is_file(), f"missing Phase 2 evidence: {PHASE2}")
        document = PHASE2.read_text(encoding="utf-8")
        index = self._load_index()
        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events = [
            json.loads(line)
            for line in EVENTS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        for term in [
            "metadata-only deterministic state-transition engine",
            "STATIC_CONTRACT_EVALUATION_ONLY",
            "runtime_transition_performed=false",
            "no queue/worker runtime",
            "STAGE-039",
            "STAGE-040",
            "STAGE-042",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
            "IDS-STAGE037-P3-GATE",
        ]:
            with self.subTest(term=term):
                self.assertIn(term, document)

        self.assertFalse(index["runtime_policy"]["queue_runtime_allowed"])
        lock_terms = [
            '      - "Phase 1"',
            '      - "Phase 2"',
            "push_allowed: false",
            "github_upload_allowed: false",
        ]
        allowed_current_states = [
            [
                'status: "stage037_phase2_in_progress"',
                'next_phase: "Phase 3"',
                'next_gate: "IDS-STAGE037-P3-GATE"',
                'current_task_id: "IDS-V0_1-STAGE037-P2"',
                'acceptance_status: "phase2_deterministic_engine_passed"',
                'next_allowed_task_id: "IDS-V0_1-STAGE037-P3"',
            ],
            [
                'status: "stage037_phase3_in_progress"',
                'next_phase: "Phase 4"',
                'next_gate: "IDS-STAGE037-P4-GATE"',
                'current_task_id: "IDS-V0_1-STAGE037-P3"',
                'acceptance_status: "phase3_adversarial_scenarios_passed"',
                'next_allowed_task_id: "IDS-V0_1-STAGE037-P4"',
            ],
            [
                'status: "stage037_phase4_completed_review_pending"',
                'next_phase: "stage_review"',
                'next_gate: "IDS-STAGE037-REVIEW-GATE"',
                'current_task_id: "IDS-V0_1-STAGE037-P4"',
                'acceptance_status: "phase4_closeout_passed_review_pending"',
                'next_allowed_task_id: "IDS-V0_1-STAGE037-REVIEW"',
            ],
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE037"',
            'current_phase_id: "IDS-STAGE037-P2"',
            'current_task_id: "IDS-V0_1-STAGE037-P2"',
            'next_gate_id: "IDS-STAGE037-P3-GATE"',
            'phase_id: "IDS-STAGE037-P2"',
            'task_id: "IDS-V0_1-STAGE037-P2"',
            'status: "passed_with_local_evidence"',
        ]
        self.assertTrue(
            any(
                all(term in lock_text for term in state)
                for state in allowed_current_states
            ),
            allowed_current_states,
        )
        for terms, text in ((lock_terms, lock_text), (roadmap_terms, roadmap_text)):
            for term in terms:
                with self.subTest(term=term):
                    self.assertIn(term, text)

        matching = [
            event
            for event in events
            if event.get("event_id") == "EVT-IDS-V0_1-STAGE037-P2-20260711-001"
        ]
        self.assertEqual(1, len(matching), matching)
        event = matching[0]
        self.assertEqual("stage_slice", event["event_type"])
        self.assertEqual("IDS-V0_1-STAGE037-P2", event["task_id"])
        self.assertEqual(["ACC-STAGE-037"], event["acceptance_ids"])
        for path in [
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
            "STAGE037_PHASE2_JOB_STATE_MODEL_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/job_state_model/"
            "stage037_job_state_model_index.json",
            "KM_IDSystem/scripts/check_job_state_model.py",
        ]:
            with self.subTest(path=path):
                self.assertIn(path, event["changed_files"])
        refs = {item["ref"] for item in event["evidence_refs"]}
        self.assertIn(
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/job_state_model/"
            "stage037_job_state_model_index.json",
            refs,
        )
        self.assertIn("runtime_transition_performed=false", event["notes"])
        self.assertIn("push_allowed=false", event["notes"])
        self.assertNotIn("next_gate=", event["notes"])


class Stage037JobStateModelPhase3Tests(unittest.TestCase):
    maxDiff = None

    EXPECTED_SCENARIOS = {
        "duplicate_click_idempotent_replay",
        "duplicate_click_payload_conflict",
        "worker_crash_retry_reservation",
        "stale_worker_fencing_block",
        "removable_drive_offline_pause",
        "drive_reconnect_no_auto_resume",
        "low_disk_retry_pause_preserves_budget",
        "same_source_concurrency_blocked",
        "lock_claim_without_proof_blocked",
        "cleanup_authorization_blocked",
    }

    _load_checker = staticmethod(Stage037JobStateModelPhase2Tests._load_checker)
    _load_index = staticmethod(Stage037JobStateModelPhase2Tests._load_index)

    def _scenario_builder(self):
        module = self._load_checker()
        self.assertTrue(
            hasattr(module, "build_stage037_scenario_validation_report"),
            "missing Stage037 Phase 3 scenario report builder",
        )
        return module, module.build_stage037_scenario_validation_report

    def test_phase3_artifact_and_scenario_contract_exist(self):
        self.assertTrue(PHASE3.is_file(), f"missing Phase 3 evidence: {PHASE3}")
        combined = "\n".join(
            [PHASE3.read_text(encoding="utf-8"), CHECKER.read_text(encoding="utf-8")]
        )
        required_terms = [
            "ids.stage037.job_state_model.phase3.v1",
            "IDS-V0_1-STAGE037-P3",
            "ACC-STAGE-037",
            "build_stage037_scenario_validation_report",
            "STATIC_JOB_STATE_ADVERSARIAL_SCENARIO_VALIDATION_ONLY",
            "STATIC_JOB_STATE_SCENARIOS_VALID_RUNTIME_DISABLED",
            "live_execution_performed=false",
            "NO_PHASE4",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
            "ab1296ab690e445f2ae915ff508d68e9fac40c888cd9ce851bfcc0cf5ce77dc2",
            *sorted(self.EXPECTED_SCENARIOS),
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_scenario_report_passes_and_keeps_every_runtime_action_disabled(self):
        _, builder = self._scenario_builder()
        report = builder()

        self.assertEqual(
            "ids.stage037.job_state_model.phase3.v1", report["schema_version"]
        )
        self.assertEqual("Phase 3", report["phase"])
        self.assertEqual("IDS-V0_1-STAGE037-P3", report["task_id"])
        self.assertEqual("ACC-STAGE-037", report["acceptance_id"])
        self.assertTrue(report["phase2_contract_valid"], report)
        self.assertTrue(report["scenario_validation_valid"], report)
        self.assertEqual(self.EXPECTED_SCENARIOS, set(report["scenario_results"]))
        self.assertFalse(report["execution_ready"])
        self.assertEqual(
            "STATIC_JOB_STATE_SCENARIOS_VALID_RUNTIME_DISABLED",
            report["execution_state"],
        )
        self.assertEqual(
            "STATIC_JOB_STATE_ADVERSARIAL_SCENARIO_VALIDATION_ONLY",
            report["execution_mode"],
        )
        for result in report["scenario_results"].values():
            self.assertEqual("PASS", result["status"], result)
            self.assertEqual("STATIC_CONTRACT_SCENARIO_ONLY", result["fact_level"])
            self.assertFalse(result["live_execution_performed"])
            self.assertTrue(all(result["invariant_checks"].values()), result)
        for field in [
            "live_execution_performed",
            "queue_runtime_performed",
            "worker_runtime_performed",
            "retry_scheduler_performed",
            "backpressure_runtime_performed",
            "lock_runtime_performed",
            "automatic_lifecycle_runtime_performed",
            "crash_recovery_runtime_performed",
            "cleanup_runtime_performed",
            "database_connection_performed",
            "schema_change_performed",
            "state_registry_write_performed",
            "runtime_output_written",
            "real_job_created",
            "fake_ids_business_data_used",
            "raw_metadata_content_accessed",
        ]:
            with self.subTest(field=field):
                self.assertFalse(report[field])
        self.assertEqual("IDS-STAGE037-P4-GATE", report["next_gate"])
        self.assertFalse(report["github_upload_allowed"])
        self.assertFalse(report["app_reinstall_allowed"])

    def test_scenarios_expose_expected_result_codes_and_state_invariants(self):
        _, builder = self._scenario_builder()
        results = builder()["scenario_results"]
        expected = {
            "duplicate_click_idempotent_replay": (
                True,
                "TRANSITION_ACCEPTED",
                "QUEUED",
            ),
            "duplicate_click_payload_conflict": (
                False,
                "TRANSITION_REQUEST_CONFLICT",
                None,
            ),
            "worker_crash_retry_reservation": (
                True,
                "TRANSITION_ACCEPTED",
                "RETRY_WAIT",
            ),
            "stale_worker_fencing_block": (
                False,
                "COMPARE_AND_SET_MISMATCH",
                None,
            ),
            "removable_drive_offline_pause": (
                True,
                "TRANSITION_ACCEPTED",
                "PAUSED",
            ),
            "drive_reconnect_no_auto_resume": (
                False,
                "MISSING_TRANSITION_GUARD",
                None,
            ),
            "low_disk_retry_pause_preserves_budget": (
                True,
                "TRANSITION_ACCEPTED",
                "PAUSED",
            ),
            "same_source_concurrency_blocked": (
                False,
                "MISSING_TRANSITION_GUARD",
                None,
            ),
            "lock_claim_without_proof_blocked": (
                False,
                "MISSING_TRANSITION_GUARD",
                None,
            ),
            "cleanup_authorization_blocked": (
                False,
                "INVALID_REQUEST_SHAPE",
                None,
            ),
        }
        for scenario_id, (accepted, code, state) in expected.items():
            with self.subTest(scenario_id=scenario_id):
                result = results[scenario_id]
                self.assertIs(accepted, result["observed_accepted"])
                self.assertIs(accepted, result["candidate_created"])
                self.assertEqual(code, result["observed_result_code"])
                self.assertEqual(state, result["observed_state"])
                self.assertRegex(result["owner_explanation_zh"], r"[\u4e00-\u9fff]")
                self.assertTrue(result["evidence"])

        required_invariants = {
            "stale_worker_fencing_block": {
                "worker_crash_prerequisite_exact",
                "no_stale_success_candidate",
            },
            "drive_reconnect_no_auto_resume": {
                "drive_pause_prerequisite_exact",
                "paused_candidate_not_resumed",
            },
            "same_source_concurrency_blocked": {
                "first_same_source_claim_accepted",
                "distinct_job_ids",
                "shared_source_identity",
                "shared_lock_key",
                "second_claim_envelope_complete",
                "no_second_claim_candidate",
            },
            "lock_claim_without_proof_blocked": {
                "positive_claim_accepted",
                "negative_claim_envelope_complete",
                "only_lock_proof_changed",
                "no_unproven_claim_candidate",
            },
            "cleanup_authorization_blocked": {
                "baseline_cancel_accepted",
                "only_cleanup_field_added",
                "state_transition_does_not_authorize_deletion",
                "cleanup_runtime_disabled",
                "no_cleanup_candidate",
            },
        }
        for scenario_id, required in required_invariants.items():
            with self.subTest(scenario_id=scenario_id, check="positive_control"):
                checks = results[scenario_id]["invariant_checks"]
                self.assertTrue(required.issubset(checks), checks)
                self.assertTrue(all(checks[name] for name in required), checks)

    def test_scenario_report_is_deterministic_and_tampering_fails_closed(self):
        module, builder = self._scenario_builder()
        first = builder()
        second = builder()
        self.assertEqual(first, second)

        contract = self._load_index()
        contract["runtime_policy"]["lock_runtime_allowed"] = True
        tampered = builder(contract=contract)
        self.assertFalse(tampered["phase2_contract_valid"])
        self.assertFalse(tampered["scenario_validation_valid"])
        self.assertEqual(
            "BLOCKED_INVALID_JOB_STATE_CONTRACT", tampered["execution_state"]
        )
        self.assertFalse(tampered["live_execution_performed"])
        for result in tampered["scenario_results"].values():
            self.assertEqual("FAIL", result["status"], result)
            self.assertIs(result["observed_accepted"], False)
            self.assertIs(result["candidate_created"], False)
            self.assertEqual("INVALID_CONTRACT", result["observed_result_code"])
            self.assertIsNone(result["observed_state"])

        malformed = builder(contract=["not", "an", "object"])
        self.assertFalse(malformed["phase2_contract_valid"])
        self.assertFalse(malformed["scenario_validation_valid"])
        self.assertEqual(
            "BLOCKED_INVALID_JOB_STATE_CONTRACT", malformed["execution_state"]
        )
        self.assertTrue(
            all(
                result["observed_result_code"] == "INVALID_CONTRACT"
                and result["observed_accepted"] is False
                and result["candidate_created"] is False
                and result["observed_state"] is None
                for result in malformed["scenario_results"].values()
            ),
            malformed["scenario_results"],
        )

        malformed_nested = self._load_index()
        malformed_nested["transition_contract"] = ["invalid"]
        nested_report = builder(contract=malformed_nested)
        self.assertFalse(nested_report["phase2_contract_valid"])
        self.assertFalse(nested_report["scenario_validation_valid"])
        self.assertTrue(
            all(
                result["observed_result_code"] == "INVALID_CONTRACT"
                and result["observed_accepted"] is False
                and result["candidate_created"] is False
                and result["observed_state"] is None
                for result in nested_report["scenario_results"].values()
            ),
            nested_report["scenario_results"],
        )

        original_loader = module.load_contract
        module.load_contract = lambda: ["invalid-loader-result"]
        try:
            loader_report = builder()
        except Exception as exc:
            self.fail(f"non-object loader result must fail closed: {exc}")
        finally:
            module.load_contract = original_loader
        self.assertFalse(loader_report["phase2_contract_valid"])
        self.assertFalse(loader_report["scenario_validation_valid"])
        self.assertEqual(
            "BLOCKED_INVALID_JOB_STATE_CONTRACT",
            loader_report["execution_state"],
        )
        self.assertTrue(
            all(
                result["candidate_created"] is False
                and result["observed_state"] is None
                for result in loader_report["scenario_results"].values()
            ),
            loader_report["scenario_results"],
        )

    def test_cli_emits_current_phase3_report_with_nested_phase2_evidence(self):
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
        self.assertEqual("Phase 4", payload["phase"])
        self.assertEqual("IDS-V0_1-STAGE037-P4", payload["task_id"])
        self.assertTrue(payload["phase3_report"]["scenario_validation_valid"])
        self.assertEqual("Phase 3", payload["phase3_report"]["phase"])
        self.assertTrue(payload["phase2_report"]["contract_valid"])
        self.assertEqual("Phase 2", payload["phase2_report"]["phase"])

    def test_phase3_governance_advances_only_to_phase4_gate_without_upload(self):
        self.assertTrue(PHASE3.is_file(), f"missing Phase 3 evidence: {PHASE3}")
        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events = [
            json.loads(line)
            for line in EVENTS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        lock_terms = [
            '      - "Phase 1"',
            '      - "Phase 2"',
            '      - "Phase 3"',
            "push_allowed: false",
            "github_upload_allowed: false",
        ]
        allowed_current_states = [
            [
                'status: "stage037_phase3_in_progress"',
                'next_phase: "Phase 4"',
                'next_gate: "IDS-STAGE037-P4-GATE"',
                'current_task_id: "IDS-V0_1-STAGE037-P3"',
                'acceptance_status: "phase3_adversarial_scenarios_passed"',
                'next_allowed_task_id: "IDS-V0_1-STAGE037-P4"',
            ],
            [
                'status: "stage037_phase4_completed_review_pending"',
                'next_phase: "stage_review"',
                'next_gate: "IDS-STAGE037-REVIEW-GATE"',
                'current_task_id: "IDS-V0_1-STAGE037-P4"',
                'acceptance_status: "phase4_closeout_passed_review_pending"',
                'next_allowed_task_id: "IDS-V0_1-STAGE037-REVIEW"',
            ],
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE037"',
            'current_phase_id: "IDS-STAGE037-P3"',
            'current_task_id: "IDS-V0_1-STAGE037-P3"',
            'next_gate_id: "IDS-STAGE037-P4-GATE"',
            'phase_id: "IDS-STAGE037-P3"',
            'task_id: "IDS-V0_1-STAGE037-P3"',
            'status: "passed_with_local_evidence"',
        ]
        self.assertTrue(
            any(
                all(term in lock_text for term in state)
                for state in allowed_current_states
            ),
            allowed_current_states,
        )
        for terms, text in ((lock_terms, lock_text), (roadmap_terms, roadmap_text)):
            for term in terms:
                with self.subTest(term=term):
                    self.assertIn(term, text)

        matching = [
            event
            for event in events
            if event.get("event_id")
            == "EVT-IDS-V0_1-STAGE037-P3-20260711-001"
        ]
        self.assertEqual(1, len(matching), matching)
        event = matching[0]
        self.assertEqual("validation", event["event_type"])
        self.assertEqual("IDS-V0_1-STAGE037-P3", event["task_id"])
        self.assertEqual(["ACC-STAGE-037"], event["acceptance_ids"])
        self.assertIn(
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/"
            "STAGE037_PHASE3_ADVERSARIAL_SCENARIOS.md",
            event["changed_files"],
        )
        self.assertIn("live_execution_performed=false", event["notes"])
        self.assertIn("push_allowed=false", event["notes"])
        self.assertNotIn("github_upload_allowed=true", event["notes"])


class Stage037JobStateModelPhase4Tests(unittest.TestCase):
    maxDiff = None

    EXPECTED_JOB_TYPES = [
        "IMPORT",
        "ARCHIVE",
        "PARSE",
        "OCR",
        "CHUNK",
        "EMBED",
        "INDEX",
        "REPORT",
    ]
    EXPECTED_JOB_STATES = [
        "CREATED",
        "QUEUED",
        "CLAIMED",
        "RUNNING",
        "PAUSE_REQUESTED",
        "PAUSED",
        "RETRY_WAIT",
        "SUCCEEDED",
        "FAILED",
        "DEAD_LETTERED",
        "CANCELLED",
    ]
    EXPECTED_SAFE_SHUTDOWN_STEPS = {
        "stop_new_admission",
        "request_safe_checkpoint",
        "deactivate_and_fence",
        "preserve_source_and_evidence",
    }
    EXPECTED_RECOVERY_STEPS = {
        "record_worker_loss_evidence",
        "cas_deactivate_expired_attempt",
        "reserve_retry_without_consuming",
        "require_owner_resource_revalidation",
        "block_stale_worker_commit",
    }
    EXPECTED_ROLLBACK_STEPS = {
        "stop_on_invalid_contract",
        "revert_phase4_contract_only",
        "preserve_phase1_phase3_evidence",
        "preserve_data_and_runtime",
    }
    EXPECTED_KNOWN_LIMITS = {
        "no_queue_or_worker_runtime",
        "numeric_policies_deferred",
        "no_live_crash_or_recovery",
        "no_cleanup_runtime",
        "no_database_or_registry_execution",
        "static_closeout_is_not_readiness",
        "stage_review_and_batch_upload_blocked",
    }

    _load_checker = staticmethod(Stage037JobStateModelPhase2Tests._load_checker)
    _load_index = staticmethod(Stage037JobStateModelPhase2Tests._load_index)

    def _delivery_builder(self):
        module = self._load_checker()
        self.assertTrue(
            hasattr(module, "build_stage037_delivery_report"),
            "missing Stage037 Phase 4 delivery report builder",
        )
        return module, module.build_stage037_delivery_report

    def test_phase4_artifact_and_machine_delivery_contract_exist(self):
        self.assertTrue(PHASE4.is_file(), f"missing Phase 4 evidence: {PHASE4}")
        combined = "\n".join(
            [PHASE4.read_text(encoding="utf-8"), CHECKER.read_text(encoding="utf-8")]
        )
        required_terms = [
            "IDS-V0_1-STAGE037-P4",
            "ACC-STAGE-037",
            "ids.stage037.job_state_model.phase4.v1",
            "ids.stage037.job_state_model.delivery_contract.v1",
            "build_stage037_delivery_report",
            "STATIC_TRACKED_CLOSEOUT_EVIDENCE_ONLY",
            "PASS_STATIC_CLOSEOUT_RUNTIME_DISABLED",
            "state_graph",
            "retry_evidence_contract",
            "backpressure_evidence_contract",
            "cleanup_evidence_contract",
            "automatic_manual_boundary",
            "safe_shutdown_steps",
            "recovery_steps",
            "rollback_steps",
            "known_limits",
            "stage_review_status=pending_next_run",
            "STAGE037_PHASE4_CLOSEOUT_NO_STAGE_REVIEW_THIS_RUN_NO_BATCH_UPLOAD_NO_GITHUB_UPLOAD",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
            "ab1296ab690e445f2ae915ff508d68e9fac40c888cd9ce851bfcc0cf5ce77dc2",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

        contract = self._load_index()["phase4_delivery_contract"]
        self.assertEqual(
            "ids.stage037.job_state_model.delivery_contract.v1",
            contract["schema_version"],
        )

    def test_delivery_report_binds_exact_state_graph_and_nested_history(self):
        _, builder = self._delivery_builder()
        report = builder()

        self.assertEqual("ids.stage037.job_state_model.phase4.v1", report["schema_version"])
        self.assertEqual("Phase 4", report["phase"])
        self.assertEqual("IDS-V0_1-STAGE037-P4", report["task_id"])
        self.assertEqual("ACC-STAGE-037", report["acceptance_id"])
        self.assertTrue(report["delivery_contract_valid"], report)
        self.assertTrue(all(report["delivery_check_results"].values()), report)
        self.assertTrue(all(report["phase4_contract_results"].values()), report)
        self.assertEqual("PASS_STATIC_CLOSEOUT_RUNTIME_DISABLED", report["result"])
        self.assertFalse(report["execution_ready"])
        self.assertEqual(
            "STATIC_JOB_STATE_CLOSEOUT_VALID_RUNTIME_DISABLED",
            report["execution_state"],
        )
        self.assertEqual(self.EXPECTED_JOB_TYPES, report["state_graph"]["job_types"])
        self.assertEqual(self.EXPECTED_JOB_STATES, report["state_graph"]["job_states"])
        self.assertEqual(21, report["state_graph"]["allowed_transition_count"])
        self.assertEqual("ids.job_state.v1", report["state_graph"]["state_model_version"])
        self.assertTrue(report["phase3_report"]["scenario_validation_valid"])
        self.assertEqual("Phase 3", report["phase3_report"]["phase"])
        self.assertTrue(report["phase2_report"]["contract_valid"])
        self.assertEqual("Phase 2", report["phase2_report"]["phase"])

    def test_retry_backpressure_cleanup_and_human_boundaries_stay_deferred(self):
        _, builder = self._delivery_builder()
        report = builder()

        retry = report["retry_evidence_contract"]
        self.assertEqual("STAGE-039", retry["runtime_owner"])
        self.assertEqual("1 + max_retries", retry["total_attempt_limit_formula"])
        self.assertFalse(retry["retry_scheduler_performed"])
        self.assertFalse(retry["dead_letter_runtime_performed"])

        backpressure = report["backpressure_evidence_contract"]
        self.assertEqual("STAGE-040", backpressure["runtime_owner"])
        self.assertFalse(backpressure["pause_reason_is_state"])
        self.assertFalse(backpressure["backpressure_runtime_performed"])
        self.assertEqual(
            "POLICY_VALUE_DEFERRED_TO_STAGE039_040_041",
            backpressure["numeric_policy"],
        )

        cleanup = report["cleanup_evidence_contract"]
        self.assertEqual("STAGE-044", cleanup["runtime_owner"])
        self.assertFalse(cleanup["state_transition_authorizes_deletion"])
        self.assertFalse(cleanup["cleanup_runtime_performed"])
        self.assertTrue(cleanup["exclusive_namespace_lock_required"])
        self.assertTrue(cleanup["writer_quiescence_required"])

        boundary = report["automatic_manual_boundary"]
        self.assertEqual("STAGE-042", boundary["runtime_owner"])
        self.assertFalse(boundary["automatic_run_allowed"])
        self.assertFalse(boundary["automatic_resume_allowed"])
        self.assertFalse(boundary["automatic_shutdown_allowed"])
        self.assertTrue(boundary["owner_revalidation_required_for_resume"])
        self.assertTrue(boundary["safe_deactivation_required_for_cancel"])

    def test_safe_shutdown_recovery_rollback_and_known_limits_are_complete(self):
        _, builder = self._delivery_builder()
        report = builder()

        for field, expected in (
            ("safe_shutdown_steps", self.EXPECTED_SAFE_SHUTDOWN_STEPS),
            ("recovery_steps", self.EXPECTED_RECOVERY_STEPS),
            ("rollback_steps", self.EXPECTED_ROLLBACK_STEPS),
        ):
            steps = report[field]
            self.assertEqual(expected, {item["step_id"] for item in steps})
            for item in steps:
                self.assertIs(item["required"], True)
                self.assertRegex(item["owner_message_zh"], r"[\u4e00-\u9fff]")

        limits = report["known_limits"]
        self.assertEqual(
            self.EXPECTED_KNOWN_LIMITS,
            {item["limit_id"] for item in limits},
        )
        self.assertTrue(all(item["acknowledged"] is True for item in limits))
        self.assertRegex(report["chinese_owner_feedback"], r"[\u4e00-\u9fff]")

        for field in [
            "live_execution_performed",
            "queue_runtime_performed",
            "worker_runtime_performed",
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
            "runtime_output_written",
            "real_job_created",
            "fake_ids_business_data_used",
            "raw_metadata_content_accessed",
        ]:
            with self.subTest(field=field):
                self.assertFalse(report[field])

    def test_phase4_tampering_and_malformed_contracts_fail_closed(self):
        _, builder = self._delivery_builder()

        mutations = []
        auto_resume = self._load_index()
        auto_resume["phase4_delivery_contract"]["automatic_manual_boundary"][
            "automatic_resume_allowed"
        ] = True
        mutations.append(auto_resume)

        missing_shutdown = self._load_index()
        missing_shutdown["phase4_delivery_contract"]["safe_shutdown_steps"].pop()
        mutations.append(missing_shutdown)

        cleanup_runtime = self._load_index()
        cleanup_runtime["phase4_delivery_contract"]["cleanup_evidence_contract"][
            "cleanup_runtime_performed"
        ] = True
        mutations.append(cleanup_runtime)

        wrong_hash = self._load_index()
        wrong_hash["phase4_delivery_contract"]["evidence_sha256"][
            "phase3_scenarios_ref"
        ] = "0" * 64
        mutations.append(wrong_hash)

        for contract in mutations:
            with self.subTest(mutation=contract["phase4_delivery_contract"]):
                report = builder(contract=contract)
                self.assertFalse(report["delivery_contract_valid"], report)
                self.assertEqual("FAIL_CLOSED", report["result"])
                self.assertEqual(
                    "BLOCKED_INVALID_JOB_STATE_CONTRACT",
                    report["execution_state"],
                )
                self.assertFalse(report["live_execution_performed"])

        malformed_nested = self._load_index()
        malformed_nested["phase4_delivery_contract"] = ["invalid"]
        for contract in (malformed_nested, ["not", "an", "object"]):
            with self.subTest(contract=contract):
                try:
                    report = builder(contract=contract)
                except Exception as exc:
                    self.fail(f"malformed Phase 4 contract must fail closed: {exc}")
                self.assertFalse(report["delivery_contract_valid"])
                self.assertEqual("FAIL_CLOSED", report["result"])
                self.assertFalse(report["live_execution_performed"])

    def test_cli_emits_phase4_and_stops_at_separate_review_gate(self):
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
        self.assertEqual("Phase 4", payload["phase"])
        self.assertEqual("IDS-V0_1-STAGE037-P4", payload["task_id"])
        self.assertTrue(payload["delivery_contract_valid"], payload)
        self.assertEqual("pending_next_run", payload["stage_review_status"])
        self.assertEqual("IDS-STAGE037-REVIEW-GATE", payload["next_gate"])
        self.assertFalse(payload["github_upload_allowed"])
        self.assertFalse(payload["app_reinstall_allowed"])
        self.assertTrue(payload["phase3_report"]["scenario_validation_valid"])
        self.assertTrue(payload["phase2_report"]["contract_valid"])

    def test_phase4_governance_records_review_pending_without_upload(self):
        self.assertTrue(PHASE4.is_file(), f"missing Phase 4 evidence: {PHASE4}")
        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events = [
            json.loads(line)
            for line in EVENTS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        lock_terms = [
            'status: "stage037_phase4_completed_review_pending"',
            '      - "Phase 4"',
            'review_status: "pending"',
            'next_phase: "stage_review"',
            'next_gate: "IDS-STAGE037-REVIEW-GATE"',
            'current_task_id: "IDS-V0_1-STAGE037-P4"',
            'acceptance_status: "phase4_closeout_passed_review_pending"',
            'next_allowed_task_id: "IDS-V0_1-STAGE037-REVIEW"',
            "push_allowed: false",
            "github_upload_allowed: false",
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE037"',
            'current_phase_id: "IDS-STAGE037-P4"',
            'current_task_id: "IDS-V0_1-STAGE037-P4"',
            'next_gate_id: "IDS-STAGE037-REVIEW-GATE"',
            'phase_id: "IDS-STAGE037-P4"',
            'task_id: "IDS-V0_1-STAGE037-P4"',
            'status: "passed_with_local_evidence"',
            "STAGE037_PHASE4_CLOSEOUT.md",
        ]
        for terms, text in ((lock_terms, lock_text), (roadmap_terms, roadmap_text)):
            for term in terms:
                with self.subTest(term=term):
                    self.assertIn(term, text)

        matching = [
            event
            for event in events
            if event.get("event_id") == "EVT-IDS-V0_1-STAGE037-P4-20260711-001"
        ]
        self.assertEqual(1, len(matching), matching)
        event = matching[0]
        self.assertEqual("phase_closeout", event["event_type"])
        self.assertEqual("IDS-V0_1-STAGE037-P4", event["task_id"])
        self.assertEqual(["ACC-STAGE-037"], event["acceptance_ids"])
        self.assertIn(
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE037_PHASE4_CLOSEOUT.md",
            event["changed_files"],
        )
        self.assertIn("live_execution_performed=false", event["notes"])
        self.assertIn("next_gate=IDS-STAGE037-REVIEW-GATE", event["notes"])
        self.assertIn("push_allowed=false", event["notes"])
        self.assertNotIn("github_upload_allowed=true", event["notes"])


if __name__ == "__main__":
    unittest.main()
