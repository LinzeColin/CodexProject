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
PHASE3 = PURSUE_ROOT / "STAGE024_PHASE3_SCENARIO_VALIDATION.md"
PHASE4 = PURSUE_ROOT / "STAGE024_PHASE4_CLOSEOUT.md"
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
            'status: "stage024_phase3_in_progress"',
            'status: "stage024_completed_local_pending_stage025"',
            'status: "stage025_phase1_in_progress"',
            'status: "stage025_phase2_in_progress"',
            'status: "stage025_phase3_in_progress"',
            'status: "stage025_completed_local_pending_stage026"',
            'status: "stage026_phase1_in_progress"',
            'status: "stage026_phase2_in_progress"',
            'status: "stage026_phase3_in_progress"',
            'status: "stage026_completed_local_pending_stage027"',
            'status: "completed_local"',
        ]
        self.assertTrue(
            any(term in text for term in allowed_status_terms),
            f"batch lock did not contain an allowed STAGE-024 transition status: {allowed_status_terms}",
        )

        allowed_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE023-P4"',
            'current_task_id: "IDS-V0_1-STAGE024-P1"',
            'current_task_id: "IDS-V0_1-STAGE024-P2"',
            'current_task_id: "IDS-V0_1-STAGE024-P3"',
            'current_task_id: "IDS-V0_1-STAGE024-P4"',
            'current_task_id: "IDS-V0_1-STAGE025-P1"',
            'current_task_id: "IDS-V0_1-STAGE025-P2"',
            'current_task_id: "IDS-V0_1-STAGE025-P3"',
            'current_task_id: "IDS-V0_1-STAGE025-P4"',
            'current_task_id: "IDS-V0_1-STAGE026-P1"',
            'current_task_id: "IDS-V0_1-STAGE026-P2"',
            'current_task_id: "IDS-V0_1-STAGE026-P3"',
            'current_task_id: "IDS-V0_1-STAGE026-P4"',
        ]
        self.assertTrue(
            any(term in text for term in allowed_task_terms),
            f"batch lock did not contain an allowed STAGE-024 current task: {allowed_task_terms}",
        )
        allowed_acceptance_terms = [
            'acceptance_status: "phase2_safe_extraction_slice_complete"',
            'acceptance_status: "phase3_scenario_validation_complete"',
            'acceptance_status: "local_passed"',
        ]
        self.assertTrue(
            any(term in text for term in allowed_acceptance_terms),
            f"batch lock did not contain an allowed STAGE-024 acceptance status: {allowed_acceptance_terms}",
        )
        allowed_gate_terms = [
            'next_gate: "IDS-STAGE024-P3-GATE"',
            'next_gate: "IDS-STAGE024-P4-GATE"',
            'next_gate: "IDS-STAGE025-P1-GATE"',
            'next_gate: "IDS-STAGE025-P2-GATE"',
            'next_gate: "IDS-STAGE025-P3-GATE"',
            'next_gate: "IDS-STAGE025-P4-GATE"',
            'next_gate: "IDS-STAGE026-P1-GATE"',
            'next_gate: "IDS-STAGE026-P2-GATE"',
            'next_gate: "IDS-STAGE026-P3-GATE"',
            'next_gate: "IDS-STAGE026-P4-GATE"',
            'next_gate: "IDS-STAGE027-P1-GATE"',
        ]
        self.assertTrue(
            any(term in text for term in allowed_gate_terms),
            f"batch lock did not contain an allowed STAGE-024 next gate: {allowed_gate_terms}",
        )
        allowed_stage_status_terms = [
            'status: "in_progress"',
            'status: "completed_local"',
        ]
        self.assertTrue(
            any(term in text for term in allowed_stage_status_terms),
            f"batch lock did not contain an allowed STAGE-024 stage status: {allowed_stage_status_terms}",
        )

        required_terms = [
            'batch_id: "IDS-V0_1-BATCH-021-030"',
            'STAGE-021:',
            'STAGE-022:',
            'STAGE-023:',
            'STAGE-024:',
            'status: "completed_local"',
            'acceptance_id: "ACC-STAGE-024"',
            'push_allowed:',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_PHASE2_SAFE_EXTRACTION_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE024_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/scripts/check_archive_threat_model.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage024_archive_threat_model.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def _write_zip(self, archive_path, entries):
        with zipfile.ZipFile(archive_path, "w") as archive:
            for entry_path, payload in entries.items():
                archive.writestr(entry_path, payload)

    def _phase3_scenario_archives(self, base):
        scenarios = {}
        scenario_entries = {
            "path_traversal": {"../escape.txt": b"escape"},
            "absolute_path": {"/absolute.txt": b"absolute"},
            "archive_bomb": {"huge.bin": b"0123456789"},
            "nested_archive": {"nested/inner.zip": b"PK\x03\x04"},
            "garbled_filename": {"bad-\ufffd-name.txt": b"garbled"},
            "too_many_files": {"safe/one.txt": b"one", "safe/two.txt": b"two"},
        }
        scenario_limits = {
            "path_traversal": {},
            "absolute_path": {},
            "archive_bomb": {"archive_total_size_limit_bytes": 4},
            "nested_archive": {"archive_nested_depth_limit": 0},
            "garbled_filename": {},
            "too_many_files": {"archive_file_count_limit": 1},
        }
        for scenario_id, entries in scenario_entries.items():
            archive_path = base / f"{scenario_id}.zip"
            staging = base / f"{scenario_id}-staging"
            staging.mkdir()
            self._write_zip(archive_path, entries)
            scenarios[scenario_id] = {
                "archive_uri": archive_path.as_uri(),
                "staging_area_uri": staging.as_uri(),
                **scenario_limits[scenario_id],
            }
        return scenarios

    def test_phase3_scenario_report_covers_required_threat_samples_and_risk_codes(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            scenarios = self._phase3_scenario_archives(Path(tmp))
            report = module.build_stage024_scenario_report(
                scenario_archives=scenarios,
                evaluated_at=EXTRACTED_AT,
            )

        self.assertEqual(report["schema_version"], "ids.stage024.archive_threat_model.scenario_validation.v1")
        self.assertEqual(report["stage"], "STAGE-024")
        self.assertEqual(report["phase"], "Phase 3")
        self.assertEqual(report["task_id"], "IDS-V0_1-STAGE024-P3")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-024")
        self.assertEqual(report["validation_state"], "ARCHIVE_THREAT_SCENARIO_VALIDATION_PASSED")
        self.assertTrue(report["required_scenarios_covered"])
        self.assertEqual(report["scenario_count"], 6)
        self.assertEqual(set(report["required_scenarios"]), {
            "path_traversal",
            "absolute_path",
            "archive_bomb",
            "nested_archive",
            "garbled_filename",
            "too_many_files",
        })

        by_id = {item["scenario_id"]: item for item in report["scenario_results"]}
        expected_risks = {
            "path_traversal": "ARCHIVE_PATH_TRAVERSAL_BLOCKED",
            "absolute_path": "ARCHIVE_ABSOLUTE_PATH_BLOCKED",
            "archive_bomb": "ARCHIVE_TOTAL_SIZE_LIMIT_EXCEEDED",
            "nested_archive": "ARCHIVE_NESTED_DEPTH_LIMIT_EXCEEDED",
            "garbled_filename": "ARCHIVE_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED",
            "too_many_files": "ARCHIVE_FILE_COUNT_LIMIT_EXCEEDED",
        }
        for scenario_id, risk_code in expected_risks.items():
            with self.subTest(scenario_id=scenario_id):
                self.assertIn(risk_code, by_id[scenario_id]["risk_codes"])
                self.assertEqual(by_id[scenario_id]["expected_risk_code"], risk_code)
                self.assertEqual(by_id[scenario_id]["scenario_state"], "ARCHIVE_THREAT_SCENARIO_VALIDATED")
                self.assertIn("archive_threat_model", by_id[scenario_id])

        serialized = json.dumps(report, ensure_ascii=False)
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertEqual(report["processing_guard"]["actual_hash_jobs_started"], 0)
        self.assertEqual(report["processing_guard"]["actual_manifest_jobs_started"], 0)
        self.assertEqual(report["processing_guard"]["actual_dedup_jobs_started"], 0)
        self.assertEqual(report["processing_guard"]["actual_parser_jobs_started"], 0)
        self.assertNotIn("/Users/linzezhang/Downloads/IDS_MetaData/raw-source", serialized)

    def test_phase3_reingest_validation_confirms_extracted_files_reenter_hash_manifest_dedup_parser(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive_path = base / "safe-reingest.zip"
            staging = base / "safe-reingest-staging"
            staging.mkdir()
            self._write_zip(archive_path, {"safe/reingest-note.txt": b"safe"})
            report = module.build_stage024_scenario_report(
                scenario_archives={
                    "safe_reingest": {
                        "archive_uri": archive_path.as_uri(),
                        "staging_area_uri": staging.as_uri(),
                    }
                },
                evaluated_at=EXTRACTED_AT,
                required_scenarios=("safe_reingest",),
            )

        reingest = report["reingest_validation"]
        self.assertEqual(reingest["state"], "POST_EXTRACT_REINGEST_VALIDATED")
        self.assertEqual(reingest["required_pipeline"], ["hash", "manifest", "dedup", "parser"])
        self.assertGreaterEqual(reingest["safe_extracted_file_count"], 1)
        for pipeline_state in reingest["pipeline_stage_states"].values():
            with self.subTest(pipeline_state=pipeline_state):
                self.assertIn("_REQUIRED", pipeline_state)
        self.assertEqual(report["processing_guard"]["actual_hash_jobs_started"], 0)
        self.assertEqual(report["processing_guard"]["actual_manifest_jobs_started"], 0)
        self.assertEqual(report["processing_guard"]["actual_dedup_jobs_started"], 0)
        self.assertEqual(report["processing_guard"]["actual_parser_jobs_started"], 0)

    def test_phase3_cleanup_validation_only_allows_staging_temp_files(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive_path = base / "cleanup.zip"
            staging = base / "cleanup-staging"
            staging.mkdir()
            self._write_zip(archive_path, {"safe/cleanup-note.txt": b"safe"})
            report = module.build_stage024_scenario_report(
                scenario_archives={
                    "safe_cleanup": {
                        "archive_uri": archive_path.as_uri(),
                        "staging_area_uri": staging.as_uri(),
                    }
                },
                evaluated_at=EXTRACTED_AT,
                required_scenarios=("safe_cleanup",),
            )
            archive_uri = archive_path.as_uri()

        cleanup = report["cleanup_validation"]
        self.assertEqual(cleanup["state"], "ARCHIVE_CLEANUP_ALLOWLIST_VALIDATED")
        self.assertTrue(cleanup["cleanup_targets_are_staging_temp_files_only"])
        self.assertTrue(cleanup["protected_refs_preserved"])
        self.assertFalse(cleanup["original_archive_in_cleanup_allowlist"])
        self.assertNotIn(archive_uri, cleanup["cleanup_allowlist_uris"])
        self.assertEqual(set(cleanup["allowed_cleanup_classes"]), {"ARCHIVE_STAGING_TEMP_FILE"})

    def test_phase3_evidence_document_records_scenarios_reingest_cleanup_no_raw_data_no_phase4(self):
        self.assertTrue(PHASE3.is_file(), f"missing phase3 evidence: {PHASE3}")
        text = PHASE3.read_text(encoding="utf-8")

        required_terms = [
            "IDS-V0_1-STAGE024-P3",
            "ACC-STAGE-024",
            "ids.stage024.archive_threat_model.scenario_validation.v1",
            "build_stage024_scenario_report",
            "路径穿越",
            "绝对路径",
            "压缩炸弹",
            "嵌套包",
            "乱码文件名",
            "超大文件数",
            "ARCHIVE_PATH_TRAVERSAL_BLOCKED",
            "ARCHIVE_ABSOLUTE_PATH_BLOCKED",
            "ARCHIVE_TOTAL_SIZE_LIMIT_EXCEEDED",
            "ARCHIVE_NESTED_DEPTH_LIMIT_EXCEEDED",
            "ARCHIVE_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED",
            "ARCHIVE_FILE_COUNT_LIMIT_EXCEEDED",
            "POST_EXTRACT_REINGEST_VALIDATED",
            "hash",
            "manifest",
            "dedup",
            "parser",
            "ARCHIVE_CLEANUP_ALLOWLIST_VALIDATED",
            "只清理允许的临时文件",
            "不删除原始文件",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_PHASE4",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase4_owner_feedback_summary_returns_archive_closeout_contract_without_outputs(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive_path = base / "closeout.zip"
            staging = base / "closeout-staging"
            staging.mkdir()
            self._write_zip(
                archive_path,
                {
                    "safe/archive-note.txt": b"safe",
                    "../blocked.txt": b"blocked",
                },
            )
            archive_report = module.safe_extract_archive(
                archive_uri=archive_path.as_uri(),
                staging_area_uri=staging.as_uri(),
                extracted_at=EXTRACTED_AT,
            )
            scenario_dir = base / "phase3-scenarios"
            scenario_dir.mkdir()
            scenario_report = module.build_stage024_scenario_report(
                scenario_archives=self._phase3_scenario_archives(scenario_dir),
                evaluated_at=EXTRACTED_AT,
            )
            feedback = module.build_archive_threat_owner_feedback_summary(
                archive_report,
                scenario_report=scenario_report,
                recorded_at=EXTRACTED_AT,
                stage_review_findings=[
                    "Phase 4 records archive_manifest sample, safety block log, cleanup allowlist, rollback, and owner feedback without creating runtime outputs.",
                    "BATCH021_030 upload remains blocked until STAGE-021..030 are complete, reviewed, and repaired.",
                ],
            )

        self.assertEqual(feedback["schema_version"], "ids.stage024.archive_threat_model.owner_feedback.v1")
        self.assertEqual(feedback["stage"], "STAGE-024")
        self.assertEqual(feedback["phase"], "Phase 4")
        self.assertEqual(feedback["task_id"], "IDS-V0_1-STAGE024-P4")
        self.assertEqual(feedback["acceptance_id"], "ACC-STAGE-024")
        self.assertEqual(feedback["recorded_at"], EXTRACTED_AT)
        self.assertEqual(feedback["report_sample"]["archive_manifest_sample"]["schema_version"], "ids.stage024.archive_manifest.v1")
        self.assertGreaterEqual(len(feedback["report_sample"]["safety_block_log"]), 1)
        self.assertGreaterEqual(len(feedback["report_sample"]["cleanup_allowlist_sample"]), 1)
        self.assertEqual(feedback["report_sample"]["scenario_validation_sample"]["schema_version"], "ids.stage024.archive_threat_model.scenario_validation.v1")
        self.assertIn("ARCHIVE_PATH_TRAVERSAL_BLOCKED", feedback["risk_checklist"])
        self.assertIn("ARCHIVE_ABSOLUTE_PATH_BLOCKED", feedback["risk_checklist"])
        self.assertIn("ARCHIVE_TOTAL_SIZE_LIMIT_EXCEEDED", feedback["risk_checklist"])
        self.assertIn("ARCHIVE_NESTED_DEPTH_LIMIT_EXCEEDED", feedback["risk_checklist"])
        self.assertIn("ARCHIVE_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED", feedback["risk_checklist"])
        self.assertIn("ARCHIVE_FILE_COUNT_LIMIT_EXCEEDED", feedback["risk_checklist"])
        self.assertIn("ARCHIVE_FORMAT_REQUIRES_EXTERNAL_ADAPTER", feedback["risk_checklist"])
        self.assertIn("ARCHIVE_SOURCE_BLOCKED_RAW_METADATA_ROOT", feedback["risk_checklist"])
        self.assertTrue(any("不覆盖原始压缩包" in item for item in feedback["automatic_extraction_boundaries"]))
        self.assertTrue(any("不写出指定 staging 区" in item for item in feedback["automatic_extraction_boundaries"]))
        self.assertTrue(any("owner review" in item or "人工复核" in item for item in feedback["automatic_extraction_boundaries"]))
        self.assertIn("ARCHIVE_EXTRACTION_BLOCKED", feedback["failure_explanations"])
        self.assertIn("ARCHIVE_EXTRACTION_OWNER_REVIEW_REQUIRED", feedback["failure_explanations"])
        self.assertIn("ARCHIVE_CLEANUP_ALLOWLIST_VALIDATED", feedback["failure_explanations"])
        self.assertTrue(feedback["staging_rollback_and_cleanup"]["cleanup_targets_are_staging_temp_files_only"])
        self.assertFalse(feedback["staging_rollback_and_cleanup"]["original_archive_in_cleanup_allowlist"])
        self.assertTrue(feedback["staging_rollback_and_cleanup"]["protected_refs_preserved"])
        self.assertGreaterEqual(len(feedback["rollback_steps"]), 4)
        self.assertEqual(feedback["whole_stage_review"]["result"], "passed_with_local_evidence")
        self.assertEqual(feedback["whole_stage_review"]["next_stage"], "STAGE-025")
        self.assertFalse(feedback["whole_stage_review"]["batch_upload_allowed"])
        self.assertEqual(feedback["whole_stage_review"]["next_batch_gate"], "IDS-STAGE025-P1-GATE")
        self.assertEqual(feedback["whole_stage_review"]["unresolved_findings"], [])
        for value in feedback["processing_guard"].values():
            self.assertEqual(value, 0)
        for value in feedback["no_persistence_deltas"].values():
            self.assertEqual(value, 0)
        self.assertTrue(feedback["does_not_write_archive_manifest_runtime_output"])
        self.assertTrue(feedback["does_not_write_report_files"])
        self.assertTrue(feedback["does_not_push_to_github"])
        self.assertTrue(feedback["does_not_reinstall_app_entries"])
        self.assertTrue(feedback["does_not_enter_stage025"])

    def test_phase4_evidence_document_records_archive_manifest_block_log_cleanup_review_raw_boundary_and_no_stage025(self):
        self.assertTrue(PHASE4.is_file(), f"missing phase4 closeout: {PHASE4}")
        text = PHASE4.read_text(encoding="utf-8")

        required_terms = [
            "IDS-V0_1-STAGE024-P4",
            "ACC-STAGE-024",
            "ids.stage024.archive_threat_model.owner_feedback.v1",
            "build_archive_threat_owner_feedback_summary",
            "archive_manifest 样例",
            "安全阻断日志",
            "清理白名单",
            "自动解压风险边界",
            "停止条件",
            "staging 区回滚",
            "Whole-Stage Review",
            "STAGE-024 已在本地完成",
            "IDS-STAGE025-P1-GATE",
            "push_allowed=false",
            "ARCHIVE_PATH_TRAVERSAL_BLOCKED",
            "ARCHIVE_ABSOLUTE_PATH_BLOCKED",
            "ARCHIVE_TOTAL_SIZE_LIMIT_EXCEEDED",
            "ARCHIVE_NESTED_DEPTH_LIMIT_EXCEEDED",
            "ARCHIVE_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED",
            "ARCHIVE_FILE_COUNT_LIMIT_EXCEEDED",
            "ARCHIVE_CLEANUP_ALLOWLIST_VALIDATED",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_STAGE025",
            "不执行 GitHub upload、PR、merge 或 app reinstall",
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
