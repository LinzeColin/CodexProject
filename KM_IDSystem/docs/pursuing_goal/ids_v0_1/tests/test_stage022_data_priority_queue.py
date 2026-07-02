from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE022_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE022_PHASE1_SCOPE_BOUNDARY.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"


class Stage022DataPriorityQueuePhase1Tests(unittest.TestCase):
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

        required_terms = [
            'batch_id: "IDS-V0_1-BATCH-021-030"',
            'status: "stage022_phase1_in_progress"',
            'stage_range: "STAGE-021..STAGE-030"',
            'acceptance_range: "ACC-STAGE-021..ACC-STAGE-030"',
            'push_allowed: false',
            'current_task_id: "IDS-V0_1-STAGE022-P1"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'next_gate: "IDS-STAGE022-P2-GATE"',
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_ENTRY_CONTRACT.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE022_PHASE1_SCOPE_BOUNDARY.md",
            "KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage022_data_priority_queue.py",
            "/Users/linzezhang/Downloads/IDS_MetaData",
            "read-only; do not modify, delete, move, scan, dump, hash, or copy raw database content",
        ]

        for term in required_terms:
            with self.subTest(term=term):
                self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
