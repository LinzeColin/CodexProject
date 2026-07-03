from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE026_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE026_PHASE1_SCOPE_BOUNDARY.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage026ArchiveManifestPhase1Tests(unittest.TestCase):
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
            "STAGE-026",
            "IDS-V0_1-STAGE026-P1",
            "ACC-STAGE-026",
            "压缩包 Manifest",
            "压缩包 hash",
            "解压文件列表",
            "解压体积",
            "嵌套层级",
            "失败项",
            "风险项",
            "IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-026_压缩包Manifest.md",
            "71f966c9a669563073a502e3beef5bc85a50d9cdb077b996687653ca48c3da70",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_archive_manifest_boundary_staging_limits_and_reingest_rules(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "archive_manifest_id",
            "archive_manifest_schema",
            "archive_source_uri",
            "original_archive_ref",
            "archive_staging_area_uri",
            "archive_hash_sha256",
            "archive_type",
            "archive_entry_manifest",
            "archive_entry_path_policy",
            "archive_file_count_limit",
            "archive_total_size_limit_bytes",
            "archive_single_file_size_limit_bytes",
            "archive_nested_depth_limit",
            "archive_failed_items",
            "archive_risk_items",
            "archive_manifest_decision_state",
            "ARCHIVE_MANIFEST_DRAFT",
            "ARCHIVE_MANIFEST_BLOCKED",
            "ARCHIVE_MANIFEST_OWNER_REVIEW_REQUIRED",
            "ARCHIVE_MANIFEST_READY_FOR_SAFE_EXTRACTION",
            "POST_EXTRACT_REINGEST_REQUIRED",
            "hash",
            "manifest",
            "dedup",
            "parser",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_preserves_no_extraction_no_runtime_manifest_and_raw_data_boundaries(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        combined = "\n".join(
            [
                ENTRY.read_text(encoding="utf-8"),
                PHASE1.read_text(encoding="utf-8"),
            ]
        )

        boundary_terms = [
            "不执行解压",
            "不覆盖原始压缩包",
            "不写出指定 staging 区",
            "不读取真实压缩包内容",
            "不写 archive_manifest runtime output",
            "不创建 staging runtime directory",
            "不启动 hash、manifest、dedup、parser、OCR、Embedding、索引或导入",
            "不生成 runtime 输出",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
            "NO_PHASE2",
        ]

        for term in boundary_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch021_030_lock_tracks_current_stage026_phase1_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")

        required_terms = [
            'batch_id: "IDS-V0_1-BATCH-021-030"',
            'status: "stage026_phase1_in_progress"',
            "STAGE-021:",
            "STAGE-022:",
            "STAGE-023:",
            "STAGE-024:",
            "STAGE-025:",
            "STAGE-026:",
            'status: "in_progress"',
            'completed_phases:',
            '      - "Phase 1"',
            'next_phase: "Phase 2"',
            'current_task_id: "IDS-V0_1-STAGE026-P1"',
            'acceptance_id: "ACC-STAGE-026"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'next_gate: "IDS-STAGE026-P2-GATE"',
            'next_allowed_task_id: "IDS-V0_1-STAGE026-P2"',
            'push_allowed: false',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage026_archive_manifest.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_roadmap_and_events_track_stage026_phase1_local_gate(self):
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        roadmap_terms = [
            'current_stage_id: "IDS-STAGE026"',
            'current_phase_id: "IDS-STAGE026-P1"',
            'current_task_id: "IDS-V0_1-STAGE026-P1"',
            'next_gate_id: "IDS-STAGE026-P2-GATE"',
            'stage_id: "IDS-STAGE026"',
            'name: "STAGE-026 · 压缩包 Manifest"',
            'phase_id: "IDS-STAGE026-P1"',
            'status: "passed_with_local_evidence"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE026_PHASE1_SCOPE_BOUNDARY.md",
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE026-P1-20260703-001"',
            '"event_type":"stage_boundary"',
            '"task_id":"IDS-V0_1-STAGE026-P1"',
            '"ACC-STAGE-026"',
            "STAGE026_PHASE1_SCOPE_BOUNDARY.md",
        ]

        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


if __name__ == "__main__":
    unittest.main()
