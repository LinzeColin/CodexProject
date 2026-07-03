from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE029_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE029_PHASE1_SCOPE_BOUNDARY.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"


class Stage029ArchiveCleanupAllowlistPhase1Tests(unittest.TestCase):
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
            "STAGE-029",
            "IDS-V0_1-STAGE029-P1",
            "ACC-STAGE-029",
            "D05-S006",
            "压缩包清理白名单",
            "IDS 系统运营入口",
            "D05 · 自动解压与压缩包安全",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-029_压缩包清理白名单.md",
            "b17be7330d9a4ce1f5a9ead4c0620d733693ccd10d6eeff7c8a1298c11889ac2",
            "STAGE-024",
            "STAGE-025",
            "STAGE-026",
            "STAGE-027",
            "STAGE-028",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_cleanup_allowlist_boundary_staging_limits_manifest_and_reingest_rules(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "archive_cleanup_allowlist_id",
            "archive_security_boundary_id",
            "cleanup_request_ref",
            "archive_source_uri",
            "original_archive_ref",
            "archive_staging_area_uri",
            "archive_manifest_ref",
            "safe_extraction_ref",
            "post_extract_reingest_ref",
            "cleanup_candidate_uri",
            "cleanup_candidate_class",
            "cleanup_allowlist_ref",
            "cleanup_decision_state",
            "cleanup_reason_code",
            "cleanup_protected_ref",
            "archive_file_count_limit",
            "archive_total_size_limit_bytes",
            "archive_single_file_size_limit_bytes",
            "archive_nested_depth_limit",
            "ARCHIVE_CLEANUP_ALLOWLIST_DRAFT",
            "ARCHIVE_CLEANUP_BLOCKED_PROTECTED_REF",
            "ARCHIVE_CLEANUP_OWNER_REVIEW_REQUIRED",
            "ARCHIVE_CLEANUP_READY_FOR_TEMP_CLEANUP",
            "ARCHIVE_STAGING_TEMP_FILE",
            "PROTECTED_ORIGINAL_ARCHIVE",
            "PROTECTED_ARCHIVE_MANIFEST",
            "PROTECTED_EVIDENCE_LEDGER",
            "PROTECTED_AUDIT_LOG",
            "PROTECTED_DELIVERED_REPORT",
            "hash",
            "manifest",
            "dedup",
            "parser",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_preserves_no_cleanup_no_delete_no_runtime_and_raw_data_boundaries(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        combined = "\n".join(
            [
                ENTRY.read_text(encoding="utf-8"),
                PHASE1.read_text(encoding="utf-8"),
            ]
        )

        boundary_terms = [
            "不执行 cleanup runner",
            "不自动清理",
            "不删除原始资料",
            "不删除原始压缩包",
            "不删除 manifest",
            "不删除 evidence",
            "不删除 audit",
            "不删除报告",
            "不覆盖原始压缩包",
            "不写出指定 staging 区",
            "不读取真实压缩包内容",
            "不写 archive_cleanup runtime output",
            "不写 archive_manifest runtime output",
            "不启动 hash、manifest、dedup、parser、OCR、Embedding、索引或导入",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
            "NO_PHASE2",
        ]

        for term in boundary_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch021_030_lock_tracks_current_stage029_phase1_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")

        required_terms = [
            'status: "stage029_phase1_in_progress"',
            "STAGE-028:",
            "STAGE-029:",
            'status: "in_progress"',
            '      - "Phase 1"',
            'next_phase: "Phase 2"',
            'current_task_id: "IDS-V0_1-STAGE029-P1"',
            'acceptance_id: "ACC-STAGE-029"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'next_gate: "IDS-STAGE029-P2-GATE"',
            'push_allowed: false',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P2"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage029_archive_cleanup_allowlist.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_roadmap_and_events_track_stage029_phase1_local_gate(self):
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        roadmap_terms = [
            'current_stage_id: "IDS-STAGE029"',
            'current_phase_id: "IDS-STAGE029-P1"',
            'current_task_id: "IDS-V0_1-STAGE029-P1"',
            'next_gate_id: "IDS-STAGE029-P2-GATE"',
            'stage_id: "IDS-STAGE029"',
            'name: "STAGE-029 · 压缩包清理白名单"',
            'phase_id: "IDS-STAGE029-P1"',
            'status: "passed_with_local_evidence"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE029_PHASE1_SCOPE_BOUNDARY.md",
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE029-P1-20260703-001"',
            '"event_type":"stage_boundary"',
            '"task_id":"IDS-V0_1-STAGE029-P1"',
            '"ACC-STAGE-029"',
            "STAGE029_PHASE1_SCOPE_BOUNDARY.md",
        ]

        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


if __name__ == "__main__":
    unittest.main()
