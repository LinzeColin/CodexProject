from __future__ import annotations

import csv
import unittest

from KMFA.tools import build_v015_s19_p1_tax_invoice_facts as builder
from KMFA.tools import v015_s19_p1_tax_invoice_facts as subject


MODEL_ID = "MOD-KMFA-TAX-INVOICE-001"
FORMULA_ID = "FORM-KMFA-V015-S19-P1-TAX-INVOICE-FACTS-001"


class TaxInvoiceFactsGovernanceTests(unittest.TestCase):
    def test_project_mirrors_track_only_s19_p1(self) -> None:
        common = (
            subject.RUN_PHASE_ID,
            subject.TASK_ID,
            subject.ACCEPTANCE_ID,
            "governance_model_count: 17",
            "active_formula_count: 389",
            "active_parameter_count: 2300",
            'current_parameter_range: "PARAM-KMFA-2666..2685"',
            "stage_execution_percentage: 33",
            's19_p1_started: true',
            's19_p1_tax_invoice_fact_count: 8',
            's19_p1_matched_count: 4',
            's19_p1_review_count: 4',
            's19_p1_anomaly_count: 5',
            's19_p1_unknown_rate_count: 1',
            's19_p1_rate_inference_count: 0',
            's19_p1_automatic_tax_adjustment_count: 0',
            's19_p1_project_burden_count: 3',
            's19_p1_burden_equation_difference_cents: 0',
            's19_p1_formal_filing_conclusion_count: 0',
            's19_p1_cross_company_leak_count: 0',
            's19_p1_browser_flow_count: 7',
            's19_p1_visual_evidence_count: 5',
            's19_p1_public_check_count: 64',
            's19_p1_raw_root_access_count: 0',
            's19_p2_started: false',
            'github_upload_performed: false',
            'app_reinstall_performed: false',
        )
        for relative in (
            "docs/governance/project.yaml",
            "metadata/project/project.yaml",
            "docs/governance/roadmap.yaml",
        ):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in common:
                self.assertIn(token, text, relative)

    def test_formula_model_and_parameters_are_bound(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        formula = (governance / "formula_registry.yaml").read_text(encoding="utf-8")
        model = (governance / "model_registry.yaml").read_text(encoding="utf-8")
        mirror = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        with (governance / "parameter_registry.csv").open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        selected = [
            row for row in rows
            if row["parameter_id"].startswith("PARAM-KMFA-")
            and 2666 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2685
        ]
        self.assertEqual(len(selected), 20)
        self.assertTrue(all(
            row["model_id"] == MODEL_ID
            and row["formula_id"] == FORMULA_ID
            and row["status"] == "active"
            and row["fact_level"] == "EXTRACTED"
            for row in selected
        ))
        for token in (
            FORMULA_ID,
            "tax_invoice_fact_count == 8",
            "unknown_rate_count == 1",
            "rate_inference_count == 0",
            "anomaly_count == 5",
            "automatic_tax_adjustment_count == 0",
            "burden_equation_difference_cents == 0",
            "formal_filing_conclusion_count == 0",
            "raw_root_access_count == 0",
        ):
            self.assertIn(token, formula)
        for text in (model, mirror):
            self.assertIn("kmfa_v015_s19_p1_tax_invoice_facts:", text)
            self.assertIn(MODEL_ID, text)

    def test_traceability_version_and_assurance_are_current(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        trace = (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        version = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        spec = (governance / "MODEL_SPEC.md").read_text(encoding="utf-8")
        self.assertIn("REQ-KMFA-V015-S19-P1-TAX-INVOICE-FACTS", trace)
        self.assertIn("PARAM-KMFA-2666;PARAM-KMFA-2667", trace)
        self.assertIn(f'{MODEL_ID}: "{subject.VERSION}"', version)
        self.assertIn(f'kmfa_v015_s19_p1_tax_invoice_facts: "{subject.VERSION}"', version)
        self.assertIn("total_active_parameters: 2300", assurance)
        self.assertIn("total_active_formulas: 389", assurance)
        self.assertIn(FORMULA_ID, spec)

    def test_human_records_use_plain_chinese(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S19-P1", text, relative)
        for relative in (
            "README.md", "HANDOFF.md", "CHANGELOG.md",
            "docs/governance/DEVELOPMENT_LEDGER.md",
            "docs/governance/OWNER_STATUS.md",
            "docs/governance/STATUS.md",
            "docs/governance/DELIVERY_PLAN.md",
        ):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S19-P1", text, relative)
        self.assertIn("不会自动补值", builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8"))
        self.assertIn("不是报税结果", builder.USER_GUIDE_PATH.read_text(encoding="utf-8"))

    def test_action_and_release_boundaries_remain_closed(self) -> None:
        manifest = builder.MANIFEST_PATH.read_text(encoding="utf-8")
        for token in (
            '"raw_root_access_count": 0',
            '"live_source_read_count": 0',
            '"external_network_request_count": 0',
            '"rate_inference_count": 0',
            '"automatic_tax_adjustment_count": 0',
            '"formal_filing_conclusion_count": 0',
            '"invoice_issue_count": 0',
            '"tax_filing_count": 0',
            '"s19_p2_started": false',
            '"github_upload_performed": false',
            '"app_reinstall_performed": false',
        ):
            self.assertIn(token, manifest)


if __name__ == "__main__":
    unittest.main()
