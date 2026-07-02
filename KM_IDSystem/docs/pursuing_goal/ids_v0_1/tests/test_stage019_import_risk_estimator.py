from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[4]
PURSUE_ROOT = ROOT / "docs" / "pursuing_goal" / "ids_v0_1"
ENTRY = PURSUE_ROOT / "STAGE019_ENTRY_CONTRACT.md"
PHASE1 = PURSUE_ROOT / "STAGE019_PHASE1_SCOPE_BOUNDARY.md"


class Stage019ImportRiskEstimatorPhase1Tests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
