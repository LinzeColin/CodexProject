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
ENTRY = PURSUE_ROOT / "STAGE019_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE019_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE019_PHASE2_RISK_ESTIMATOR_SLICE.md"
PHASE3 = PURSUE_ROOT / "STAGE019_PHASE3_SCENARIO_VALIDATION.md"
PHASE4 = PURSUE_ROOT / "STAGE019_PHASE4_CLOSEOUT.md"
SCRIPT = ROOT / "scripts" / "check_import_risk_estimator.py"
PRECHECKED_AT = "2026-07-02T20:49:12Z"


class Stage019ImportRiskEstimatorPhase1Tests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage019_import_risk_estimator", SCRIPT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_phase1_contracts_exist_and_bind_taskpack_identity(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")

        entry_text = ENTRY.read_text(encoding="utf-8")
        phase1_text = PHASE1.read_text(encoding="utf-8")

        for text in [entry_text, phase1_text]:
            self.assertIn("STAGE-019", text)
            self.assertIn("IDS-V0_1-STAGE019-P1", text)
            self.assertIn("ACC-STAGE-019", text)
            self.assertIn("导入风险估算器", text)
            self.assertIn("人类产品入口 + IDS 系统运营入口", text)

    def test_phase1_defines_risk_estimator_inputs_outputs_and_confirmation_boundary(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        phase1_text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "risk_estimation_request_id",
            "candidate_file_metadata",
            "storage_budget_snapshot",
            "high_risk_file_count",
            "oversized_file_count",
            "suspicious_archive_count",
            "unknown_format_count",
            "insufficient_space_risk",
            "risk_score_band",
            "cost_items",
            "RISK_OWNER_REVIEW_REQUIRED",
            "RISK_OWNER_APPROVED",
            "owner 确认后才进入批量处理",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, phase1_text)

    def test_phase1_preserves_raw_data_and_no_processing_boundaries(self):
        self.assertTrue(ENTRY.is_file(), f"missing entry contract: {ENTRY}")
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        combined = "\n".join(
            [
                ENTRY.read_text(encoding="utf-8"),
                PHASE1.read_text(encoding="utf-8"),
            ]
        )

        forbidden_boundary_terms = [
            "不解析正文",
            "不修改原始文件",
            "不启动 OCR",
            "不启动 Embedding",
            "不建立索引",
            "不启动实际导入",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
        ]

        for term in forbidden_boundary_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase2_metadata_only_risk_estimator_counts_risks_costs_priority_and_entrance(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            docs = base / "risk-input"
            docs.mkdir()
            shutil.copy2(ENTRY, docs / "stage019-entry.md")
            shutil.copy2(PHASE1, docs / "stage019-scope.md")
            (docs / "owner-candidate.zip").write_bytes(b"PK\x03\x04ids-structural-archive-candidate")
            (docs / "scan-page.png").write_bytes(b"\x89PNG\r\n\x1a\nids-structural-scan-candidate")
            (docs / "unknown-format.weird").write_bytes(b"ids-structural-unknown-format-candidate")

            report = module.evaluate_import_risk_estimate(
                source_uris=[docs.as_uri()],
                estimated_at=PRECHECKED_AT,
                oversized_file_threshold_bytes=1,
                available_space_bytes=10**9,
            )

        serialized = json.dumps(report, ensure_ascii=False)

        self.assertEqual(report["schema_version"], "ids.stage019.import_risk_estimator.v1")
        self.assertEqual(report["stage"], "STAGE-019")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-019")
        self.assertEqual(report["entrance"], "人类产品入口 + IDS 系统运营入口")
        self.assertTrue(report["customer_visible"])
        self.assertEqual(report["source_preflight_schema"], "ids.stage018.import_preflight.v1")
        self.assertEqual(report["file_count_estimate"], 5)
        self.assertEqual(report["format_counts"][".md"], 2)
        self.assertEqual(report["format_counts"][".zip"], 1)
        self.assertEqual(report["format_counts"][".png"], 1)
        self.assertEqual(report["format_counts"][".weird"], 1)
        self.assertEqual(report["suspicious_archive_count"], 1)
        self.assertEqual(report["scanned_document_candidate_count"], 1)
        self.assertEqual(report["unknown_format_count"], 1)
        self.assertEqual(report["oversized_file_count"], 5)
        self.assertGreaterEqual(report["high_risk_file_count"], 5)
        self.assertFalse(report["insufficient_space_risk"])
        self.assertEqual(report["risk_score_band"], "high")
        self.assertIn("RISK_SUSPICIOUS_ARCHIVE_PRESENT", report["risk_items"])
        self.assertIn("RISK_UNKNOWN_FORMAT_PRESENT", report["risk_items"])
        self.assertIn("RISK_OVERSIZED_FILE_PRESENT", report["risk_items"])
        self.assertEqual(report["priority_hint"], "archive_review_first")
        self.assertEqual(report["confirmation_status"], "RISK_OWNER_REVIEW_REQUIRED")
        self.assertEqual(report["cost_items"]["archive_review_class"], "low")
        self.assertEqual(report["cost_items"]["operator_review_class"], "medium")
        entrance_payload = report["human_product_entrance_payload"]
        self.assertEqual(entrance_payload["title"], "导入风险估算器")
        self.assertIn("cancel_without_side_effects", entrance_payload["owner_actions"])
        self.assertIn("split_batch", entrance_payload["owner_actions"])
        self.assertIn("skip_high_risk", entrance_payload["owner_actions"])
        self.assertIn("review_later", entrance_payload["owner_actions"])
        self.assertNotIn("# IDS v0.1 STAGE-019 Entry Contract", serialized)
        self.assertNotIn("raw_payload", serialized)
        self.assertTrue(report["does_not_parse_body_text"])
        self.assertTrue(report["does_not_start_ocr"])
        self.assertTrue(report["does_not_create_embeddings"])
        self.assertTrue(report["does_not_build_index"])
        self.assertTrue(report["does_not_start_import"])
        self.assertTrue(report["does_not_write_database"])

    def test_phase2_blocks_ids_metadata_path_before_directory_listing_and_reports_no_side_effects(self):
        module = self._load_module()
        report = module.evaluate_import_risk_estimate(
            source_uris=["file:///Users/linzezhang/Downloads/IDS_MetaData"],
            estimated_at=PRECHECKED_AT,
        )

        self.assertEqual(report["overall_state"], "RISK_BLOCKED")
        self.assertEqual(report["risk_score_band"], "blocked")
        self.assertEqual(report["priority_hint"], "blocked")
        self.assertEqual(report["file_count_estimate"], 0)
        self.assertEqual(report["high_risk_file_count"], 0)
        self.assertIn("RISK_SOURCE_BLOCKED", report["risk_items"])
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertEqual(report["no_persistence_deltas"]["database_write_delta"], 0)

    def test_phase2_cli_returns_json_without_runtime_writes(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            shutil.copy2(ENTRY, base / "stage019-entry.md")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--source-uri",
                    base.as_uri(),
                    "--estimated-at",
                    PRECHECKED_AT,
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        report = json.loads(result.stdout)

        self.assertEqual(report["stage"], "STAGE-019")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["file_count_estimate"], 1)
        self.assertEqual(report["risk_score_band"], "low")
        self.assertEqual(report["confirmation_status"], "RISK_READY")
        self.assertTrue(report["human_product_entrance_payload"]["customer_visible"])
        self.assertEqual(report["no_persistence_deltas"]["report_write_delta"], 0)
        self.assertTrue(report["does_not_write_manifest_files"])

    def test_phase2_evidence_document_records_no_raw_data_no_phase3_no_runtime_outputs(self):
        self.assertTrue(PHASE2.is_file(), f"missing phase2 evidence: {PHASE2}")
        text = PHASE2.read_text(encoding="utf-8")

        for term in [
            "IDS-V0_1-STAGE019-P2",
            "ACC-STAGE-019",
            "check_import_risk_estimator.py",
            "human_product_entrance_payload",
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
            shutil.copy2(ENTRY, small_dir / "stage019-entry.md")
            shutil.copy2(PHASE1, small_dir / "stage019-scope.md")
            for index in range(101):
                shutil.copy2(ENTRY, large_dir / f"stage019-entry-{index:03}.md")
            shutil.copy2(ENTRY, archive_dir / "stage019-entry.md")
            (archive_dir / "owner-candidate.zip").write_bytes(b"PK\x03\x04ids-structural-archive-candidate")

            scenario_report = module.build_stage019_scenario_report(
                scenario_sources={
                    "empty_directory": {"source_uris": [empty_dir.as_uri()]},
                    "small_directory": {"source_uris": [small_dir.as_uri()]},
                    "large_directory": {"source_uris": [large_dir.as_uri()]},
                    "offline_drive": {"source_uris": [small_dir.as_uri()], "drive_state": "offline"},
                    "archive_present": {"source_uris": [archive_dir.as_uri()]},
                    "insufficient_space": {"source_uris": [small_dir.as_uri()], "available_space_bytes": 1},
                },
                estimated_at=PRECHECKED_AT,
                batch_size=50,
            )

        self.assertEqual(scenario_report["schema_version"], "ids.stage019.import_risk_estimator.scenario_validation.v1")
        self.assertEqual(scenario_report["stage"], "STAGE-019")
        self.assertEqual(scenario_report["phase"], "Phase 3")
        self.assertEqual(scenario_report["acceptance_id"], "ACC-STAGE-019")
        self.assertEqual(scenario_report["validation_state"], "SCENARIO_VALIDATION_PASSED")
        self.assertTrue(scenario_report["required_scenarios_covered"])
        self.assertEqual(scenario_report["scenario_count"], 6)

        scenarios = scenario_report["scenario_results"]
        self.assertEqual(scenarios["empty_directory"]["risk_estimate"]["risk_score_band"], "low")
        self.assertEqual(scenarios["small_directory"]["risk_estimate"]["risk_score_band"], "low")
        self.assertIn("RISK_LARGE_BATCH_PRESENT", scenarios["large_directory"]["risk_estimate"]["risk_items"])
        self.assertGreater(scenarios["large_directory"]["operator_decision_plan"]["batch_plan"]["batch_count"], 1)
        self.assertEqual(scenarios["offline_drive"]["risk_estimate"]["overall_state"], "RISK_BLOCKED")
        self.assertIn("RISK_SUSPICIOUS_ARCHIVE_PRESENT", scenarios["archive_present"]["risk_estimate"]["risk_items"])
        self.assertEqual(scenarios["insufficient_space"]["risk_estimate"]["overall_state"], "RISK_BLOCKED")
        self.assertIn("RISK_INSUFFICIENT_SPACE", scenarios["insufficient_space"]["risk_estimate"]["risk_items"])

        for key in [
            "actual_parse_jobs_started",
            "actual_ocr_jobs_started",
            "actual_embedding_jobs_started",
            "actual_index_jobs_started",
            "actual_import_jobs_started",
        ]:
            self.assertEqual(scenario_report["processing_guard"][key], 0)

    def test_phase3_operator_decision_plan_supports_save_cancel_split_and_skip_without_persistence(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            docs = base / "operator"
            docs.mkdir()
            shutil.copy2(ENTRY, docs / "stage019-entry.md")
            shutil.copy2(PHASE1, docs / "stage019-scope.md")
            (docs / "scan-page.png").write_bytes(b"\x89PNG\r\n\x1a\nids-structural-scan-candidate")

            risk_report = module.evaluate_import_risk_estimate(
                source_uris=[docs.as_uri()],
                estimated_at=PRECHECKED_AT,
            )
            decision = module.build_risk_operator_decision_plan(risk_report, batch_size=2)

        self.assertEqual(decision["schema_version"], "ids.stage019.import_risk_estimator.operator_decision.v1")
        self.assertEqual(decision["stage"], "STAGE-019")
        self.assertEqual(decision["phase"], "Phase 3")
        self.assertEqual(decision["save_contract"]["state"], "RISK_RESULT_SERIALIZABLE")
        self.assertTrue(decision["save_contract"]["can_save_result"])
        self.assertFalse(decision["save_contract"]["persisted_by_helper"])
        self.assertEqual(decision["cancel_contract"]["state"], "RISK_CANCEL_READY")
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
            "IDS-V0_1-STAGE019-P3",
            "ACC-STAGE-019",
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

    def test_phase4_owner_feedback_summary_contains_sample_risks_uncertainty_failure_and_rollback(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            docs = base / "feedback"
            docs.mkdir()
            shutil.copy2(ENTRY, docs / "stage019-entry.md")
            shutil.copy2(PHASE1, docs / "stage019-scope.md")
            (docs / "owner-candidate.zip").write_bytes(b"PK\x03\x04ids-structural-archive-candidate")
            (docs / "unknown-format.weird").write_bytes(b"ids-structural-unknown-format-candidate")

            risk_report = module.evaluate_import_risk_estimate(
                source_uris=[docs.as_uri()],
                estimated_at=PRECHECKED_AT,
                available_space_bytes=1,
            )
            decision = module.build_risk_operator_decision_plan(risk_report, batch_size=2)
            feedback = module.build_owner_feedback_summary(
                risk_report,
                decision,
                feedback_at=PRECHECKED_AT,
            )

        self.assertEqual(feedback["schema_version"], "ids.stage019.import_risk_estimator.owner_feedback.v1")
        self.assertEqual(feedback["stage"], "STAGE-019")
        self.assertEqual(feedback["phase"], "Phase 4")
        self.assertEqual(feedback["acceptance_id"], "ACC-STAGE-019")
        self.assertEqual(feedback["entrance"], "人类产品入口 + IDS 系统运营入口")
        self.assertTrue(feedback["customer_visible"])
        self.assertEqual(feedback["report_sample"]["overall_state"], "RISK_BLOCKED")
        self.assertEqual(feedback["report_sample"]["file_count_estimate"], 4)
        self.assertIn("RISK_SUSPICIOUS_ARCHIVE_PRESENT", feedback["risk_checklist"])
        self.assertIn("RISK_UNKNOWN_FORMAT_PRESENT", feedback["risk_checklist"])
        self.assertIn("RISK_INSUFFICIENT_SPACE", feedback["risk_checklist"])
        self.assertEqual(feedback["report_sample"]["human_product_entrance_payload"]["title"], "导入风险估算器")
        flow_text = "\n".join(feedback["confirmation_flow_log"])
        self.assertIn("保存风险估算结果", flow_text)
        self.assertIn("取消", flow_text)
        self.assertIn("分批", flow_text)
        self.assertIn("跳过高风险文件", flow_text)
        self.assertIn("owner 确认后才进入批量处理", flow_text)
        self.assertGreaterEqual(len(feedback["uncertainty_notes"]), 3)
        self.assertIn("RISK_DRIVE_OFFLINE", feedback["failure_explanations"])
        self.assertIn("RISK_SOURCE_BLOCKED", feedback["failure_explanations"])
        self.assertIn("RISK_INSUFFICIENT_SPACE", feedback["failure_explanations"])
        self.assertIn("RISK_SUSPICIOUS_ARCHIVE_PRESENT", feedback["failure_explanations"])
        self.assertIn("RISK_UNKNOWN_FORMAT_PRESENT", feedback["failure_explanations"])
        self.assertIn("RISK_OVERSIZED_FILE_PRESENT", feedback["failure_explanations"])
        self.assertTrue(any("回滚" in step for step in feedback["rollback_steps"]))
        self.assertFalse(feedback["sample_persistence"]["persisted_by_helper"])
        self.assertEqual(feedback["no_persistence_deltas"]["database_write_delta"], 0)

    def test_phase4_owner_feedback_serializes_without_raw_body_or_runtime_writes(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            docs = base / "owner"
            docs.mkdir()
            shutil.copy2(ENTRY, docs / "stage019-entry.md")

            risk_report = module.evaluate_import_risk_estimate(
                source_uris=[docs.as_uri()],
                estimated_at=PRECHECKED_AT,
            )
            decision = module.build_risk_operator_decision_plan(risk_report, batch_size=50)
            feedback = module.build_owner_feedback_summary(
                risk_report,
                decision,
                feedback_at=PRECHECKED_AT,
            )

        serialized = json.dumps(feedback, ensure_ascii=False)

        self.assertNotIn("# IDS v0.1 STAGE-019 Entry Contract", serialized)
        self.assertNotIn("raw_payload", serialized)
        self.assertTrue(feedback["does_not_parse_body_text"])
        self.assertTrue(feedback["does_not_start_ocr"])
        self.assertTrue(feedback["does_not_create_embeddings"])
        self.assertTrue(feedback["does_not_build_index"])
        self.assertTrue(feedback["does_not_start_import"])
        self.assertTrue(feedback["does_not_write_database"])

    def test_phase4_closeout_document_records_delivery_no_raw_data_no_stage020(self):
        self.assertTrue(PHASE4.is_file(), f"missing phase4 closeout: {PHASE4}")
        text = PHASE4.read_text(encoding="utf-8")

        for term in [
            "IDS-V0_1-STAGE019-P4",
            "ACC-STAGE-019",
            "预检报告样例",
            "风险清单",
            "用户确认流程日志",
            "估算不确定性",
            "失败解释文案",
            "回滚方式",
            "build_owner_feedback_summary",
            "不解析正文",
            "不启动 OCR",
            "不启动 Embedding",
            "不建立索引",
            "不启动实际导入",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "NO_STAGE020",
        ]:
            with self.subTest(term=term):
                self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
