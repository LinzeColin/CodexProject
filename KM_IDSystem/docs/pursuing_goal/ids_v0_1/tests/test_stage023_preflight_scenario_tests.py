import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE023_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE023_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE023_PHASE2_PREFLIGHT_SCENARIO_TESTS_SLICE.md"
PHASE3 = PURSUE_ROOT / "STAGE023_PHASE3_SCENARIO_VALIDATION.md"
PHASE4 = PURSUE_ROOT / "STAGE023_PHASE4_CLOSEOUT.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"
SCRIPT = ROOT / "scripts" / "check_preflight_scenario_tests.py"
EVALUATED_AT = "2026-07-03T01:18:21Z"


class Stage023PreflightScenarioTestsPhase1Tests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage023_preflight_scenario_tests", SCRIPT)
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
            "STAGE-023",
            "IDS-V0_1-STAGE023-P1",
            "ACC-STAGE-023",
            "预检场景测试",
            "empty_directory",
            "small_directory",
            "large_directory",
            "offline_drive",
            "bad_file",
            "archive_present",
            "insufficient_space",
            "人类产品入口 + IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-023_预检场景测试.md",
            "dce8e78bea790c56b16b9b4035b82160056f51ea0b7ddf020a19ddc465cadc2d",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_scenario_inputs_outputs_risks_costs_and_confirmation_states(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "preflight_scenario_suite_id",
            "scenario_id",
            "scenario_input_directory_uri",
            "scenario_source_preflight_snapshot_ref",
            "preflight_summary_snapshot",
            "risk_summary_snapshot",
            "cost_summary_snapshot",
            "scenario_validation_summary",
            "required_scenarios",
            "scenario_results",
            "owner_confirmation_context",
            "PREFLIGHT_SCENARIO_DRAFT",
            "PREFLIGHT_SCENARIO_READY",
            "PREFLIGHT_SCENARIO_OWNER_REVIEW_REQUIRED",
            "PREFLIGHT_SCENARIO_WAITING_OWNER_CONFIRMATION",
            "PREFLIGHT_SCENARIO_OWNER_APPROVED",
            "owner 确认后才进入批量处理",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase4_owner_feedback_summary_returns_closeout_contract_without_outputs(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "preflight-closeout"
            docs.mkdir()
            shutil.copy2(ENTRY, docs / "preflight-structural-note.md")
            shutil.copy2(PHASE1, docs / "preflight-structural-reference.csv")
            (docs / "owner-candidate.zip").write_bytes(b"PK\x03\x04ids-structural-archive-candidate")
            (docs / "scan-page.png").write_bytes(b"\x89PNG\r\n\x1a\nids-structural-scan-candidate")
            (docs / "unknown-format.weird").write_bytes(b"ids-structural-unknown-format-candidate")
            (docs / "broken-source.bad").write_bytes(b"")

            preflight_report = module.evaluate_preflight_scenario_tests(
                source_uris=[docs.as_uri()],
                evaluated_at=EVALUATED_AT,
                oversized_file_threshold_bytes=1,
            )
            feedback = module.build_preflight_scenario_owner_feedback_summary(
                preflight_report,
                recorded_at=EVALUATED_AT,
                stage_review_findings=[
                    "Phase 4 records closeout evidence without creating runtime outputs.",
                    "BATCH021_030 upload remains blocked until STAGE-021..030 are complete and reviewed.",
                ],
            )

        self.assertEqual(feedback["schema_version"], "ids.stage023.preflight_scenario_tests.owner_feedback.v1")
        self.assertEqual(feedback["stage"], "STAGE-023")
        self.assertEqual(feedback["phase"], "Phase 4")
        self.assertEqual(feedback["task_id"], "IDS-V0_1-STAGE023-P4")
        self.assertEqual(feedback["acceptance_id"], "ACC-STAGE-023")
        self.assertEqual(feedback["recorded_at"], EVALUATED_AT)
        self.assertEqual(feedback["report_sample"]["schema_version"], "ids.stage023.preflight_scenario_tests.v1")
        self.assertIn("scenario_validation_summary", feedback["report_sample"])
        self.assertIn("human_product_entrance_payload", feedback["report_sample"])
        self.assertIn("ui_component_contract", feedback["report_sample"])
        self.assertIn("embedding_token_estimate", feedback["report_sample"])
        self.assertIn("ocr_page_estimate", feedback["report_sample"])
        self.assertIn("index_size_estimate", feedback["report_sample"])
        self.assertIn("SCENARIO_ARCHIVE_REVIEW_REQUIRED", feedback["risk_checklist"])
        self.assertIn("SCENARIO_BAD_FILE_PRESENT", feedback["risk_checklist"])
        self.assertIn("SCENARIO_INSUFFICIENT_SPACE", feedback["risk_checklist"])
        self.assertGreaterEqual(len(feedback["user_confirmation_flow_log"]), 6)
        self.assertTrue(any("预检报告" in step for step in feedback["user_confirmation_flow_log"]))
        self.assertTrue(any("保存" in step for step in feedback["user_confirmation_flow_log"]))
        self.assertTrue(any("取消" in step for step in feedback["user_confirmation_flow_log"]))
        self.assertTrue(any("分批" in step for step in feedback["user_confirmation_flow_log"]))
        self.assertTrue(any("高风险" in step for step in feedback["user_confirmation_flow_log"]))
        self.assertTrue(any("Embedding" in item for item in feedback["estimation_uncertainty"]))
        self.assertTrue(any("OCR" in item for item in feedback["estimation_uncertainty"]))
        self.assertTrue(any("外部 API" in item for item in feedback["estimation_uncertainty"]))
        self.assertTrue(any("索引" in item for item in feedback["estimation_uncertainty"]))
        self.assertIn("PREFLIGHT_SCENARIO_BLOCKED", feedback["failure_explanations"])
        self.assertIn("PREFLIGHT_SCENARIO_OWNER_REVIEW_REQUIRED", feedback["failure_explanations"])
        self.assertIn("SCENARIO_BAD_FILE_PRESENT", feedback["failure_explanations"])
        self.assertGreaterEqual(len(feedback["rollback_steps"]), 4)
        self.assertEqual(feedback["whole_stage_review"]["result"], "passed_with_local_evidence")
        self.assertEqual(feedback["whole_stage_review"]["next_stage"], "STAGE-024")
        self.assertFalse(feedback["whole_stage_review"]["batch_upload_allowed"])
        self.assertEqual(feedback["whole_stage_review"]["next_batch_gate"], "IDS-STAGE024-P1-GATE")
        self.assertEqual(feedback["whole_stage_review"]["unresolved_findings"], [])
        for value in feedback["processing_guard"].values():
            self.assertEqual(value, 0)
        for value in feedback["no_persistence_deltas"].values():
            self.assertEqual(value, 0)
        self.assertTrue(feedback["does_not_create_screenshots"])
        self.assertTrue(feedback["does_not_write_report_files"])
        self.assertTrue(feedback["does_not_push_to_github"])
        self.assertTrue(feedback["does_not_reinstall_app_entries"])
        self.assertTrue(feedback["does_not_enter_stage024"])

    def test_phase4_evidence_document_records_delivery_review_raw_boundary_and_no_stage024(self):
        self.assertTrue(PHASE4.is_file(), f"missing phase4 closeout: {PHASE4}")
        text = PHASE4.read_text(encoding="utf-8")

        required_terms = [
            "IDS-V0_1-STAGE023-P4",
            "ACC-STAGE-023",
            "预检报告样例",
            "风险清单",
            "用户确认流程日志",
            "估算不确定性",
            "失败解释文案",
            "回滚方式",
            "Whole-Stage Review",
            "STAGE-023 已在本地完成",
            "IDS-STAGE024-P1-GATE",
            "push_allowed=false",
            "empty_directory",
            "small_directory",
            "large_directory",
            "offline_drive",
            "bad_file",
            "archive_present",
            "insufficient_space",
            "PreflightScenarioTestsPanel",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_STAGE024",
            "不执行 GitHub upload、PR、merge 或 app reinstall",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase3_scenario_report_covers_required_scenarios_and_no_processing_boundaries(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            empty_dir = base / "empty"
            small_dir = base / "small"
            large_dir = base / "large"
            archive_dir = base / "archive"
            bad_dir = base / "bad"
            for path in [empty_dir, small_dir, large_dir, archive_dir, bad_dir]:
                path.mkdir()
            shutil.copy2(ENTRY, small_dir / "preflight-structural-note.md")
            shutil.copy2(PHASE1, small_dir / "preflight-structural-reference.csv")
            for index in range(101):
                shutil.copy2(ENTRY, large_dir / f"accepted-preflight-package-{index:03}.md")
            shutil.copy2(ENTRY, archive_dir / "preflight-structural-note.md")
            (archive_dir / "owner-candidate.zip").write_bytes(b"PK\x03\x04ids-structural-archive-candidate")
            (bad_dir / "broken-source.bad").write_bytes(b"")

            scenario_report = module.build_stage023_scenario_report(
                scenario_sources={
                    "empty_directory": {"source_uris": [empty_dir.as_uri()]},
                    "small_directory": {"source_uris": [small_dir.as_uri()]},
                    "large_directory": {"source_uris": [large_dir.as_uri()]},
                    "offline_drive": {"source_uris": [small_dir.as_uri()], "drive_state": "offline"},
                    "bad_file": {"source_uris": [bad_dir.as_uri()]},
                    "archive_present": {"source_uris": [archive_dir.as_uri()]},
                    "insufficient_space": {"source_uris": [small_dir.as_uri()], "available_space_bytes": 1},
                },
                evaluated_at=EVALUATED_AT,
                batch_size=50,
                oversized_file_threshold_bytes=10**9,
            )

        self.assertEqual(
            scenario_report["schema_version"],
            "ids.stage023.preflight_scenario_tests.scenario_validation.v1",
        )
        self.assertEqual(scenario_report["stage"], "STAGE-023")
        self.assertEqual(scenario_report["phase"], "Phase 3")
        self.assertEqual(scenario_report["task_id"], "IDS-V0_1-STAGE023-P3")
        self.assertEqual(scenario_report["acceptance_id"], "ACC-STAGE-023")
        self.assertEqual(scenario_report["validation_state"], "SCENARIO_VALIDATION_PASSED")
        self.assertTrue(scenario_report["required_scenarios_covered"])
        self.assertEqual(scenario_report["scenario_count"], 7)
        self.assertEqual(
            set(scenario_report["required_scenarios"]),
            {
                "empty_directory",
                "small_directory",
                "large_directory",
                "offline_drive",
                "bad_file",
                "archive_present",
                "insufficient_space",
            },
        )

        scenarios = scenario_report["scenario_results"]
        self.assertEqual(scenarios["empty_directory"]["preflight_scenario_tests"]["file_count_estimate"], 0)
        self.assertIn(
            scenarios["small_directory"]["preflight_scenario_tests"]["confirmation_status"],
            {"PREFLIGHT_SCENARIO_READY", "PREFLIGHT_SCENARIO_OWNER_REVIEW_REQUIRED"},
        )
        self.assertGreater(
            scenarios["large_directory"]["owner_decision_plan"]["batch_plan"]["batch_count"],
            1,
        )
        self.assertEqual(
            scenarios["offline_drive"]["preflight_scenario_tests"]["overall_state"],
            "PREFLIGHT_SCENARIO_BLOCKED",
        )
        self.assertIn(
            "SCENARIO_BAD_FILE_PRESENT",
            scenarios["bad_file"]["preflight_scenario_tests"]["risk_items"],
        )
        self.assertIn(
            "SCENARIO_ARCHIVE_REVIEW_REQUIRED",
            scenarios["archive_present"]["preflight_scenario_tests"]["risk_items"],
        )
        self.assertEqual(
            scenarios["insufficient_space"]["preflight_scenario_tests"]["overall_state"],
            "PREFLIGHT_SCENARIO_BLOCKED",
        )

        for key in [
            "actual_parse_jobs_started",
            "actual_ocr_jobs_started",
            "actual_embedding_jobs_started",
            "actual_index_jobs_started",
            "actual_import_jobs_started",
            "actual_external_api_calls_started",
            "actual_scenario_runner_jobs_started",
        ]:
            self.assertEqual(scenario_report["processing_guard"][key], 0)
        self.assertTrue(scenario_report["does_not_parse_body_text"])
        self.assertTrue(scenario_report["does_not_start_ocr"])
        self.assertTrue(scenario_report["does_not_create_embeddings"])
        self.assertTrue(scenario_report["does_not_build_index"])
        self.assertTrue(scenario_report["does_not_start_import"])
        self.assertTrue(scenario_report["does_not_write_scenario_results"])

    def test_phase3_owner_decision_plan_supports_save_cancel_split_and_skip_without_persistence(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "preflight-owner"
            docs.mkdir()
            shutil.copy2(ENTRY, docs / "preflight-structural-note.md")
            shutil.copy2(PHASE1, docs / "preflight-structural-reference.csv")
            (docs / "owner-candidate.zip").write_bytes(b"PK\x03\x04ids-structural-archive-candidate")
            (docs / "unknown-format.weird").write_bytes(b"ids-structural-unknown-format-candidate")
            (docs / "broken-source.bad").write_bytes(b"")

            report = module.evaluate_preflight_scenario_tests(
                source_uris=[docs.as_uri()],
                evaluated_at=EVALUATED_AT,
                oversized_file_threshold_bytes=10**9,
            )
            decision = module.build_preflight_scenario_owner_decision_plan(report, batch_size=2)

        self.assertEqual(
            decision["schema_version"],
            "ids.stage023.preflight_scenario_tests.owner_decision.v1",
        )
        self.assertEqual(decision["stage"], "STAGE-023")
        self.assertEqual(decision["phase"], "Phase 3")
        self.assertEqual(decision["task_id"], "IDS-V0_1-STAGE023-P3")
        self.assertEqual(decision["save_contract"]["state"], "PREFLIGHT_SCENARIO_RESULT_SERIALIZABLE")
        self.assertTrue(decision["save_contract"]["can_save_result"])
        self.assertFalse(decision["save_contract"]["persisted_by_helper"])
        self.assertEqual(decision["cancel_contract"]["state"], "PREFLIGHT_SCENARIO_CANCEL_READY")
        self.assertEqual(decision["cancel_contract"]["document_delta"], 0)
        self.assertTrue(decision["batch_plan"]["can_split"])
        self.assertEqual(decision["batch_plan"]["batch_count"], 3)
        self.assertGreaterEqual(decision["skip_high_risk_plan"]["high_risk_file_count"], 3)
        self.assertGreaterEqual(decision["skip_high_risk_plan"]["kept_file_count"], 2)

        for action in [
            "save_for_owner_review",
            "pause_without_side_effects",
            "cancel_without_side_effects",
            "split_into_batches",
            "skip_high_risk_files",
        ]:
            with self.subTest(action=action):
                self.assertIn(action, decision["supported_owner_actions"])

        for key in [
            "document_delta",
            "chunk_delta",
            "job_delta",
            "index_delta",
            "import_write_delta",
            "manifest_write_delta",
            "database_write_delta",
            "scenario_result_write_delta",
        ]:
            self.assertEqual(decision["no_persistence_deltas"][key], 0)
            self.assertEqual(decision["cancel_contract"][key], 0)

    def test_phase3_evidence_document_records_scenarios_no_raw_data_no_phase4(self):
        self.assertTrue(PHASE3.is_file(), f"missing phase3 evidence: {PHASE3}")
        text = PHASE3.read_text(encoding="utf-8")

        required_terms = [
            "IDS-V0_1-STAGE023-P3",
            "ACC-STAGE-023",
            "ids.stage023.preflight_scenario_tests.scenario_validation.v1",
            "ids.stage023.preflight_scenario_tests.owner_decision.v1",
            "build_stage023_scenario_report",
            "build_preflight_scenario_owner_decision_plan",
            "empty_directory",
            "small_directory",
            "large_directory",
            "offline_drive",
            "bad_file",
            "archive_present",
            "insufficient_space",
            "save_for_owner_review",
            "pause_without_side_effects",
            "cancel_without_side_effects",
            "split_into_batches",
            "skip_high_risk_files",
            "只读取元信息",
            "不解析正文",
            "不启动 OCR",
            "不启动 Embedding",
            "不建立索引",
            "不启动实际导入",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_PHASE4",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase1_preserves_metadata_only_no_processing_and_raw_data_boundaries(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        combined = "\n".join(
            [
                ENTRY.read_text(encoding="utf-8"),
                PHASE1.read_text(encoding="utf-8"),
            ]
        )

        boundary_terms = [
            "只读取元信息",
            "不解析正文",
            "不修改原始文件",
            "不启动 OCR",
            "不启动 Embedding",
            "不建立索引",
            "不启动实际导入",
            "不生成 runtime 输出",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
            "NO_PHASE2",
        ]

        for term in boundary_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_batch021_030_lock_tracks_current_stage023_phase_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")

        allowed_status_terms = [
            'status: "stage023_phase1_in_progress"',
            'status: "stage023_phase2_in_progress"',
            'status: "stage023_phase3_in_progress"',
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
            f"batch lock did not contain an allowed STAGE-023 transition status: {allowed_status_terms}",
        )

        allowed_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE023-P1"',
            'current_task_id: "IDS-V0_1-STAGE023-P2"',
            'current_task_id: "IDS-V0_1-STAGE023-P3"',
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
            f"batch lock did not contain an allowed STAGE-023 current task: {allowed_task_terms}",
        )

        required_terms = [
            'batch_id: "IDS-V0_1-BATCH-021-030"',
            'STAGE-021:',
            'STAGE-022:',
            'STAGE-023:',
            'status: "completed_local"',
            'acceptance_id: "ACC-STAGE-023"',
            'push_allowed: false',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE3_SCENARIO_VALIDATION.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE4_CLOSEOUT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage023_preflight_scenario_tests.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase2_metadata_only_preflight_scenario_payload_estimates_cost_and_shows_human_product_payload(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "scenario-input"
            base.mkdir()
            shutil.copy2(ENTRY, base / "critical-repair-plan.md")
            shutil.copy2(PHASE1, base / "equipment-reference.csv")
            (base / "scan-page.png").write_bytes(b"\x89PNG\r\n\x1a\nids-structural-scan-candidate")
            (base / "owner-candidate.zip").write_bytes(b"PK\x03\x04ids-structural-archive-candidate")
            (base / "unknown-format.weird").write_bytes(b"ids-structural-unknown-format-candidate")
            (base / "bad-file.bad").write_bytes(b"")

            report = module.evaluate_preflight_scenario_tests(
                source_uris=[base.as_uri()],
                evaluated_at=EVALUATED_AT,
                available_space_bytes=10**9,
                oversized_file_threshold_bytes=10**9,
            )

        serialized = json.dumps(report, ensure_ascii=False)

        self.assertEqual(report["schema_version"], "ids.stage023.preflight_scenario_tests.v1")
        self.assertEqual(report["stage"], "STAGE-023")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["task_id"], "IDS-V0_1-STAGE023-P2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-023")
        self.assertEqual(report["entrance"], "人类产品入口 + IDS 系统运营入口")
        self.assertTrue(report["customer_visible"])
        self.assertEqual(report["source_preflight_schema"], "ids.stage018.import_preflight.v1")
        self.assertEqual(report["source_cost_schema"], "ids.stage020.import_cost_estimator.v1")
        self.assertEqual(report["file_count_estimate"], 6)
        self.assertEqual(report["format_counts"][".md"], 1)
        self.assertEqual(report["format_counts"][".csv"], 1)
        self.assertEqual(report["archive_candidate_count"], 1)
        self.assertEqual(report["scanned_document_candidate_count"], 1)
        self.assertGreaterEqual(report["unknown_format_count"], 2)
        self.assertGreaterEqual(report["bad_file_candidate_count"], 1)
        self.assertGreater(report["embedding_token_estimate"]["high"], 0)
        self.assertGreaterEqual(report["ocr_page_estimate"]["high"], 1)
        self.assertGreater(report["external_api_cost_estimate"]["high"], 0)
        self.assertGreater(report["index_size_estimate"]["high_bytes"], 0)
        self.assertEqual(report["confirmation_status"], "PREFLIGHT_SCENARIO_OWNER_REVIEW_REQUIRED")
        self.assertIn(report["priority_suggestion"], {"owner_review_required", "split_or_skip_risk_items"})
        self.assertIn("SCENARIO_ARCHIVE_REVIEW_REQUIRED", report["risk_items"])
        self.assertIn("SCENARIO_UNKNOWN_FORMAT_PRESENT", report["risk_items"])
        self.assertIn("SCENARIO_BAD_FILE_PRESENT", report["risk_items"])
        self.assertIn("review_preflight_scenario_tests", report["human_product_entrance_payload"]["owner_actions"])
        self.assertIn("approve_preflight_scenarios", report["human_product_entrance_payload"]["owner_actions"])
        self.assertIn("split_batch", report["human_product_entrance_payload"]["owner_actions"])
        self.assertIn("skip_high_risk_files", report["human_product_entrance_payload"]["owner_actions"])
        self.assertIn("确认前不会启动解析、OCR、Embedding、索引或实际导入", report["human_product_entrance_payload"]["message"])
        self.assertGreaterEqual(len(report["human_product_entrance_payload"]["summary_cards"]), 9)
        self.assertEqual(report["ui_component_contract"]["component_name"], "PreflightScenarioTestsPanel")
        self.assertEqual(report["processing_guard"]["actual_parse_jobs_started"], 0)
        self.assertEqual(report["processing_guard"]["actual_ocr_jobs_started"], 0)
        self.assertEqual(report["processing_guard"]["actual_embedding_jobs_started"], 0)
        self.assertEqual(report["processing_guard"]["actual_index_jobs_started"], 0)
        self.assertEqual(report["processing_guard"]["actual_import_jobs_started"], 0)
        self.assertTrue(report["does_not_parse_body_text"])
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertNotIn("# IDS v0.1 STAGE-023 Entry Contract", serialized)
        self.assertNotIn("raw_payload", serialized)

    def test_phase2_evidence_document_records_metadata_only_payload_and_no_processing_boundaries(self):
        self.assertTrue(PHASE2.is_file(), f"missing phase2 evidence: {PHASE2}")
        text = PHASE2.read_text(encoding="utf-8")

        required_terms = [
            "IDS-V0_1-STAGE023-P2",
            "ids.stage023.preflight_scenario_tests.v1",
            "check_preflight_scenario_tests.py",
            "PreflightScenarioTestsPanel",
            "file_count_estimate",
            "format_counts",
            "archive_candidate_count",
            "scanned_document_candidate_count",
            "bad_file_candidate_count",
            "embedding_token_estimate",
            "ocr_page_estimate",
            "external_api_cost_estimate",
            "index_size_estimate",
            "risk_items",
            "cost_items",
            "priority_suggestion",
            "human_product_entrance_payload",
            "只读取元信息",
            "不解析正文",
            "不修改原始文件",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_PHASE3",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)
