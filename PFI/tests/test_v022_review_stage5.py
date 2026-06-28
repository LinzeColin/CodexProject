from __future__ import annotations

import importlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestV022ReviewStage5(unittest.TestCase):
    def _stage5_module(self):
        try:
            return importlib.import_module("pfi_v02.stage_v022_ledger_taxonomy")
        except ModuleNotFoundError as exc:
            self.fail(f"Stage 5 ledger taxonomy module is missing: {exc}")

    def test_taxonomy_validator_rejects_non_single_primary_category(self) -> None:
        module = self._stage5_module()
        taxonomy = [dict(row) for row in module.build_stage5_consumption_taxonomy()]
        taxonomy[0] = dict(taxonomy[0], primary_category_per_transaction=2)

        validation = module.validate_stage5_taxonomy_constraints(taxonomy)

        self.assertEqual(validation["status"], "失败")
        self.assertIn("primary_category_per_transaction", validation["violations"])

    def test_taxonomy_validator_exposes_future_merge_to_ten_or_fewer_groups(self) -> None:
        module = self._stage5_module()
        validation = module.validate_stage5_taxonomy_constraints()

        self.assertEqual(validation["future_merge_target_max_l1"], 10)
        self.assertLessEqual(validation["future_merge_l1_count"], 10)
        self.assertIn("生活必要", validation["future_merge_groups"])
        self.assertIn("可选消费", validation["future_merge_groups"])
        self.assertTrue(validation["multi_dimensional_analysis_uses_tags"])

    def test_stage5_contract_and_parameter_catalog_record_review_guardrails(self) -> None:
        governance = importlib.import_module("pfi_v02.stage_v022_database_governance")
        contract = governance.build_v022_stage5_contract()
        policy = contract["consumption_taxonomy_policy"]

        self.assertEqual(policy["future_merge_target_max_l1"], 10)
        self.assertTrue(policy["multi_dimensional_analysis_uses_tags"])
        self.assertLessEqual(policy["validation"]["future_merge_l1_count"], 10)

        catalog = governance.load_v022_parameter_catalog(ROOT / "config" / "pfi_parameters.yaml")
        categories = catalog["parameters"]["consumption_categories"]
        self.assertEqual(categories["future_merge_target_max_l1"]["value"], 10)
        self.assertTrue(categories["multi_dimensional_analysis_uses_tags"]["value"])
        self.assertEqual(categories["default_taxonomy"]["validation"]["future_merge_target_max_l1"], 10)
        self.assertLessEqual(categories["default_taxonomy"]["validation"]["future_merge_l1_count"], 10)

    def test_stage5_review_report_records_fixes_acceptance_stop_conditions_and_validation(self) -> None:
        report = ROOT / "docs" / "pfi_v022" / "reviews" / "STAGE5_REVIEW_20260628.md"
        self.assertTrue(report.exists(), "Stage 5 复审修复报告缺失")
        text = report.read_text(encoding="utf-8")

        for required in (
            "v0.2.2 Stage 5 复审并解决",
            "本轮只复审解决 Stage 5",
            "不复审 Stage 6-13",
            "真实 8501 UIUX 入口阻断已复验关闭",
            "上线阻塞项：1",
            "UIUX_REAL_ENTRY_BLOCKER_20260628.md",
            "TEST_DATA_AUDIT_STAGE5_20260628.md",
            "/tmp/pfi_uiux_recheck_stage5_fixed2/summary.json",
            "桌面和移动均为 iframe=1、15/15 一级入口可见且可点击",
            "S5-P1-T1",
            "S5-P1-T2",
            "S5-P2-T1",
            "S5-P2-T2",
            "S5-P2-T3",
            "S5-P3-T1",
            "S5-P3-T2",
            "S5-P3-T3",
            "S5-P3-T4",
            "修复 1：分类验证真正检查每笔交易只有一个主分类",
            "修复 2：补齐后续压缩到 10 类以内的机器验收字段",
            "事件类型不足以表达真实资金流时停止",
            "影响口径缺失时停止",
            "投资入金未计入消费总流出时停止",
            "生活消费被投资入金污染时停止",
            "只显示一个消费数字导致误解时停止",
            "分类超过限制时停止",
            "后续无法合并分类时停止",
            "tests/test_v022_review_stage5.py",
            "tests/test_v022_stage5_ledger_taxonomy.py",
            "src/pfi_v02/stage_v022_ledger_taxonomy.py",
            "config/pfi_parameters.yaml",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_stage5_review_records_real_entry_and_test_data_blockers(self) -> None:
        uiux_blocker = ROOT / "docs" / "pfi_v022" / "reviews" / "UIUX_REAL_ENTRY_BLOCKER_20260628.md"
        test_data_audit = ROOT / "docs" / "pfi_v022" / "reviews" / "TEST_DATA_AUDIT_STAGE5_20260628.md"
        self.assertTrue(uiux_blocker.exists(), "真实入口 UIUX 阻断记录缺失")
        self.assertTrue(test_data_audit.exists(), "测试/样例/模拟数据审计记录缺失")

        uiux_text = uiux_blocker.read_text(encoding="utf-8")
        for required in (
            "http://127.0.0.1:8501",
            "移动 390x844",
            "最终复验更新",
            "/tmp/pfi_uiux_recheck_stage5_fixed2/summary.json",
            "搜索结果一次 Escape 后关闭",
            "真实 8501 UIUX 入口阻断：已关闭",
            "移动端一级入口不可见：已关闭",
            "PFI/web/index.html",
            "PFI/web/app/shell.js",
            "PFI/src/pfi_os/app/streamlit_app.py",
        ):
            with self.subTest(uiux_required=required):
                self.assertIn(required, uiux_text)

        audit_text = test_data_audit.read_text(encoding="utf-8")
        for required in (
            "175 个文件、604 处命中",
            "完整 `pytest tests` 只能作为 legacy regression 信号",
            "不新增任何虚构账单、虚构交易、虚构持仓",
            "MetaDatabase",
        ):
            with self.subTest(audit_required=required):
                self.assertIn(required, audit_text)


if __name__ == "__main__":
    unittest.main()
