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
        ]
        self.assertTrue(
            any(term in text for term in allowed_status_terms),
            f"batch lock did not contain an allowed STAGE-023 transition status: {allowed_status_terms}",
        )

        allowed_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE023-P1"',
            'current_task_id: "IDS-V0_1-STAGE023-P2"',
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
            'status: "in_progress"',
            'acceptance_id: "ACC-STAGE-023"',
            'push_allowed: false',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE023_PHASE1_SCOPE_BOUNDARY.md",
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
