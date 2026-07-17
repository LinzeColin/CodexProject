from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s19_p3_tax_policy_reporting as builder
from KMFA.tools import v015_s19_p3_tax_policy_reporting as subject


MODEL_ID = "MOD-KMFA-TAX-POLICY-REPORTING-001"
FORMULA_ID = "FORM-KMFA-V015-S19-P3-TAX-POLICY-REPORTING-001"


class TaxPolicyReportingGovernanceTests(unittest.TestCase):
    def test_project_mirrors_track_only_s19_p3(self) -> None:
        common = (
            subject.RUN_PHASE_ID, subject.TASK_ID, subject.ACCEPTANCE_ID,
            "governance_model_count: 19", "active_formula_count: 391",
            "active_parameter_count: 2340", 'current_parameter_range: "PARAM-KMFA-2706..2725"',
            "stage_execution_percentage: 100", "s19_p3_started: true",
            "s19_p3_tax_review_invoice_count: 4", "s19_p3_policy_report_count: 3",
            "s19_p3_review_basis_count: 12",
            "s19_p3_formal_filing_conclusion_count: 0",
            "s19_p3_formal_eligibility_conclusion_count: 0",
            "s19_p3_unauthorized_review_success_count: 0",
            "s19_stage_review_started: false", "github_upload_performed: false",
            "app_reinstall_performed: false",
        )
        file_specific = {
            "docs/governance/project.yaml": (
                "s19_p3_professional_role_count: 2", "s19_p3_review_update_count: 0",
                "s19_p3_review_delete_count: 0",
            ),
            "metadata/project/project.yaml": (
                "s19_p3_professional_role_count: 2", "s19_p3_review_update_count: 0",
                "s19_p3_review_delete_count: 0",
            ),
            "docs/governance/roadmap.yaml": (
                "s19_p3_professional_review_role_count: 2",
                "s19_p3_review_event_update_count: 0",
                "s19_p3_review_event_delete_count: 0",
            ),
        }
        for relative, specific in file_specific.items():
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (*common, *specific):
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
            and 2706 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2725
        ]
        self.assertEqual(len(selected), 20)
        self.assertTrue(all(
            row["model_id"] == MODEL_ID and row["formula_id"] == FORMULA_ID
            and row["status"] == "active" and row["fact_level"] == "EXTRACTED"
            for row in selected
        ))
        for token in (
            FORMULA_ID, "tax_review_invoice_count == 4", "policy_report_count == 3",
            "professional_review_role_count == 2", "review_basis_count == 12",
            "formal_filing_conclusion_count == 0", "formal_eligibility_conclusion_count == 0",
            "unauthorized_review_success_count == 0", "review_event_update_count == 0",
            "review_event_delete_count == 0", "public_check_count == 72",
            "raw_root_access_count == 0",
        ):
            self.assertIn(token, formula)
        for text in (model, mirror):
            self.assertIn(MODEL_ID, text)
            self.assertIn("kmfa_v015_s19_p3_tax_policy_reporting:", text)

    def test_traceability_version_assurance_and_spec_are_current(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        trace = (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        version = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        spec = (governance / "MODEL_SPEC.md").read_text(encoding="utf-8")
        self.assertIn("REQ-KMFA-V015-S19-P3-TAX-POLICY-REPORTING", trace)
        self.assertIn("PARAM-KMFA-2706;PARAM-KMFA-2707", trace)
        self.assertIn(f'{MODEL_ID}: "{subject.VERSION}"', version)
        self.assertIn(f'kmfa_v015_s19_p3_tax_policy_reporting: "{subject.VERSION}"', version)
        self.assertIn("total_active_parameters: 2340", assurance)
        self.assertIn("total_active_formulas: 391", assurance)
        self.assertIn(FORMULA_ID, spec)

    def test_human_records_and_evidence_are_plain_chinese(self) -> None:
        for relative in (
            "README.md", "HANDOFF.md", "CHANGELOG.md", "功能清单.md", "开发记录.md",
            "模型参数文件.md", "docs/governance/DEVELOPMENT_LEDGER.md",
            "docs/governance/OWNER_STATUS.md", "docs/governance/STATUS.md",
            "docs/governance/DELIVERY_PLAN.md",
        ):
            self.assertIn("S19-P3", (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8"), relative)
        self.assertIn("不计算补税", builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8"))
        self.assertIn("不能覆盖或删除", builder.USER_GUIDE_PATH.read_text(encoding="utf-8"))

    def test_action_review_and_release_boundaries_remain_closed(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        for key in (
            "raw_root_access_count", "external_network_request_count", "real_business_action_count",
            "formal_filing_conclusion_count", "formal_eligibility_conclusion_count",
            "recognition_result_promise_count", "unauthorized_review_success_count",
            "cross_company_review_leak_count", "review_event_update_count",
            "review_event_delete_count",
        ):
            self.assertEqual(manifest[key], 0, key)
        self.assertFalse(manifest["s19_stage_review_started"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
