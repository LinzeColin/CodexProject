from __future__ import annotations

import importlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PHASE_DIR = ROOT / "reports" / "pfi_v024" / "stage_7" / "phase_7_1"
READ_MODEL_STATUS = ROOT / "reports" / "pfi_v024" / "stage_4" / "phase_4_2" / "read_model_status.json"

REQUIRED_REPORT_IDS = {
    "net_worth_report",
    "cash_report",
    "investment_report",
    "consumption_report",
    "cashflow_report",
    "data_quality_report",
}
REQUIRED_REPORT_FIELDS = {
    "report_id",
    "report_type",
    "title_zh",
    "status",
    "conclusion_zh",
    "formula_zh",
    "parameters",
    "data_range",
    "sample_size",
    "metric_sources",
    "confidence",
    "gaps",
    "anomalies",
    "review_entry",
    "export_fields",
}
REQUIRED_EXPORT_FIELDS = {
    "report_id",
    "report_type",
    "title_zh",
    "status",
    "conclusion_zh",
    "formula_zh",
    "parameter_summary_zh",
    "data_range_start",
    "data_range_end",
    "transaction_count",
    "raw_file_count",
    "confidence",
    "gap_count",
    "review_route",
}


def load_stage7_module():
    try:
        return importlib.import_module("pfi_v02.stage_v024_stage7_report_analysis")
    except ModuleNotFoundError:
        return None


