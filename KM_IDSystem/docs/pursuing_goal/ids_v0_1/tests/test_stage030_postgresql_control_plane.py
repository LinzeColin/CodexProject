from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE030_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE030_PHASE1_SCOPE_BOUNDARY.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage030PostgreSQLControlPlaneTests(unittest.TestCase):
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

    def test_batch021_030_lock_tracks_current_stage030_phase1_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")

        required_terms = [
            'status: "stage030_phase1_in_progress"',
            "STAGE-030:",
            '      - "Phase 1"',
            'next_phase: "Phase 2"',
            'next_gate: "IDS-STAGE030-P2-GATE"',
            'current_task_id: "IDS-V0_1-STAGE030-P1"',
            'acceptance_id: "ACC-STAGE-030"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage030_postgresql_control_plane.py",
            'next_allowed_task_id: "IDS-V0_1-STAGE030-P2"',
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
            'current_phase_id: "IDS-STAGE030-P1"',
            'current_task_id: "IDS-V0_1-STAGE030-P1"',
            'next_gate_id: "IDS-STAGE030-P2-GATE"',
            'stage_id: "IDS-STAGE030"',
            'name: "STAGE-030 · PostgreSQL 控制面启动"',
            'phase_id: "IDS-STAGE030-P1"',
            'status: "passed_with_local_evidence"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE030_PHASE1_SCOPE_BOUNDARY.md",
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


if __name__ == "__main__":
    unittest.main()
