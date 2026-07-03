from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE028_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE028_PHASE1_SCOPE_BOUNDARY.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage028ArchiveAdversarialTestsPhase1Tests(unittest.TestCase):
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
            "STAGE-028",
            "IDS-V0_1-STAGE028-P1",
            "ACC-STAGE-028",
            "D05-S005",
            "压缩包对抗测试",
            "IDS 系统运营入口",
            "D05 · 自动解压与压缩包安全",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-028_压缩包对抗测试.md",
            "a3fb4b9bcfe0772fe3860ddfa01f342fc42d05380802d555f21e7c73e6d60d6e",
            "STAGE-024",
            "STAGE-025",
            "STAGE-026",
            "STAGE-027",
            "路径穿越",
            "压缩炸弹",
            "嵌套包",
            "乱码文件名",
            "超大文件数量",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_adversarial_boundary_staging_limits_manifest_reingest_and_cleanup_rules(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "archive_adversarial_test_id",
            "archive_security_boundary_id",
            "archive_source_uri",
            "original_archive_ref",
            "archive_staging_area_uri",
            "archive_file_count_limit",
            "archive_total_size_limit_bytes",
            "archive_single_file_size_limit_bytes",
            "archive_nested_depth_limit",
            "archive_entry_path_policy",
            "adversarial_scenario_id",
            "adversarial_expected_risk_code",
            "adversarial_expected_decision_state",
            "archive_manifest_ref",
            "safe_extraction_ref",
            "cleanup_allowlist_ref",
            "post_extract_reingest_ref",
            "ARCHIVE_ADVERSARIAL_TEST_DRAFT",
            "ARCHIVE_ADVERSARIAL_TEST_BLOCKED",
            "ARCHIVE_ADVERSARIAL_OWNER_REVIEW_REQUIRED",
            "ARCHIVE_ADVERSARIAL_READY_FOR_SAFE_EXTRACTION",
            "ARCHIVE_ADVERSARIAL_MANIFEST_REQUIRED",
            "ARCHIVE_ADVERSARIAL_REINGEST_REQUIRED",
            "ARCHIVE_ADVERSARIAL_CLEANUP_ALLOWLIST_REQUIRED",
            "path_traversal",
            "absolute_path",
            "archive_bomb",
            "nested_archive",
            "garbled_filename",
            "too_many_files",
            "hash",
            "manifest",
            "dedup",
            "parser",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_preserves_no_adversarial_runtime_no_extraction_no_raw_data_boundaries(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        combined = "\n".join(
            [
                ENTRY.read_text(encoding="utf-8"),
                PHASE1.read_text(encoding="utf-8"),
            ]
        )

        boundary_terms = [
            "不执行压缩包对抗测试 runner",
            "不自动解压",
            "不覆盖原始压缩包",
            "不写出指定 staging 区",
            "不移动、删除、覆盖原始文件",
            "不读取真实压缩包内容",
            "不写 archive_adversarial runtime output",
            "不写 archive_manifest runtime output",
            "不创建 staging runtime directory",
            "不启动 hash、manifest、dedup、parser、OCR、Embedding、索引或导入",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
            "NO_PHASE2",
        ]

        for term in boundary_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch021_030_lock_tracks_current_stage028_phase1_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")

        required_terms = [
            'status: "stage028_phase1_in_progress"',
            "STAGE-028:",
            'status: "in_progress"',
            '      - "Phase 1"',
            'next_phase: "Phase 2"',
            'current_task_id: "IDS-V0_1-STAGE028-P1"',
            'acceptance_id: "ACC-STAGE-028"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'next_gate: "IDS-STAGE028-P2-GATE"',
            'push_allowed: false',
            'next_allowed_task_id: "IDS-V0_1-STAGE028-P2"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage028_archive_adversarial_tests.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_roadmap_and_events_track_stage028_phase1_local_gate(self):
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        roadmap_terms = [
            'current_stage_id: "IDS-STAGE028"',
            'current_phase_id: "IDS-STAGE028-P1"',
            'current_task_id: "IDS-V0_1-STAGE028-P1"',
            'next_gate_id: "IDS-STAGE028-P2-GATE"',
            'stage_id: "IDS-STAGE028"',
            'name: "STAGE-028 · 压缩包对抗测试"',
            'phase_id: "IDS-STAGE028-P1"',
            'status: "passed_with_local_evidence"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_PHASE1_SCOPE_BOUNDARY.md",
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE028-P1-20260703-001"',
            '"event_type":"stage_boundary"',
            '"task_id":"IDS-V0_1-STAGE028-P1"',
            '"ACC-STAGE-028"',
            "STAGE028_PHASE1_SCOPE_BOUNDARY.md",
        ]
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


if __name__ == "__main__":
    unittest.main()
