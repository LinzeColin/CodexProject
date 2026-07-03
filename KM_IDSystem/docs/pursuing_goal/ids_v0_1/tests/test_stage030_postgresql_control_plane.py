import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE030_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE030_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE030_PHASE2_POSTGRES_CONTROL_PLANE_SLICE.md"
POSTGRES_ROOT = PURSUE_ROOT / "postgresql_control_plane"
SCHEMA_SQL = POSTGRES_ROOT / "001_control_plane_schema.sql"
SCHEMA_INDEX = POSTGRES_ROOT / "control_plane_schema_index.json"
SCRIPT = ROOT / "scripts" / "check_postgresql_control_plane.py"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage030PostgreSQLControlPlaneTests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.is_file(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage030_postgresql_control_plane", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_entry_contract_records_postgresql_control_plane_phase1_boundary(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        text = ENTRY.read_text(encoding="utf-8")

        required_terms = [
            "IDS v0.1 STAGE-030 Entry Contract",
            "STAGE-030 · PostgreSQL 控制面启动",
            "IDS-V0_1-STAGE030-P1",
            "ACC-STAGE-030",
            "D06-S001",
            "D06 · PostgreSQL 控制面",
            "PostgreSQL 控制面",
            "metadata",
            "job",
            "document",
            "chunk",
            "evidence",
            "audit",
            "index version",
            "connection",
            "migration",
            "rollback",
            "recovery",
            "只存控制面、状态和热索引",
            "不存 500GB 原始文件",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "path-only read-only real database source boundary",
            "不得使用虚构 IDS 业务数据",
            "NO_PHASE2",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_scope_boundary_defines_schema_migration_connection_storage_recovery(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "ids.stage030.postgresql_control_plane.phase1.v1",
            "postgres_control_plane_schema_id",
            "metadata_table_contract",
            "job_table_contract",
            "document_table_contract",
            "chunk_table_contract",
            "evidence_table_contract",
            "audit_table_contract",
            "index_version_table_contract",
            "migration_id",
            "migration_dry_run_required",
            "migration_rollback_required",
            "connection_url_ref",
            "connection_pool_boundary",
            "storage_boundary",
            "hot_index_boundary",
            "backup_restore_smoke_ref",
            "POSTGRES_CONTROL_PLANE_DRAFT",
            "POSTGRES_MIGRATION_ROLLBACK_REQUIRED",
            "POSTGRES_RAW_CONTENT_BLOCKED",
            "NO_RAW_DB_CONTENT",
            "NO_PHASE2",
            "不读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不提交 secrets、API key、数据库密码或云端凭证",
            "不得使用虚构 IDS 业务数据",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_batch021_030_lock_retains_phase1_evidence_and_tracks_current_phase2(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")

        required_terms = [
            'status: "stage030_phase2_in_progress"',
            "STAGE-030:",
            '      - "Phase 1"',
            '      - "Phase 2"',
            'next_phase: "Phase 3"',
            'next_gate: "IDS-STAGE030-P3-GATE"',
            'current_task_id: "IDS-V0_1-STAGE030-P2"',
            'acceptance_id: "ACC-STAGE-030"',
            'acceptance_status: "phase2_schema_migration_slice_complete"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/scripts/check_postgresql_control_plane.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/001_control_plane_schema.sql",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/control_plane_schema_index.json",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_PHASE2_POSTGRES_CONTROL_PLANE_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage030_postgresql_control_plane.py",
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P3"',
            'push_allowed: false',
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
            "All IDS runtime corpus, database-backed content, analytics inputs, reports, indexes, manifests, and committed examples must use real user-approved data",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_roadmap_and_events_track_stage030_phase1_local_gate(self):
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        roadmap_terms = [
            'current_stage_id: "IDS-STAGE030"',
            'current_phase_id: "IDS-STAGE030-P2"',
            'current_task_id: "IDS-V0_1-STAGE030-P2"',
            'next_gate_id: "IDS-STAGE030-P3-GATE"',
            'stage_id: "IDS-STAGE030"',
            'name: "STAGE-030 · PostgreSQL 控制面启动"',
            'phase_id: "IDS-STAGE030-P1"',
            'phase_id: "IDS-STAGE030-P2"',
            'status: "passed_with_local_evidence"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/scripts/check_postgresql_control_plane.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/001_control_plane_schema.sql",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/control_plane_schema_index.json",
            "PostgreSQL 只存控制面、状态和热索引，不存 500GB 原始文件",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE030-P1-20260703-001"',
            '"event_type":"stage_boundary"',
            '"task_id":"IDS-V0_1-STAGE030-P1"',
            '"ACC-STAGE-030"',
            "STAGE030_PHASE1_SCOPE_BOUNDARY.md",
            "PostgreSQL control plane",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)

    def test_phase2_builds_schema_migration_connection_and_guard_report_without_runtime_connection(self):
        module = self._load_module()
        self.assertTrue(SCHEMA_SQL.is_file(), f"missing SQL migration: {SCHEMA_SQL}")
        self.assertTrue(SCHEMA_INDEX.is_file(), f"missing schema index: {SCHEMA_INDEX}")

        report = module.build_stage030_control_plane_report(SCHEMA_SQL, SCHEMA_INDEX)

        self.assertEqual(report["schema_version"], "ids.stage030.postgresql_control_plane.phase2.v1")
        self.assertEqual(report["stage"], "STAGE-030")
        self.assertEqual(report["task_id"], "IDS-V0_1-STAGE030-P2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-030")
        self.assertEqual(report["migration_id"], "ids_stage030_001_control_plane")
        self.assertEqual(report["required_tables"], module.REQUIRED_TABLES)
        self.assertTrue(all(report["table_presence"].values()), report["table_presence"])
        self.assertTrue(report["migration_guards"]["has_up"])
        self.assertTrue(report["migration_guards"]["has_down"])
        self.assertTrue(report["migration_guards"]["has_dry_run"])
        self.assertTrue(report["migration_guards"]["has_rollback"])
        self.assertTrue(all(report["connection_pool_guards"].values()), report["connection_pool_guards"])
        self.assertTrue(all(report["storage_quality_guards"].values()), report["storage_quality_guards"])
        self.assertEqual(report["raw_metadata_boundary"]["path"], "/Users/linzezhang/Downloads/IDS_MetaData")
        self.assertTrue(report["raw_metadata_boundary"]["path_only"])
        self.assertTrue(report["raw_metadata_boundary"]["no_raw_content_access"])
        self.assertTrue(report["does_not_connect_to_postgres"])
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertTrue(report["does_not_write_runtime_outputs"])
        self.assertTrue(report["does_not_use_fake_ids_business_data"])

    def test_sql_migration_defines_required_tables_reversible_guards_and_no_raw_payload_columns(self):
        self.assertTrue(SCHEMA_SQL.is_file(), f"missing SQL migration: {SCHEMA_SQL}")
        sql = SCHEMA_SQL.read_text(encoding="utf-8")

        required_terms = [
            "-- migrate:up",
            "-- migrate:down",
            "CREATE TABLE IF NOT EXISTS ids_metadata_sources",
            "CREATE TABLE IF NOT EXISTS ids_jobs",
            "CREATE TABLE IF NOT EXISTS ids_documents",
            "CREATE TABLE IF NOT EXISTS ids_chunks",
            "CREATE TABLE IF NOT EXISTS ids_evidence_records",
            "CREATE TABLE IF NOT EXISTS ids_audit_events",
            "CREATE TABLE IF NOT EXISTS ids_index_versions",
            "CREATE TABLE IF NOT EXISTS ids_schema_migrations",
            "DROP TABLE IF EXISTS ids_schema_migrations",
            "DROP TABLE IF EXISTS ids_metadata_sources",
            "chk_no_raw_content_stored",
            "chk_payload_size_bytes",
            "chk_connection_pool_size",
            "chk_fact_level",
            "chk_index_state",
            "ENV:IDS_POSTGRES_DSN",
            "NO_RAW_DB_CONTENT",
            "/Users/linzezhang/Downloads/IDS_MetaData",
        ]
        forbidden_terms = [
            "raw_file_body",
            "raw_database_dump",
            "document_body",
            "chunk_text",
            "embedding_vector",
            "api_key",
            "password=",
            "postgresql://",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, sql)
        for term in forbidden_terms:
            with self.subTest(term=term):
                self.assertNotIn(term, sql.lower())

    def test_machine_readable_index_records_schema_connection_pool_storage_and_quality_guards(self):
        self.assertTrue(SCHEMA_INDEX.is_file(), f"missing schema index: {SCHEMA_INDEX}")
        index = json.loads(SCHEMA_INDEX.read_text(encoding="utf-8"))

        self.assertEqual(index["schema_version"], "ids.stage030.postgresql_control_plane.index.v1")
        self.assertEqual(index["task_id"], "IDS-V0_1-STAGE030-P2")
        self.assertEqual(index["acceptance_id"], "ACC-STAGE-030")
        self.assertEqual(index["migration"]["id"], "ids_stage030_001_control_plane")
        self.assertEqual(index["migration"]["file"], "001_control_plane_schema.sql")
        self.assertTrue(index["migration"]["dry_run_required"])
        self.assertTrue(index["migration"]["rollback_required"])
        self.assertEqual(index["connection"]["connection_url_ref"], "ENV:IDS_POSTGRES_DSN")
        self.assertTrue(index["connection"]["secrets_forbidden"])
        self.assertLessEqual(index["connection_pool"]["max_pool_size"], 10)
        self.assertLessEqual(index["connection_pool"]["statement_timeout_ms"], 30000)
        self.assertLessEqual(index["database_size_guard"]["max_control_plane_payload_bytes"], 1048576)
        self.assertEqual(index["raw_metadata_boundary"]["path"], "/Users/linzezhang/Downloads/IDS_MetaData")
        self.assertTrue(index["raw_metadata_boundary"]["path_only"])
        self.assertFalse(index["raw_metadata_boundary"]["content_access_allowed"])
        self.assertIn("NO_RAW_DB_CONTENT", index["storage_boundary"]["blocked_payloads"])
        self.assertIn("fake IDS business data", index["quality_guards"]["forbidden"])

    def test_phase2_doc_batch_roadmap_and_events_track_local_no_upload_gate(self):
        self.assertTrue(PHASE2.is_file(), f"missing phase2 evidence: {PHASE2}")
        phase2_text = PHASE2.read_text(encoding="utf-8")
        batch_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        phase2_terms = [
            "IDS-V0_1-STAGE030-P2",
            "ids.stage030.postgresql_control_plane.phase2.v1",
            "001_control_plane_schema.sql",
            "control_plane_schema_index.json",
            "check_postgresql_control_plane.py",
            "metadata、job、document、chunk、evidence、audit、index version",
            "数据库大小",
            "连接池",
            "质量约束",
            "migration dry-run",
            "rollback",
            "不连接 PostgreSQL",
            "不读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
            "NO_PHASE3",
        ]
        batch_terms = [
            'status: "stage030_phase2_in_progress"',
            '      - "Phase 1"',
            '      - "Phase 2"',
            'next_phase: "Phase 3"',
            'next_gate: "IDS-STAGE030-P3-GATE"',
            'current_task_id: "IDS-V0_1-STAGE030-P2"',
            'acceptance_status: "phase2_schema_migration_slice_complete"',
            "KM_IDSystem/scripts/check_postgresql_control_plane.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/001_control_plane_schema.sql",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/postgresql_control_plane/control_plane_schema_index.json",
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P3"',
            'push_allowed: false',
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE030"',
            'current_phase_id: "IDS-STAGE030-P2"',
            'current_task_id: "IDS-V0_1-STAGE030-P2"',
            'next_gate_id: "IDS-STAGE030-P3-GATE"',
            'phase_id: "IDS-STAGE030-P2"',
            'status: "passed_with_local_evidence"',
            "KM_IDSystem/scripts/check_postgresql_control_plane.py",
            "001_control_plane_schema.sql",
            "control_plane_schema_index.json",
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE030-P2-20260703-001"',
            '"event_type":"implementation"',
            '"task_id":"IDS-V0_1-STAGE030-P2"',
            '"ACC-STAGE-030"',
            "check_postgresql_control_plane.py",
            "001_control_plane_schema.sql",
            "control_plane_schema_index.json",
        ]
        for term in phase2_terms:
            with self.subTest(term=term):
                self.assertIn(term, phase2_text)
        for term in batch_terms:
            with self.subTest(term=term):
                self.assertIn(term, batch_text)
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


if __name__ == "__main__":
    unittest.main()
