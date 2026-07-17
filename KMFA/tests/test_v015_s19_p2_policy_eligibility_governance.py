from __future__ import annotations

import csv
import unittest

from KMFA.tools import build_v015_s19_p2_policy_eligibility as builder
from KMFA.tools import v015_s19_p2_policy_eligibility as subject


MODEL_ID = "MOD-KMFA-POLICY-ELIGIBILITY-001"
FORMULA_ID = "FORM-KMFA-V015-S19-P2-POLICY-ELIGIBILITY-001"


class PolicyEligibilityGovernanceTests(unittest.TestCase):
    def test_project_mirrors_track_only_s19_p2(self) -> None:
        common = (
            subject.RUN_PHASE_ID, subject.TASK_ID, subject.ACCEPTANCE_ID,
            "governance_model_count: 18", "active_formula_count: 390", "active_parameter_count: 2320",
            'current_parameter_range: "PARAM-KMFA-2686..2705"', "stage_execution_percentage: 67",
            "s19_p2_started: true", "s19_p2_policy_count: 6", "s19_p2_evidence_item_count: 12",
            "s19_p2_formal_eligibility_conclusion_count: 0", "s19_p2_fabricated_evidence_count: 0",
            "s19_p2_source_gate_bypass_count: 0", "s19_p3_started: false",
            "github_upload_performed: false", "app_reinstall_performed: false",
        )
        for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
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
        selected = [row for row in rows if row["parameter_id"].startswith("PARAM-KMFA-") and 2686 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2705]
        self.assertEqual(len(selected), 20)
        self.assertTrue(all(row["model_id"] == MODEL_ID and row["formula_id"] == FORMULA_ID and row["status"] == "active" and row["fact_level"] == "EXTRACTED" for row in selected))
        for token in (FORMULA_ID, "policy_count == 6", "blocked_policy_count == 1", "expired_policy_deterministic_conclusion_count == 0", "formal_eligibility_conclusion_count == 0", "fabricated_evidence_count == 0", "source_gate_bypass_count == 0", "public_check_count == 80", "raw_root_access_count == 0"):
            self.assertIn(token, formula)
        self.assertIn(MODEL_ID, model)
        for text in (model, mirror):
            self.assertIn("kmfa_v015_s19_p2_policy_eligibility:", text)

    def test_traceability_version_and_assurance_are_current(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        trace = (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        version = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        spec = (governance / "MODEL_SPEC.md").read_text(encoding="utf-8")
        self.assertIn("REQ-KMFA-V015-S19-P2-POLICY-ELIGIBILITY", trace)
        self.assertIn("PARAM-KMFA-2686;PARAM-KMFA-2687", trace)
        self.assertIn(f'{MODEL_ID}: "{subject.VERSION}"', version)
        self.assertIn(f'kmfa_v015_s19_p2_policy_eligibility: "{subject.VERSION}"', version)
        self.assertIn("total_active_parameters: 2320", assurance)
        self.assertIn("total_active_formulas: 390", assurance)
        self.assertIn(FORMULA_ID, spec)

    def test_human_records_use_plain_chinese(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S19-P2", text, relative)
        for relative in ("README.md", "HANDOFF.md", "CHANGELOG.md", "docs/governance/DEVELOPMENT_LEDGER.md", "docs/governance/OWNER_STATUS.md", "docs/governance/STATUS.md", "docs/governance/DELIVERY_PLAN.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S19-P2", text, relative)
        self.assertIn("不判断申报资格", builder.IMPLEMENTATION_REPORT_PATH.read_text(encoding="utf-8"))
        self.assertIn("没有已核验来源不能完成", builder.USER_GUIDE_PATH.read_text(encoding="utf-8"))

    def test_action_and_release_boundaries_remain_closed(self) -> None:
        manifest = builder.MANIFEST_PATH.read_text(encoding="utf-8")
        for token in ('"raw_root_access_count": 0', '"external_network_request_count": 0', '"formal_eligibility_conclusion_count": 0', '"fabricated_evidence_count": 0', '"material_packaging_assistance_count": 0', '"source_gate_bypass_count": 0', '"s19_p3_started": false', '"github_upload_performed": false', '"app_reinstall_performed": false'):
            self.assertIn(token, manifest)


if __name__ == "__main__":
    unittest.main()
