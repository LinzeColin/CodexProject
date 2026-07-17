from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s09_p1_scope_rule_modeling as builder


FORMULA_ID = "FORM-KMFA-V015-S09-P1-SCOPE-RULE-MODELING-001"
PARAMETER_IDS = [f"PARAM-KMFA-{number}" for number in range(2046, 2055)]


class ScopeRuleModelingGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.final = self.manifest["phase_acceptance_status"] == "PASSED"

    def test_project_governance_matches_phase_state(self) -> None:
        acceptance = "PASSED" if self.final else "PENDING_FINAL_VALIDATION"
        decision = "CONTINUE_TO_S09_P2_ONLY" if self.final else "REMAIN_IN_S09_P1_FINAL_VALIDATION"
        for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                "V015_S09_P1_SCOPE_RULE_MODELING",
                "KMFA-V015-S09-P1-SCOPE-RULE-MODELING-20260715",
                "ACC-KMFA-V015-S09-P1-SCOPE-RULE-MODELING",
                "active_formula_count: 349",
                "active_parameter_count: 1669",
                'current_parameter_range: "PARAM-KMFA-2046..2054"',
                f'phase_acceptance_status: "{acceptance}"',
                'stage_lifecycle_status: "IN_PROGRESS"',
                'stage_acceptance_status: "PENDING"',
                "stage_execution_percentage: 33",
                f'decision: "{decision}"',
                "s09_p1_started: true",
                f's09_p1_acceptance_status: "{acceptance}"',
                f"s09_p2_entry_allowed: {str(self.final).lower()}",
                "s09_p2_started: false",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text, f"missing {token} from {relative}")

    def test_formula_model_and_parameters_are_registered_once(self) -> None:
        formula_text = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        model_text = (builder.PROJECT_ROOT / "docs/governance/model_registry.yaml").read_text(encoding="utf-8")
        metadata_model_text = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        self.assertEqual(formula_text.count(f'formula_id: "{FORMULA_ID}"'), 1)
        self.assertEqual(model_text.count("kmfa_v015_s09_p1_scope_rule_modeling:"), 1)
        self.assertEqual(metadata_model_text.count("kmfa_v015_s09_p1_scope_rule_modeling:"), 1)
        self.assertIn(FORMULA_ID, model_text)
        self.assertIn(FORMULA_ID, metadata_model_text)
        with (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        ids = [row["parameter_id"] for row in rows]
        for parameter_id in PARAMETER_IDS:
            self.assertEqual(ids.count(parameter_id), 1)
        self.assertEqual(sum(row.get("status") == "active" for row in rows), 1669)

    def test_chinese_entry_files_explain_the_boundary(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md", "HANDOFF.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S09-P1", text)
            self.assertIn("唯一账本", text)
            self.assertIn("高风险", text)
        handoff = (builder.PROJECT_ROOT / "HANDOFF.md").read_text(encoding="utf-8")
        self.assertLess(handoff.index("S09-P1"), handoff.index("S08"))

    def test_later_work_and_release_remain_unperformed(self) -> None:
        self.assertFalse(self.manifest["s09_p2_started"])
        self.assertFalse(self.manifest["s09_p3_entry_allowed"])
        self.assertFalse(self.manifest["s09_stage_review_entry_allowed"])
        self.assertFalse(self.manifest["formal_report_generated"])
        self.assertFalse(self.manifest["github_upload_performed"])
        self.assertFalse(self.manifest["app_reinstall_performed"])
        self.assertEqual(self.manifest["raw_root_access_count"], 0)


if __name__ == "__main__":
    unittest.main()
