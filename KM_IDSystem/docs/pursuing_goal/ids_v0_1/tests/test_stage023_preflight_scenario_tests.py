from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE023_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE023_PHASE1_SCOPE_BOUNDARY.md"
BATCH_LOCK = PURSUE_ROOT / "BATCH021_030_UPLOAD_LOCK.yaml"


class Stage023PreflightScenarioTestsPhase1Tests(unittest.TestCase):
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

    def test_batch021_030_lock_tracks_current_stage023_phase1_without_upload_permission(self):
        self.assertTrue(BATCH_LOCK.is_file(), f"missing batch lock: {BATCH_LOCK}")
        text = BATCH_LOCK.read_text(encoding="utf-8")

        required_terms = [
            'batch_id: "IDS-V0_1-BATCH-021-030"',
            'status: "stage023_phase1_in_progress"',
            'STAGE-021:',
            'STAGE-022:',
            'STAGE-023:',
            'status: "completed_local"',
            'status: "in_progress"',
            'current_task_id: "IDS-V0_1-STAGE023-P1"',
            'acceptance_id: "ACC-STAGE-023"',
            'acceptance_status: "phase1_scope_boundary_defined"',
            'next_gate: "IDS-STAGE023-P2-GATE"',
            'next_allowed_task_id: "IDS-V0_1-STAGE023-P2"',
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
