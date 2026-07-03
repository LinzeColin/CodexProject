import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE021_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE021_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE021_PHASE2_PREFLIGHT_CONFIRMATION_UI_SLICE.md"
PHASE3 = PURSUE_ROOT / "STAGE021_PHASE3_SCENARIO_VALIDATION.md"
PHASE4 = PURSUE_ROOT / "STAGE021_PHASE4_CLOSEOUT.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"
SCRIPT = ROOT / "scripts" / "check_preflight_confirmation_ui.py"
CONFIRMED_AT = "2026-07-02T23:01:12Z"


class Stage021PreflightConfirmationUiPhase1Tests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage021_preflight_confirmation_ui", SCRIPT)
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
            "STAGE-021",
            "IDS-V0_1-STAGE021-P1",
            "ACC-STAGE-021",
            "预检确认 UI",
            "人类产品入口 + IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-021_预检确认UI.md",
            "2428711c7a935317de9bed7d50bbd02b7954ec7cdc5e1bfb832149a0c30103e8",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_preflight_ui_inputs_outputs_risks_costs_and_confirmation_states(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "preflight_confirmation_request_id",
            "input_directory_uri",
            "preflight_summary_snapshot",
            "risk_summary_snapshot",
            "cost_summary_snapshot",
            "owner_confirmation_context",
            "output_summary",
            "risk_items",
            "cost_items",
            "priority_hint",
            "confirmation_status",
            "human_product_entrance_payload",
            "PREFLIGHT_OWNER_REVIEW_REQUIRED",
            "PREFLIGHT_OWNER_APPROVED_CONTINUE",
            "PREFLIGHT_OWNER_PAUSED",
            "PREFLIGHT_OWNER_SPLIT_BATCH",
            "PREFLIGHT_OWNER_EXCLUDED_ITEMS",
            "owner 确认后才进入批量处理",
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

    def test_batch021_030_lock_tracks_current_stage021_phase_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")

        allowed_status_terms = [
            'status: "stage021_completed_local_pending_stage022"',
            'status: "stage022_phase1_in_progress"',
            'status: "stage022_phase2_in_progress"',
            'status: "stage022_phase3_in_progress"',
            'status: "stage022_completed_local_pending_stage023"',
            'status: "stage023_phase1_in_progress"',
            'status: "stage023_phase2_in_progress"',
        ]
        self.assertTrue(
            any(term in text for term in allowed_status_terms),
            f"batch lock did not contain an allowed STAGE-021/022 transition status: {allowed_status_terms}",
        )

        required_terms = [
            'batch_id: "IDS-V0_1-BATCH-021-030"',
            'stage_range: "STAGE-021..STAGE-030"',
            'acceptance_range: "ACC-STAGE-021..ACC-STAGE-030"',
            'push_allowed: false',
            'current_task_id: "IDS-V0_1-STAGE021-P4"',
            'acceptance_status: "local_passed"',
            'next_gate: "IDS-STAGE022-P1-GATE"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE2_PREFLIGHT_CONFIRMATION_UI_SLICE.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE3_SCENARIO_VALIDATION.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE4_CLOSEOUT.md",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase2_metadata_only_confirmation_ui_payload_shows_preflight_risk_cost_and_owner_actions(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            docs = base / "preflight-ui-input"
            docs.mkdir()
            shutil.copy2(ENTRY, docs / "stage021-entry.md")
            shutil.copy2(PHASE1, docs / "stage021-scope.md")
            (docs / "owner-candidate.zip").write_bytes(b"PK\x03\x04ids-structural-archive-candidate")
            (docs / "scan-page.png").write_bytes(b"\x89PNG\r\n\x1a\nids-structural-scan-candidate")
            (docs / "unknown-format.weird").write_bytes(b"ids-structural-unknown-format-candidate")

            report = module.evaluate_preflight_confirmation_ui(
                source_uris=[docs.as_uri()],
                confirmed_at=CONFIRMED_AT,
                available_space_bytes=10**9,
                oversized_file_threshold_bytes=1,
            )

        serialized = json.dumps(report, ensure_ascii=False)

        self.assertEqual(report["schema_version"], "ids.stage021.preflight_confirmation_ui.v1")
        self.assertEqual(report["stage"], "STAGE-021")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-021")
        self.assertEqual(report["entrance"], "人类产品入口 + IDS 系统运营入口")
        self.assertTrue(report["customer_visible"])
        self.assertEqual(report["source_preflight_schema"], "ids.stage018.import_preflight.v1")
        self.assertEqual(report["source_risk_schema"], "ids.stage019.import_risk_estimator.v1")
        self.assertEqual(report["source_cost_schema"], "ids.stage020.import_cost_estimator.v1")
        self.assertEqual(report["file_count_estimate"], 5)
        self.assertEqual(report["format_counts"][".md"], 2)
        self.assertEqual(report["archive_candidate_count"], 1)
        self.assertEqual(report["scanned_document_candidate_count"], 1)
        self.assertEqual(report["unknown_format_count"], 1)
        self.assertGreater(report["embedding_token_estimate"]["high"], 0)
        self.assertGreaterEqual(report["ocr_page_estimate"]["high"], 1)
        self.assertGreater(report["external_api_cost_estimate"]["high"], 0)
        self.assertGreater(report["index_size_estimate"]["high_bytes"], 0)
        self.assertEqual(report["confirmation_status"], "PREFLIGHT_OWNER_REVIEW_REQUIRED")
        self.assertIn("COST_ARCHIVE_REVIEW_REQUIRED", report["risk_items"])
        self.assertIn("COST_UNKNOWN_FORMAT_PRESENT", report["risk_items"])
        self.assertIn("COST_OVERSIZED_FILE_PRESENT", report["risk_items"])
        self.assertIn(report["priority_hint"], {"archive_review_first", "split_large_files", "manual_review_first"})
        self.assertIn("continue_after_owner_confirmation", report["owner_decision_options"])
        self.assertIn("pause_without_side_effects", report["owner_decision_options"])
        self.assertIn("split_batch", report["owner_decision_options"])
        self.assertIn("exclude_selected_items", report["owner_decision_options"])
        payload = report["human_product_entrance_payload"]
        self.assertEqual(payload["title"], "预检确认")
        self.assertTrue(payload["customer_visible"])
        self.assertTrue(payload["confirmation_required"])
        self.assertGreaterEqual(len(payload["summary_cards"]), 8)
        self.assertIn("continue_after_owner_confirmation", [item["action"] for item in payload["decision_buttons"]])
        self.assertIn("pause_without_side_effects", [item["action"] for item in payload["decision_buttons"]])
        self.assertIn("split_batch", [item["action"] for item in payload["decision_buttons"]])
        self.assertIn("exclude_selected_items", [item["action"] for item in payload["decision_buttons"]])
        self.assertIn("确认前不会启动解析、OCR、Embedding、索引或实际导入", payload["message"])
        self.assertEqual(report["ui_component_contract"]["component_name"], "PreflightConfirmationPanel")
        self.assertNotIn("# IDS v0.1 STAGE-021 Entry Contract", serialized)
        self.assertNotIn("raw_payload", serialized)
        self.assertTrue(report["does_not_parse_body_text"])
        self.assertTrue(report["does_not_start_ocr"])
        self.assertTrue(report["does_not_create_embeddings"])
        self.assertTrue(report["does_not_build_index"])
        self.assertTrue(report["does_not_start_import"])
        self.assertTrue(report["does_not_call_external_apis"])
        self.assertTrue(report["does_not_write_database"])

    def test_phase2_blocks_ids_metadata_path_before_directory_listing_and_reports_no_side_effects(self):
        module = self._load_module()
        report = module.evaluate_preflight_confirmation_ui(
            source_uris=["file:///Users/linzezhang/Downloads/IDS_MetaData"],
            confirmed_at=CONFIRMED_AT,
        )

        self.assertEqual(report["overall_state"], "PREFLIGHT_BLOCKED")
        self.assertEqual(report["confirmation_status"], "PREFLIGHT_BLOCKED")
        self.assertEqual(report["file_count_estimate"], 0)
        self.assertEqual(report["priority_hint"], "blocked")
        self.assertIn("COST_SOURCE_BLOCKED", report["risk_items"])
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertEqual(report["no_persistence_deltas"]["database_write_delta"], 0)

    def test_phase2_cli_returns_json_payload_without_runtime_writes(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            shutil.copy2(ENTRY, base / "stage021-entry.md")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--source-uri",
                    base.as_uri(),
                    "--confirmed-at",
                    CONFIRMED_AT,
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        report = json.loads(result.stdout)

        self.assertEqual(report["stage"], "STAGE-021")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["file_count_estimate"], 1)
        self.assertIn(report["confirmation_status"], {"PREFLIGHT_READY", "PREFLIGHT_OWNER_REVIEW_REQUIRED"})
        self.assertTrue(report["human_product_entrance_payload"]["customer_visible"])
        self.assertEqual(report["no_persistence_deltas"]["report_write_delta"], 0)
        self.assertTrue(report["does_not_write_manifest_files"])

    def test_phase2_evidence_document_records_ui_slice_no_raw_data_no_phase3(self):
        self.assertTrue(PHASE2.is_file(), f"missing phase2 evidence: {PHASE2}")
        text = PHASE2.read_text(encoding="utf-8")

        for term in [
            "IDS-V0_1-STAGE021-P2",
            "ACC-STAGE-021",
            "check_preflight_confirmation_ui.py",
            "human_product_entrance_payload",
            "PreflightConfirmationPanel",
            "continue_after_owner_confirmation",
            "pause_without_side_effects",
            "split_batch",
            "exclude_selected_items",
            "不解析正文",
            "不启动 OCR",
            "不启动 Embedding",
            "不建立索引",
            "不启动实际导入",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_PHASE3",
        ]:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase3_scenario_report_covers_empty_small_large_offline_archive_and_space(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            empty_dir = base / "empty"
            small_dir = base / "small"
            large_dir = base / "large"
            archive_dir = base / "archive"
            for path in [empty_dir, small_dir, large_dir, archive_dir]:
                path.mkdir()
            shutil.copy2(ENTRY, small_dir / "stage021-entry.md")
            shutil.copy2(PHASE1, small_dir / "stage021-scope.md")
            for index in range(101):
                shutil.copy2(ENTRY, large_dir / f"stage021-entry-{index:03}.md")
            shutil.copy2(ENTRY, archive_dir / "stage021-entry.md")
            (archive_dir / "owner-candidate.zip").write_bytes(b"PK\x03\x04ids-structural-archive-candidate")

            scenario_report = module.build_stage021_scenario_report(
                scenario_sources={
                    "empty_directory": {"source_uris": [empty_dir.as_uri()]},
                    "small_directory": {"source_uris": [small_dir.as_uri()]},
                    "large_directory": {"source_uris": [large_dir.as_uri()]},
                    "offline_drive": {"source_uris": [small_dir.as_uri()], "drive_state": "offline"},
                    "archive_present": {"source_uris": [archive_dir.as_uri()]},
                    "insufficient_space": {"source_uris": [small_dir.as_uri()], "available_space_bytes": 1},
                },
                confirmed_at=CONFIRMED_AT,
                batch_size=50,
                oversized_file_threshold_bytes=1,
            )

        self.assertEqual(
            scenario_report["schema_version"],
            "ids.stage021.preflight_confirmation_ui.scenario_validation.v1",
        )
        self.assertEqual(scenario_report["stage"], "STAGE-021")
        self.assertEqual(scenario_report["phase"], "Phase 3")
        self.assertEqual(scenario_report["acceptance_id"], "ACC-STAGE-021")
        self.assertEqual(scenario_report["validation_state"], "SCENARIO_VALIDATION_PASSED")
        self.assertTrue(scenario_report["required_scenarios_covered"])
        self.assertEqual(scenario_report["scenario_count"], 6)

        scenarios = scenario_report["scenario_results"]
        self.assertEqual(scenarios["empty_directory"]["preflight_confirmation"]["file_count_estimate"], 0)
        self.assertIn(
            scenarios["small_directory"]["preflight_confirmation"]["confirmation_status"],
            {"PREFLIGHT_READY", "PREFLIGHT_OWNER_REVIEW_REQUIRED"},
        )
        self.assertGreater(
            scenarios["large_directory"]["owner_decision_plan"]["batch_plan"]["batch_count"],
            1,
        )
        self.assertEqual(
            scenarios["offline_drive"]["preflight_confirmation"]["overall_state"],
            "PREFLIGHT_BLOCKED",
        )
        self.assertIn(
            "COST_ARCHIVE_REVIEW_REQUIRED",
            scenarios["archive_present"]["preflight_confirmation"]["risk_items"],
        )
        self.assertEqual(
            scenarios["insufficient_space"]["preflight_confirmation"]["overall_state"],
            "PREFLIGHT_BLOCKED",
        )
        self.assertIn(
            "COST_LOCAL_SPACE_BLOCKED",
            scenarios["insufficient_space"]["preflight_confirmation"]["risk_items"],
        )

        for key in [
            "actual_parse_jobs_started",
            "actual_ocr_jobs_started",
            "actual_embedding_jobs_started",
            "actual_index_jobs_started",
            "actual_import_jobs_started",
            "actual_external_api_calls_started",
        ]:
            self.assertEqual(scenario_report["processing_guard"][key], 0)

    def test_phase3_owner_decision_plan_supports_save_cancel_split_and_skip_without_persistence(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            docs = base / "operator"
            docs.mkdir()
            shutil.copy2(ENTRY, docs / "stage021-entry.md")
            shutil.copy2(PHASE1, docs / "stage021-scope.md")
            (docs / "scan-page.png").write_bytes(b"\x89PNG\r\n\x1a\nids-structural-scan-candidate")

            preflight_report = module.evaluate_preflight_confirmation_ui(
                source_uris=[docs.as_uri()],
                confirmed_at=CONFIRMED_AT,
                oversized_file_threshold_bytes=10**9,
            )
            decision = module.build_preflight_owner_decision_plan(preflight_report, batch_size=2)

        self.assertEqual(decision["schema_version"], "ids.stage021.preflight_confirmation_ui.owner_decision.v1")
        self.assertEqual(decision["stage"], "STAGE-021")
        self.assertEqual(decision["phase"], "Phase 3")
        self.assertEqual(decision["save_contract"]["state"], "PREFLIGHT_RESULT_SERIALIZABLE")
        self.assertTrue(decision["save_contract"]["can_save_result"])
        self.assertFalse(decision["save_contract"]["persisted_by_helper"])
        self.assertEqual(decision["cancel_contract"]["state"], "PREFLIGHT_CANCEL_READY")
        self.assertEqual(decision["cancel_contract"]["document_delta"], 0)
        self.assertTrue(decision["batch_plan"]["can_split"])
        self.assertEqual(decision["batch_plan"]["batch_count"], 2)
        self.assertEqual(decision["skip_high_risk_plan"]["high_risk_file_count"], 1)
        self.assertEqual(decision["skip_high_risk_plan"]["kept_file_count"], 2)
        self.assertIn("save_for_owner_review", decision["supported_owner_actions"])
        self.assertIn("cancel_without_side_effects", decision["supported_owner_actions"])
        self.assertIn("split_into_batches", decision["supported_owner_actions"])
        self.assertIn("skip_high_risk_files", decision["supported_owner_actions"])
        for key in [
            "document_delta",
            "chunk_delta",
            "job_delta",
            "index_delta",
            "import_write_delta",
            "manifest_write_delta",
            "database_write_delta",
        ]:
            self.assertEqual(decision["no_persistence_deltas"][key], 0)

    def test_phase3_evidence_document_records_scenarios_no_raw_data_no_phase4(self):
        self.assertTrue(PHASE3.is_file(), f"missing phase3 evidence: {PHASE3}")
        text = PHASE3.read_text(encoding="utf-8")

        for term in [
            "IDS-V0_1-STAGE021-P3",
            "ACC-STAGE-021",
            "empty_directory",
            "small_directory",
            "large_directory",
            "offline_drive",
            "archive_present",
            "insufficient_space",
            "save_for_owner_review",
            "cancel_without_side_effects",
            "split_into_batches",
            "skip_high_risk_files",
            "PreflightConfirmationPanel",
            "不解析正文",
            "不启动 OCR",
            "不启动 Embedding",
            "不建立索引",
            "不启动实际导入",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_PHASE4",
        ]:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase4_owner_feedback_summary_returns_closeout_contract_without_outputs(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            docs = base / "preflight-closeout"
            docs.mkdir()
            shutil.copy2(ENTRY, docs / "stage021-entry.md")
            shutil.copy2(PHASE1, docs / "stage021-scope.md")
            (docs / "owner-candidate.zip").write_bytes(b"PK\x03\x04ids-structural-archive-candidate")
            (docs / "scan-page.png").write_bytes(b"\x89PNG\r\n\x1a\nids-structural-scan-candidate")
            (docs / "unknown-format.weird").write_bytes(b"ids-structural-unknown-format-candidate")

            preflight_report = module.evaluate_preflight_confirmation_ui(
                source_uris=[docs.as_uri()],
                confirmed_at=CONFIRMED_AT,
                oversized_file_threshold_bytes=1,
            )
            feedback = module.build_preflight_owner_feedback_summary(
                preflight_report,
                recorded_at=CONFIRMED_AT,
                stage_review_findings=[
                    "Phase 4 records closeout evidence without creating runtime outputs.",
                    "BATCH021_030 upload remains blocked until STAGE-021..030 are complete and reviewed.",
                ],
            )

        self.assertEqual(feedback["schema_version"], "ids.stage021.preflight_confirmation_ui.owner_feedback.v1")
        self.assertEqual(feedback["stage"], "STAGE-021")
        self.assertEqual(feedback["phase"], "Phase 4")
        self.assertEqual(feedback["task_id"], "IDS-V0_1-STAGE021-P4")
        self.assertEqual(feedback["acceptance_id"], "ACC-STAGE-021")
        self.assertEqual(feedback["recorded_at"], CONFIRMED_AT)
        self.assertEqual(feedback["report_sample"]["schema_version"], "ids.stage021.preflight_confirmation_ui.v1")
        self.assertIn("human_product_entrance_payload", feedback["report_sample"])
        self.assertIn("ui_component_contract", feedback["report_sample"])
        self.assertIn("embedding_token_estimate", feedback["report_sample"])
        self.assertIn("ocr_page_estimate", feedback["report_sample"])
        self.assertIn("index_size_estimate", feedback["report_sample"])
        self.assertIn("COST_ARCHIVE_REVIEW_REQUIRED", feedback["risk_checklist"])
        self.assertIn("COST_UNKNOWN_FORMAT_PRESENT", feedback["risk_checklist"])
        self.assertGreaterEqual(len(feedback["user_confirmation_flow_log"]), 6)
        self.assertTrue(any("继续" in step for step in feedback["user_confirmation_flow_log"]))
        self.assertTrue(any("保存" in step for step in feedback["user_confirmation_flow_log"]))
        self.assertTrue(any("取消" in step for step in feedback["user_confirmation_flow_log"]))
        self.assertTrue(any("分批" in step for step in feedback["user_confirmation_flow_log"]))
        self.assertTrue(any("高风险" in step for step in feedback["user_confirmation_flow_log"]))
        self.assertTrue(any("Embedding" in item for item in feedback["estimation_uncertainty"]))
        self.assertTrue(any("OCR" in item for item in feedback["estimation_uncertainty"]))
        self.assertTrue(any("外部 API" in item for item in feedback["estimation_uncertainty"]))
        self.assertTrue(any("索引" in item for item in feedback["estimation_uncertainty"]))
        self.assertIn("PREFLIGHT_BLOCKED", feedback["failure_explanations"])
        self.assertIn("PREFLIGHT_OWNER_REVIEW_REQUIRED", feedback["failure_explanations"])
        self.assertGreaterEqual(len(feedback["rollback_steps"]), 4)
        self.assertEqual(feedback["whole_stage_review"]["result"], "passed_with_local_evidence")
        self.assertEqual(feedback["whole_stage_review"]["next_stage"], "STAGE-022")
        self.assertFalse(feedback["whole_stage_review"]["batch_upload_allowed"])
        self.assertEqual(feedback["whole_stage_review"]["next_batch_gate"], "IDS-STAGE022-P1-GATE")
        self.assertEqual(feedback["whole_stage_review"]["unresolved_findings"], [])
        for value in feedback["processing_guard"].values():
            self.assertEqual(value, 0)
        for value in feedback["no_persistence_deltas"].values():
            self.assertEqual(value, 0)
        self.assertTrue(feedback["does_not_create_screenshots"])
        self.assertTrue(feedback["does_not_write_report_files"])
        self.assertTrue(feedback["does_not_push_to_github"])
        self.assertTrue(feedback["does_not_enter_stage022"])

    def test_phase4_evidence_document_records_delivery_review_raw_boundary_and_no_stage022(self):
        self.assertTrue(PHASE4.is_file(), f"missing phase4 closeout: {PHASE4}")
        text = PHASE4.read_text(encoding="utf-8")

        for term in [
            "IDS-V0_1-STAGE021-P4",
            "ACC-STAGE-021",
            "预检报告样例",
            "风险清单",
            "用户确认流程日志",
            "估算不确定性",
            "失败解释文案",
            "回滚方式",
            "Whole-Stage Review",
            "STAGE-021 已在本地完成",
            "IDS-STAGE022-P1-GATE",
            "push_allowed=false",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_STAGE022",
            "不执行 GitHub upload、PR、merge 或 app reinstall",
        ]:
            with self.subTest(term=term):
                self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
