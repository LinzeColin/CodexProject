import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE024_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE024_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE024_PHASE2_SAFE_EXTRACTION_SLICE.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"
SCRIPT = ROOT / "scripts" / "check_archive_threat_model.py"
EXTRACTED_AT = "2026-07-03T03:12:44Z"


class Stage024ArchiveThreatModelPhase1Tests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage024_archive_threat_model", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

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
            'status: "stage024_phase2_in_progress"',
        ]
        self.assertTrue(
            any(term in text for term in allowed_status_terms),
            f"batch lock did not contain an allowed STAGE-024 transition status: {allowed_status_terms}",
        )

        allowed_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE023-P4"',
            'current_task_id: "IDS-V0_1-STAGE024-P1"',
            'current_task_id: "IDS-V0_1-STAGE024-P2"',
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
            'acceptance_status: "phase2_safe_extraction_slice_complete"',
            'next_gate: "IDS-STAGE024-P3-GATE"',
            'push_allowed: false',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_PHASE2_SAFE_EXTRACTION_SLICE.md",
            "KM_IDSystem/scripts/check_archive_threat_model.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage024_archive_threat_model.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase2_safe_zip_extraction_filters_paths_marks_risks_and_builds_reingest_plan(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive_path = base / "owner-archive.zip"
            staging = base / "staging"
            staging.mkdir()
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("safe/manifest-note.md", b"safe")
                archive.writestr("../escape.txt", b"escape")
                archive.writestr("/absolute.txt", b"absolute")
                archive.writestr("too-large.bin", b"0123456789")

            report = module.safe_extract_archive(
                archive_uri=archive_path.as_uri(),
                staging_area_uri=staging.as_uri(),
                extracted_at=EXTRACTED_AT,
                archive_file_count_limit=10,
                archive_total_size_limit_bytes=1000,
                archive_single_file_size_limit_bytes=4,
                archive_nested_depth_limit=1,
            )

            safe_output = staging / "safe" / "manifest-note.md"
            outside_escape = base / "escape.txt"
            safe_output_exists = safe_output.exists()
            outside_escape_exists = outside_escape.exists()
            safe_output_uri = safe_output.resolve(strict=False).as_uri()
            archive_uri = archive_path.as_uri()

        serialized = json.dumps(report, ensure_ascii=False)
        self.assertEqual(report["schema_version"], "ids.stage024.archive_threat_model.v1")
        self.assertEqual(report["stage"], "STAGE-024")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["task_id"], "IDS-V0_1-STAGE024-P2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-024")
        self.assertEqual(report["archive_type"], "ZIP")
        self.assertEqual(report["extraction_state"], "ARCHIVE_EXTRACTION_OWNER_REVIEW_REQUIRED")
        self.assertTrue(report["original_archive_preserved"])
        self.assertTrue(report["does_not_overwrite_original_archive"])
        self.assertTrue(report["does_not_write_outside_staging"])
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertEqual(report["safe_extracted_file_count"], 1)
        self.assertEqual(report["blocked_entry_count"], 3)
        self.assertGreaterEqual(report["quarantine_entry_count"], 3)
        self.assertTrue(safe_output_exists)
        self.assertFalse(outside_escape_exists)
        risk_codes = {item["risk_code"] for item in report["risk_entries"]}
        self.assertIn("ARCHIVE_PATH_TRAVERSAL_BLOCKED", risk_codes)
        self.assertIn("ARCHIVE_ABSOLUTE_PATH_BLOCKED", risk_codes)
        self.assertIn("ARCHIVE_ENTRY_SIZE_LIMIT_EXCEEDED", risk_codes)
        self.assertEqual(report["post_extract_reingest"]["required_pipeline"], ["hash", "manifest", "dedup", "parser"])
        self.assertEqual(len(report["post_extract_reingest"]["reingest_queue"]), 1)
        self.assertIn("POST_EXTRACT_REINGEST_REQUIRED", report["post_extract_reingest"]["state"])
        self.assertEqual(report["processing_guard"]["actual_hash_jobs_started"], 0)
        self.assertEqual(report["processing_guard"]["actual_manifest_jobs_started"], 0)
        self.assertEqual(report["processing_guard"]["actual_dedup_jobs_started"], 0)
        self.assertEqual(report["processing_guard"]["actual_parser_jobs_started"], 0)
        cleanup_uris = {item["uri"] for item in report["cleanup_allowlist"]}
        self.assertIn(safe_output_uri, cleanup_uris)
        self.assertNotIn(archive_uri, cleanup_uris)
        self.assertTrue(report["cleanup_policy"]["does_not_clean_original_archive"])
        self.assertTrue(report["cleanup_policy"]["does_not_clean_fact_source_or_evidence"])
        self.assertNotIn("# IDS v0.1 STAGE-024 Entry Contract", serialized)

    def test_phase2_tar_safe_extraction_uses_same_manifest_and_reingest_contract(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive_path = base / "owner-archive.tar"
            staging = base / "staging"
            staging.mkdir()
            payload = b"tar-safe"
            with tarfile.open(archive_path, "w") as archive:
                info = tarfile.TarInfo("safe/tar-note.txt")
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))

            report = module.safe_extract_archive(
                archive_uri=archive_path.as_uri(),
                staging_area_uri=staging.as_uri(),
                extracted_at=EXTRACTED_AT,
            )
            safe_output = staging / "safe" / "tar-note.txt"
            safe_output_exists = safe_output.exists()

        self.assertEqual(report["archive_type"], "TAR")
        self.assertEqual(report["extraction_state"], "ARCHIVE_EXTRACTION_READY_FOR_REINGEST")
        self.assertEqual(report["safe_extracted_file_count"], 1)
        self.assertEqual(report["blocked_entry_count"], 0)
        self.assertTrue(safe_output_exists)
        self.assertEqual(report["archive_manifest"]["entry_count"], 1)
        self.assertEqual(report["post_extract_reingest"]["reingest_queue"][0]["pipeline_stage_states"]["hash"], "POST_EXTRACT_HASH_REQUIRED")
        self.assertTrue(report["does_not_write_archive_manifest_runtime_output"])

    def test_phase2_rar_and_7z_are_owner_review_without_fake_extraction_support(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            staging = base / "staging"
            staging.mkdir()
            reports = []
            for suffix in [".rar", ".7z"]:
                archive_path = base / f"owner-archive{suffix}"
                archive_path.write_bytes(b"structural archive adapter placeholder")
                reports.append(
                    module.safe_extract_archive(
                        archive_uri=archive_path.as_uri(),
                        staging_area_uri=staging.as_uri(),
                        extracted_at=EXTRACTED_AT,
                    )
                )

        for report in reports:
            self.assertIn(report["archive_type"], {"RAR", "7Z"})
            self.assertEqual(report["extraction_state"], "ARCHIVE_EXTRACTION_OWNER_REVIEW_REQUIRED")
            self.assertEqual(report["safe_extracted_file_count"], 0)
            self.assertEqual(report["blocked_entry_count"], 1)
            self.assertIn("ARCHIVE_FORMAT_REQUIRES_EXTERNAL_ADAPTER", {item["risk_code"] for item in report["risk_entries"]})
            self.assertTrue(report["does_not_fake_rar_7z_support"])
            self.assertTrue(report["does_not_write_archive_manifest_runtime_output"])

    def test_phase2_blocks_ids_metadata_path_before_file_access_and_reports_no_side_effects(self):
        module = self._load_module()
        report = module.safe_extract_archive(
            archive_uri="file:///Users/linzezhang/Downloads/IDS_MetaData/raw-source.zip",
            staging_area_uri="file:///tmp/ids-stage024-test-staging",
            extracted_at=EXTRACTED_AT,
        )

        self.assertEqual(report["extraction_state"], "ARCHIVE_EXTRACTION_BLOCKED")
        self.assertEqual(report["safe_extracted_file_count"], 0)
        self.assertEqual(report["blocked_entry_count"], 1)
        self.assertIn("ARCHIVE_SOURCE_BLOCKED_RAW_METADATA_ROOT", {item["risk_code"] for item in report["risk_entries"]})
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertEqual(report["no_persistence_deltas"]["database_write_delta"], 0)
        self.assertEqual(report["no_persistence_deltas"]["manifest_write_delta"], 0)

    def test_phase2_cli_returns_json_payload_without_runtime_manifest_or_database_writes(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive_path = base / "owner-cli.zip"
            staging = base / "staging"
            staging.mkdir()
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("safe/cli-note.md", b"cli-safe")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--archive-uri",
                    archive_path.as_uri(),
                    "--staging-area-uri",
                    staging.as_uri(),
                    "--extracted-at",
                    EXTRACTED_AT,
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        report = json.loads(result.stdout)
        self.assertEqual(report["stage"], "STAGE-024")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["safe_extracted_file_count"], 1)
        self.assertEqual(report["archive_manifest"]["schema_version"], "ids.stage024.archive_manifest.v1")
        self.assertEqual(report["no_persistence_deltas"]["manifest_write_delta"], 0)
        self.assertEqual(report["no_persistence_deltas"]["database_write_delta"], 0)
        self.assertTrue(report["does_not_write_archive_manifest_runtime_output"])

    def test_phase2_evidence_document_records_safe_extraction_slice_no_raw_data_no_phase3(self):
        self.assertTrue(PHASE2.is_file(), f"missing phase2 evidence: {PHASE2}")
        text = PHASE2.read_text(encoding="utf-8")

        required_terms = [
            "IDS-V0_1-STAGE024-P2",
            "ACC-STAGE-024",
            "ids.stage024.archive_threat_model.v1",
            "ids.stage024.archive_manifest.v1",
            "check_archive_threat_model.py",
            "safe_extract_archive",
            "安全解压",
            "路径过滤",
            "风险标记",
            "解压产物重新进入导入管线",
            "ARCHIVE_EXTRACTION_OWNER_REVIEW_REQUIRED",
            "ARCHIVE_EXTRACTION_BLOCKED",
            "ARCHIVE_FORMAT_REQUIRES_EXTERNAL_ADAPTER",
            "ARCHIVE_PATH_TRAVERSAL_BLOCKED",
            "POST_EXTRACT_REINGEST_REQUIRED",
            "hash",
            "manifest",
            "dedup",
            "parser",
            "清理白名单",
            "不清理事实源和证据产物",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_PHASE3",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
