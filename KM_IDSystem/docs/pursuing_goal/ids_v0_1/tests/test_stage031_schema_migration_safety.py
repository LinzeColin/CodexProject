from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE031_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE031_PHASE1_SCOPE_BOUNDARY.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage031SchemaMigrationSafetyPhase1Tests(unittest.TestCase):
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
            'status: "stage031_phase1_in_progress"',
            'stage_range: "STAGE-031..STAGE-040"',
            'acceptance_range: "ACC-STAGE-031..ACC-STAGE-040"',
            'push_allowed: false',
            'current_task_id: "IDS-V0_1-STAGE031-P1"',
            'acceptance_id: "ACC-STAGE-031"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'next_gate: "IDS-STAGE031-P2-GATE"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE031_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage031_schema_migration_safety.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE031"',
            'current_phase_id: "IDS-STAGE031-P1"',
            'current_task_id: "IDS-V0_1-STAGE031-P1"',
            'next_gate_id: "IDS-STAGE031-P2-GATE"',
            'stage_id: "IDS-STAGE031"',
            'name: "STAGE-031 · Schema 迁移安全"',
            'phase_id: "IDS-STAGE031-P1"',
            'status: "passed_with_local_evidence"',
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
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


if __name__ == "__main__":
    unittest.main()
