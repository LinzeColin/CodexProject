from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE032_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE032_PHASE1_SCOPE_BOUNDARY.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage032DatabaseConnectionPoolPhase1Tests(unittest.TestCase):
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
            "STAGE-032 · 数据库连接与连接池基线",
            "IDS-V0_1-STAGE032-P1",
            "ACC-STAGE-032",
            "D06-S003",
            "D06 · PostgreSQL 控制面",
            "IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-032_数据库连接与连接池基线.md",
            "a780cbf5eaf4b565dc0f0e7da1c503275bfa4e066d3409f8a258f13f09a0035a",
            "建立后端、worker、报告任务、检索任务的数据库连接策略",
            "Phase 1 · 范围、输入输出与边界确认",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_connection_pool_inputs_outputs_boundaries_and_recovery(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "database_connection_pool_contract_id",
            "backend_connection_profile",
            "worker_connection_profile",
            "report_task_connection_profile",
            "retrieval_task_connection_profile",
            "connection_url_ref",
            "credential_source_policy",
            "pool_size_boundary",
            "statement_timeout_boundary",
            "transaction_boundary",
            "retry_backoff_boundary",
            "healthcheck_boundary",
            "schema_migration_dependency_ref",
            "control_plane_storage_boundary",
            "hot_index_storage_boundary",
            "backup_restore_requirement",
            "CONNECTION_POOL_DRAFT",
            "CONNECTION_POOL_SECRETS_BLOCKED",
            "CONNECTION_POOL_RAW_CONTENT_BLOCKED",
            "CONNECTION_POOL_READY_FOR_PHASE2_SLICE",
            "只存控制面、状态和热索引",
            "不存 500GB 原始文件",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_blocks_live_postgres_raw_data_secrets_runtime_outputs_and_fake_data(self):
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
            "NO_CONNECTION_POOL_RUNTIME",
            "NO_LIVE_MIGRATION",
            "NO_RAW_DB_CONTENT",
            "不创建 PostgreSQL database、schema、migration 文件、连接配置或连接池 runtime",
            "不连接 PostgreSQL",
            "不执行 migration dry-run、apply、rollback、backup、restore 或 schema diff",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不提交 secrets、API key、数据库密码、credential-bearing DSN 或云端凭证",
            "不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch031_040_lock_roadmap_and_event_track_stage032_phase1_without_upload(self):
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
            "STAGE-032:",
            'status: "stage032_phase1_in_progress"',
            '      - "Phase 1"',
            'next_phase: "Phase 2"',
            'next_gate: "IDS-STAGE032-P2-GATE"',
            'current_task_id: "IDS-V0_1-STAGE032-P1"',
            'acceptance_id: "ACC-STAGE-032"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE032_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage032_database_connection_pool.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE032"',
            'current_phase_id: "IDS-STAGE032-P1"',
            'current_task_id: "IDS-V0_1-STAGE032-P1"',
            'next_gate_id: "IDS-STAGE032-P2-GATE"',
            'stage_id: "IDS-STAGE032"',
            'name: "STAGE-032 · 数据库连接与连接池基线"',
            'phase_id: "IDS-STAGE032-P1"',
            'status: "passed_with_local_evidence"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE032-P1-20260703-001"',
            '"event_type":"stage_boundary"',
            '"task_id":"IDS-V0_1-STAGE032-P1"',
            '"ACC-STAGE-032"',
            "STAGE032_PHASE1_SCOPE_BOUNDARY.md",
            "数据库连接与连接池基线",
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
