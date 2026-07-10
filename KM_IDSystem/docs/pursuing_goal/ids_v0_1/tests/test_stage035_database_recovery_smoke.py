from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE035_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE035_PHASE1_SCOPE_BOUNDARY.md"
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
            'status: "stage035_phase1_in_progress"',
            'push_allowed: false',
            "STAGE-035:",
            '      - "Phase 1"',
            'next_phase: "Phase 2"',
            'next_gate: "IDS-STAGE035-P2-GATE"',
            'current_task_id: "IDS-V0_1-STAGE035-P1"',
            'acceptance_id: "ACC-STAGE-035"',
            'acceptance_status: "phase1_scope_boundary_defined"',
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
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


if __name__ == "__main__":
    unittest.main()
