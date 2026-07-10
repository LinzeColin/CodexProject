import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE035_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE035_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE035_PHASE2_DATABASE_RECOVERY_SMOKE_SLICE.md"
PHASE3 = PURSUE_ROOT / "STAGE035_PHASE3_SCENARIO_VALIDATION.md"
PHASE4 = PURSUE_ROOT / "STAGE035_PHASE4_CLOSEOUT.md"
STAGE_REVIEW = PURSUE_ROOT / "STAGE035_STAGE_REVIEW.md"
INDEX = (
    PURSUE_ROOT
    / "database_recovery_smoke"
    / "stage035_database_recovery_smoke_index.json"
)
SCRIPT = ROOT / "scripts" / "check_database_recovery_smoke.py"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage035DatabaseRecoverySmokePhase1Tests(unittest.TestCase):
    def test_phase1_contracts_exist_and_bind_taskpack_identity(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")

        combined = "\n".join(
            [
                ENTRY.read_text(encoding="utf-8"),
                PHASE1.read_text(encoding="utf-8"),
            ]
        )
        required_terms = [
            "STAGE-035 · 数据库恢复冒烟测试",
            "IDS-V0_1-STAGE035-P1",
            "ACC-STAGE-035",
            "D06-S006",
            "D06 · PostgreSQL 控制面",
            "IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-035_数据库恢复冒烟测试.md",
            "2bb4847b6514e63d8f8e07be5c890e05b5d0875cd206ccf9e82b21a6ebccca62",
            "验证 metadata dump 能恢复到可运行状态",
            "Phase 1 · 范围、输入输出与边界确认",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_dump_restore_inputs_outputs_states_and_recovery(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "database_recovery_smoke_contract_id",
            "metadata_dump_ref",
            "metadata_dump_identity",
            "control_plane_schema_ref",
            "schema_migration_safety_ref",
            "connection_pool_contract_ref",
            "database_size_guard_ref",
            "data_retention_table_ref",
            "restore_target_contract",
            "restore_preflight_checklist",
            "restore_execution_plan",
            "restore_validation_checklist",
            "backup_checkpoint_ref",
            "rollback_plan_ref",
            "recovery_audit_ref",
            "owner_authorized_real_metadata_dump_required",
            "database_recovery_smoke_summary",
            "metadata_dump_identity_payload",
            "restore_preflight_payload",
            "restore_validation_payload",
            "rollback_verification_payload",
            "phase2_ready_contract",
            "DATABASE_RECOVERY_SMOKE_DRAFT",
            "DATABASE_RECOVERY_REAL_DUMP_REQUIRED",
            "DATABASE_RECOVERY_DUMP_IDENTITY_VERIFIED",
            "DATABASE_RECOVERY_ISOLATED_TARGET_REQUIRED",
            "DATABASE_RECOVERY_SCHEMA_COMPATIBILITY_REQUIRED",
            "DATABASE_RECOVERY_VALIDATION_REQUIRED",
            "DATABASE_RECOVERY_OWNER_CONFIRMATION_REQUIRED",
            "DATABASE_RECOVERY_RAW_CONTENT_BLOCKED",
            "DATABASE_RECOVERY_READY_FOR_PHASE2_SLICE",
            "PostgreSQL 只存控制面、状态和热索引，不存 500GB 原始文件",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_blocks_dump_access_live_restore_raw_data_secrets_outputs_and_fake_data(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        combined = "\n".join(
            [
                ENTRY.read_text(encoding="utf-8"),
                PHASE1.read_text(encoding="utf-8"),
            ]
        )

        required_terms = [
            "NO_PHASE2",
            "NO_POSTGRES_CONNECTION",
            "NO_DUMP_ACCESS",
            "NO_LIVE_MIGRATION",
            "NO_LIVE_RESTORE",
            "NO_RAW_DB_CONTENT",
            "NO_FAKE_DATA",
            "不创建 PostgreSQL database、schema、migration 文件、连接配置、metadata dump、恢复目标或恢复任务",
            "不连接 PostgreSQL",
            "不执行 migration dry-run、apply、rollback、backup、restore、schema diff 或恢复冒烟",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不提交 secrets、API key、数据库密码、credential-bearing DSN 或云端凭证",
            "不得使用虚构 IDS 业务数据、虚构数据库行、虚构 metadata dump、placeholder corpus 或伪造证据",
            "无 owner 授权真实 metadata dump 时必须停止",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch031_040_lock_roadmap_and_event_track_stage035_phase1_without_upload(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")

        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        lock_terms = [
            'batch_id: "IDS-V0_1-BATCH-031-040"',
            'push_allowed: false',
            "STAGE-035:",
            '      - "Phase 1"',
            'acceptance_id: "ACC-STAGE-035"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE035_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE035_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage035_database_recovery_smoke.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE035"',
            'current_phase_id: "IDS-STAGE035-P1"',
            'current_task_id: "IDS-V0_1-STAGE035-P1"',
            'next_gate_id: "IDS-STAGE035-P2-GATE"',
            'stage_id: "IDS-STAGE035"',
            'name: "STAGE-035 · 数据库恢复冒烟测试"',
            'phase_id: "IDS-STAGE035-P1"',
            'task_id: "IDS-V0_1-STAGE035-P1"',
            'status: "passed_with_local_evidence"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE035-P1-20260710-001"',
            '"event_type":"stage_boundary"',
            '"task_id":"IDS-V0_1-STAGE035-P1"',
            '"ACC-STAGE-035"',
            "STAGE035_PHASE1_SCOPE_BOUNDARY.md",
            "数据库恢复冒烟测试",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]

        self.assertNotIn('current_task_id: "IDS_V0_1-STAGE035-P1"', lock_text)
        for term in lock_terms:
            with self.subTest(term=term):
                self.assertIn(term, lock_text)
        allowed_current_states = [
            'status: "stage035_phase1_in_progress"',
            'status: "stage035_phase2_in_progress"',
            'status: "stage035_phase3_in_progress"',
            'status: "stage035_completed_local_pending_review"',
            'status: "stage035_completed_reviewed_local"',
        ]
        allowed_next_phases = [
            'next_phase: "Phase 2"',
            'next_phase: "Phase 3"',
            'next_phase: "Phase 4"',
            'next_phase: "stage_review_gate"',
            'next_stage: "STAGE-036"',
        ]
        allowed_next_gates = [
            'next_gate: "IDS-STAGE035-P2-GATE"',
            'next_gate: "IDS-STAGE035-P3-GATE"',
            'next_gate: "IDS-STAGE035-P4-GATE"',
            'next_gate: "IDS-STAGE035-REVIEW-GATE"',
            'next_gate: "IDS-STAGE036-P1-GATE"',
        ]
        allowed_current_tasks = [
            'current_task_id: "IDS-V0_1-STAGE035-P1"',
            'current_task_id: "IDS-V0_1-STAGE035-P2"',
            'current_task_id: "IDS-V0_1-STAGE035-P3"',
            'current_task_id: "IDS-V0_1-STAGE035-P4"',
            'current_task_id: "IDS-V0_1-STAGE035-REVIEW"',
        ]
        allowed_acceptance_states = [
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_static_recovery_smoke_contract_validated"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "reviewed_local_passed"',
        ]
        for allowed in [
            allowed_current_states,
            allowed_next_phases,
            allowed_next_gates,
            allowed_current_tasks,
            allowed_acceptance_states,
        ]:
            self.assertTrue(any(term in lock_text for term in allowed), allowed)
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


class Stage035DatabaseRecoverySmokePhase2Tests(unittest.TestCase):
    def _load_checker_module(self):
        self.assertTrue(SCRIPT.is_file(), f"missing checker script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage035_database_recovery_smoke", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_phase2_static_recovery_smoke_artifacts_exist(self):
        for path in [PHASE2, INDEX, SCRIPT]:
            self.assertTrue(path.is_file(), f"missing Phase 2 artifact: {path}")

        combined = "\n".join(
            [
                PHASE2.read_text(encoding="utf-8"),
                INDEX.read_text(encoding="utf-8"),
                SCRIPT.read_text(encoding="utf-8"),
            ]
        )
        required_terms = [
            "ids.stage035.database_recovery_smoke.index.v1",
            "ids.stage035.database_recovery_smoke.phase2.v1",
            "IDS-V0_1-STAGE035-P2",
            "ACC-STAGE-035",
            "database_recovery_smoke_contract_id",
            "STATIC_RECOVERY_PREFLIGHT_CONTRACT_VALID",
            "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP",
            "contract_valid",
            "execution_ready",
            "owner_authorized_real_dump_required",
            "owner_authorized_real_dump_available",
            "metadata_dump_contract",
            "restore_target_contract",
            "schema_migration_compatibility",
            "connection_pool_guard",
            "database_size_guard",
            "quality_constraint_guard",
            "storage_boundary",
            "restore_validation_contract",
            "rollback_contract",
            "audit_contract",
            "real_data_only_guard",
            "stage035_database_recovery_smoke_index.json",
            "check_database_recovery_smoke.py",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_checker_validates_integrated_contract_but_blocks_live_execution(self):
        module = self._load_checker_module()
        report = module.build_stage035_database_recovery_smoke_report(INDEX)

        self.assertEqual("ids.stage035.database_recovery_smoke.phase2.v1", report["schema_version"])
        self.assertEqual("ids.stage035.database_recovery_smoke.index.v1", report["index_schema_version"])
        self.assertEqual("IDS-V0_1-STAGE035-P2", report["task_id"])
        self.assertEqual("ACC-STAGE-035", report["acceptance_id"])
        self.assertTrue(report["contract_valid"])
        self.assertFalse(report["execution_ready"])
        self.assertEqual(
            "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP",
            report["execution_state"],
        )
        self.assertEqual(
            "无 owner 授权真实 metadata dump，恢复执行保持阻断。",
            report["block_reason_zh"],
        )
        self.assertTrue(all(report["contract_results"].values()), report["contract_results"])
        self.assertTrue(all(report["dependency_results"].values()), report["dependency_results"])
        self.assertTrue(all(report["runtime_policy_results"].values()), report["runtime_policy_results"])
        self.assertTrue(report["does_not_read_metadata_dump"])
        self.assertTrue(report["does_not_connect_to_postgres"])
        self.assertTrue(report["does_not_execute_restore"])
        self.assertTrue(report["does_not_write_runtime_outputs"])
        self.assertTrue(report["does_not_use_fake_ids_data"])

    def test_machine_index_binds_real_dependencies_and_fail_closed_guards(self):
        self.assertTrue(INDEX.is_file(), f"missing machine index: {INDEX}")
        index = json.loads(INDEX.read_text(encoding="utf-8"))

        self.assertEqual("ids.stage035.database_recovery_smoke.index.v1", index["schema_version"])
        self.assertEqual("IDS-V0_1-STAGE035-P2", index["task_id"])
        self.assertEqual("ACC-STAGE-035", index["acceptance_id"])
        self.assertEqual(
            "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP",
            index["metadata_dump_contract"]["execution_state"],
        )
        self.assertTrue(index["metadata_dump_contract"]["owner_authorized_real_dump_required"])
        self.assertFalse(index["metadata_dump_contract"]["owner_authorized_real_dump_available"])
        self.assertFalse(index["metadata_dump_contract"]["fabricated_dump_allowed"])
        self.assertFalse(index["metadata_dump_contract"]["fake_rows_allowed"])
        self.assertFalse(index["metadata_dump_contract"]["placeholder_corpus_allowed"])
        self.assertTrue(index["restore_target_contract"]["isolated_non_production_target_required"])
        self.assertFalse(index["restore_target_contract"]["production_target_allowed"])
        self.assertFalse(index["restore_target_contract"]["source_database_mutation_allowed"])
        self.assertEqual(10, index["connection_pool_guard"]["aggregate_max_pool_size"])
        self.assertEqual(0, index["connection_pool_guard"]["max_overflow"])
        self.assertTrue(index["database_size_guard"]["stage033_guard_authoritative"])
        self.assertTrue(index["quality_constraint_guard"]["chinese_failure_reason_required"])
        self.assertFalse(index["storage_boundary"]["stores_raw_files"])
        self.assertFalse(index["storage_boundary"]["stores_raw_database_rows"])
        self.assertFalse(index["storage_boundary"]["stores_unbounded_derived_artifacts"])
        self.assertFalse(index["runtime_policy"]["read_metadata_dump"])
        self.assertFalse(index["runtime_policy"]["connect_to_postgres"])
        self.assertFalse(index["runtime_policy"]["execute_restore"])
        self.assertFalse(index["runtime_policy"]["write_runtime_outputs"])

    def test_invalid_in_memory_contract_fails_closed_without_creating_files(self):
        module = self._load_checker_module()
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        index["metadata_dump_contract"]["fabricated_dump_allowed"] = True
        index["restore_target_contract"]["production_target_allowed"] = True
        index["runtime_policy"]["read_metadata_dump"] = True

        original_loader = module._load_json
        module._load_json = (
            lambda path: copy.deepcopy(index)
            if Path(path) == INDEX
            else original_loader(path)
        )
        try:
            report = module.build_stage035_database_recovery_smoke_report(INDEX)
        finally:
            module._load_json = original_loader

        self.assertFalse(report["contract_valid"])
        self.assertFalse(report["execution_ready"])
        self.assertEqual("BLOCKED_INVALID_RECOVERY_CONTRACT", report["execution_state"])
        self.assertFalse(report["contract_results"]["metadata_dump_contract_guard"])
        self.assertFalse(report["contract_results"]["isolated_restore_target_guard"])
        self.assertFalse(report["runtime_policy_results"]["read_metadata_dump"])
        self.assertFalse(report["does_not_read_metadata_dump"])

    def test_tampered_identity_or_missing_runtime_guard_fails_closed(self):
        module = self._load_checker_module()
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        index["database_recovery_smoke_contract_id"] = "tampered_contract"
        index["runtime_policy"].pop("read_metadata_dump")

        original_loader = module._load_json
        module._load_json = (
            lambda path: copy.deepcopy(index)
            if Path(path) == INDEX
            else original_loader(path)
        )
        try:
            report = module.build_stage035_database_recovery_smoke_report(INDEX)
        finally:
            module._load_json = original_loader

        self.assertFalse(report["contract_valid"])
        self.assertEqual("BLOCKED_INVALID_RECOVERY_CONTRACT", report["execution_state"])
        self.assertFalse(report["contract_results"]["contract_identity_guard"])
        self.assertFalse(report["runtime_policy_results"]["keys_exact"])
        self.assertFalse(report["runtime_policy_results"]["read_metadata_dump"])
        self.assertFalse(report["does_not_read_metadata_dump"])

    def test_checker_cli_emits_truthful_stdout_json_without_live_side_effects(self):
        self.assertTrue(SCRIPT.is_file(), f"missing checker script: {SCRIPT}")
        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPT)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual("Phase 4", payload["phase"])
        phase2 = payload["phase2_report"]
        self.assertTrue(phase2["contract_valid"])
        self.assertFalse(phase2["execution_ready"])
        self.assertEqual(
            "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP",
            phase2["execution_state"],
        )
        self.assertTrue(phase2["does_not_read_metadata_dump"])
        self.assertTrue(phase2["does_not_connect_to_postgres"])
        self.assertTrue(phase2["does_not_execute_restore"])
        self.assertEqual("", completed.stderr)

    def test_phase2_doc_and_governance_record_blocked_static_slice_without_upload(self):
        self.assertTrue(PHASE2.is_file(), f"missing phase2 evidence: {PHASE2}")
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")

        phase2_text = PHASE2.read_text(encoding="utf-8")
        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        phase2_terms = [
            "Phase 2 · 静态恢复 preflight 合同切片",
            "contract_valid=true",
            "execution_ready=false",
            "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP",
            "无 owner 授权真实 metadata dump，恢复执行保持阻断",
            "不执行 pg_dump、pg_restore、psql、migration、backup、restore 或 recovery smoke",
            "不得使用虚构 IDS 业务数据、虚构数据库行、虚构 metadata dump、placeholder corpus 或伪造证据",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_PHASE3",
        ]
        lock_terms = [
            "STAGE-035:",
            '      - "Phase 1"',
            '      - "Phase 2"',
            "STAGE035_PHASE2_DATABASE_RECOVERY_SMOKE_SLICE.md",
            "stage035_database_recovery_smoke_index.json",
            "check_database_recovery_smoke.py",
            'push_allowed: false',
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE035"',
            'current_phase_id: "IDS-STAGE035-P2"',
            'current_task_id: "IDS-V0_1-STAGE035-P2"',
            'next_gate_id: "IDS-STAGE035-P3-GATE"',
            'phase_id: "IDS-STAGE035-P2"',
            'task_id: "IDS-V0_1-STAGE035-P2"',
            'status: "passed_with_local_evidence"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE035-P2-20260710-001"',
            '"event_type":"stage_slice"',
            '"task_id":"IDS-V0_1-STAGE035-P2"',
            '"ACC-STAGE-035"',
            "STAGE035_PHASE2_DATABASE_RECOVERY_SMOKE_SLICE.md",
            "stage035_database_recovery_smoke_index.json",
            "check_database_recovery_smoke.py",
            "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP",
        ]

        for term in phase2_terms:
            with self.subTest(term=term):
                self.assertIn(term, phase2_text)
        for term in lock_terms:
            with self.subTest(term=term):
                self.assertIn(term, lock_text)
        allowed_current_states = [
            'status: "stage035_phase2_in_progress"',
            'status: "stage035_phase3_in_progress"',
            'status: "stage035_completed_local_pending_review"',
            'status: "stage035_completed_reviewed_local"',
        ]
        allowed_next_phases = [
            'next_phase: "Phase 3"',
            'next_phase: "Phase 4"',
            'next_phase: "stage_review_gate"',
            'next_stage: "STAGE-036"',
        ]
        allowed_next_gates = [
            'next_gate: "IDS-STAGE035-P3-GATE"',
            'next_gate: "IDS-STAGE035-P4-GATE"',
            'next_gate: "IDS-STAGE035-REVIEW-GATE"',
            'next_gate: "IDS-STAGE036-P1-GATE"',
        ]
        allowed_current_tasks = [
            'current_task_id: "IDS-V0_1-STAGE035-P2"',
            'current_task_id: "IDS-V0_1-STAGE035-P3"',
            'current_task_id: "IDS-V0_1-STAGE035-P4"',
            'current_task_id: "IDS-V0_1-STAGE035-REVIEW"',
        ]
        allowed_acceptance_states = [
            'acceptance_status: "phase2_static_recovery_smoke_contract_validated"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "reviewed_local_passed"',
        ]
        for allowed in [
            allowed_current_states,
            allowed_next_phases,
            allowed_next_gates,
            allowed_current_tasks,
            allowed_acceptance_states,
        ]:
            self.assertTrue(any(term in lock_text for term in allowed), allowed)
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


class Stage035DatabaseRecoverySmokePhase3Tests(unittest.TestCase):
    EXPECTED_SCENARIOS = {
        "migration_dry_run",
        "repeat_execution",
        "failure_rollback",
        "recovery_smoke",
        "owner_dump_absence_stop_gate",
        "raw_large_file_block",
        "unbounded_derived_artifact_block",
        "connection_pool_boundary",
        "transaction_boundary",
        "constraint_error_explanations",
        "source_non_interference",
    }

    def _load_checker_module(self):
        self.assertTrue(SCRIPT.is_file(), f"missing checker script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage035_database_recovery_smoke_p3", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _scenario_builder(self):
        module = self._load_checker_module()
        self.assertTrue(
            hasattr(module, "build_stage035_scenario_validation_report"),
            "missing Phase 3 scenario report builder",
        )
        return module, module.build_stage035_scenario_validation_report

    def test_phase3_artifact_and_scenario_contract_exist(self):
        self.assertTrue(PHASE3.is_file(), f"missing Phase 3 evidence: {PHASE3}")
        combined = "\n".join(
            [PHASE3.read_text(encoding="utf-8"), SCRIPT.read_text(encoding="utf-8")]
        )
        required_terms = [
            "ids.stage035.database_recovery_smoke.phase3.v1",
            "IDS-V0_1-STAGE035-P3",
            "ACC-STAGE-035",
            "build_stage035_scenario_validation_report",
            "scenario_validation_valid",
            "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP",
            "live_execution_performed",
            "NO_PHASE4",
        ] + sorted(self.EXPECTED_SCENARIOS)
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_scenario_report_passes_static_checks_but_keeps_recovery_blocked(self):
        _, builder = self._scenario_builder()
        report = builder(INDEX)

        self.assertEqual("ids.stage035.database_recovery_smoke.phase3.v1", report["schema_version"])
        self.assertEqual("Phase 3", report["phase"])
        self.assertEqual("IDS-V0_1-STAGE035-P3", report["task_id"])
        self.assertEqual("ACC-STAGE-035", report["acceptance_id"])
        self.assertEqual(self.EXPECTED_SCENARIOS, set(report["scenario_results"]))
        self.assertTrue(report["phase2_contract_valid"])
        self.assertTrue(report["scenario_validation_valid"])
        self.assertFalse(report["execution_ready"])
        self.assertEqual(
            "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP",
            report["execution_state"],
        )
        self.assertTrue(
            all(result["status"] == "PASS" for result in report["scenario_results"].values()),
            report["scenario_results"],
        )
        recovery = report["scenario_results"]["recovery_smoke"]
        self.assertEqual(
            "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP",
            recovery["observed_state"],
        )
        self.assertTrue(recovery["expected_block"])
        self.assertFalse(recovery["live_execution_performed"])
        self.assertFalse(report["live_execution_performed"])
        self.assertTrue(report["does_not_read_metadata_dump"])
        self.assertTrue(report["does_not_connect_to_postgres"])
        self.assertTrue(report["does_not_execute_restore"])
        self.assertTrue(report["does_not_execute_migration"])
        self.assertTrue(report["does_not_write_runtime_outputs"])
        self.assertTrue(report["does_not_use_fake_ids_data"])
        self.assertEqual("IDS-STAGE035-P4-GATE", report["next_gate"])
        self.assertFalse(report["github_upload_allowed"])
        self.assertFalse(report["app_reinstall_allowed"])

    def test_scenario_report_is_deterministic_and_owner_explainable(self):
        _, builder = self._scenario_builder()
        first = builder(INDEX)
        second = builder(INDEX)

        self.assertEqual(first["scenario_results"], second["scenario_results"])
        for scenario_id, result in first["scenario_results"].items():
            with self.subTest(scenario_id=scenario_id):
                self.assertTrue(result["evidence"])
                self.assertTrue(result["owner_explanation_zh"])
                self.assertFalse(result["live_execution_performed"])

    def test_invalid_runtime_restore_contract_fails_scenarios_closed(self):
        module, builder = self._scenario_builder()
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        index["runtime_policy"]["execute_restore"] = True

        original_loader = module._load_json
        module._load_json = (
            lambda path: copy.deepcopy(index)
            if Path(path) == INDEX
            else original_loader(path)
        )
        try:
            report = builder(INDEX)
        finally:
            module._load_json = original_loader

        self.assertFalse(report["phase2_contract_valid"])
        self.assertFalse(report["scenario_validation_valid"])
        self.assertEqual("BLOCKED_INVALID_RECOVERY_CONTRACT", report["execution_state"])
        self.assertEqual("FAIL", report["scenario_results"]["recovery_smoke"]["status"])
        self.assertFalse(report["does_not_execute_restore"])
        self.assertFalse(report["live_execution_performed"])

    def test_checker_cli_includes_phase3_report_without_live_side_effects(self):
        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPT)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIn("scenario_report", payload)
        scenario = payload["scenario_report"]
        self.assertTrue(scenario["scenario_validation_valid"])
        self.assertFalse(scenario["execution_ready"])
        self.assertFalse(scenario["live_execution_performed"])
        self.assertEqual(
            "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP",
            scenario["scenario_results"]["recovery_smoke"]["observed_state"],
        )
        self.assertEqual("", completed.stderr)

    def test_phase3_doc_and_governance_record_static_validation_without_upload(self):
        self.assertTrue(PHASE3.is_file(), f"missing Phase 3 evidence: {PHASE3}")
        phase3_text = PHASE3.read_text(encoding="utf-8")
        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        phase3_terms = [
            "Phase 3 · 数据库恢复冒烟测试专项验证与异常场景",
            "recovery_smoke",
            "observed_state=BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP",
            "live_execution_performed=false",
            "不执行 live migration dry-run、apply、rollback、backup、restore、schema diff 或 recovery smoke",
            "不得使用虚构 IDS 业务数据、虚构数据库行、虚构 metadata dump、placeholder corpus 或伪造证据",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_PHASE4",
        ]
        lock_terms = [
            '      - "Phase 3"',
            "STAGE035_PHASE3_SCENARIO_VALIDATION.md",
            'push_allowed: false',
        ]
        allowed_current_states = [
            'status: "stage035_phase3_in_progress"',
            'status: "stage035_completed_local_pending_review"',
            'status: "stage035_completed_reviewed_local"',
        ]
        allowed_next_phases = [
            'next_phase: "Phase 4"',
            'next_phase: "stage_review_gate"',
            'next_stage: "STAGE-036"',
        ]
        allowed_next_gates = [
            'next_gate: "IDS-STAGE035-P4-GATE"',
            'next_gate: "IDS-STAGE035-REVIEW-GATE"',
            'next_gate: "IDS-STAGE036-P1-GATE"',
        ]
        allowed_current_tasks = [
            'current_task_id: "IDS-V0_1-STAGE035-P3"',
            'current_task_id: "IDS-V0_1-STAGE035-P4"',
            'current_task_id: "IDS-V0_1-STAGE035-REVIEW"',
        ]
        allowed_acceptance_states = [
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "reviewed_local_passed"',
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE035"',
            'current_phase_id: "IDS-STAGE035-P3"',
            'current_task_id: "IDS-V0_1-STAGE035-P3"',
            'next_gate_id: "IDS-STAGE035-P4-GATE"',
            'phase_id: "IDS-STAGE035-P3"',
            'task_id: "IDS-V0_1-STAGE035-P3"',
            'status: "passed_with_local_evidence"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE035-P3-20260710-001"',
            '"event_type":"validation"',
            '"task_id":"IDS-V0_1-STAGE035-P3"',
            '"ACC-STAGE-035"',
            "STAGE035_PHASE3_SCENARIO_VALIDATION.md",
            "build_stage035_scenario_validation_report",
            "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP",
        ]
        for terms, text in [
            (phase3_terms, phase3_text),
            (lock_terms, lock_text),
            (roadmap_terms, roadmap_text),
            (event_terms, events_text),
        ]:
            for term in terms:
                with self.subTest(term=term):
                    self.assertIn(term, text)
        for allowed in [
            allowed_current_states,
            allowed_next_phases,
            allowed_next_gates,
            allowed_current_tasks,
            allowed_acceptance_states,
        ]:
            self.assertTrue(any(term in lock_text for term in allowed), allowed)


class Stage035DatabaseRecoverySmokePhase4Tests(unittest.TestCase):
    def _load_checker_module(self):
        self.assertTrue(SCRIPT.is_file(), f"missing checker script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage035_database_recovery_smoke_p4", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _delivery_builder(self):
        module = self._load_checker_module()
        self.assertTrue(
            hasattr(module, "build_stage035_delivery_report"),
            "missing Phase 4 delivery report builder",
        )
        return module, module.build_stage035_delivery_report

    def test_phase4_artifact_and_delivery_contract_exist(self):
        self.assertTrue(PHASE4.is_file(), f"missing Phase 4 evidence: {PHASE4}")
        combined = "\n".join(
            [PHASE4.read_text(encoding="utf-8"), SCRIPT.read_text(encoding="utf-8")]
        )
        required_terms = [
            "ids.stage035.database_recovery_smoke.phase4.v1",
            "IDS-V0_1-STAGE035-P4",
            "ACC-STAGE-035",
            "build_stage035_delivery_report",
            "delivery_contract_valid",
            "schema_diff",
            "migration_output",
            "recovery_test_log",
            "known_limits",
            "destructive_migration_confirmation",
            "rollback_steps",
            "backup_restore_steps",
            "chinese_owner_feedback",
            "PASS_WITH_EXPECTED_BLOCK",
            "NO_STAGE_REVIEW_THIS_RUN",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_delivery_report_is_valid_but_does_not_claim_live_restore(self):
        _, builder = self._delivery_builder()
        report = builder(INDEX)

        self.assertEqual("ids.stage035.database_recovery_smoke.phase4.v1", report["schema_version"])
        self.assertEqual("Phase 4", report["phase"])
        self.assertEqual("IDS-V0_1-STAGE035-P4", report["task_id"])
        self.assertEqual("ACC-STAGE-035", report["acceptance_id"])
        self.assertTrue(report["delivery_contract_valid"])
        self.assertTrue(all(report["delivery_check_results"].values()))
        self.assertEqual("IDS-STAGE035-REVIEW-GATE", report["next_gate"])
        self.assertEqual("pending_next_run", report["stage_review_status"])
        self.assertFalse(report["github_upload_allowed"])
        self.assertFalse(report["app_reinstall_allowed"])
        self.assertFalse(report["live_execution_performed"])
        self.assertTrue(report["does_not_read_metadata_dump"])
        self.assertTrue(report["does_not_connect_to_postgres"])
        self.assertTrue(report["does_not_execute_restore"])
        self.assertTrue(report["does_not_execute_migration"])
        self.assertTrue(report["does_not_write_runtime_outputs"])
        self.assertTrue(report["does_not_use_fake_ids_data"])

    def test_delivery_evidence_distinguishes_static_contract_from_live_outputs(self):
        _, builder = self._delivery_builder()
        report = builder(INDEX)

        self.assertEqual(
            "static_recovery_contract_diff_not_executed",
            report["schema_diff"]["mode"],
        )
        self.assertEqual("NOT_EXECUTED", report["schema_diff"]["live_schema_diff_result"])
        self.assertEqual(
            "static_recovery_migration_output_not_executed",
            report["migration_output"]["mode"],
        )
        self.assertEqual("NOT_EXECUTED", report["migration_output"]["live_migration_result"])
        self.assertEqual(
            "static_recovery_test_log_expected_block",
            report["recovery_test_log"]["mode"],
        )
        self.assertEqual("NOT_EXECUTED", report["recovery_test_log"]["live_restore_result"])
        self.assertEqual("PASS_WITH_EXPECTED_BLOCK", report["recovery_test_log"]["result"])
        self.assertEqual(
            "BLOCKED_PENDING_OWNER_AUTHORIZED_REAL_METADATA_DUMP",
            report["recovery_test_log"]["execution_state"],
        )
        confirmation = report["destructive_migration_confirmation"]
        self.assertTrue(confirmation["required"])
        self.assertFalse(confirmation["destructive_allowed_by_default"])
        self.assertTrue(confirmation["manual_owner_confirmation_required"])
        self.assertGreaterEqual(len(report["rollback_steps"]), 4)
        self.assertGreaterEqual(len(report["backup_restore_steps"]), 5)
        self.assertGreaterEqual(len(report["known_limits"]), 5)
        self.assertIn("未执行真实恢复", report["chinese_owner_feedback"])

    def test_invalid_restore_policy_fails_delivery_closed_without_creating_files(self):
        module, builder = self._delivery_builder()
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        index["runtime_policy"]["execute_restore"] = True

        original_loader = module._load_json
        module._load_json = (
            lambda path: copy.deepcopy(index)
            if Path(path) == INDEX
            else original_loader(path)
        )
        try:
            report = builder(INDEX)
        finally:
            module._load_json = original_loader

        self.assertFalse(report["delivery_contract_valid"])
        self.assertFalse(report["delivery_check_results"]["phase2_contract_valid"])
        self.assertFalse(report["delivery_check_results"]["phase3_scenarios_valid"])
        self.assertEqual("FAIL_CLOSED", report["recovery_test_log"]["result"])
        self.assertEqual("BLOCKED_INVALID_RECOVERY_CONTRACT", report["execution_state"])
        self.assertFalse(report["does_not_execute_restore"])
        self.assertFalse(report["live_execution_performed"])

    def test_checker_cli_includes_phase4_delivery_without_live_side_effects(self):
        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPT)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIn("delivery_report", payload)
        delivery = payload["delivery_report"]
        self.assertTrue(delivery["delivery_contract_valid"])
        self.assertEqual("PASS_WITH_EXPECTED_BLOCK", delivery["recovery_test_log"]["result"])
        self.assertEqual("NOT_EXECUTED", delivery["recovery_test_log"]["live_restore_result"])
        self.assertFalse(delivery["live_execution_performed"])
        self.assertEqual("IDS-STAGE035-REVIEW-GATE", delivery["next_gate"])
        self.assertEqual("", completed.stderr)

    def test_phase4_doc_and_governance_stop_at_separate_review_gate(self):
        self.assertTrue(PHASE4.is_file(), f"missing Phase 4 evidence: {PHASE4}")
        phase4_text = PHASE4.read_text(encoding="utf-8")
        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        phase4_terms = [
            "Phase 4 · 数据库恢复冒烟测试交付证据、回滚与中文反馈",
            "live_schema_diff_result=NOT_EXECUTED",
            "live_migration_result=NOT_EXECUTED",
            "live_restore_result=NOT_EXECUTED",
            "result=PASS_WITH_EXPECTED_BLOCK",
            "stage_review_status=pending_next_run",
            "任何破坏性 migration 或 restore 必须单独人工确认",
            "不得使用虚构 IDS 业务数据、虚构数据库行、虚构 metadata dump、placeholder corpus 或伪造证据",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_STAGE_REVIEW_THIS_RUN",
        ]
        lock_terms = [
            '      - "Phase 4"',
            "STAGE035_PHASE4_CLOSEOUT.md",
            'push_allowed: false',
        ]
        allowed_current_states = [
            'status: "stage035_completed_local_pending_review"',
            'status: "stage035_completed_reviewed_local"',
        ]
        allowed_next_phases = [
            'next_phase: "stage_review_gate"',
            'next_stage: "STAGE-036"',
        ]
        allowed_next_gates = [
            'next_gate: "IDS-STAGE035-REVIEW-GATE"',
            'next_gate: "IDS-STAGE036-P1-GATE"',
        ]
        allowed_current_tasks = [
            'current_task_id: "IDS-V0_1-STAGE035-P4"',
            'current_task_id: "IDS-V0_1-STAGE035-REVIEW"',
        ]
        allowed_acceptance_states = [
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "reviewed_local_passed"',
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE035"',
            'current_phase_id: "IDS-STAGE035-P4"',
            'current_task_id: "IDS-V0_1-STAGE035-P4"',
            'next_gate_id: "IDS-STAGE035-REVIEW-GATE"',
            'phase_id: "IDS-STAGE035-P4"',
            'task_id: "IDS-V0_1-STAGE035-P4"',
            'status: "passed_no_github_upload_until_stage_review"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE035-P4-20260710-001"',
            '"event_type":"stage_closeout"',
            '"task_id":"IDS-V0_1-STAGE035-P4"',
            '"ACC-STAGE-035"',
            "STAGE035_PHASE4_CLOSEOUT.md",
            "build_stage035_delivery_report",
            "PASS_WITH_EXPECTED_BLOCK",
            "IDS-STAGE035-REVIEW-GATE",
        ]
        for terms, text in [
            (phase4_terms, phase4_text),
            (lock_terms, lock_text),
            (roadmap_terms, roadmap_text),
            (event_terms, events_text),
        ]:
            for term in terms:
                with self.subTest(term=term):
                    self.assertIn(term, text)
        for allowed in [
            allowed_current_states,
            allowed_next_phases,
            allowed_next_gates,
            allowed_current_tasks,
            allowed_acceptance_states,
        ]:
            self.assertTrue(any(term in lock_text for term in allowed), allowed)


class Stage035DatabaseRecoverySmokeReviewTests(unittest.TestCase):
    def _load_checker_module(self):
        self.assertTrue(SCRIPT.is_file(), f"missing checker script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location(
            "stage035_database_recovery_smoke_review", SCRIPT
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _delivery_with_index(self, module, index):
        original_loader = module._load_json
        module._load_json = (
            lambda path: copy.deepcopy(index)
            if Path(path).resolve() == INDEX
            else original_loader(path)
        )
        try:
            return module.build_stage035_delivery_report(INDEX)
        finally:
            module._load_json = original_loader

    def test_stage_review_artifact_records_phase_audit_findings_and_no_upload_boundary(self):
        self.assertTrue(STAGE_REVIEW.is_file(), f"missing stage review: {STAGE_REVIEW}")
        review_text = STAGE_REVIEW.read_text(encoding="utf-8")

        required_terms = [
            "IDS-V0_1-STAGE035-REVIEW",
            "ACC-STAGE-035",
            "STAGE-035 · 数据库恢复冒烟测试",
            "STAGE035-REVIEW-F1",
            "STAGE035-REVIEW-F2",
            "STAGE035-REVIEW-F3",
            "P0 source binding",
            "Phase 1 boundary",
            "Phase 2 static recovery preflight",
            "Phase 3 scenario validation",
            "Phase 4 closeout",
            "build_stage035_delivery_report",
            "PASS_WITH_EXPECTED_BLOCK",
            "completed_reviewed_local",
            "IDS-STAGE036-P1-GATE",
            "NO_GITHUB_UPLOAD",
            "NO_APP_REINSTALL",
            "NO_STAGE036_THIS_RUN",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, review_text)

    def test_stage_review_gate_batch_roadmap_and_event_track_reviewed_local_no_upload(self):
        self.assertTrue(STAGE_REVIEW.is_file(), f"missing stage review: {STAGE_REVIEW}")
        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        lock_terms = [
            'STAGE-035:',
            'status: "completed_reviewed_local"',
            '      - "Phase 1"',
            '      - "Phase 2"',
            '      - "Phase 3"',
            '      - "Phase 4"',
            'review_status: "passed"',
            'next_stage: "STAGE-036"',
            'next_gate: "IDS-STAGE036-P1-GATE"',
            'current_task_id: "IDS-V0_1-STAGE035-REVIEW"',
            'acceptance_status: "reviewed_local_passed"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE035_STAGE_REVIEW.md",
            'push_allowed: false',
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE035"',
            'current_phase_id: "IDS-STAGE035-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE035-REVIEW"',
            'next_gate_id: "IDS-STAGE036-P1-GATE"',
            'review_id: "IDS-STAGE035-REVIEW"',
            'task_id: "IDS-V0_1-STAGE035-REVIEW"',
            'status: "completed"',
            "STAGE035_STAGE_REVIEW.md",
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE035-REVIEW-20260710-001"',
            '"event_type":"stage_review"',
            '"task_id":"IDS-V0_1-STAGE035-REVIEW"',
            '"ACC-STAGE-035"',
            "STAGE035_STAGE_REVIEW.md",
            "IDS-STAGE036-P1-GATE",
        ]

        for terms, text in [
            (lock_terms, lock_text),
            (roadmap_terms, roadmap_text),
            (event_terms, events_text),
        ]:
            for term in terms:
                with self.subTest(term=term):
                    self.assertIn(term, text)

    def test_review_repair_promotes_phase4_delivery_to_cli_top_level(self):
        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPT)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual("ids.stage035.database_recovery_smoke.phase4.v1", payload["schema_version"])
        self.assertEqual("Phase 4", payload["phase"])
        self.assertEqual("IDS-V0_1-STAGE035-P4", payload["task_id"])
        self.assertEqual("IDS-STAGE035-REVIEW-GATE", payload["next_gate"])
        self.assertTrue(payload["delivery_contract_valid"])
        self.assertIn("phase2_report", payload)
        self.assertIn("scenario_report", payload)
        self.assertIn("delivery_report", payload)

    def test_review_repair_uses_one_immutable_index_snapshot(self):
        module = self._load_checker_module()
        valid_index = json.loads(INDEX.read_text(encoding="utf-8"))
        first_snapshot = copy.deepcopy(valid_index)
        first_snapshot["metadata_dump_contract"][
            "owner_authorized_real_dump_available"
        ] = True
        load_count = 0
        original_loader = module._load_json

        def sequenced_loader(path):
            nonlocal load_count
            if Path(path).resolve() == INDEX:
                load_count += 1
                return copy.deepcopy(first_snapshot if load_count == 1 else valid_index)
            return original_loader(path)

        module._load_json = sequenced_loader
        try:
            report = module.build_stage035_delivery_report(INDEX)
        finally:
            module._load_json = original_loader

        self.assertEqual(1, load_count)
        self.assertFalse(report["delivery_contract_valid"])
        self.assertEqual("FAIL_CLOSED", report["recovery_test_log"]["result"])
        self.assertEqual("BLOCKED_INVALID_RECOVERY_CONTRACT", report["execution_state"])
        self.assertTrue(report["recovery_test_log"]["owner_authorized_real_dump_available"])

    def test_review_repair_rejects_unvalidated_security_fields(self):
        module = self._load_checker_module()
        base = json.loads(INDEX.read_text(encoding="utf-8"))
        cases = {
            "plaintext_credential_policy": lambda index: index["restore_target_contract"].__setitem__(
                "credential_ref_policy", "plaintext_credential_allowed"
            ),
            "missing_migration_validation_checks": lambda index: index[
                "schema_migration_compatibility"
            ].__setitem__("required_validation_checks", []),
            "raw_log_body_storage": lambda index: index["storage_boundary"].__setitem__(
                "stores_raw_log_bodies", True
            ),
        }

        for name, mutate in cases.items():
            with self.subTest(case=name):
                index = copy.deepcopy(base)
                mutate(index)
                report = self._delivery_with_index(module, index)
                self.assertFalse(report["delivery_contract_valid"])
                self.assertFalse(report["delivery_check_results"]["phase2_contract_valid"])
                self.assertEqual("FAIL_CLOSED", report["recovery_test_log"]["result"])

    def test_review_repair_binds_phase4_evidence_to_machine_contract(self):
        module = self._load_checker_module()
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        self.assertIn("phase4_delivery_contract", index)
        report = self._delivery_with_index(module, index)
        self.assertIn("phase4_contract_results", report)
        self.assertTrue(all(report["phase4_contract_results"].values()))

        tampered = copy.deepcopy(index)
        rollback = {
            step["step_id"]: step
            for step in tampered["phase4_delivery_contract"]["rollback_steps"]
        }
        rollback["preserve_source_database"]["source_database_mutation_allowed"] = True
        tampered_report = self._delivery_with_index(module, tampered)

        self.assertFalse(tampered_report["delivery_contract_valid"])
        self.assertFalse(
            tampered_report["phase4_contract_results"]["rollback_steps_valid"]
        )
        self.assertEqual("FAIL_CLOSED", tampered_report["recovery_test_log"]["result"])

    def test_owner_render_uses_singular_risk_field(self):
        scripts_dir = ROOT.parent / "scripts"
        spec = importlib.util.spec_from_file_location(
            "stage035_lean_governance_review", scripts_dir / "lean_governance.py"
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        sys.path.insert(0, str(scripts_dir))
        try:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            sys.path.remove(str(scripts_dir))

        roadmap = {
            "project_id": "KM_IDSystem",
            "stages": [
                {
                    "stage_id": "IDS-STAGE035",
                    "name": "review fixture",
                    "phases": [
                        {
                            "phase_id": "IDS-STAGE035-P4",
                            "name": "review fixture",
                            "tasks": [
                                {
                                    "task_id": "IDS-V0_1-STAGE035-P4",
                                    "name": "review fixture",
                                    "status": "completed",
                                    "estimated_hours": 1,
                                    "risk": "phase4 risk must remain owner-visible",
                                }
                            ],
                        }
                    ],
                }
            ],
        }
        rendered = "\n".join(module.render_roadmap_body(roadmap))
        self.assertIn(
            "IDS-V0_1-STAGE035-P4 risks: `phase4 risk must remain owner-visible`",
            rendered,
        )


if __name__ == "__main__":
    unittest.main()
