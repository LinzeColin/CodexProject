from __future__ import annotations

import csv
import unittest

from KMFA.tools import build_v015_s12_p2_core_calculations as builder
from KMFA.tools import v015_s12_p2_core_calculations as kernel


class S12P2GovernanceTests(unittest.TestCase):
    def test_project_mirrors_are_accepted_s12_p2(self) -> None:
        for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                kernel.RUN_PHASE_ID,
                kernel.TASK_ID,
                kernel.ACCEPTANCE_ID,
                'phase_acceptance_status: "PASSED"',
                'evidence_validation_status: "PASS"',
                "stage_execution_percentage: 67",
                'decision: "CONTINUE_TO_S12_P3_ONLY"',
                "s12_p2_started: true",
                's12_p2_acceptance_status: "PASSED"',
                "s12_p3_entry_allowed: true",
                "s12_p3_started: false",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text, relative)

    def test_model_registry_mirrors_are_exact(self) -> None:
        primary = (builder.PROJECT_ROOT / "docs/governance/model_registry.yaml").read_text(encoding="utf-8")
        mirror = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        for text in (primary, mirror):
            self.assertIn("kmfa_v015_s12_p2_core_calculations", text)
            self.assertIn("MOD-KMFA-COST-001", text)
            self.assertIn("FORM-KMFA-V015-S12-P2-CORE-CALCULATIONS-001", text)
            for number in range(2196, 2212):
                self.assertIn(f"PARAM-KMFA-{number}", text)

    def test_formula_registry_has_core_calculation_contract(self) -> None:
        text = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        self.assertIn("FORM-KMFA-V015-S12-P2-CORE-CALCULATIONS-001", text)
        self.assertIn("confirmed_collection_cents", text)
        self.assertIn("INSUFFICIENT_DATA", text)
        self.assertIn(kernel.RUN_PHASE_ID, text)

    def test_parameter_registry_has_exact_new_range(self) -> None:
        path = builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        selected = [row for row in rows if row["parameter_id"] in {f"PARAM-KMFA-{number}" for number in range(2196, 2212)}]
        self.assertEqual(len(selected), 16)
        self.assertEqual({row["formula_id"] for row in selected}, {"FORM-KMFA-V015-S12-P2-CORE-CALCULATIONS-001"})
        self.assertEqual({row["model_id"] for row in selected}, {"MOD-KMFA-COST-001"})

    def test_human_governance_files_name_current_phase(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(kernel.RUN_PHASE_ID, text, relative)


if __name__ == "__main__":
    unittest.main()
