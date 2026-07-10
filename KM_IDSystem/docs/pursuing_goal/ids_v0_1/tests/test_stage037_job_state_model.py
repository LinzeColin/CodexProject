import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE037_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE037_PHASE1_SCOPE_BOUNDARY.md"
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
        phase2 = roadmap.split('phase_id: "IDS-STAGE037-P2"', 1)[1].split(
            'phase_id: "IDS-STAGE037-P3"', 1
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
            'status: "stage037_phase1_in_progress"',
            "STAGE-037:",
            'completed_phases:',
            '      - "Phase 1"',
            'next_phase: "Phase 2"',
            'next_gate: "IDS-STAGE037-P2-GATE"',
            'current_task_id: "IDS-V0_1-STAGE037-P1"',
            'acceptance_id: "ACC-STAGE-037"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'next_allowed_task_id: "IDS-V0_1-STAGE037-P2"',
            'push_allowed: false',
            'github_upload_allowed: false',
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


if __name__ == "__main__":
    unittest.main()
