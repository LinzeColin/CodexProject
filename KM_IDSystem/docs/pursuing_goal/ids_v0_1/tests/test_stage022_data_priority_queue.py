import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE022_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE022_PHASE1_SCOPE_BOUNDARY.md"
PHASE2 = PURSUE_ROOT / "STAGE022_PHASE2_DATA_PRIORITY_QUEUE_SLICE.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"
SCRIPT = ROOT / "scripts" / "check_data_priority_queue.py"
QUEUED_AT = "2026-07-02T23:40:12Z"


class Stage022DataPriorityQueuePhase1Tests(unittest.TestCase):
    def _load_module(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        spec = importlib.util.spec_from_file_location("stage022_data_priority_queue", SCRIPT)
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
            "STAGE-022",
            "IDS-V0_1-STAGE022-P1",
            "ACC-STAGE-022",
            "数据优先级队列",
            "P0/P1/P2/P3",
            "人类产品入口 + IDS 系统运营入口",
            "IDS_v0_1_Final_Chinese_Revised/stages/STAGE-022_数据优先级队列.md",
            "4a1c62ec99fec7e267737bdd3306a2b568f06bf682b33b32ec66615bb2760c0b",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, combined)

    def test_phase1_defines_priority_queue_inputs_outputs_risks_costs_and_confirmation_states(self):
        self.assertTrue(PHASE1.is_file(), f"missing phase1 boundary: {PHASE1}")
        text = PHASE1.read_text(encoding="utf-8")

        required_terms = [
            "priority_queue_request_id",
            "input_directory_uri",
            "source_preflight_snapshot_ref",
            "preflight_summary_snapshot",
            "risk_summary_snapshot",
            "cost_summary_snapshot",
            "priority_signal_snapshot",
            "priority_queue_summary",
            "priority_buckets",
            "priority_class",
            "priority_reason_codes",
            "owner_confirmation_context",
            "P0_CRITICAL_ENGINEERING_DATA",
            "P1_HIGH_VALUE_ENGINEERING_DATA",
            "P2_SUPPORTING_ENGINEERING_DATA",
            "P3_LOW_VALUE_OR_DEFERRED_DATA",
            "PRIORITY_QUEUE_OWNER_REVIEW_REQUIRED",
            "PRIORITY_QUEUE_READY",
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

    def test_batch021_030_lock_tracks_current_stage022_phase_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")

        allowed_status_terms = [
            'status: "stage022_phase1_in_progress"',
            'status: "stage022_phase2_in_progress"',
        ]
        self.assertTrue(
            any(term in text for term in allowed_status_terms),
            f"batch lock did not contain an allowed STAGE-022 transition status: {allowed_status_terms}",
        )

        allowed_task_terms = [
            'current_task_id: "IDS-V0_1-STAGE022-P1"',
            'current_task_id: "IDS-V0_1-STAGE022-P2"',
        ]
        self.assertTrue(
            any(term in text for term in allowed_task_terms),
            f"batch lock did not contain an allowed STAGE-022 current task: {allowed_task_terms}",
        )

        required_terms = [
            'batch_id: "IDS-V0_1-BATCH-021-030"',
            'stage_range: "STAGE-021..STAGE-030"',
            'acceptance_range: "ACC-STAGE-021..ACC-STAGE-030"',
            'push_allowed: false',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage022_data_priority_queue.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def test_phase2_metadata_only_priority_queue_payload_ranks_files_and_shows_human_product_payload(self):
        module = self._load_module()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "priority-input"
            base.mkdir()
            shutil.copy2(ENTRY, base / "critical-repair-plan.md")
            shutil.copy2(PHASE1, base / "equipment-reference.csv")
            shutil.copy2(ENTRY, base / "meeting-note.txt")
            (base / "scan-page.png").write_bytes(b"\x89PNG\r\n\x1a\nids-structural-scan-candidate")
            (base / "owner-candidate.zip").write_bytes(b"PK\x03\x04ids-structural-archive-candidate")
            (base / "unknown-format.weird").write_bytes(b"ids-structural-unknown-format-candidate")

            report = module.evaluate_data_priority_queue(
                source_uris=[base.as_uri()],
                queued_at=QUEUED_AT,
                available_space_bytes=10**9,
                oversized_file_threshold_bytes=10**9,
            )

        serialized = json.dumps(report, ensure_ascii=False)

        self.assertEqual(report["schema_version"], "ids.stage022.data_priority_queue.v1")
        self.assertEqual(report["stage"], "STAGE-022")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["acceptance_id"], "ACC-STAGE-022")
        self.assertEqual(report["entrance"], "人类产品入口 + IDS 系统运营入口")
        self.assertTrue(report["customer_visible"])
        self.assertEqual(report["source_cost_schema"], "ids.stage020.import_cost_estimator.v1")
        self.assertEqual(report["file_count_estimate"], 6)
        self.assertEqual(report["format_counts"][".md"], 1)
        self.assertEqual(report["format_counts"][".csv"], 1)
        self.assertEqual(report["archive_candidate_count"], 1)
        self.assertEqual(report["scanned_document_candidate_count"], 1)
        self.assertEqual(report["unknown_format_count"], 1)
        self.assertGreater(report["embedding_token_estimate"]["high"], 0)
        self.assertGreaterEqual(report["ocr_page_estimate"]["high"], 1)
        self.assertGreater(report["external_api_cost_estimate"]["high"], 0)
        self.assertGreater(report["index_size_estimate"]["high_bytes"], 0)
        self.assertEqual(report["confirmation_status"], "PRIORITY_QUEUE_OWNER_REVIEW_REQUIRED")
        self.assertIn(report["priority_hint"], {"process_p0_first_with_owner_review", "owner_review_required"})
        self.assertEqual(report["priority_bucket_order"], ["P0", "P1", "P2", "P3"])
        self.assertGreaterEqual(report["priority_buckets"]["P0"]["count"], 1)
        self.assertGreaterEqual(report["priority_buckets"]["P1"]["count"], 1)
        self.assertGreaterEqual(report["priority_buckets"]["P2"]["count"], 1)
        self.assertGreaterEqual(report["priority_buckets"]["P3"]["count"], 2)
        self.assertIn("PRIORITY_DEFERRED_RISK", report["priority_buckets"]["P3"]["reason_codes"])
        self.assertIn("COST_ARCHIVE_REVIEW_REQUIRED", report["risk_items"])
        self.assertIn("COST_UNKNOWN_FORMAT_PRESENT", report["risk_items"])
        payload = report["human_product_entrance_payload"]
        self.assertEqual(payload["title"], "数据优先级队列")
        self.assertTrue(payload["customer_visible"])
        self.assertTrue(payload["confirmation_required"])
        self.assertGreaterEqual(len(payload["summary_cards"]), 8)
        self.assertIn("review_priority_queue", payload["owner_actions"])
        self.assertIn("approve_priority_queue", payload["owner_actions"])
        self.assertIn("defer_p3_items", payload["owner_actions"])
        self.assertIn("确认前不会启动解析、OCR、Embedding、索引或实际导入", payload["message"])
        self.assertEqual(report["ui_component_contract"]["component_name"], "DataPriorityQueuePanel")
        self.assertNotIn("# IDS v0.1 STAGE-022 Entry Contract", serialized)
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
        report = module.evaluate_data_priority_queue(
            source_uris=["file:///Users/linzezhang/Downloads/IDS_MetaData"],
            queued_at=QUEUED_AT,
        )

        self.assertEqual(report["overall_state"], "PRIORITY_QUEUE_BLOCKED")
        self.assertEqual(report["confirmation_status"], "PRIORITY_QUEUE_BLOCKED")
        self.assertEqual(report["file_count_estimate"], 0)
        self.assertEqual(report["priority_hint"], "blocked")
        self.assertEqual(report["priority_buckets"]["P0"]["count"], 0)
        self.assertEqual(report["priority_buckets"]["P3"]["count"], 0)
        self.assertIn("COST_SOURCE_BLOCKED", report["risk_items"])
        self.assertTrue(report["does_not_read_raw_metadata"])
        self.assertEqual(report["no_persistence_deltas"]["database_write_delta"], 0)

    def test_phase2_cli_returns_json_payload_without_runtime_writes(self):
        self.assertTrue(SCRIPT.exists(), f"missing script: {SCRIPT}")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            shutil.copy2(ENTRY, base / "critical-repair-plan.md")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--source-uri",
                    base.as_uri(),
                    "--queued-at",
                    QUEUED_AT,
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        report = json.loads(result.stdout)

        self.assertEqual(report["stage"], "STAGE-022")
        self.assertEqual(report["phase"], "Phase 2")
        self.assertEqual(report["file_count_estimate"], 1)
        self.assertIn(report["confirmation_status"], {"PRIORITY_QUEUE_READY", "PRIORITY_QUEUE_OWNER_REVIEW_REQUIRED"})
        self.assertTrue(report["human_product_entrance_payload"]["customer_visible"])
        self.assertEqual(report["no_persistence_deltas"]["report_write_delta"], 0)
        self.assertTrue(report["does_not_write_manifest_files"])

    def test_phase2_evidence_document_records_priority_queue_slice_no_raw_data_no_phase3(self):
        self.assertTrue(PHASE2.is_file(), f"missing phase2 evidence: {PHASE2}")
        text = PHASE2.read_text(encoding="utf-8")

        for term in [
            "IDS-V0_1-STAGE022-P2",
            "ACC-STAGE-022",
            "check_data_priority_queue.py",
            "human_product_entrance_payload",
            "DataPriorityQueuePanel",
            "P0_CRITICAL_ENGINEERING_DATA",
            "P1_HIGH_VALUE_ENGINEERING_DATA",
            "P2_SUPPORTING_ENGINEERING_DATA",
            "P3_LOW_VALUE_OR_DEFERRED_DATA",
            "process_p0_first_with_owner_review",
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
