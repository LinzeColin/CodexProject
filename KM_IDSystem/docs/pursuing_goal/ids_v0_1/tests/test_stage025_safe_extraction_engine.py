from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE025_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE025_PHASE1_SCOPE_BOUNDARY.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"


class Stage025SafeExtractionEnginePhase1Tests(unittest.TestCase):
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
            "STAGE-025",
            "IDS-V0_1-STAGE025-P1",
            "ACC-STAGE-025",
            "安全解压引擎",
            "自动解压到 staging 区",
            "路径穿越",
            "绝对路径",
            "覆盖原文件",
            "误执行",
            "IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-025_安全解压引擎.md",
            "ab244ea554dc30616115d6db8baaef53d339b21d53a6d5c51013660ea30e6807",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_engine_boundary_staging_limits_manifest_and_reingest_rules(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "safe_extraction_engine_id",
            "archive_source_uri",
            "original_archive_ref",
            "archive_staging_area_uri",
            "archive_manifest_ref",
            "archive_manifest_schema",
            "archive_file_count_limit",
            "archive_total_size_limit_bytes",
            "archive_single_file_size_limit_bytes",
            "archive_nested_depth_limit",
            "archive_entry_path_policy",
            "safe_extraction_decision_state",
            "SAFE_EXTRACTION_DRAFT",
            "SAFE_EXTRACTION_BLOCKED",
            "SAFE_EXTRACTION_OWNER_REVIEW_REQUIRED",
            "SAFE_EXTRACTION_READY_FOR_STAGING",
            "SAFE_EXTRACTION_READY_FOR_REINGEST",
            "ARCHIVE_MANIFEST_DRAFT",
            "POST_EXTRACT_REINGEST_REQUIRED",
            "hash",
            "manifest",
            "dedup",
            "parser",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_preserves_no_execution_no_overwrite_no_out_of_staging_and_raw_boundaries(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        combined = "\n".join(
            [
                ENTRY.read_text(encoding="utf-8"),
                PHASE1.read_text(encoding="utf-8"),
            ]
        )

        boundary_terms = [
            "不执行解压引擎",
            "不覆盖原始压缩包",
            "不写出指定 staging 区",
            "不移动、删除、覆盖原始文件",
            "不写 archive_manifest runtime output",
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

    def test_batch021_030_lock_tracks_stage025_phase1_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")

        required_terms = [
            'batch_id: "IDS-V0_1-BATCH-021-030"',
            'status: "stage025_phase1_in_progress"',
            'STAGE-024:\n    status: "completed_local"',
            "STAGE-025:",
            'status: "in_progress"',
            '      - "Phase 1"',
            'next_phase: "Phase 2"',
            'next_gate: "IDS-STAGE025-P2-GATE"',
            'current_task_id: "IDS-V0_1-STAGE025-P1"',
            'acceptance_id: "ACC-STAGE-025"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'push_allowed: false',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE025_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE025_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage025_safe_extraction_engine.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_LOCK.yaml",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
