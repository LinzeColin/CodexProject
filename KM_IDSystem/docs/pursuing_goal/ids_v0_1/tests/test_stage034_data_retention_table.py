from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE034_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE034_PHASE1_SCOPE_BOUNDARY.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage034DataRetentionTablePhase1Tests(unittest.TestCase):
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
            "STAGE-034 · 数据保留表",
            "IDS-V0_1-STAGE034-P1",
            "ACC-STAGE-034",
            "D06-S005",
            "D06 · PostgreSQL 控制面",
            "IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-034_数据保留表.md",
            "af3196bb6ce76bbf22888abbb8c178b3deb0570e6cd2e19235853bac649b818d",
            "定义临时文件、缓存、旧索引、日志、报告快照的保留策略字段",
            "Phase 1 · 范围、输入输出与边界确认",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_retention_inputs_outputs_states_and_recovery(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "data_retention_table_contract_id",
            "control_plane_schema_ref",
            "schema_migration_safety_ref",
            "connection_pool_contract_ref",
            "database_size_guard_ref",
            "retention_subject_class",
            "temp_file_retention_policy",
            "cache_retention_policy",
            "old_index_retention_policy",
            "log_retention_policy",
            "report_snapshot_retention_policy",
            "retention_ttl_policy",
            "owner_hold_policy",
            "cleanup_dry_run_requirement",
            "deletion_stop_gate",
            "audit_evidence_ref",
            "rollback_restore_ref",
            "DATA_RETENTION_TABLE_DRAFT",
            "DATA_RETENTION_TEMP_FILES_POLICY_DEFINED",
            "DATA_RETENTION_CACHES_POLICY_DEFINED",
            "DATA_RETENTION_OLD_INDEXES_POLICY_DEFINED",
            "DATA_RETENTION_LOGS_POLICY_DEFINED",
            "DATA_RETENTION_REPORT_SNAPSHOTS_POLICY_DEFINED",
            "DATA_RETENTION_CLEANUP_OWNER_CONFIRMATION_REQUIRED",
            "DATA_RETENTION_READY_FOR_PHASE2_SLICE",
            "临时文件",
            "缓存",
            "旧索引",
            "日志",
            "报告快照",
            "不执行删除",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_blocks_live_postgres_cleanup_raw_data_secrets_outputs_and_fake_data(self):
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
            "NO_RETENTION_CLEANUP_RUNTIME",
            "NO_LIVE_MIGRATION",
            "NO_RAW_DB_CONTENT",
            "不创建 PostgreSQL database、schema、migration 文件、连接配置、数据保留 runtime 或清理任务",
            "不连接 PostgreSQL",
            "不执行 migration dry-run、apply、rollback、backup、restore、schema diff、清理、删除、retention 或恢复冒烟",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不提交 secrets、API key、数据库密码、credential-bearing DSN 或云端凭证",
            "不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch031_040_lock_roadmap_and_event_track_stage034_phase1_without_upload(self):
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
            "STAGE-034:",
            'status: "stage034_phase1_in_progress"',
            '      - "Phase 1"',
            'next_phase: "Phase 2"',
            'next_gate: "IDS-STAGE034-P2-GATE"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'acceptance_id: "ACC-STAGE-034"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE034_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage034_data_retention_table.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE034"',
            'current_phase_id: "IDS-STAGE034-P1"',
            'current_task_id: "IDS-V0_1-STAGE034-P1"',
            'next_gate_id: "IDS-STAGE034-P2-GATE"',
            'stage_id: "IDS-STAGE034"',
            'name: "STAGE-034 · 数据保留表"',
            'phase_id: "IDS-STAGE034-P1"',
            'task_id: "IDS-V0_1-STAGE034-P1"',
            'status: "passed_with_local_evidence"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE034-P1-20260704-001"',
            '"event_type":"stage_boundary"',
            '"task_id":"IDS-V0_1-STAGE034-P1"',
            '"ACC-STAGE-034"',
            "STAGE034_PHASE1_SCOPE_BOUNDARY.md",
            "数据保留表",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]

        self.assertNotIn('current_task_id: "IDS_V0_1-STAGE034-P1"', lock_text)
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