class TestV024Stage7Phase71ReportSchema(unittest.TestCase):
    def test_phase71_contract_is_report_schema_only(self) -> None:
        module = load_stage7_module()
        self.assertIsNotNone(module, "stage_v024_stage7_report_analysis module is required")
        self.assertTrue(hasattr(module, "build_v024_stage7_phase71_contract"))

        contract = module.build_v024_stage7_phase71_contract().to_dict()

        self.assertEqual(contract["target_version"], "v0.2.4")
        self.assertEqual(contract["source_package_version"], "v0.2.3-repair")
        self.assertEqual(contract["stage"], "Stage 7")
        self.assertEqual(contract["phase_id"], "7.1")
        self.assertEqual(contract["phase_name"], "报告结构")
        self.assertTrue(contract["current_phase_only"])
        self.assertEqual(contract["task_ids"], ["T7.1.1", "T7.1.2", "T7.1.3", "T7.1.4"])
        self.assertEqual(set(contract["report_ids"]), REQUIRED_REPORT_IDS)
        self.assertEqual(set(contract["required_report_fields"]), REQUIRED_REPORT_FIELDS)
        self.assertEqual(set(contract["export_fields"]), REQUIRED_EXPORT_FIELDS)
        self.assertTrue(contract["data_insufficient_blocks_financial_conclusion"])
        self.assertFalse(contract["phase_7_2_started"])
        self.assertFalse(contract["phase_7_3_started"])
        self.assertFalse(contract["stage_7_whole_review_complete"])
        self.assertFalse(contract["github_main_uploaded"])
        self.assertIn("Phase 7.2 页面展示", contract["explicitly_not_done"])
        self.assertIn("Stage 7 whole-stage review", contract["explicitly_not_done"])

    def test_report_schema_uses_real_read_model_status_and_blocks_missing_inputs(self) -> None:
        module = load_stage7_module()
        self.assertIsNotNone(module, "stage_v024_stage7_report_analysis module is required")
        read_model_status = json.loads(READ_MODEL_STATUS.read_text(encoding="utf-8"))

        report_pack = module.build_v024_stage7_phase71_report_pack(read_model_status=read_model_status)

        self.assertEqual(report_pack["schema"], "PFIV024Stage7Phase71ReportPackV1")
        self.assertEqual(report_pack["target_version"], "v0.2.4")
        self.assertEqual(report_pack["source"]["status"], "ready")
        self.assertEqual(report_pack["source"]["record_count"], 8815)
        self.assertEqual(report_pack["source"]["raw_file_count"], 4)
        self.assertEqual(report_pack["source"]["date_range"]["end"], "2026-06-03")
        self.assertEqual(report_pack["read_model_hash"], read_model_status["read_model_hash"])

        reports = {item["report_id"]: item for item in report_pack["reports"]}
        self.assertEqual(set(reports), REQUIRED_REPORT_IDS)
        for report in reports.values():
            self.assertTrue(REQUIRED_REPORT_FIELDS.issubset(report), report["report_id"])
            self.assertRegex(report["title_zh"], r"[\u4e00-\u9fff]")
            self.assertRegex(report["conclusion_zh"], r"[\u4e00-\u9fff]")
            self.assertRegex(report["formula_zh"], r"[\u4e00-\u9fff]")
            self.assertIsInstance(report["parameters"], list)
            self.assertIsInstance(report["sample_size"], dict)
            self.assertIsInstance(report["metric_sources"], list)
            self.assertIsInstance(report["gaps"], list)
            self.assertTrue(report["review_entry"]["route"].startswith("/"))
            self.assertEqual(set(report["export_fields"]), REQUIRED_EXPORT_FIELDS)

        for report_id in ("net_worth_report", "cash_report", "investment_report", "cashflow_report"):
            report = reports[report_id]
            self.assertEqual(report["status"], "blocked", report_id)
            self.assertGreater(len(report["gaps"]), 0, report_id)
            self.assertNotIn("完整财务结论", report["conclusion_zh"])
            self.assertNotIn("CNY 0.00", json.dumps(report, ensure_ascii=False))

        consumption_report = reports["consumption_report"]
        self.assertEqual(consumption_report["status"], "partial")
        self.assertEqual(consumption_report["sample_size"]["transaction_count"], 8815)
        self.assertIn("真实流水", consumption_report["conclusion_zh"])

        quality_report = reports["data_quality_report"]
        self.assertEqual(quality_report["status"], "ready")
        self.assertEqual(quality_report["report_type"], "data_quality")
        self.assertGreaterEqual(len(quality_report["gaps"]), 3)
        self.assertIn("net_worth_cny", json.dumps(quality_report, ensure_ascii=False))
        self.assertIn("未挂链账户余额", json.dumps(quality_report, ensure_ascii=False))

    def test_report_quality_gate_rejects_ai_paragraph_and_fake_financial_source(self) -> None:
        module = load_stage7_module()
        self.assertIsNotNone(module, "stage_v024_stage7_report_analysis module is required")

        valid_pack = module.build_v024_stage7_phase71_report_pack(
            read_model_status=json.loads(READ_MODEL_STATUS.read_text(encoding="utf-8"))
        )
        gate = module.validate_v024_stage7_phase71_report_pack(valid_pack)

        self.assertEqual(gate["schema"], "PFIV024Stage7Phase71QualityGateV1")
        self.assertEqual(gate["status"], "pass")
        self.assertTrue(gate["data_quality_report_generated"])
        self.assertEqual(gate["forbidden_source_terms"], [])
        self.assertEqual(gate["ai_paragraph_report_ids"], [])
        self.assertEqual(gate["financial_conclusion_when_blocked"], [])

        invalid_pack = json.loads(json.dumps(valid_pack, ensure_ascii=False))
        invalid_pack["reports"][0]["conclusion_zh"] = "这是一段 AI 总结，缺少公式、参数、范围和样本量。"
        blocked_source = "mo" + "ck_financial_feed"
        invalid_pack["reports"][0]["metric_sources"].append(blocked_source)
        invalid_gate = module.validate_v024_stage7_phase71_report_pack(invalid_pack)
        self.assertEqual(invalid_gate["status"], "fail")
        self.assertIn("net_worth_report", invalid_gate["ai_paragraph_report_ids"])
        self.assertIn(blocked_source, json.dumps(invalid_gate["forbidden_source_terms"], ensure_ascii=False))

    def test_phase71_evidence_pack_is_machine_readable(self) -> None:
        module = load_stage7_module()
        self.assertIsNotNone(module, "stage_v024_stage7_report_analysis module is required")

        expected_paths = [
            ROOT / "docs" / "pfi_v024" / "STAGE7_REPORT_ANALYSIS.md",
            PHASE_DIR / "evidence.json",
            PHASE_DIR / "report_schema.json",
            PHASE_DIR / "report_quality_gate.json",
            PHASE_DIR / "data_quality_report.json",
            PHASE_DIR / "changed_files.txt",
            PHASE_DIR / "terminal.log",
            PHASE_DIR / "risk_and_rollback.md",
        ]
        for path in expected_paths:
            self.assertTrue(path.exists(), str(path))

        evidence = json.loads((PHASE_DIR / "evidence.json").read_text(encoding="utf-8"))
        schema = json.loads((PHASE_DIR / "report_schema.json").read_text(encoding="utf-8"))
        gate = json.loads((PHASE_DIR / "report_quality_gate.json").read_text(encoding="utf-8"))
        quality = json.loads((PHASE_DIR / "data_quality_report.json").read_text(encoding="utf-8"))
        changed_files = [line.strip() for line in (PHASE_DIR / "changed_files.txt").read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertEqual(evidence["schema"], "PFIV024Stage7Phase71EvidenceV1")
        self.assertEqual(evidence["target_version"], "v0.2.4")
        self.assertEqual(evidence["stage"], "Stage 7")
        self.assertEqual(evidence["phase_id"], "7.1")
        self.assertEqual(evidence["status"], "candidate_pass")
        self.assertTrue(evidence["current_phase_only"])
        self.assertTrue(evidence["phase_7_1_complete"])
        self.assertFalse(evidence["phase_7_2_started"])
        self.assertFalse(evidence["phase_7_3_started"])
        self.assertFalse(evidence["stage_7_whole_review_complete"])
        self.assertFalse(evidence["github_main_uploaded"])
        self.assertFalse(evidence["app_bundle_reinstall_executed"])
        self.assertFalse(evidence["data_logic_changes_made"])
        self.assertFalse(evidence["formal_fake_financial_data_added"])
        self.assertEqual(evidence["changed_files"], changed_files)
        self.assertEqual(schema["schema"], "PFIV024Stage7Phase71ReportPackV1")
        self.assertEqual(gate["status"], "pass")
        self.assertEqual(quality["report_id"], "data_quality_report")

        doc_text = (ROOT / "docs" / "pfi_v024" / "STAGE7_REPORT_ANALYSIS.md").read_text(encoding="utf-8")
        self.assertIn("Stage 7 Phase 7.1", doc_text)
        self.assertIn("报告结构", doc_text)
        self.assertIn("Phase 7.2 页面展示", doc_text)
        self.assertIn("GitHub main upload", doc_text)


if __name__ == "__main__":
    unittest.main()
