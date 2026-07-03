from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE024_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE024_PHASE1_SCOPE_BOUNDARY.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"


class Stage024ArchiveThreatModelPhase1Tests(unittest.TestCase):
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
            "STAGE-024",
            "IDS-V0_1-STAGE024-P1",
            "ACC-STAGE-024",
            "压缩包威胁模型",
            "ZIP",
            "RAR",
            "7Z",
            "TAR",
            "IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-024_压缩包威胁模型.md",
            "add98ee0f7852ed4cd1b1aa9ef1266094ab6cbc26d88696c14f2553e1ef60745",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_archive_security_boundary_staging_limits_manifest_and_reingest_rules(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "archive_security_boundary_id",
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
            "archive_extract_decision_state",
            "ARCHIVE_EXTRACTION_DRAFT",
            "ARCHIVE_EXTRACTION_BLOCKED",
            "ARCHIVE_EXTRACTION_OWNER_REVIEW_REQUIRED",
            "ARCHIVE_EXTRACTION_READY_FOR_SAFE_STAGING",
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

    def test_phase1_preserves_no_extraction_no_overwrite_no_out_of_staging_and_raw_boundaries(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        combined = "\n".join(
            [
                ENTRY.read_text(encoding="utf-8"),
                PHASE1.read_text(encoding="utf-8"),
            ]
        )

        boundary_terms = [
            "不自动解压",
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

    def test_batch021_030_lock_tracks_current_stage024_phase_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")

        allowed_status_terms = [
            'status: "stage023_completed_local_pending_stage024"',
            'status: "stage024_phase1_in_progress"',
        ]
        self.assertTrue(
            any(term in text for term in allowed_status_terms),
            f"batch lock did not contain an allowed STAGE-024 transition status: {allowed_status_terms}",
        )

        allowed_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE023-P4"',
            'current_task_id: "IDS-V0_1-STAGE024-P1"',
        ]
        self.assertTrue(
            any(term in text for term in allowed_task_terms),
            f"batch lock did not contain an allowed STAGE-024 current task: {allowed_task_terms}",
        )

        required_terms = [
            'batch_id: "IDS-V0_1-BATCH-021-030"',
            'STAGE-021:',
            'STAGE-022:',
            'STAGE-023:',
            'STAGE-024:',
            'status: "completed_local"',
            'status: "in_progress"',
            'acceptance_id: "ACC-STAGE-024"',
            'push_allowed: false',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage024_archive_threat_model.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
