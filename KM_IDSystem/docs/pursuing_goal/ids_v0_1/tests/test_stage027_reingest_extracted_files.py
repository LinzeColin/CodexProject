from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE027_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE027_PHASE1_SCOPE_BOUNDARY.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage027ReingestExtractedFilesPhase1Tests(unittest.TestCase):
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
            "STAGE-027",
            "IDS-V0_1-STAGE027-P1",
            "ACC-STAGE-027",
            "D05-S004",
            "解压文件重新入库",
            "IDS 系统运营入口",
            "D05 · 自动解压与压缩包安全",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-027_解压文件重新入库.md",
            "STAGE-025",
            "STAGE-026",
            "hash",
            "manifest",
            "dedup",
            "parser",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_reingest_boundary_fields_states_and_pipeline_rules(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "reingest_job_id",
            "reingest_batch_id",
            "extracted_file_ref",
            "extracted_file_uri",
            "archive_manifest_ref",
            "original_archive_ref",
            "safe_extraction_ref",
            "reingest_source_state",
            "reingest_idempotency_key",
            "reingest_duplicate_policy",
            "reingest_owner_decision_state",
            "REINGEST_DRAFT",
            "REINGEST_BLOCKED",
            "REINGEST_OWNER_REVIEW_REQUIRED",
            "REINGEST_READY_FOR_HASH",
            "REINGEST_READY_FOR_MANIFEST",
            "REINGEST_READY_FOR_DEDUP",
            "REINGEST_READY_FOR_PARSER",
            "REINGEST_READY_FOR_IMPORT_QUEUE",
            "hash",
            "manifest",
            "dedup",
            "parser",
            "STAGE-016",
            "STAGE-018",
            "STAGE-021",
            "STAGE-022",
            "STAGE-023",
            "STAGE-025",
            "STAGE-026",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_preserves_no_runtime_ingest_no_raw_data_and_original_archive_boundaries(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        combined = "\n".join(
            [
                ENTRY.read_text(encoding="utf-8"),
                PHASE1.read_text(encoding="utf-8"),
            ]
        )

        boundary_terms = [
            "不执行重新入库",
            "不读取真实 extracted file 内容",
            "不打开、hash 或复制真实 extracted file",
            "不写 reingest runtime output",
            "不创建 document/chunk/job/index/import row",
            "不启动 hash、manifest、dedup、parser、OCR、Embedding、索引或导入",
            "不覆盖、移动、删除、清理原始压缩包或事实源",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
            "NO_PHASE2",
        ]

        for term in boundary_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch021_030_lock_tracks_current_stage027_phase1_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")

        required_terms = [
            'batch_id: "IDS-V0_1-BATCH-021-030"',
            'status: "stage027_phase1_in_progress"',
            "STAGE-026:",
            'status: "completed_local"',
            'current_task_id: "IDS-V0_1-STAGE026-P4"',
            "STAGE-027:",
            'status: "in_progress"',
            '      - "Phase 1"',
            'next_phase: "Phase 2"',
            'current_task_id: "IDS-V0_1-STAGE027-P1"',
            'acceptance_id: "ACC-STAGE-027"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'next_gate: "IDS-STAGE027-P2-GATE"',
            'push_allowed: false',
            'next_allowed_task_id: "IDS-V0_1-STAGE027-P2"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage027_reingest_extracted_files.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_roadmap_and_events_track_stage027_phase1_local_gate(self):
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        roadmap_terms = [
            'current_stage_id: "IDS-STAGE027"',
            'current_phase_id: "IDS-STAGE027-P1"',
            'current_task_id: "IDS-V0_1-STAGE027-P1"',
            'next_gate_id: "IDS-STAGE027-P2-GATE"',
            'stage_id: "IDS-STAGE027"',
            'name: "STAGE-027 · 解压文件重新入库"',
            'phase_id: "IDS-STAGE027-P1"',
            'status: "passed_with_local_evidence"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE027_PHASE1_SCOPE_BOUNDARY.md",
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE027-P1-20260703-001"',
            '"event_type":"stage_boundary"',
            '"task_id":"IDS-V0_1-STAGE027-P1"',
            '"ACC-STAGE-027"',
            "STAGE027_PHASE1_SCOPE_BOUNDARY.md",
        ]

        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


if __name__ == "__main__":
    unittest.main()
