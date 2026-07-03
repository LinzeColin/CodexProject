import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE025_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE025_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE025_PHASE2_SAFE_EXTRACTION_ENGINE_SLICE.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"
SCRIPT = ROOT / "scripts" / "check_safe_extraction_engine.py"
EXTRACTED_AT = "2026-07-03T05:42:18Z"


class Stage025SafeExtractionEnginePhase1Tests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage025_safe_extraction_engine", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _write_zip(self, archive_path, entries):
        with zipfile.ZipFile(archive_path, "w") as archive:
            for entry_path, payload in entries.items():
                archive.writestr(entry_path, payload)

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

    def test_phase2_engine_extracts_safe_zip_entries_marks_risks_and_builds_reingest_plan(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive_path = base / "owner-safe-extraction.zip"
            staging = base / "staging"
            outside = base / "escape.txt"
            self._write_zip(
                archive_path,
                {
                    "safe/manifest-note.md": b"safe",
                    "../escape.txt": b"escape",
                    "/absolute.txt": b"absolute",
                    "too-large.bin": b"0123456789",
                },
            )
            report = module.run_safe_extraction_engine(
                archive_uri=archive_path.as_uri(),
                staging_area_uri=staging.as_uri(),
                extracted_at=EXTRACTED_AT,
                archive_single_file_size_limit_bytes=4,
            )

            safe_target = staging / "safe" / "manifest-note.md"
            self.assertTrue(safe_target.is_file())
            self.assertEqual(safe_target.read_bytes(), b"safe")
            self.assertTrue(archive_path.is_file())
            self.assertFalse(outside.exists())

        self.assertEqual(report["schema_version"], "ids.stage025.safe_extraction_engine.v1")
        self.assertEqual(report["stage"], "STAGE-025")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["task_id"], "IDS-V0_1-STAGE025-P2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-025")
        self.assertEqual(report["safe_extraction_decision_state"], "SAFE_EXTRACTION_OWNER_REVIEW_REQUIRED")
        self.assertEqual(report["safe_extraction_engine_id"], "ids.stage025.safe_extraction_engine")
        self.assertEqual(report["archive_manifest"]["schema_version"], "ids.stage025.archive_manifest.v1")
        self.assertEqual(report["archive_manifest"]["source_schema_version"], "ids.stage024.archive_manifest.v1")
        self.assertEqual(report["safe_extracted_file_count"], 1)
        self.assertGreaterEqual(report["blocked_entry_count"], 3)
        self.assertEqual(report["post_extract_reingest"]["state"], "POST_EXTRACT_REINGEST_REQUIRED")
        self.assertEqual(report["post_extract_reingest"]["required_pipeline"], ["hash", "manifest", "dedup", "parser"])
        self.assertEqual(len(report["post_extract_reingest"]["reingest_queue"]), 1)
        risk_codes = {entry["risk_code"] for entry in report["risk_entries"]}
        self.assertIn("SAFE_EXTRACTION_PATH_TRAVERSAL_BLOCKED", risk_codes)
        self.assertIn("SAFE_EXTRACTION_ABSOLUTE_PATH_BLOCKED", risk_codes)
        self.assertIn("SAFE_EXTRACTION_ENTRY_SIZE_LIMIT_EXCEEDED", risk_codes)
        self.assertTrue(report["original_archive_preserved"])
        self.assertTrue(report["does_not_overwrite_original_archive"])
        self.assertTrue(report["does_not_write_outside_staging"])
        self.assertTrue(report["does_not_write_archive_manifest_runtime_output"])
        for value in report["processing_guard"].values():
            self.assertEqual(value, 0)
        for value in report["no_persistence_deltas"].values():
            self.assertEqual(value, 0)

    def test_phase2_engine_routes_unsupported_formats_missing_sources_and_raw_paths_to_review_or_block(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            staging = base / "staging"
            rar_path = base / "owner-archive.rar"
            seven_z_path = base / "owner-archive.7z"
            rar_path.write_bytes(b"rar structural fixture")
            seven_z_path.write_bytes(b"7z structural fixture")

            rar_report = module.run_safe_extraction_engine(
                archive_uri=rar_path.as_uri(),
                staging_area_uri=staging.as_uri(),
                extracted_at=EXTRACTED_AT,
            )
            seven_z_report = module.run_safe_extraction_engine(
                archive_uri=seven_z_path.as_uri(),
                staging_area_uri=staging.as_uri(),
                extracted_at=EXTRACTED_AT,
            )
            missing_report = module.run_safe_extraction_engine(
                archive_uri=(base / "missing.zip").as_uri(),
                staging_area_uri=staging.as_uri(),
                extracted_at=EXTRACTED_AT,
            )
            raw_report = module.run_safe_extraction_engine(
                archive_uri="/Users/linzezhang/Downloads/IDS_MetaData/raw.zip",
                staging_area_uri=staging.as_uri(),
                extracted_at=EXTRACTED_AT,
            )

        self.assertEqual(rar_report["safe_extraction_decision_state"], "SAFE_EXTRACTION_OWNER_REVIEW_REQUIRED")
        self.assertEqual(seven_z_report["safe_extraction_decision_state"], "SAFE_EXTRACTION_OWNER_REVIEW_REQUIRED")
        self.assertEqual(missing_report["safe_extraction_decision_state"], "SAFE_EXTRACTION_BLOCKED")
        self.assertEqual(raw_report["safe_extraction_decision_state"], "SAFE_EXTRACTION_BLOCKED")
        self.assertIn("SAFE_EXTRACTION_ADAPTER_OWNER_REVIEW_REQUIRED", {entry["risk_code"] for entry in rar_report["risk_entries"]})
        self.assertIn("SAFE_EXTRACTION_ADAPTER_OWNER_REVIEW_REQUIRED", {entry["risk_code"] for entry in seven_z_report["risk_entries"]})
        self.assertIn("SAFE_EXTRACTION_SOURCE_MISSING", {entry["risk_code"] for entry in missing_report["risk_entries"]})
        self.assertIn("SAFE_EXTRACTION_SOURCE_BLOCKED_RAW_METADATA_ROOT", {entry["risk_code"] for entry in raw_report["risk_entries"]})
        self.assertTrue(rar_report["does_not_fake_rar_7z_support"])
        self.assertTrue(seven_z_report["does_not_fake_rar_7z_support"])
        self.assertTrue(raw_report["does_not_read_raw_metadata"])
        self.assertEqual(raw_report["safe_extracted_file_count"], 0)

    def test_phase2_engine_blocks_staging_overwrite_and_cleanup_allowlist_preserves_sources(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive_path = base / "overwrite.zip"
            staging = base / "staging"
            existing = staging / "safe" / "manifest-note.md"
            existing.parent.mkdir(parents=True)
            existing.write_bytes(b"existing")
            self._write_zip(archive_path, {"safe/manifest-note.md": b"new"})
            report = module.run_safe_extraction_engine(
                archive_uri=archive_path.as_uri(),
                staging_area_uri=staging.as_uri(),
                extracted_at=EXTRACTED_AT,
            )
            self.assertEqual(existing.read_bytes(), b"existing")
            archive_uri = archive_path.as_uri()

        self.assertEqual(report["safe_extraction_decision_state"], "SAFE_EXTRACTION_BLOCKED")
        risk_codes = {entry["risk_code"] for entry in report["risk_entries"]}
        self.assertIn("SAFE_EXTRACTION_STAGING_OVERWRITE_BLOCKED", risk_codes)
        self.assertEqual(report["safe_extracted_file_count"], 0)
        self.assertNotIn(archive_uri, [item["uri"] for item in report["cleanup_allowlist"]])
        self.assertTrue(report["cleanup_policy"]["does_not_clean_original_archive"])
        self.assertTrue(report["cleanup_policy"]["does_not_clean_fact_source_or_evidence"])
        self.assertTrue(report["cleanup_policy"]["does_not_clean_manifest_or_audit_outputs"])

    def test_phase2_evidence_document_records_engine_slice_boundaries_and_no_phase3(self):
        self.assertTrue(PHASE2.is_file(), f"missing phase2 evidence: {PHASE2}")
        text = PHASE2.read_text(encoding="utf-8")

        required_terms = [
            "IDS-V0_1-STAGE025-P2",
            "ACC-STAGE-025",
            "ids.stage025.safe_extraction_engine.v1",
            "run_safe_extraction_engine",
            "安全解压",
            "路径过滤",
            "风险标记",
            "重新进入导入管线",
            "人工复核",
            "隔离状态",
            "清理白名单",
            "SAFE_EXTRACTION_PATH_TRAVERSAL_BLOCKED",
            "SAFE_EXTRACTION_ABSOLUTE_PATH_BLOCKED",
            "SAFE_EXTRACTION_ENTRY_SIZE_LIMIT_EXCEEDED",
            "SAFE_EXTRACTION_STAGING_OVERWRITE_BLOCKED",
            "SAFE_EXTRACTION_ADAPTER_OWNER_REVIEW_REQUIRED",
            "SAFE_EXTRACTION_SOURCE_BLOCKED_RAW_METADATA_ROOT",
            "POST_EXTRACT_REINGEST_REQUIRED",
            "hash",
            "manifest",
            "dedup",
            "parser",
            "process-owned temporary structural archive fixtures",
            "不是 IDS corpus、database rows、business evidence、raw metadata 或 committed user data",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_PHASE3",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_batch021_030_lock_tracks_stage025_phase2_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")

        required_terms = [
            'batch_id: "IDS-V0_1-BATCH-021-030"',
            'status: "stage025_phase2_in_progress"',
            "STAGE-025:",
            'status: "in_progress"',
            '      - "Phase 1"',
            '      - "Phase 2"',
            'next_phase: "Phase 3"',
            'next_gate: "IDS-STAGE025-P3-GATE"',
            'current_task_id: "IDS-V0_1-STAGE025-P2"',
            'acceptance_id: "ACC-STAGE-025"',
            'acceptance_status: "phase2_safe_extraction_engine_slice_complete"',
            'push_allowed: false',
            "KM_IDSystem/scripts/check_safe_extraction_engine.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE025_PHASE2_SAFE_EXTRACTION_ENGINE_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage025_safe_extraction_engine.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH021_030_UPLOAD_LOCK.yaml",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/IDS_METADATA_RAW_DATA_BOUNDARY.md",
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
            'STAGE-024:\n    status: "completed_local"',
            "STAGE-025:",
            'status: "in_progress"',
            '      - "Phase 1"',
            'acceptance_id: "ACC-STAGE-025"',
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

        allowed_status_terms = [
            'status: "stage025_phase1_in_progress"',
            'status: "stage025_phase2_in_progress"',
        ]
        self.assertTrue(any(term in text for term in allowed_status_terms), allowed_status_terms)

        allowed_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE025-P1"',
            'current_task_id: "IDS-V0_1-STAGE025-P2"',
        ]
        self.assertTrue(any(term in text for term in allowed_task_terms), allowed_task_terms)

        allowed_acceptance_terms = [
            'acceptance_status: "phase1_scope_boundary_defined"',
            'acceptance_status: "phase2_safe_extraction_engine_slice_complete"',
        ]
        self.assertTrue(any(term in text for term in allowed_acceptance_terms), allowed_acceptance_terms)

        allowed_gate_terms = [
            'next_gate: "IDS-STAGE025-P2-GATE"',
            'next_gate: "IDS-STAGE025-P3-GATE"',
        ]
        self.assertTrue(any(term in text for term in allowed_gate_terms), allowed_gate_terms)


if __name__ == "__main__":
    unittest.main()
