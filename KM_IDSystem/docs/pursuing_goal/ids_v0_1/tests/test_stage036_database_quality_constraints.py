from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE036_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE036_PHASE1_SCOPE_BOUNDARY.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH031_040_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage036DatabaseQualityConstraintsPhase1Tests(unittest.TestCase):
    def test_phase1_contracts_exist_and_bind_taskpack_identity(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing Phase 1 boundary: {PHASE1}")

        combined = "\n".join(
            [ENTRY.read_text(encoding="utf-8"), PHASE1.read_text(encoding="utf-8")]
        )
        required_terms = [
            "STAGE-036 · 数据库质量约束",
            "IDS-V0_1-STAGE036-P1",
            "ACC-STAGE-036",
            "D06-S007",
            "D06 · PostgreSQL 控制面",
            "IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-036_数据库质量约束.md",
            "13037f63e370759fcf0411a062a4b74086fa9ce1ab1410ed443c4ba171450a7b",
            "增加关键唯一性、非空、外键、状态枚举和一致性约束",
            "Phase 1 · 范围、输入输出与边界确认",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_real_schema_inputs_constraint_classes_and_outputs(self):
        self.assertTrue(PHASE1.is_file(), f"missing Phase 1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")
        required_terms = [
            "database_quality_constraint_contract_id",
            "control_plane_schema_ref",
            "control_plane_schema_index_ref",
            "schema_migration_safety_ref",
            "connection_pool_contract_ref",
            "database_size_guard_ref",
            "data_retention_table_ref",
            "database_recovery_smoke_ref",
            "constraint_inventory",
            "PRIMARY_KEY_UNIQUENESS",
            "COMPOSITE_UNIQUENESS",
            "NOT_NULL_REQUIRED",
            "FOREIGN_KEY_INTEGRITY",
            "STATUS_VALUESET_INTEGRITY",
            "CROSS_FIELD_CONSISTENCY",
            "ids_chunks(document_id, chunk_ordinal)",
            "ids_documents.source_id -> ids_metadata_sources.source_id",
            "ids_chunks.document_id -> ids_documents.document_id",
            "ids_jobs.parent_job_id -> ids_jobs.job_id",
            "database_quality_constraint_summary",
            "constraint_inventory_payload",
            "constraint_migration_plan_payload",
            "constraint_validation_payload",
            "constraint_violation_payload",
            "rollback_verification_payload",
            "phase2_ready_contract",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_preserves_stage037_extensibility_and_blocks_live_or_fake_work(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing Phase 1 boundary: {PHASE1}")
        combined = "\n".join(
            [ENTRY.read_text(encoding="utf-8"), PHASE1.read_text(encoding="utf-8")]
        )
        required_terms = [
            "versioned_state_registry",
            "state_namespace",
            "STAGE-037",
            "job_state",
            "parser_state",
            "validation_state",
            "decision_state",
            "DB_QUALITY_STATE_REGISTRY_DEFERRED_TO_STAGE037",
            "DB_QUALITY_DATA_PROFILE_REQUIRED",
            "DB_QUALITY_MIGRATION_SAFETY_REQUIRED",
            "DB_QUALITY_READY_FOR_PHASE2_SLICE",
            "NO_PHASE2",
            "NO_POSTGRES_CONNECTION",
            "NO_SCHEMA_CHANGE",
            "NO_LIVE_MIGRATION",
            "NO_LIVE_CONSTRAINT_VALIDATION",
            "NO_RAW_DB_CONTENT",
            "NO_FAKE_DATA",
            "NO_STAGE037",
            "PostgreSQL 只存控制面、状态和热索引，不存 500GB 原始文件",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据、虚构数据库行、placeholder corpus 或伪造证据",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch_lock_roadmap_and_event_track_stage036_phase1_without_upload(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")

        lock_text = BATCH_LOCK.read_text(encoding="utf-8")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")
        lock_terms = [
            'status: "stage036_phase1_in_progress"',
            'push_allowed: false',
            "STAGE-036:",
            'next_phase: "Phase 2"',
            'next_gate: "IDS-STAGE036-P2-GATE"',
            'current_task_id: "IDS-V0_1-STAGE036-P1"',
            'acceptance_id: "ACC-STAGE-036"',
            'acceptance_status: "phase1_scope_boundary_defined"',
        ]
        roadmap_terms = [
            'current_stage_id: "IDS-STAGE036"',
            'current_phase_id: "IDS-STAGE036-P1"',
            'current_task_id: "IDS-V0_1-STAGE036-P1"',
            'next_gate_id: "IDS-STAGE036-P2-GATE"',
            'stage_id: "IDS-STAGE036"',
            'phase_id: "IDS-STAGE036-P1"',
            'task_id: "IDS-V0_1-STAGE036-P1"',
            'status: "passed_with_local_evidence"',
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE036-P1-20260710-001"',
            '"event_type":"stage_boundary"',
            '"task_id":"IDS-V0_1-STAGE036-P1"',
            '"ACC-STAGE-036"',
            "STAGE036_PHASE1_SCOPE_BOUNDARY.md",
            "数据库质量约束",
        ]

        for terms, text in [
            (lock_terms, lock_text),
            (roadmap_terms, roadmap_text),
            (event_terms, events_text),
        ]:
            for term in terms:
                with self.subTest(term=term):
                    self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
