from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s20_p2_confirmation_workbench as builder
from KMFA.tools import v015_s20_p2_confirmation_workbench as subject


MODEL_ID = "MOD-KMFA-ACTION-001"
FORMULA_ID = "FORM-KMFA-V015-S20-P2-CONFIRMATION-WORKBENCH-001"


class ConfirmationWorkbenchGovernanceTests(unittest.TestCase):
    def test_project_mirrors_track_only_s20_p2(self) -> None:
        common = (
            subject.RUN_PHASE_ID, subject.TASK_ID, subject.ACCEPTANCE_ID,
            "governance_model_count: 19", "active_formula_count: 394",
            "active_parameter_count: 2400", 'current_parameter_range: "PARAM-KMFA-2766..2785"',
            "stage_execution_percentage: 67", "s20_p1_started: true",
            's20_p1_acceptance_status: "PASSED"', "s20_p2_started: true",
            "s20_p2_business_issue_count: 6", "s20_p2_default_issue_count: 5",
            "s20_p2_governance_log_count_in_main_list: 0", "s20_p2_detail_count: 5",
            "s20_p2_high_impact_without_preview_success_count: 0",
            "s20_p2_raw_source_fact_mutation_count: 0", "s20_p3_started: false",
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
        selected = [row for row in rows if row["parameter_id"].startswith("PARAM-KMFA-") and 2766 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2785]
        self.assertEqual(len(selected), 20)
        self.assertTrue(all(row["model_id"] == MODEL_ID and row["formula_id"] == FORMULA_ID and row["status"] == "active" and row["fact_level"] == "EXTRACTED" for row in selected))
        for token in (
            FORMULA_ID, "business_issue_count == 6", "default_issue_count == 5",
            "governance_log_count_in_main_list == 0", "detail_count == 5",
            "high_impact_without_preview_success_count == 0", "public_check_count == 55",
            "browser_flow_count == 7", "raw_source_fact_mutation_count == 0;0;0",
        ):
            self.assertIn(token, formula)
        for text in (model, mirror):
            self.assertIn(MODEL_ID, text)
            self.assertIn("kmfa_v015_s20_p2_confirmation_workbench:", text)

    def test_traceability_version_assurance_and_spec_are_current(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        trace = (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8")
        version = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        spec = (governance / "MODEL_SPEC.md").read_text(encoding="utf-8")
        self.assertIn("REQ-KMFA-V015-S20-P2-CONFIRMATION-WORKBENCH", trace)
        self.assertIn("PARAM-KMFA-2766;PARAM-KMFA-2767", trace)
        self.assertIn(f'{MODEL_ID}: "{subject.VERSION}"', version)
        self.assertIn(f'kmfa_v015_s20_p2_confirmation_workbench: "{subject.VERSION}"', version)
        self.assertIn("total_active_parameters: 2400", assurance)
        self.assertIn("total_active_formulas: 394", assurance)
        self.assertIn(FORMULA_ID, spec)

    def test_human_records_are_plain_chinese_and_boundaries_closed(self) -> None:
        for relative in (
            "README.md", "HANDOFF.md", "CHANGELOG.md", "功能清单.md", "开发记录.md", "模型参数文件.md",
            "docs/governance/DEVELOPMENT_LEDGER.md", "docs/governance/OWNER_STATUS.md",
            "docs/governance/STATUS.md", "docs/governance/DELIVERY_PLAN.md",
        ):
            self.assertIn("S20-P2", (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8"), relative)
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        for key in (
            "raw_root_access_count", "raw_write_count", "source_value_edit_count", "fact_layer_mutation_count",
            "high_impact_without_preview_success_count", "unauthorised_action_success_count",
            "s20_p3_recalculation_count", "report_refresh_count", "external_network_request_count", "real_business_action_count",
        ):
            self.assertEqual(manifest[key], 0, key)
        self.assertFalse(manifest["s20_p3_started"])
        self.assertFalse(manifest["github_upload_performed"])
        self.assertFalse(manifest["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
