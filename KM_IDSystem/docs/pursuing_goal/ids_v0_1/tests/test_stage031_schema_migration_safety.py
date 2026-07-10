import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE031_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE031_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE031_PHASE2_SCHEMA_MIGRATION_SAFETY_SLICE.md"
PHASE3 = PURSUE_ROOT / "STAGE031_PHASE3_SCENARIO_VALIDATION.md"
PHASE4 = PURSUE_ROOT / "STAGE031_PHASE4_CLOSEOUT.md"
STAGE_REVIEW = PURSUE_ROOT / "STAGE031_STAGE_REVIEW.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
SAFETY_ROOT = PURSUE_ROOT / "schema_migration_safety"
SAFETY_INDEX = SAFETY_ROOT / "stage031_migration_safety_index.json"
CONTROL_PLANE_ROOT = PURSUE_ROOT / "postgresql_control_plane"
CONTROL_PLANE_SQL = CONTROL_PLANE_ROOT / "001_control_plane_schema.sql"
CONTROL_PLANE_INDEX = CONTROL_PLANE_ROOT / "control_plane_schema_index.json"
SCRIPT = ROOT / "scripts" / "check_schema_migration_safety.py"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage031SchemaMigrationSafetyPhase1Tests(unittest.TestCase):
    def _load_phase2_module(self):
        self.assertTrue(SCRIPT.is_file(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage031_schema_migration_safety", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

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
            "STAGE-031 · Schema 迁移安全",
            "IDS-V0_1-STAGE031-P1",
            "ACC-STAGE-031",
            "D06-S002",
            "D06 · PostgreSQL 控制面",
            "IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-031_Schema迁移安全.md",
            "17a91f01a284d4046a0a17f17f02a5be60b2c351b82a91c87c9c75106800be88",
            "所有 schema migration 必须有 dry-run、备份、校验和回滚",
            "Phase 1 · 范围、输入输出与边界确认",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_migration_safety_inputs_outputs_and_owner_states(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "schema_migration_safety_contract_id",
            "schema_change_set_ref",
            "migration_dry_run_plan",
            "backup_checkpoint_ref",
            "validation_checklist",
            "rollback_plan_ref",
            "recovery_smoke_plan_ref",
            "migration_audit_ref",
            "destructive_migration_review_state",
            "migration_safety_summary",
            "rollback_verification_requirements",
            "owner_stop_gate_payload",
            "SCHEMA_MIGRATION_DRAFT",
            "SCHEMA_MIGRATION_DRY_RUN_REQUIRED",
            "SCHEMA_MIGRATION_BACKUP_REQUIRED",
            "SCHEMA_MIGRATION_ROLLBACK_REQUIRED",
            "SCHEMA_MIGRATION_DESTRUCTIVE_OWNER_CONFIRMATION_REQUIRED",
            "SCHEMA_MIGRATION_READY_FOR_PHASE2_SLICE",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_blocks_runtime_migration_raw_data_secrets_and_fake_data(self):
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
            "NO_LIVE_MIGRATION",
            "NO_POSTGRES_CONNECTION",
            "NO_RAW_DB_CONTENT",
            "不创建 PostgreSQL database、schema、migration 文件或连接配置",
            "不连接 PostgreSQL",
            "不执行 migration dry-run、apply、rollback、backup、restore 或 schema diff",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不提交 secrets、API key、数据库密码或云端凭证",
            "不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch031_040_lock_roadmap_and_event_track_stage031_phase1_without_upload(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")

        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        lock_terms = [
            'batch_id: "IDS-V0_1-BATCH-031-040"',
            'stage_range: "STAGE-031..STAGE-040"',
            'acceptance_range: "ACC-STAGE-031..ACC-STAGE-040"',
            'push_allowed: false',
            'acceptance_id: "ACC-STAGE-031"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage031_schema_migration_safety.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]
        roadmap_terms = [
            'stage_id: "IDS-STAGE031"',
            'name: "STAGE-031 · Schema 迁移安全"',
            'phase_id: "IDS-STAGE031-P1"',
            'status: "passed_with_local_evidence"',
        ]
        allowed_roadmap_stage_terms = [
            'current_stage_id: "IDS-STAGE031"',
            'current_stage_id: "IDS-STAGE032"',
            'current_stage_id: "IDS-STAGE033"',
            'current_stage_id: "IDS-STAGE034"',
            'current_stage_id: "IDS-STAGE035"',
        ]
        allowed_lock_current_terms = [
            'status: "stage031_phase1_in_progress"',
            'status: "stage031_phase2_in_progress"',
            'status: "stage031_phase3_in_progress"',
            'status: "stage031_completed_local_pending_review"',
            'status: "stage031_completed_reviewed_local"',
            'status: "stage032_phase1_in_progress"',
            'status: "stage032_phase2_in_progress"',
            'status: "stage032_phase3_in_progress"',
            'status: "stage032_completed_local_pending_review"',
            'status: "stage032_completed_reviewed_local"',
            'status: "stage033_phase1_in_progress"',
            'status: "stage033_phase2_in_progress"',
            'status: "stage033_phase3_in_progress"',
            'status: "stage033_completed_local_pending_review"',
            'status: "stage033_completed_reviewed_local"',
            'status: "stage034_phase1_in_progress"',
            'status: "stage034_phase2_in_progress"',
            'status: "stage034_phase3_in_progress"',
            'status: "stage034_completed_local_pending_review"',
            'status: "stage034_completed_reviewed_local"',
            'status: "stage035_phase1_in_progress"',
            'status: "stage035_phase2_in_progress"',
            'status: "stage035_phase3_in_progress"',
            'status: "stage035_completed_local_pending_review"',
        ]
        allowed_lock_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE031-P1"',
            'current_task_id: "IDS-V0_1-STAGE031-P2"',
            'current_task_id: "IDS-V0_1-STAGE031-P3"',
            'current_task_id: "IDS-V0_1-STAGE031-P4"',
            'current_task_id: "IDS-V0_1-STAGE031-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE032-P1"',
            'current_task_id: "IDS-V0_1-STAGE032-P4"',
            'current_task_id: "IDS-V0_1-STAGE032-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE033-P1"',
            'current_task_id: "IDS-V0_1-STAGE033-P2"',
            'current_task_id: "IDS-V0_1-STAGE033-P3"',
            'current_task_id: "IDS-V0_1-STAGE033-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
        ]
        allowed_lock_acceptance_terms = [
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "phase2_size_guard_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "phase2_safety_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_defined"',
            'acceptance_status: "local_passed_pending_stage_review"',
            'acceptance_status: "reviewed_local_passed"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
        ]
        allowed_lock_gate_terms = [
            'next_gate: "IDS-STAGE031-P2-GATE"',
            'next_gate: "IDS-STAGE031-P3-GATE"',
            'next_gate: "IDS-STAGE031-P4-GATE"',
            'next_gate: "IDS-STAGE031-REVIEW-GATE"',
            'next_gate: "IDS-STAGE032-P1-GATE"',
            'next_gate: "IDS-STAGE032-P2-GATE"',
            'next_gate: "IDS-STAGE032-REVIEW-GATE"',
            'next_gate: "IDS-STAGE033-P1-GATE"',
            'next_gate: "IDS-STAGE033-P2-GATE"',
            'next_gate: "IDS-STAGE033-P3-GATE"',
            'next_gate: "IDS-STAGE033-P4-GATE"',
            'next_gate: "IDS-STAGE033-REVIEW-GATE"',
            'next_gate: "IDS-STAGE034-P1-GATE"',
            'next_gate: "IDS-STAGE034-P2-GATE"',
            'next_gate: "IDS-STAGE034-P3-GATE"',
            'next_gate: "IDS-STAGE034-P4-GATE"',
            'next_gate: "IDS-STAGE034-REVIEW-GATE"',
            'next_gate: "IDS-STAGE035-P2-GATE"',
        ]
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE031-P1"',
            'current_phase_id: "IDS-STAGE031-P2"',
            'current_phase_id: "IDS-STAGE031-P3"',
            'current_phase_id: "IDS-STAGE031-P4"',
            'current_phase_id: "IDS-STAGE031-REVIEW"',
            'current_phase_id: "IDS-STAGE032-P1"',
            'current_phase_id: "IDS-STAGE032-P4"',
            'current_phase_id: "IDS-STAGE032-REVIEW"',
            'current_phase_id: "IDS-STAGE033-P1"',
            'current_phase_id: "IDS-STAGE033-P2"',
            'current_phase_id: "IDS-STAGE033-P3"',
            'current_phase_id: "IDS-STAGE033-P4"',
            'current_phase_id: "IDS-STAGE033-REVIEW"',
            'current_phase_id: "IDS-STAGE034-P1"',
            'current_phase_id: "IDS-STAGE034-P2"',
            'current_phase_id: "IDS-STAGE034-P3"',
            'current_phase_id: "IDS-STAGE034-P4"',
        ]
        allowed_roadmap_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE031-P1"',
            'current_task_id: "IDS-V0_1-STAGE031-P2"',
            'current_task_id: "IDS-V0_1-STAGE031-P3"',
            'current_task_id: "IDS-V0_1-STAGE031-P4"',
            'current_task_id: "IDS-V0_1-STAGE031-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE032-P1"',
            'current_task_id: "IDS-V0_1-STAGE032-P4"',
            'current_task_id: "IDS-V0_1-STAGE032-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE033-P1"',
            'current_task_id: "IDS-V0_1-STAGE033-P2"',
            'current_task_id: "IDS-V0_1-STAGE033-P3"',
            'current_task_id: "IDS-V0_1-STAGE033-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
            'current_task_id: "IDS-V0_1-STAGE035-P1"',
        ]
        allowed_roadmap_gate_terms = [
            'next_gate_id: "IDS-STAGE031-P2-GATE"',
            'next_gate_id: "IDS-STAGE031-P3-GATE"',
            'next_gate_id: "IDS-STAGE031-P4-GATE"',
            'next_gate_id: "IDS-STAGE031-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE032-P1-GATE"',
            'next_gate_id: "IDS-STAGE032-P2-GATE"',
            'next_gate_id: "IDS-STAGE032-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE033-P1-GATE"',
            'next_gate_id: "IDS-STAGE033-P2-GATE"',
            'next_gate_id: "IDS-STAGE033-P3-GATE"',
            'next_gate_id: "IDS-STAGE033-P4-GATE"',
            'next_gate_id: "IDS-STAGE033-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE034-P1-GATE"',
            'next_gate_id: "IDS-STAGE034-P2-GATE"',
            'next_gate_id: "IDS-STAGE034-P3-GATE"',
            'next_gate_id: "IDS-STAGE034-P4-GATE"',
            'next_gate_id: "IDS-STAGE034-REVIEW-GATE"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE031-P1-20260703-001"',
            '"event_type":"stage_boundary"',
            '"task_id":"IDS-V0_1-STAGE031-P1"',
            '"ACC-STAGE-031"',
            "STAGE031_PHASE1_SCOPE_BOUNDARY.md",
            "Schema migration",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]

        for term in lock_terms:
            with self.subTest(term=term):
                self.assertIn(term, lock_text)
        self.assertTrue(any(term in lock_text for term in allowed_lock_current_terms), allowed_lock_current_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_task_terms), allowed_lock_task_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_acceptance_terms), allowed_lock_acceptance_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_gate_terms), allowed_lock_gate_terms)
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_stage_terms), allowed_roadmap_stage_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_phase_terms), allowed_roadmap_phase_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_task_terms), allowed_roadmap_task_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_gate_terms), allowed_roadmap_gate_terms)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)

    def test_phase2_safety_index_records_dry_run_backup_validation_rollback_and_recovery_guards(self):
        self.assertTrue(SAFETY_INDEX.is_file(), f"missing safety index: {SAFETY_INDEX}")
        index = json.loads(SAFETY_INDEX.read_text(encoding="utf-8"))

        self.assertEqual(index["schema_version"], "ids.stage031.schema_migration_safety.index.v1")
        self.assertEqual(index["stage"], "STAGE-031")
        self.assertEqual(index["task_id"], "IDS-V0_1-STAGE031-P2")
        self.assertEqual(index["acceptance_id"], "ACC-STAGE-031")
        self.assertEqual(index["source_schema_change"]["migration_id"], "ids_stage030_001_control_plane")
        self.assertEqual(index["source_schema_change"]["schema_sql_ref"], "../postgresql_control_plane/001_control_plane_schema.sql")
        self.assertTrue(index["dry_run_guard"]["required"])
        self.assertTrue(index["backup_checkpoint_guard"]["required"])
        self.assertTrue(index["validation_guard"]["required"])
        self.assertTrue(index["rollback_guard"]["required"])
        self.assertTrue(index["recovery_smoke_guard"]["required"])
        self.assertTrue(index["audit_guard"]["required"])
        self.assertFalse(index["owner_stop_gate"]["destructive_auto_approval_allowed"])
        self.assertLessEqual(index["connection_pool_guard"]["max_pool_size"], 10)
        self.assertLessEqual(index["database_size_guard"]["max_control_plane_payload_bytes"], 1048576)
        self.assertIn("NO_RAW_DB_CONTENT", index["storage_quality_guard"]["blocked_payloads"])
        self.assertIn("fake IDS business data", index["storage_quality_guard"]["forbidden"])
        self.assertFalse(index["runtime_policy"]["connect_to_postgres"])
        self.assertFalse(index["runtime_policy"]["execute_migration"])
        self.assertFalse(index["runtime_policy"]["write_runtime_outputs"])
        self.assertEqual(index["raw_metadata_boundary"]["path"], "/Users/linzezhang/Downloads/IDS_MetaData")
        self.assertFalse(index["raw_metadata_boundary"]["content_access_allowed"])

    def test_phase2_script_builds_migration_safety_report_without_runtime_side_effects(self):
        module = self._load_phase2_module()
        self.assertTrue(CONTROL_PLANE_SQL.is_file(), f"missing schema sql: {CONTROL_PLANE_SQL}")
        self.assertTrue(CONTROL_PLANE_INDEX.is_file(), f"missing schema index: {CONTROL_PLANE_INDEX}")
        self.assertTrue(SAFETY_INDEX.is_file(), f"missing safety index: {SAFETY_INDEX}")

        report = module.build_stage031_migration_safety_report(
            SAFETY_INDEX,
            CONTROL_PLANE_SQL,
            CONTROL_PLANE_INDEX,
        )

        self.assertEqual(report["schema_version"], "ids.stage031.schema_migration_safety.phase2.v1")
        self.assertEqual(report["stage"], "STAGE-031")
        self.assertEqual(report["task_id"], "IDS-V0_1-STAGE031-P2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-031")
        self.assertEqual(report["migration_id"], "ids_stage030_001_control_plane")
        self.assertTrue(all(report["safety_gate_results"].values()), report["safety_gate_results"])
        self.assertTrue(all(report["guardrail_results"].values()), report["guardrail_results"])
        self.assertEqual(report["raw_metadata_boundary"]["path"], "/Users/linzezhang/Downloads/IDS_MetaData")
        self.assertTrue(report["raw_metadata_boundary"]["path_only"])
        self.assertTrue(report["raw_metadata_boundary"]["no_raw_content_access"])
        self.assertTrue(report["does_not_connect_to_postgres"])
        self.assertTrue(report["does_not_execute_migration"])
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertTrue(report["does_not_write_runtime_outputs"])
        self.assertTrue(report["does_not_use_fake_ids_business_data"])

    def test_phase2_doc_batch_roadmap_and_event_track_local_no_upload_gate(self):
        self.assertTrue(PHASE2.is_file(), f"missing phase2 evidence: {PHASE2}")
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")

        phase2_text = PHASE2.read_text(encoding="utf-8")
        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        phase2_terms = [
            "ids.stage031.schema_migration_safety.phase2.v1",
            "IDS-V0_1-STAGE031-P2",
            "ACC-STAGE-031",
            "KM_IDSystem/scripts/check_schema_migration_safety.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/schema_migration_safety/stage031_migration_safety_index.json",
            "dry-run",
            "backup checkpoint",
            "validation checklist",
            "rollback guard",
            "recovery smoke",
            "owner stop-gate",
            "不连接 PostgreSQL",
            "不执行 migration dry-run、apply、rollback、backup、restore 或 schema diff",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
            "NO_PHASE3",
        ]
        lock_terms = [
            '      - "Phase 1"',
            '      - "Phase 2"',
            "KM_IDSystem/scripts/check_schema_migration_safety.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/schema_migration_safety/stage031_migration_safety_index.json",
            'push_allowed: false',
        ]
        roadmap_terms = [
            'phase_id: "IDS-STAGE031-P2"',
            'status: "passed_with_local_evidence"',
            "KM_IDSystem/scripts/check_schema_migration_safety.py",
            "stage031_migration_safety_index.json",
            "STAGE031_PHASE2_SCHEMA_MIGRATION_SAFETY_SLICE.md",
        ]
        allowed_roadmap_stage_terms = [
            'current_stage_id: "IDS-STAGE031"',
            'current_stage_id: "IDS-STAGE032"',
            'current_stage_id: "IDS-STAGE033"',
        ]
        allowed_lock_current_terms = [
            'status: "stage031_phase2_in_progress"',
            'status: "stage031_phase3_in_progress"',
            'status: "stage031_completed_local_pending_review"',
            'status: "stage031_completed_reviewed_local"',
            'status: "stage032_phase1_in_progress"',
            'status: "stage032_phase2_in_progress"',
            'status: "stage032_phase3_in_progress"',
            'status: "stage032_completed_local_pending_review"',
            'status: "stage032_completed_reviewed_local"',
            'status: "stage033_phase1_in_progress"',
            'status: "stage033_phase2_in_progress"',
            'status: "stage033_phase3_in_progress"',
            'status: "stage033_completed_local_pending_review"',
            'status: "stage033_completed_reviewed_local"',
            'status: "stage034_phase1_in_progress"',
            'status: "stage034_phase2_in_progress"',
            'status: "stage034_phase3_in_progress"',
            'status: "stage034_completed_local_pending_review"',
            'status: "stage034_completed_reviewed_local"',
            'status: "stage035_phase1_in_progress"',
            'status: "stage035_phase2_in_progress"',
            'status: "stage035_phase3_in_progress"',
            'status: "stage035_completed_local_pending_review"',
        ]
        allowed_lock_next_terms = [
            'next_phase: "Phase 3"',
            'next_phase: "Phase 4"',
            'next_phase: "Phase 4"',
            'next_phase: "stage_review_gate"',
            'next_phase: "Phase 2"',
            'next_stage: "STAGE-032"',
            'next_stage: "STAGE-033"',
        ]
        allowed_lock_gate_terms = [
            'next_gate: "IDS-STAGE031-P3-GATE"',
            'next_gate: "IDS-STAGE031-P4-GATE"',
            'next_gate: "IDS-STAGE031-REVIEW-GATE"',
            'next_gate: "IDS-STAGE032-P1-GATE"',
            'next_gate: "IDS-STAGE032-P2-GATE"',
            'next_gate: "IDS-STAGE032-REVIEW-GATE"',
            'next_gate: "IDS-STAGE033-P1-GATE"',
            'next_gate: "IDS-STAGE033-P2-GATE"',
            'next_gate: "IDS-STAGE033-P3-GATE"',
            'next_gate: "IDS-STAGE033-P4-GATE"',
            'next_gate: "IDS-STAGE033-REVIEW-GATE"',
            'next_gate: "IDS-STAGE034-P1-GATE"',
            'next_gate: "IDS-STAGE034-P2-GATE"',
            'next_gate: "IDS-STAGE034-P3-GATE"',
            'next_gate: "IDS-STAGE034-P4-GATE"',
            'next_gate: "IDS-STAGE034-REVIEW-GATE"',
        ]
        allowed_lock_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE031-P2"',
            'current_task_id: "IDS-V0_1-STAGE031-P3"',
            'current_task_id: "IDS-V0_1-STAGE031-P4"',
            'current_task_id: "IDS-V0_1-STAGE031-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE032-P1"',
            'current_task_id: "IDS-V0_1-STAGE032-P4"',
            'current_task_id: "IDS-V0_1-STAGE032-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE033-P1"',
            'current_task_id: "IDS-V0_1-STAGE033-P2"',
            'current_task_id: "IDS-V0_1-STAGE033-P3"',
            'current_task_id: "IDS-V0_1-STAGE033-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
        ]
        allowed_lock_acceptance_terms = [
            'acceptance_status: "phase2_safety_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_defined"',
            'acceptance_status: "local_passed_pending_stage_review"',
            'acceptance_status: "reviewed_local_passed"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
        ]
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE031-P2"',
            'current_phase_id: "IDS-STAGE031-P3"',
            'current_phase_id: "IDS-STAGE031-P4"',
            'current_phase_id: "IDS-STAGE031-REVIEW"',
            'current_phase_id: "IDS-STAGE032-P1"',
            'current_phase_id: "IDS-STAGE032-P4"',
            'current_phase_id: "IDS-STAGE032-REVIEW"',
            'current_phase_id: "IDS-STAGE033-P1"',
            'current_phase_id: "IDS-STAGE033-P2"',
            'current_phase_id: "IDS-STAGE033-P3"',
            'current_phase_id: "IDS-STAGE033-P4"',
            'current_phase_id: "IDS-STAGE033-REVIEW"',
            'current_phase_id: "IDS-STAGE034-P1"',
            'current_phase_id: "IDS-STAGE034-P2"',
            'current_phase_id: "IDS-STAGE034-P3"',
            'current_phase_id: "IDS-STAGE034-P4"',
        ]
        allowed_roadmap_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE031-P2"',
            'current_task_id: "IDS-V0_1-STAGE031-P3"',
            'current_task_id: "IDS-V0_1-STAGE031-P4"',
            'current_task_id: "IDS-V0_1-STAGE031-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE032-P1"',
            'current_task_id: "IDS-V0_1-STAGE032-P4"',
            'current_task_id: "IDS-V0_1-STAGE032-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE033-P1"',
            'current_task_id: "IDS-V0_1-STAGE033-P2"',
            'current_task_id: "IDS-V0_1-STAGE033-P3"',
            'current_task_id: "IDS-V0_1-STAGE033-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
        ]
        allowed_roadmap_gate_terms = [
            'next_gate_id: "IDS-STAGE031-P3-GATE"',
            'next_gate_id: "IDS-STAGE031-P4-GATE"',
            'next_gate_id: "IDS-STAGE031-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE032-P1-GATE"',
            'next_gate_id: "IDS-STAGE032-P2-GATE"',
            'next_gate_id: "IDS-STAGE032-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE033-P1-GATE"',
            'next_gate_id: "IDS-STAGE033-P2-GATE"',
            'next_gate_id: "IDS-STAGE033-P3-GATE"',
            'next_gate_id: "IDS-STAGE033-P4-GATE"',
            'next_gate_id: "IDS-STAGE033-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE034-P1-GATE"',
            'next_gate_id: "IDS-STAGE034-P2-GATE"',
            'next_gate_id: "IDS-STAGE034-P3-GATE"',
            'next_gate_id: "IDS-STAGE034-P4-GATE"',
            'next_gate_id: "IDS-STAGE034-REVIEW-GATE"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE031-P2-20260703-001"',
            '"event_type":"implementation"',
            '"task_id":"IDS-V0_1-STAGE031-P2"',
            '"ACC-STAGE-031"',
            "check_schema_migration_safety.py",
            "stage031_migration_safety_index.json",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]

        for term in phase2_terms:
            with self.subTest(term=term):
                self.assertIn(term, phase2_text)
        for term in lock_terms:
            with self.subTest(term=term):
                self.assertIn(term, lock_text)
        self.assertTrue(any(term in lock_text for term in allowed_lock_current_terms), allowed_lock_current_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_next_terms), allowed_lock_next_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_gate_terms), allowed_lock_gate_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_task_terms), allowed_lock_task_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_acceptance_terms), allowed_lock_acceptance_terms)
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_stage_terms), allowed_roadmap_stage_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_phase_terms), allowed_roadmap_phase_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_task_terms), allowed_roadmap_task_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_gate_terms), allowed_roadmap_gate_terms)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)

    def test_phase3_scenario_validation_report_covers_migration_failure_recovery_and_constraints(self):
        module = self._load_phase2_module()
        self.assertTrue(CONTROL_PLANE_SQL.is_file(), f"missing schema sql: {CONTROL_PLANE_SQL}")
        self.assertTrue(CONTROL_PLANE_INDEX.is_file(), f"missing schema index: {CONTROL_PLANE_INDEX}")
        self.assertTrue(SAFETY_INDEX.is_file(), f"missing safety index: {SAFETY_INDEX}")

        report = module.build_stage031_scenario_validation_report(
            SAFETY_INDEX,
            CONTROL_PLANE_SQL,
            CONTROL_PLANE_INDEX,
        )

        self.assertEqual(report["schema_version"], "ids.stage031.schema_migration_safety.phase3.v1")
        self.assertEqual(report["stage"], "STAGE-031")
        self.assertEqual(report["task_id"], "IDS-V0_1-STAGE031-P3")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-031")
        self.assertTrue(report["does_not_connect_to_postgres"])
        self.assertTrue(report["does_not_execute_migration"])
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertTrue(report["does_not_write_runtime_outputs"])
        self.assertTrue(report["does_not_use_fake_ids_business_data"])

        scenario_results = report["scenario_results"]
        expected_scenarios = [
            "migration_dry_run",
            "repeat_execution",
            "failure_rollback",
            "backup_restore_checkpoint",
            "recovery_smoke",
            "raw_payload_block",
            "connection_pool_boundary",
            "transaction_boundary",
            "constraint_error_explanations",
        ]
        self.assertEqual(sorted(scenario_results), sorted(expected_scenarios))
        for scenario_id, result in scenario_results.items():
            with self.subTest(scenario_id=scenario_id):
                self.assertEqual(result["status"], "PASS")
                self.assertTrue(result["evidence"])
                self.assertTrue(result["owner_explanation"])

        explanations = scenario_results["constraint_error_explanations"]["explanations"]
        for constraint_id in [
            "chk_payload_size_bytes",
            "chk_connection_pool_size",
            "chk_no_raw_content_stored",
            "chk_fact_level",
            "chk_index_state",
        ]:
            with self.subTest(constraint_id=constraint_id):
                self.assertIn(constraint_id, explanations)

    def test_phase3_doc_batch_roadmap_and_event_track_local_no_upload_gate(self):
        self.assertTrue(PHASE3.is_file(), f"missing phase3 evidence: {PHASE3}")
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")

        phase3_text = PHASE3.read_text(encoding="utf-8")
        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        phase3_terms = [
            "ids.stage031.schema_migration_safety.phase3.v1",
            "IDS-V0_1-STAGE031-P3",
            "ACC-STAGE-031",
            "build_stage031_scenario_validation_report",
            "migration_dry_run",
            "repeat_execution",
            "failure_rollback",
            "backup_restore_checkpoint",
            "recovery_smoke",
            "raw_payload_block",
            "connection_pool_boundary",
            "transaction_boundary",
            "constraint_error_explanations",
            "不连接 PostgreSQL",
            "不执行 live migration dry-run、apply、rollback、backup、restore 或 schema diff",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
            "NO_PHASE4",
        ]
        lock_terms = [
            '      - "Phase 1"',
            '      - "Phase 2"',
            '      - "Phase 3"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_PHASE3_SCENARIO_VALIDATION.md",
            'push_allowed: false',
        ]
        allowed_lock_current_terms = [
            'status: "stage031_phase3_in_progress"',
            'status: "stage031_completed_local_pending_review"',
            'status: "stage031_completed_reviewed_local"',
            'status: "stage032_phase1_in_progress"',
            'status: "stage032_phase2_in_progress"',
            'status: "stage032_phase3_in_progress"',
            'status: "stage032_completed_local_pending_review"',
            'status: "stage032_completed_reviewed_local"',
            'status: "stage033_phase1_in_progress"',
            'status: "stage033_phase2_in_progress"',
            'status: "stage033_phase3_in_progress"',
            'status: "stage033_completed_local_pending_review"',
            'status: "stage033_completed_reviewed_local"',
            'status: "stage034_phase1_in_progress"',
            'status: "stage034_phase2_in_progress"',
            'status: "stage034_phase3_in_progress"',
            'status: "stage034_completed_local_pending_review"',
            'status: "stage034_completed_reviewed_local"',
            'status: "stage035_phase1_in_progress"',
            'status: "stage035_phase2_in_progress"',
            'status: "stage035_phase3_in_progress"',
            'status: "stage035_completed_local_pending_review"',
        ]
        allowed_lock_next_terms = [
            'next_phase: "Phase 4"',
            'next_phase: "stage_review_gate"',
            'next_phase: "Phase 2"',
            'next_stage: "STAGE-032"',
            'next_stage: "STAGE-033"',
        ]
        allowed_lock_gate_terms = [
            'next_gate: "IDS-STAGE031-P4-GATE"',
            'next_gate: "IDS-STAGE031-REVIEW-GATE"',
            'next_gate: "IDS-STAGE032-P1-GATE"',
            'next_gate: "IDS-STAGE032-P2-GATE"',
            'next_gate: "IDS-STAGE032-REVIEW-GATE"',
            'next_gate: "IDS-STAGE033-P1-GATE"',
            'next_gate: "IDS-STAGE033-P2-GATE"',
            'next_gate: "IDS-STAGE033-P3-GATE"',
            'next_gate: "IDS-STAGE033-P4-GATE"',
            'next_gate: "IDS-STAGE033-REVIEW-GATE"',
            'next_gate: "IDS-STAGE034-P1-GATE"',
            'next_gate: "IDS-STAGE034-P2-GATE"',
            'next_gate: "IDS-STAGE034-P3-GATE"',
            'next_gate: "IDS-STAGE034-P4-GATE"',
            'next_gate: "IDS-STAGE034-REVIEW-GATE"',
        ]
        allowed_lock_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE031-P3"',
            'current_task_id: "IDS-V0_1-STAGE031-P4"',
            'current_task_id: "IDS-V0_1-STAGE031-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE032-P1"',
            'current_task_id: "IDS-V0_1-STAGE032-P4"',
            'current_task_id: "IDS-V0_1-STAGE032-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE033-P1"',
            'current_task_id: "IDS-V0_1-STAGE033-P2"',
            'current_task_id: "IDS-V0_1-STAGE033-P3"',
            'current_task_id: "IDS-V0_1-STAGE033-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
        ]
        allowed_lock_acceptance_terms = [
            'acceptance_status: "phase3_scenario_validation_defined"',
            'acceptance_status: "local_passed_pending_stage_review"',
            'acceptance_status: "reviewed_local_passed"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
        ]
        roadmap_terms = [
            'phase_id: "IDS-STAGE031-P3"',
            'status: "passed_with_local_evidence"',
            "STAGE031_PHASE3_SCENARIO_VALIDATION.md",
            "build_stage031_scenario_validation_report",
        ]
        allowed_roadmap_stage_terms = [
            'current_stage_id: "IDS-STAGE031"',
            'current_stage_id: "IDS-STAGE032"',
            'current_stage_id: "IDS-STAGE033"',
        ]
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE031-P3"',
            'current_phase_id: "IDS-STAGE031-P4"',
            'current_phase_id: "IDS-STAGE031-REVIEW"',
            'current_phase_id: "IDS-STAGE032-P1"',
            'current_phase_id: "IDS-STAGE032-P4"',
            'current_phase_id: "IDS-STAGE032-REVIEW"',
            'current_phase_id: "IDS-STAGE033-P1"',
            'current_phase_id: "IDS-STAGE033-P2"',
            'current_phase_id: "IDS-STAGE033-P3"',
            'current_phase_id: "IDS-STAGE033-P4"',
            'current_phase_id: "IDS-STAGE033-REVIEW"',
            'current_phase_id: "IDS-STAGE034-P1"',
            'current_phase_id: "IDS-STAGE034-P2"',
            'current_phase_id: "IDS-STAGE034-P3"',
            'current_phase_id: "IDS-STAGE034-P4"',
        ]
        allowed_roadmap_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE031-P3"',
            'current_task_id: "IDS-V0_1-STAGE031-P4"',
            'current_task_id: "IDS-V0_1-STAGE031-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE032-P1"',
            'current_task_id: "IDS-V0_1-STAGE032-P4"',
            'current_task_id: "IDS-V0_1-STAGE032-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE033-P1"',
            'current_task_id: "IDS-V0_1-STAGE033-P2"',
            'current_task_id: "IDS-V0_1-STAGE033-P3"',
            'current_task_id: "IDS-V0_1-STAGE033-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
        ]
        allowed_roadmap_gate_terms = [
            'next_gate_id: "IDS-STAGE031-P4-GATE"',
            'next_gate_id: "IDS-STAGE031-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE032-P1-GATE"',
            'next_gate_id: "IDS-STAGE032-P2-GATE"',
            'next_gate_id: "IDS-STAGE032-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE033-P1-GATE"',
            'next_gate_id: "IDS-STAGE033-P2-GATE"',
            'next_gate_id: "IDS-STAGE033-P3-GATE"',
            'next_gate_id: "IDS-STAGE033-P4-GATE"',
            'next_gate_id: "IDS-STAGE033-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE034-P1-GATE"',
            'next_gate_id: "IDS-STAGE034-P2-GATE"',
            'next_gate_id: "IDS-STAGE034-P3-GATE"',
            'next_gate_id: "IDS-STAGE034-P4-GATE"',
            'next_gate_id: "IDS-STAGE034-REVIEW-GATE"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE031-P3-20260703-001"',
            '"event_type":"validation"',
            '"task_id":"IDS-V0_1-STAGE031-P3"',
            '"ACC-STAGE-031"',
            "STAGE031_PHASE3_SCENARIO_VALIDATION.md",
            "build_stage031_scenario_validation_report",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]

        for term in phase3_terms:
            with self.subTest(term=term):
                self.assertIn(term, phase3_text)
        for term in lock_terms:
            with self.subTest(term=term):
                self.assertIn(term, lock_text)
        self.assertTrue(any(term in lock_text for term in allowed_lock_current_terms), allowed_lock_current_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_next_terms), allowed_lock_next_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_gate_terms), allowed_lock_gate_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_task_terms), allowed_lock_task_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_acceptance_terms), allowed_lock_acceptance_terms)
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_stage_terms), allowed_roadmap_stage_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_phase_terms), allowed_roadmap_phase_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_task_terms), allowed_roadmap_task_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_gate_terms), allowed_roadmap_gate_terms)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)

    def test_stage_review_artifact_records_findings_repairs_and_no_upload_boundary(self):
        self.assertTrue(STAGE_REVIEW.is_file(), f"missing stage review: {STAGE_REVIEW}")
        review_text = STAGE_REVIEW.read_text(encoding="utf-8")

        required_terms = [
            "IDS-V0_1-STAGE031-REVIEW",
            "ACC-STAGE-031",
            "STAGE-031 · Schema 迁移安全",
            "STAGE031-REVIEW-F1",
            "STAGE031-REVIEW-F2",
            "STAGE031-REVIEW-F3",
            "STAGE031-REVIEW-F5",
            "scripts/lean_governance.py",
            "Python 3.9",
            "P0 source binding",
            "Phase 1 boundary",
            "Phase 2 safety checker",
            "Phase 3 scenario validation",
            "Phase 4 closeout",
            "build_stage031_delivery_report",
            "completed_reviewed_local",
            "IDS-STAGE032-P1-GATE",
            "NO_GITHUB_UPLOAD",
            "NO_APP_REINSTALL",
            "NO_STAGE032_THIS_RUN",
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
            'status: "completed_reviewed_local"',
            '      - "Phase 1"',
            '      - "Phase 2"',
            '      - "Phase 3"',
            '      - "Phase 4"',
            'review_status: "passed"',
            'next_stage: "STAGE-032"',
            'next_gate: "IDS-STAGE032-P1-GATE"',
            'current_task_id: "IDS-V0_1-STAGE031-REVIEW"',
            'acceptance_status: "reviewed_local_passed"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_STAGE_REVIEW.md",
            'push_allowed: false',
        ]
        allowed_acceptance_status_terms = [
            'acceptance_status: "reviewed_local_passed"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
        ]
        roadmap_terms = [
            'review_id: "IDS-STAGE031-REVIEW"',
            'task_id: "IDS-V0_1-STAGE031-REVIEW"',
            'status: "completed"',
            "STAGE031_STAGE_REVIEW.md",
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE031-REVIEW-20260703-001"',
            '"event_id":"EVT-IDS-V0_1-STAGE031-REVIEW-20260703-002"',
            '"event_type":"stage_review"',
            '"task_id":"IDS-V0_1-STAGE031-REVIEW"',
            '"ACC-STAGE-031"',
            "STAGE031_STAGE_REVIEW.md",
            "scripts/lean_governance.py",
            "IDS-STAGE032-P1-GATE",
        ]

        for term in lock_terms:
            with self.subTest(term=term):
                self.assertIn(term, lock_text)
        self.assertTrue(
            any(term in lock_text for term in allowed_acceptance_status_terms),
            allowed_acceptance_status_terms,
        )
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)

    def test_phase4_builds_delivery_evidence_rollback_backup_and_owner_feedback_without_live_database(self):
        module = self._load_phase2_module()

        report = module.build_stage031_delivery_report(
            SAFETY_INDEX,
            CONTROL_PLANE_SQL,
            CONTROL_PLANE_INDEX,
        )

        self.assertEqual(report["schema_version"], "ids.stage031.schema_migration_safety.phase4.v1")
        self.assertEqual(report["stage"], "STAGE-031")
        self.assertEqual(report["phase"], "Phase 4")
        self.assertEqual(report["task_id"], "IDS-V0_1-STAGE031-P4")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-031")
        self.assertEqual(report["next_gate"], "IDS-STAGE031-REVIEW-GATE")
        self.assertEqual(report["stage_review_status"], "pending_next_run")
        self.assertFalse(report["github_upload_allowed"])
        self.assertFalse(report["app_reinstall_allowed"])
        self.assertTrue(report["does_not_connect_to_postgres"])
        self.assertTrue(report["does_not_execute_migration"])
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertTrue(report["does_not_write_runtime_outputs"])
        self.assertTrue(report["does_not_use_fake_ids_business_data"])

        self.assertEqual(report["schema_diff"]["mode"], "static_schema_migration_safety_diff_not_executed")
        self.assertEqual(report["migration_output"]["mode"], "static_migration_safety_output_not_executed")
        self.assertEqual(report["recovery_test_log"]["mode"], "static_recovery_log_not_executed")
        self.assertIn("dry_run_guard", report["schema_diff"]["safety_gates_added"])
        self.assertIn("constraint_error_explanations", report["migration_output"]["scenario_results"])
        self.assertIn("recovery_checkpoint_ref", report["recovery_test_log"]["checks"])
        self.assertTrue(report["destructive_migration_confirmation"]["required"])
        self.assertFalse(report["destructive_migration_confirmation"]["destructive_allowed_by_default"])
        self.assertGreaterEqual(len(report["rollback_backup_steps"]), 5)
        self.assertTrue(any("backup" in step.lower() or "备份" in step for step in report["rollback_backup_steps"]))
        self.assertTrue(any("PostgreSQL" in item for item in report["known_limits"]))
        self.assertIn("STAGE-031 已完成 Phase 4", report["chinese_owner_feedback"])

    def test_phase4_closeout_batch_roadmap_and_events_track_completed_local_no_upload_gate(self):
        self.assertTrue(PHASE4.is_file(), f"missing phase4 closeout: {PHASE4}")
        phase4_text = PHASE4.read_text(encoding="utf-8")
        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        phase4_terms = [
            "IDS-V0_1-STAGE031-P4",
            "ACC-STAGE-031",
            "schema diff",
            "migration 输出",
            "恢复测试日志",
            "已知限制",
            "破坏性迁移",
            "数据库回滚",
            "备份恢复步骤",
            "IDS-STAGE031-REVIEW-GATE",
            "push_allowed=false",
            "STAGE-031 已完成 Phase 4",
            "pending_next_run",
            "不连接 PostgreSQL",
            "不执行真实 migration dry-run、apply、rollback、backup、restore 或 schema diff",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
            "NO_BATCH_UPLOAD",
            "NO_STAGE_REVIEW_THIS_RUN",
        ]
        lock_terms = [
            '      - "Phase 1"',
            '      - "Phase 2"',
            '      - "Phase 3"',
            '      - "Phase 4"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_PHASE4_CLOSEOUT.md",
            'push_allowed: false',
        ]
        roadmap_terms = [
            'phase_id: "IDS-STAGE031-P4"',
            'status: "passed_with_local_evidence"',
            "STAGE031_PHASE4_CLOSEOUT.md",
            "build_stage031_delivery_report",
        ]
        allowed_roadmap_stage_terms = [
            'current_stage_id: "IDS-STAGE031"',
            'current_stage_id: "IDS-STAGE032"',
            'current_stage_id: "IDS-STAGE033"',
        ]
        allowed_lock_current_terms = [
            'status: "stage031_completed_local_pending_review"',
            'status: "stage031_completed_reviewed_local"',
            'status: "stage032_phase1_in_progress"',
            'status: "stage032_phase2_in_progress"',
            'status: "stage032_phase3_in_progress"',
            'status: "stage032_completed_local_pending_review"',
            'status: "stage032_completed_reviewed_local"',
            'status: "stage033_phase1_in_progress"',
            'status: "stage033_phase2_in_progress"',
            'status: "stage033_phase3_in_progress"',
            'status: "stage033_completed_local_pending_review"',
            'status: "stage033_completed_reviewed_local"',
            'status: "stage034_phase1_in_progress"',
            'status: "stage034_phase2_in_progress"',
            'status: "stage034_phase3_in_progress"',
            'status: "stage034_completed_local_pending_review"',
            'status: "stage034_completed_reviewed_local"',
            'status: "stage035_phase1_in_progress"',
            'status: "stage035_phase2_in_progress"',
            'status: "stage035_phase3_in_progress"',
            'status: "stage035_completed_local_pending_review"',
        ]
        allowed_lock_next_terms = [
            'next_phase: "stage_review_gate"',
            'next_phase: "Phase 2"',
            'next_phase: "Phase 3"',
            'next_phase: "Phase 4"',
            'next_stage: "STAGE-032"',
            'next_stage: "STAGE-033"',
        ]
        allowed_lock_gate_terms = [
            'next_gate: "IDS-STAGE031-REVIEW-GATE"',
            'next_gate: "IDS-STAGE032-P1-GATE"',
            'next_gate: "IDS-STAGE032-P2-GATE"',
            'next_gate: "IDS-STAGE032-P3-GATE"',
            'next_gate: "IDS-STAGE032-REVIEW-GATE"',
            'next_gate: "IDS-STAGE033-P1-GATE"',
            'next_gate: "IDS-STAGE033-P2-GATE"',
            'next_gate: "IDS-STAGE033-P3-GATE"',
            'next_gate: "IDS-STAGE033-P4-GATE"',
            'next_gate: "IDS-STAGE033-REVIEW-GATE"',
            'next_gate: "IDS-STAGE034-P1-GATE"',
            'next_gate: "IDS-STAGE034-P2-GATE"',
            'next_gate: "IDS-STAGE034-P3-GATE"',
            'next_gate: "IDS-STAGE034-P4-GATE"',
            'next_gate: "IDS-STAGE034-REVIEW-GATE"',
        ]
        allowed_lock_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE031-P4"',
            'current_task_id: "IDS-V0_1-STAGE031-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE032-P1"',
            'current_task_id: "IDS-V0_1-STAGE032-P2"',
            'current_task_id: "IDS-V0_1-STAGE032-P4"',
            'current_task_id: "IDS-V0_1-STAGE032-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE033-P1"',
            'current_task_id: "IDS-V0_1-STAGE033-P2"',
            'current_task_id: "IDS-V0_1-STAGE033-P3"',
            'current_task_id: "IDS-V0_1-STAGE033-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
        ]
        allowed_lock_acceptance_terms = [
            'acceptance_status: "local_passed_pending_stage_review"',
            'acceptance_status: "reviewed_local_passed"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_retention_table_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "phase2_size_guard_slice_defined"',
            'acceptance_status: "phase3_scenario_validation_passed"',
            'acceptance_status: "phase4_closeout_complete"',
            'acceptance_status: "phase2_connection_pool_slice_defined"',
        ]
        allowed_lock_next_allowed_terms = [
            'next_allowed_task_id: "IDS-V0_1-STAGE031-REVIEW-GATE"',
            'next_allowed_task_id: "IDS-V0_1-STAGE032-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE032-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE032-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE032-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE032-REVIEW"',
            'next_allowed_task_id: "IDS-V0_1-STAGE033-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE033-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE033-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE033-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'next_allowed_task_id: "IDS-V0_1-STAGE034-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE034-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE034-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE034-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE034-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE034-REVIEW"',
            'next_allowed_task_id: "IDS-V0_1-STAGE035-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE035-P2"',
            'next_allowed_task_id: "IDS-V0_1-STAGE035-P3"',
            'next_allowed_task_id: "IDS-V0_1-STAGE035-P4"',
            'next_allowed_task_id: "IDS-V0_1-STAGE035-REVIEW"',
        ]
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE031-P4"',
            'current_phase_id: "IDS-STAGE031-REVIEW"',
            'current_phase_id: "IDS-STAGE032-P1"',
            'current_phase_id: "IDS-STAGE032-P2"',
            'current_phase_id: "IDS-STAGE032-P4"',
            'current_phase_id: "IDS-STAGE032-REVIEW"',
            'current_phase_id: "IDS-STAGE033-P1"',
            'current_phase_id: "IDS-STAGE033-P2"',
            'current_phase_id: "IDS-STAGE033-P3"',
            'current_phase_id: "IDS-STAGE033-P4"',
            'current_phase_id: "IDS-STAGE033-REVIEW"',
            'current_phase_id: "IDS-STAGE034-P1"',
            'current_phase_id: "IDS-STAGE034-P2"',
            'current_phase_id: "IDS-STAGE034-P3"',
            'current_phase_id: "IDS-STAGE034-P4"',
            'current_phase_id: "IDS-STAGE034-REVIEW"',
            'current_phase_id: "IDS-STAGE035-P1"',
            'current_phase_id: "IDS-STAGE035-P2"',
            'current_phase_id: "IDS-STAGE035-P3"',
            'current_phase_id: "IDS-STAGE035-P4"',
        ]
        allowed_roadmap_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE031-P4"',
            'current_task_id: "IDS-V0_1-STAGE031-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE032-P1"',
            'current_task_id: "IDS-V0_1-STAGE032-P2"',
            'current_task_id: "IDS-V0_1-STAGE032-P4"',
            'current_task_id: "IDS-V0_1-STAGE032-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE033-P1"',
            'current_task_id: "IDS-V0_1-STAGE033-P2"',
            'current_task_id: "IDS-V0_1-STAGE033-P3"',
            'current_task_id: "IDS-V0_1-STAGE033-P4"',
            'current_task_id: "IDS-V0_1-STAGE033-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P2"',
            'current_task_id: "IDS-V0_1-STAGE034-P3"',
            'current_task_id: "IDS-V0_1-STAGE034-P4"',
            'current_task_id: "IDS-V0_1-STAGE034-REVIEW"',
            'current_task_id: "IDS-V0_1-STAGE035-P1"',
            'current_task_id: "IDS-V0_1-STAGE035-P2"',
            'current_task_id: "IDS-V0_1-STAGE035-P3"',
            'current_task_id: "IDS-V0_1-STAGE035-P4"',
        ]
        allowed_roadmap_gate_terms = [
            'next_gate_id: "IDS-STAGE031-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE032-P1-GATE"',
            'next_gate_id: "IDS-STAGE032-P2-GATE"',
            'next_gate_id: "IDS-STAGE032-P3-GATE"',
            'next_gate_id: "IDS-STAGE032-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE033-P1-GATE"',
            'next_gate_id: "IDS-STAGE033-P2-GATE"',
            'next_gate_id: "IDS-STAGE033-P3-GATE"',
            'next_gate_id: "IDS-STAGE033-P4-GATE"',
            'next_gate_id: "IDS-STAGE033-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE034-P1-GATE"',
            'next_gate_id: "IDS-STAGE034-P2-GATE"',
            'next_gate_id: "IDS-STAGE034-P3-GATE"',
            'next_gate_id: "IDS-STAGE034-P4-GATE"',
            'next_gate_id: "IDS-STAGE034-REVIEW-GATE"',
            'next_gate_id: "IDS-STAGE035-P1-GATE"',
            'next_gate_id: "IDS-STAGE035-P2-GATE"',
            'next_gate_id: "IDS-STAGE035-P3-GATE"',
            'next_gate_id: "IDS-STAGE035-P4-GATE"',
            'next_gate_id: "IDS-STAGE035-REVIEW-GATE"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE031-P4-20260703-001"',
            '"event_type":"stage_closeout"',
            '"task_id":"IDS-V0_1-STAGE031-P4"',
            '"ACC-STAGE-031"',
            "STAGE031_PHASE4_CLOSEOUT.md",
            "build_stage031_delivery_report",
            "IDS-STAGE031-REVIEW-GATE",
        ]

        for term in phase4_terms:
            with self.subTest(term=term):
                self.assertIn(term, phase4_text)
        for term in lock_terms:
            with self.subTest(term=term):
                self.assertIn(term, lock_text)
        self.assertTrue(any(term in lock_text for term in allowed_lock_current_terms), allowed_lock_current_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_next_terms), allowed_lock_next_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_gate_terms), allowed_lock_gate_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_task_terms), allowed_lock_task_terms)
        self.assertTrue(any(term in lock_text for term in allowed_lock_acceptance_terms), allowed_lock_acceptance_terms)
        self.assertTrue(
            any(term in lock_text for term in allowed_lock_next_allowed_terms),
            allowed_lock_next_allowed_terms,
        )
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_stage_terms), allowed_roadmap_stage_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_phase_terms), allowed_roadmap_phase_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_task_terms), allowed_roadmap_task_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_gate_terms), allowed_roadmap_gate_terms)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


if __name__ == "__main__":
    unittest.main()
