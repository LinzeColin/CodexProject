from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE033_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE033_PHASE1_SCOPE_BOUNDARY.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage033DatabaseSizeGuardPhase1Tests(unittest.TestCase):
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
            "STAGE-033 · 数据库体积护栏",
            "IDS-V0_1-STAGE033-P1",
            "ACC-STAGE-033",
            "D06-S004",
            "D06 · PostgreSQL 控制面",
            "IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-033_数据库体积护栏.md",
            "454efae78a2a493bce9af351384a0d0d634c197f32d0936d8466382d6b67f777",
            "防止 PostgreSQL 无边界存 raw/OCR/大文件派生产物，保护 800GB 内置盘",
            "Phase 1 · 范围、输入输出与边界确认",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_size_guard_inputs_outputs_boundaries_and_recovery(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "database_size_guard_contract_id",
            "control_plane_schema_ref",
            "schema_migration_safety_ref",
            "connection_pool_contract_ref",
            "postgres_storage_scope",
            "raw_content_storage_block",
            "ocr_full_text_storage_block",
            "large_file_storage_block",
            "derived_artifact_limit",
            "database_size_budget",
            "table_size_guard",
            "index_bloat_guard",
            "row_payload_guard",
            "retention_and_cleanup_boundary",
            "audit_evidence_ref",
            "rollback_verification_requirement",
            "DATABASE_SIZE_GUARD_DRAFT",
            "DATABASE_SIZE_GUARD_RAW_CONTENT_BLOCKED",
            "DATABASE_SIZE_GUARD_DERIVED_ARTIFACT_BLOCKED",
            "DATABASE_SIZE_GUARD_READY_FOR_PHASE2_SLICE",
            "只存控制面、状态和热索引",
            "不存 500GB 原始文件",
            "不存 OCR 全文",
            "不存无限制派生产物",
            "保护 800GB 内置盘",
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
            "NO_SIZE_GUARD_RUNTIME",
            "NO_LIVE_MIGRATION",
            "NO_RAW_DB_CONTENT",
            "不创建 PostgreSQL database、schema、migration 文件、连接配置、体积统计 runtime 或清理任务",
            "不连接 PostgreSQL",
            "不执行 migration dry-run、apply、rollback、backup、restore、schema diff、VACUUM、清理或体积统计查询",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不提交 secrets、API key、数据库密码、credential-bearing DSN 或云端凭证",
            "不得使用虚构 IDS 业务数据、虚构数据库行、虚构源文档、placeholder corpus 或伪造证据",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch031_040_lock_roadmap_and_event_track_stage033_phase1_without_upload(self):
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
            "STAGE-033:",
            'status: "stage033_phase1_in_progress"',
            '      - "Phase 1"',
            'next_phase: "Phase 2"',
            'next_gate: "IDS-STAGE033-P2-GATE"',
        ]
        typo_guard_terms = [
            'current_task_id: "IDS-V0_1-STAGE033-P1"',
            'acceptance_id: "ACC-STAGE-033"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE033_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage033_database_size_guard.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE033"',
            'current_phase_id: "IDS-STAGE033-P1"',
            'current_task_id: "IDS-V0_1-STAGE033-P1"',
            'next_gate_id: "IDS-STAGE033-P2-GATE"',
            'stage_id: "IDS-STAGE033"',
            'name: "STAGE-033 · 数据库体积护栏"',
            'phase_id: "IDS-STAGE033-P1"',
            'status: "passed_with_local_evidence"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE033-P1-20260703-001"',
            '"event_type":"stage_boundary"',
            '"task_id":"IDS-V0_1-STAGE033-P1"',
            '"ACC-STAGE-033"',
            "STAGE033_PHASE1_SCOPE_BOUNDARY.md",
            "数据库体积护栏",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]

        self.assertNotIn('current_task_id: "IDS_V0_1-STAGE033-P1"', lock_text)
        for term in lock_terms[0:9]:
            with self.subTest(term=term):
                self.assertIn(term, lock_text)
        for term in typo_guard_terms:
            with self.subTest(term=term):
                self.assertIn(term, lock_text)
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)
