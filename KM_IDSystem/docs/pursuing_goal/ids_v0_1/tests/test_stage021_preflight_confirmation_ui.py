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

        required_terms = [
            'batch_id: "IDS-V0_1-BATCH-021-030"',
            'status: "stage021_phase2_in_progress"',
            'stage_range: "STAGE-021..STAGE-030"',
            'acceptance_range: "ACC-STAGE-021..ACC-STAGE-030"',
            'push_allowed: false',
            'current_task_id: "IDS-V0_1-STAGE021-P2"',
            'acceptance_status: "phase2_preflight_confirmation_ui_slice_complete"',
            'next_gate: "IDS-STAGE021-P3-GATE"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE021_PHASE2_PREFLIGHT_CONFIRMATION_UI_SLICE.md",
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


if __name__ == "__main__":
    unittest.main()
