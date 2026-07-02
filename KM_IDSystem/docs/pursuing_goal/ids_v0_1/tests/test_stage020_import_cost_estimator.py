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
ENTRY = PURSUE_ROOT / "STAGE020_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE020_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE020_PHASE2_COST_ESTIMATOR_SLICE.md"
SCRIPT = ROOT / "scripts" / "check_import_cost_estimator.py"
ESTIMATED_AT = "2026-07-02T21:34:00Z"


class Stage020ImportCostEstimatorPhase1Tests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage020_import_cost_estimator", SCRIPT)
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
            self.assertIn("STAGE-020", text)
            self.assertIn("IDS-V0_1-STAGE020-P1", text)
            self.assertIn("ACC-STAGE-020", text)
            self.assertIn("导入成本估算器", text)
            self.assertIn("人类产品入口 + IDS 系统运营入口", text)

    def test_phase1_defines_import_cost_inputs_outputs_and_owner_confirmation_boundary(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        phase1_text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "cost_estimation_request_id",
            "candidate_file_metadata",
            "storage_budget_snapshot",
            "embedding_token_estimate",
            "external_api_cost_estimate",
            "ocr_page_estimate",
            "index_size_estimate",
            "local_space_pressure",
            "cost_score_band",
            "cost_items",
            "COST_OWNER_REVIEW_REQUIRED",
            "COST_OWNER_APPROVED",
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
            "只读取元信息",
            "不解析正文",
            "不修改原始文件",
            "不启动 OCR",
            "不启动 Embedding",
            "不建立索引",
            "不启动实际导入",
            "不得读取、列出、hash、打开、复制、移动、删除、修改、dump 或扫描",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "不得使用虚构 IDS 业务数据",
            "NO_PHASE2",
        ]

        for term in forbidden_boundary_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase2_metadata_only_cost_estimator_counts_workloads_costs_priority_and_entrance(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            docs = base / "cost-input"
            docs.mkdir()
            shutil.copy2(ENTRY, docs / "stage020-entry.md")
            shutil.copy2(PHASE1, docs / "stage020-scope.md")
            (docs / "owner-candidate.zip").write_bytes(b"PK\x03\x04ids-structural-archive-candidate")
            (docs / "scan-page.png").write_bytes(b"\x89PNG\r\n\x1a\nids-structural-scan-candidate")
            (docs / "unknown-format.weird").write_bytes(b"ids-structural-unknown-format-candidate")

            report = module.evaluate_import_cost_estimate(
                source_uris=[docs.as_uri()],
                estimated_at=ESTIMATED_AT,
                available_space_bytes=10**9,
                oversized_file_threshold_bytes=1,
            )

        serialized = json.dumps(report, ensure_ascii=False)

        self.assertEqual(report["schema_version"], "ids.stage020.import_cost_estimator.v1")
        self.assertEqual(report["stage"], "STAGE-020")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-020")
        self.assertEqual(report["entrance"], "人类产品入口 + IDS 系统运营入口")
        self.assertTrue(report["customer_visible"])
        self.assertEqual(report["source_preflight_schema"], "ids.stage018.import_preflight.v1")
        self.assertEqual(report["source_risk_schema"], "ids.stage019.import_risk_estimator.v1")
        self.assertEqual(report["file_count_estimate"], 5)
        self.assertEqual(report["format_counts"][".md"], 2)
        self.assertEqual(report["format_counts"][".zip"], 1)
        self.assertEqual(report["format_counts"][".png"], 1)
        self.assertEqual(report["format_counts"][".weird"], 1)
        self.assertEqual(report["archive_candidate_count"], 1)
        self.assertEqual(report["scanned_document_candidate_count"], 1)
        self.assertEqual(report["unknown_format_count"], 1)
        self.assertGreater(report["embedding_token_estimate"]["high"], 0)
        self.assertGreaterEqual(report["ocr_page_estimate"]["high"], 1)
        self.assertGreater(report["external_api_cost_estimate"]["high"], 0)
        self.assertGreater(report["index_size_estimate"]["high_bytes"], 0)
        self.assertIn(report["local_space_pressure"], {"low", "medium", "high"})
        self.assertEqual(report["cost_score_band"], "high")
        self.assertEqual(report["confirmation_status"], "COST_OWNER_REVIEW_REQUIRED")
        self.assertIn("COST_ARCHIVE_REVIEW_REQUIRED", report["risk_items"])
        self.assertIn("COST_UNKNOWN_FORMAT_PRESENT", report["risk_items"])
        self.assertIn("COST_OVERSIZED_FILE_PRESENT", report["risk_items"])
        self.assertEqual(report["priority_hint"], "archive_review_first")
        self.assertEqual(report["cost_items"]["embedding_workload_class"], "high")
        self.assertEqual(report["cost_items"]["ocr_workload_class"], "low")
        self.assertEqual(report["cost_items"]["api_cost_class"], "low")
        entrance_payload = report["human_product_entrance_payload"]
        self.assertEqual(entrance_payload["title"], "导入成本估算器")
        self.assertIn("review_cost_before_import", entrance_payload["owner_actions"])
        self.assertIn("approve_cost_and_continue", entrance_payload["owner_actions"])
        self.assertIn("cancel_without_side_effects", entrance_payload["owner_actions"])
        self.assertTrue(entrance_payload["confirmation_required"])
        self.assertNotIn("# IDS v0.1 STAGE-020 Entry Contract", serialized)
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
        report = module.evaluate_import_cost_estimate(
            source_uris=["file:///Users/linzezhang/Downloads/IDS_MetaData"],
            estimated_at=ESTIMATED_AT,
        )

        self.assertEqual(report["overall_state"], "COST_BLOCKED")
        self.assertEqual(report["cost_score_band"], "blocked")
        self.assertEqual(report["priority_hint"], "blocked")
        self.assertEqual(report["file_count_estimate"], 0)
        self.assertEqual(report["embedding_token_estimate"]["high"], 0)
        self.assertEqual(report["external_api_cost_estimate"]["high"], 0)
        self.assertIn("COST_SOURCE_BLOCKED", report["risk_items"])
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertEqual(report["no_persistence_deltas"]["database_write_delta"], 0)

    def test_phase2_cli_returns_json_without_runtime_writes(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            shutil.copy2(ENTRY, base / "stage020-entry.md")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--source-uri",
                    base.as_uri(),
                    "--estimated-at",
                    ESTIMATED_AT,
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        report = json.loads(result.stdout)

        self.assertEqual(report["stage"], "STAGE-020")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["file_count_estimate"], 1)
        self.assertEqual(report["confirmation_status"], "COST_READY")
        self.assertTrue(report["human_product_entrance_payload"]["customer_visible"])
        self.assertEqual(report["no_persistence_deltas"]["report_write_delta"], 0)
        self.assertTrue(report["does_not_write_manifest_files"])

    def test_phase2_evidence_document_records_cost_estimator_no_raw_data_no_phase3(self):
        self.assertTrue(PHASE2.is_file(), f"missing phase2 evidence: {PHASE2}")
        text = PHASE2.read_text(encoding="utf-8")

        for term in [
            "IDS-V0_1-STAGE020-P2",
            "ACC-STAGE-020",
            "check_import_cost_estimator.py",
            "human_product_entrance_payload",
            "embedding_token_estimate",
            "external_api_cost_estimate",
            "ocr_page_estimate",
            "index_size_estimate",
            "local_space_pressure",
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
