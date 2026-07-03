import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
SCRIPT = ROOT / "scripts" / "check_archive_adversarial_tests.py"
ENTRY = PURSUE_ROOT / "STAGE028_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE028_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE028_PHASE2_ARCHIVE_ADVERSARIAL_SLICE.md"
PHASE3 = PURSUE_ROOT / "STAGE028_PHASE3_SCENARIO_VALIDATION.md"
PHASE4 = PURSUE_ROOT / "STAGE028_PHASE4_CLOSEOUT.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"
ROADMAP = ROOT / "docs" / "governance" / "roadmap.yaml"
EVENTS = ROOT / "docs" / "governance" / "events.jsonl"
EVALUATED_AT = "2026-07-03T10:48:09Z"


class Stage028ArchiveAdversarialTestsPhase1Tests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage028_archive_adversarial_tests", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _write_archive(self, archive_path: Path) -> bytes:
        self.assertTrue(ENTRY.is_file(), f"missing real tracked payload source: {ENTRY}")
        payload = ENTRY.read_bytes()
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("safe/real-stage028-entry.md", payload)
            archive.writestr("nested/inner.zip", payload)
            archive.writestr("too-many/real-stage028-extra.md", payload)
            archive.writestr("../escape.md", payload)
            archive.writestr("/absolute.md", payload)
            archive.writestr("bad\ufffdname.md", payload)
        return payload

    def _write_zip(self, archive_path: Path, entries: dict[str, bytes]) -> None:
        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for entry_path, payload in entries.items():
                archive.writestr(entry_path, payload)

    def _phase3_scenario_archives(self, base: Path) -> dict[str, dict[str, object]]:
        self.assertTrue(ENTRY.is_file(), f"missing real tracked payload source: {ENTRY}")
        payload = ENTRY.read_bytes()

        def scenario(name: str, entries: dict[str, bytes], **limits: object) -> dict[str, object]:
            scenario_dir = base / name
            scenario_dir.mkdir(parents=True, exist_ok=True)
            archive_path = scenario_dir / f"{name}.zip"
            self._write_zip(archive_path, entries)
            return {
                "archive_uri": archive_path.as_uri(),
                "staging_area_uri": (scenario_dir / "staging").as_uri(),
                **limits,
            }

        return {
            "path_traversal": scenario(
                "path-traversal",
                {
                    "safe/path-traversal.md": payload,
                    "../escape.md": payload,
                },
            ),
            "absolute_path": scenario(
                "absolute-path",
                {
                    "safe/absolute.md": payload,
                    "/absolute.md": payload,
                },
            ),
            "archive_bomb": scenario(
                "archive-bomb",
                {
                    "safe/archive-bomb.md": payload,
                },
                archive_total_size_limit_bytes=max(1, len(payload) // 2),
            ),
            "nested_archive": scenario(
                "nested-archive",
                {
                    "safe/nested.md": payload,
                    "nested/inner.zip": payload,
                },
                archive_nested_depth_limit=0,
            ),
            "garbled_filename": scenario(
                "garbled-filename",
                {
                    "safe/garbled.md": payload,
                    "bad\ufffdname.md": payload,
                },
            ),
            "too_many_files": scenario(
                "too-many-files",
                {
                    "safe/first.md": payload,
                    "safe/second.md": payload,
                },
                archive_file_count_limit=1,
            ),
        }

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

    def test_phase2_adversarial_slice_runs_safe_extraction_path_filter_risk_and_reingest_without_persistence(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive_path = base / "stage028-real-governance-payload.zip"
            payload = self._write_archive(archive_path)
            staging = base / "stage028-staging"

            report = module.run_archive_adversarial_test(
                archive_uri=archive_path.as_uri(),
                staging_area_uri=staging.as_uri(),
                evaluated_at="2026-07-03T10:12:37Z",
                archive_file_count_limit=2,
                archive_total_size_limit_bytes=len(payload) * 20,
                archive_single_file_size_limit_bytes=len(payload) * 2,
                archive_nested_depth_limit=0,
            )

        self.assertEqual(report["schema_version"], "ids.stage028.archive_adversarial_tests.v1")
        self.assertEqual(report["stage"], "STAGE-028")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["task_id"], "IDS-V0_1-STAGE028-P2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-028")
        self.assertEqual(report["entrance"], "IDS 系统运营入口")
        self.assertEqual(
            report["archive_adversarial_test_state"],
            "ARCHIVE_ADVERSARIAL_OWNER_REVIEW_REQUIRED",
        )
        self.assertGreaterEqual(report["safe_extracted_file_count"], 1)
        self.assertGreaterEqual(report["blocked_entry_count"], 5)
        self.assertGreaterEqual(report["quarantine_entry_count"], 5)

        risk_codes = {entry["risk_code"] for entry in report["risk_entries"]}
        self.assertTrue(
            {
                "ARCHIVE_ADVERSARIAL_PATH_TRAVERSAL_BLOCKED",
                "ARCHIVE_ADVERSARIAL_ABSOLUTE_PATH_BLOCKED",
                "ARCHIVE_ADVERSARIAL_FILE_COUNT_LIMIT_EXCEEDED",
                "ARCHIVE_ADVERSARIAL_NESTED_DEPTH_LIMIT_EXCEEDED",
                "ARCHIVE_ADVERSARIAL_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED",
            }
            <= risk_codes,
            risk_codes,
        )
        self.assertEqual(
            report["post_extract_reingest"]["required_pipeline"],
            ["hash", "manifest", "dedup", "parser"],
        )
        self.assertGreaterEqual(len(report["post_extract_reingest"]["reingest_queue"]), 1)
        self.assertEqual(report["reingest_validation"]["actual_jobs_started"]["hash"], 0)
        self.assertEqual(report["cleanup_validation"]["state"], "ARCHIVE_ADVERSARIAL_CLEANUP_ALLOWLIST_VALIDATED")
        self.assertFalse(report["cleanup_validation"]["original_archive_in_cleanup_allowlist"])
        self.assertTrue(report["cleanup_validation"]["protected_refs_preserved"])
        self.assertTrue(report["manual_review_routing"]["risk_files_to_owner_review"])
        self.assertTrue(report["manual_review_routing"]["quarantine_required"])
        self.assertEqual(report["processing_guard"]["actual_import_jobs_started"], 0)
        self.assertTrue(all(delta == 0 for delta in report["no_persistence_deltas"].values()))
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertTrue(report["does_not_write_archive_adversarial_runtime_output"])
        self.assertTrue(report["does_not_write_archive_manifest_runtime_output"])
        self.assertTrue(report["does_not_write_runtime_outputs"])
        self.assertTrue(report["does_not_create_import_queue"])
        self.assertTrue(report["does_not_write_database"])
        self.assertTrue(report["does_not_call_external_apis"])
        self.assertTrue(report["does_not_use_fake_ids_business_data"])

    def test_phase2_blocks_raw_metadata_path_before_archive_access(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            staging = Path(tmp) / "stage028-staging"
            report = module.run_archive_adversarial_test(
                archive_uri="file:///Users/linzezhang/Downloads/IDS_MetaData/raw-owner.zip",
                staging_area_uri=staging.as_uri(),
                evaluated_at="2026-07-03T10:12:37Z",
            )

        self.assertEqual(report["archive_adversarial_test_state"], "ARCHIVE_ADVERSARIAL_BLOCKED")
        self.assertEqual(report["safe_extracted_file_count"], 0)
        self.assertEqual(report["post_extract_reingest"]["reingest_queue"], [])
        self.assertEqual(
            {entry["risk_code"] for entry in report["risk_entries"]},
            {"ARCHIVE_ADVERSARIAL_SOURCE_BLOCKED_RAW_METADATA_ROOT"},
        )
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertTrue(report["does_not_write_runtime_outputs"])

    def test_phase2_evidence_doc_records_implementation_boundaries(self):
        self.assertTrue(PHASE2.is_file(), f"missing phase2 slice: {PHASE2}")
        text = PHASE2.read_text(encoding="utf-8")

        required_terms = [
            "STAGE-028",
            "IDS-V0_1-STAGE028-P2",
            "ACC-STAGE-028",
            "check_archive_adversarial_tests.py",
            "ids.stage028.archive_adversarial_tests.v1",
            "safe extraction",
            "路径过滤",
            "风险标记",
            "人工复核",
            "隔离",
            "cleanup allowlist",
            "post_extract_reingest",
            "hash",
            "manifest",
            "dedup",
            "parser",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "path-only read-only real database source boundary",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "不得使用虚构 IDS 业务数据",
            "NO_PHASE3",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase3_scenario_report_validates_adversarial_cases_reingest_cleanup_and_no_runtime_output(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            report = module.build_stage028_scenario_report(
                scenario_archives=self._phase3_scenario_archives(Path(tmp)),
                evaluated_at=EVALUATED_AT,
            )

        self.assertEqual(report["schema_version"], "ids.stage028.archive_adversarial_tests.scenario_validation.v1")
        self.assertEqual(report["stage"], "STAGE-028")
        self.assertEqual(report["phase"], "Phase 3")
        self.assertEqual(report["task_id"], "IDS-V0_1-STAGE028-P3")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-028")
        self.assertEqual(report["archive_adversarial_schema"], "ids.stage028.archive_adversarial_tests.v1")
        self.assertEqual(report["validation_state"], "ARCHIVE_ADVERSARIAL_SCENARIO_VALIDATION_PASSED")
        self.assertTrue(report["required_scenarios_covered"])
        self.assertEqual(
            report["required_scenarios"],
            [
                "path_traversal",
                "absolute_path",
                "archive_bomb",
                "nested_archive",
                "garbled_filename",
                "too_many_files",
            ],
        )
        self.assertEqual(report["scenario_count"], 6)
        expected_risks = {
            "path_traversal": "ARCHIVE_ADVERSARIAL_PATH_TRAVERSAL_BLOCKED",
            "absolute_path": "ARCHIVE_ADVERSARIAL_ABSOLUTE_PATH_BLOCKED",
            "archive_bomb": "ARCHIVE_ADVERSARIAL_TOTAL_SIZE_LIMIT_EXCEEDED",
            "nested_archive": "ARCHIVE_ADVERSARIAL_NESTED_DEPTH_LIMIT_EXCEEDED",
            "garbled_filename": "ARCHIVE_ADVERSARIAL_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED",
            "too_many_files": "ARCHIVE_ADVERSARIAL_FILE_COUNT_LIMIT_EXCEEDED",
        }
        by_id = {item["scenario_id"]: item for item in report["scenario_results"]}
        self.assertEqual(set(by_id), set(expected_risks))
        for scenario_id, risk_code in expected_risks.items():
            with self.subTest(scenario_id=scenario_id):
                result = by_id[scenario_id]
                self.assertEqual(result["scenario_state"], "ARCHIVE_ADVERSARIAL_SCENARIO_VALIDATED")
                self.assertEqual(result["expected_risk_code"], risk_code)
                self.assertTrue(result["expected_risk_observed"])
                self.assertIn(risk_code, result["risk_codes"])
                self.assertEqual(
                    result["archive_adversarial_report"]["schema_version"],
                    "ids.stage028.archive_adversarial_tests.v1",
                )

        reingest_validation = report["reingest_validation"]
        self.assertEqual(reingest_validation["state"], "ARCHIVE_ADVERSARIAL_REINGEST_VALIDATED")
        self.assertEqual(reingest_validation["required_pipeline"], ["hash", "manifest", "dedup", "parser"])
        self.assertGreaterEqual(reingest_validation["safe_extracted_file_count"], 1)
        self.assertEqual(
            reingest_validation["actual_jobs_started"],
            {"hash": 0, "manifest": 0, "dedup": 0, "parser": 0, "ocr": 0, "embedding": 0, "index": 0, "import": 0},
        )

        cleanup_validation = report["cleanup_validation"]
        self.assertEqual(cleanup_validation["state"], "ARCHIVE_ADVERSARIAL_CLEANUP_ALLOWLIST_VALIDATED")
        self.assertTrue(cleanup_validation["cleanup_targets_are_staging_temp_files_only"])
        self.assertFalse(cleanup_validation["original_archive_in_cleanup_allowlist"])
        self.assertTrue(cleanup_validation["protected_refs_preserved"])

        manual_review_validation = report["manual_review_validation"]
        self.assertEqual(manual_review_validation["state"], "ARCHIVE_ADVERSARIAL_MANUAL_REVIEW_VALIDATED")
        self.assertGreaterEqual(manual_review_validation["owner_review_entry_count"], 6)
        self.assertGreaterEqual(manual_review_validation["quarantine_entry_count"], 6)

        for value in report["processing_guard"].values():
            self.assertEqual(value, 0)
        for value in report["no_persistence_deltas"].values():
            self.assertEqual(value, 0)
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertTrue(report["does_not_write_archive_adversarial_runtime_output"])
        self.assertTrue(report["does_not_write_archive_manifest_runtime_output"])
        self.assertTrue(report["does_not_write_runtime_outputs"])
        self.assertTrue(report["does_not_start_processing_jobs"])
        self.assertTrue(report["does_not_use_fake_ids_business_data"])

    def test_phase3_evidence_doc_records_scenarios_reingest_cleanup_raw_boundary_and_no_phase4(self):
        self.assertTrue(PHASE3.is_file(), f"missing phase3 evidence: {PHASE3}")
        text = PHASE3.read_text(encoding="utf-8")

        required_terms = [
            "IDS-V0_1-STAGE028-P3",
            "ACC-STAGE-028",
            "ids.stage028.archive_adversarial_tests.scenario_validation.v1",
            "build_stage028_scenario_report",
            "路径穿越",
            "绝对路径",
            "压缩炸弹",
            "嵌套包",
            "乱码文件名",
            "超大文件数",
            "ARCHIVE_ADVERSARIAL_PATH_TRAVERSAL_BLOCKED",
            "ARCHIVE_ADVERSARIAL_ABSOLUTE_PATH_BLOCKED",
            "ARCHIVE_ADVERSARIAL_TOTAL_SIZE_LIMIT_EXCEEDED",
            "ARCHIVE_ADVERSARIAL_NESTED_DEPTH_LIMIT_EXCEEDED",
            "ARCHIVE_ADVERSARIAL_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED",
            "ARCHIVE_ADVERSARIAL_FILE_COUNT_LIMIT_EXCEEDED",
            "ARCHIVE_ADVERSARIAL_REINGEST_VALIDATED",
            "hash",
            "manifest",
            "dedup",
            "parser",
            "ARCHIVE_ADVERSARIAL_CLEANUP_ALLOWLIST_VALIDATED",
            "只清理允许的临时文件",
            "不删除原始文件",
            "process-owned temporary archive fixtures",
            "不是 IDS corpus、database rows、business evidence、raw metadata 或 committed user data",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_PHASE4",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase4_closeout_summary_records_delivery_evidence_rollback_owner_feedback_and_no_upload(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            scenario_report = module.build_stage028_scenario_report(
                scenario_archives=self._phase3_scenario_archives(Path(tmp)),
                evaluated_at=EVALUATED_AT,
            )
            closeout = module.build_stage028_closeout_summary(
                scenario_report=scenario_report,
                evaluated_at=EVALUATED_AT,
            )

        self.assertEqual(closeout["schema_version"], "ids.stage028.archive_adversarial_tests.closeout.v1")
        self.assertEqual(closeout["stage"], "STAGE-028")
        self.assertEqual(closeout["phase"], "Phase 4")
        self.assertEqual(closeout["task_id"], "IDS-V0_1-STAGE028-P4")
        self.assertEqual(closeout["acceptance_id"], "ACC-STAGE-028")
        self.assertEqual(closeout["closeout_state"], "ARCHIVE_ADVERSARIAL_STAGE_CLOSEOUT_PASSED")
        self.assertEqual(closeout["whole_stage_review"]["result"], "passed_with_local_evidence")
        self.assertEqual(closeout["next_allowed_task_id"], "IDS-V0_1-STAGE029-P1")
        self.assertFalse(closeout["github_upload_allowed"])
        self.assertFalse(closeout["app_reinstall_allowed"])

        delivery = closeout["delivery_evidence"]
        self.assertEqual(delivery["evidence_state"], "ARCHIVE_ADVERSARIAL_DELIVERY_EVIDENCE_READY")
        manifest_sample = delivery["archive_manifest_sample"]
        self.assertEqual(manifest_sample["schema_version"], "ids.stage028.archive_adversarial_manifest.v1")
        self.assertGreaterEqual(manifest_sample["entry_count"], 1)
        self.assertTrue(manifest_sample["runtime_output_written"] is False)

        block_log = delivery["safety_block_log_sample"]
        self.assertEqual(block_log["state"], "ARCHIVE_ADVERSARIAL_BLOCK_LOG_READY")
        self.assertTrue(
            {
                "ARCHIVE_ADVERSARIAL_PATH_TRAVERSAL_BLOCKED",
                "ARCHIVE_ADVERSARIAL_ABSOLUTE_PATH_BLOCKED",
                "ARCHIVE_ADVERSARIAL_TOTAL_SIZE_LIMIT_EXCEEDED",
                "ARCHIVE_ADVERSARIAL_NESTED_DEPTH_LIMIT_EXCEEDED",
                "ARCHIVE_ADVERSARIAL_GARBLED_FILENAME_OWNER_REVIEW_REQUIRED",
                "ARCHIVE_ADVERSARIAL_FILE_COUNT_LIMIT_EXCEEDED",
            }
            <= set(block_log["risk_codes"]),
            block_log,
        )
        self.assertGreaterEqual(block_log["blocked_entry_count"], 6)

        cleanup_sample = delivery["cleanup_allowlist_sample"]
        self.assertEqual(cleanup_sample["state"], "ARCHIVE_ADVERSARIAL_CLEANUP_ALLOWLIST_VALIDATED")
        self.assertTrue(cleanup_sample["cleanup_targets_are_staging_temp_files_only"])
        self.assertFalse(cleanup_sample["original_archive_in_cleanup_allowlist"])
        self.assertTrue(cleanup_sample["protected_refs_preserved"])

        risk_boundary = closeout["risk_boundary"]
        self.assertTrue(risk_boundary["raw_metadata_path_only_boundary"])
        self.assertTrue(risk_boundary["real_data_only_policy"])
        self.assertTrue(risk_boundary["no_runtime_output"])
        self.assertTrue(risk_boundary["no_processing_jobs"])
        self.assertIn("/Users/linzezhang/Downloads/IDS_MetaData", risk_boundary["raw_metadata_root"])

        rollback = closeout["staging_rollback"]
        self.assertEqual(rollback["rollback_state"], "ARCHIVE_ADVERSARIAL_STAGING_ROLLBACK_DOCUMENTED")
        self.assertTrue(rollback["cleanup_instructions"]["temp_only"])
        self.assertTrue(rollback["cleanup_instructions"]["do_not_delete_original_archive"])
        self.assertTrue(rollback["cleanup_instructions"]["do_not_touch_raw_metadata_root"])
        self.assertGreaterEqual(len(closeout["owner_feedback_zh"]), 3)
        self.assertTrue(closeout["does_not_read_raw_metadata"])
        self.assertTrue(closeout["does_not_write_runtime_outputs"])
        self.assertTrue(closeout["does_not_use_fake_ids_business_data"])

    def test_phase4_closeout_doc_records_delivery_evidence_risk_stop_rollback_and_chinese_feedback(self):
        self.assertTrue(PHASE4.is_file(), f"missing phase4 closeout: {PHASE4}")
        text = PHASE4.read_text(encoding="utf-8")

        required_terms = [
            "IDS-V0_1-STAGE028-P4",
            "ACC-STAGE-028",
            "ids.stage028.archive_adversarial_tests.closeout.v1",
            "build_stage028_closeout_summary",
            "archive_manifest 样例",
            "安全阻断日志",
            "清理白名单",
            "自动解压风险边界",
            "停止条件",
            "staging 区回滚",
            "清理说明",
            "Whole-Stage Review",
            "中文 owner feedback",
            "ARCHIVE_ADVERSARIAL_STAGE_CLOSEOUT_PASSED",
            "ARCHIVE_ADVERSARIAL_DELIVERY_EVIDENCE_READY",
            "ARCHIVE_ADVERSARIAL_STAGING_ROLLBACK_DOCUMENTED",
            "No GitHub upload",
            "No app reinstall",
            "next allowed task",
            "IDS-V0_1-STAGE029-P1",
            "process-owned temporary archive fixtures",
            "不得使用虚构 IDS 业务数据",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_STAGE029",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_batch021_030_lock_tracks_stage028_completed_local_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")

        required_terms = [
            "STAGE-028:",
            'status: "completed_local"',
            '      - "Phase 1"',
            '      - "Phase 2"',
            '      - "Phase 3"',
            '      - "Phase 4"',
            'next_stage: "STAGE-029"',
            'current_task_id: "IDS-V0_1-STAGE028-P4"',
            'acceptance_id: "ACC-STAGE-028"',
            'acceptance_status: "local_passed"',
            'next_gate: "IDS-STAGE029-P1-GATE"',
            'push_allowed: false',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_PHASE2_ARCHIVE_ADVERSARIAL_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_PHASE3_SCENARIO_VALIDATION.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/scripts/check_archive_adversarial_tests.py",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage028_archive_adversarial_tests.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]
        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)
        allowed_status_terms = [
            'status: "stage028_completed_local_pending_stage029"',
            'status: "stage029_phase1_in_progress"',
        ]
        allowed_next_terms = [
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P1"',
            'next_allowed_task_id: "IDS-V0_1-STAGE029-P2"',
        ]
        self.assertTrue(any(term in text for term in allowed_status_terms), allowed_status_terms)
        self.assertTrue(any(term in text for term in allowed_next_terms), allowed_next_terms)

    def test_roadmap_and_events_track_stage028_phase4_closeout_local_gate(self):
        self.assertTrue(ROADMAP.is_file(), f"missing roadmap: {ROADMAP}")
        self.assertTrue(EVENTS.is_file(), f"missing events: {EVENTS}")
        roadmap_text = ROADMAP.read_text(encoding="utf-8")
        events_text = EVENTS.read_text(encoding="utf-8")

        roadmap_terms = [
            'stage_id: "IDS-STAGE028"',
            'name: "STAGE-028 · 压缩包对抗测试"',
            'phase_id: "IDS-STAGE028-P4"',
            'status: "passed_with_local_evidence"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE028_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/scripts/check_archive_adversarial_tests.py",
            "build_stage028_closeout_summary",
        ]
        event_terms = [
            '"event_id":"EVT-IDS-V0_1-STAGE028-P4-20260703-001"',
            '"event_type":"stage_closeout"',
            '"task_id":"IDS-V0_1-STAGE028-P4"',
            '"ACC-STAGE-028"',
            "STAGE028_PHASE4_CLOSEOUT.md",
            "check_archive_adversarial_tests.py",
            "build_stage028_closeout_summary",
        ]
        for term in roadmap_terms:
            with self.subTest(term=term):
                self.assertIn(term, roadmap_text)
        allowed_roadmap_stage_terms = [
            'current_stage_id: "IDS-STAGE028"',
            'current_stage_id: "IDS-STAGE029"',
        ]
        allowed_roadmap_phase_terms = [
            'current_phase_id: "IDS-STAGE028-P4"',
            'current_phase_id: "IDS-STAGE029-P1"',
        ]
        allowed_roadmap_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE028-P4"',
            'current_task_id: "IDS-V0_1-STAGE029-P1"',
        ]
        allowed_roadmap_gate_terms = [
            'next_gate_id: "IDS-STAGE029-P1-GATE"',
            'next_gate_id: "IDS-STAGE029-P2-GATE"',
        ]
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_stage_terms), allowed_roadmap_stage_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_phase_terms), allowed_roadmap_phase_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_task_terms), allowed_roadmap_task_terms)
        self.assertTrue(any(term in roadmap_text for term in allowed_roadmap_gate_terms), allowed_roadmap_gate_terms)
        for term in event_terms:
            with self.subTest(term=term):
                self.assertIn(term, events_text)


if __name__ == "__main__":
    unittest.main()
