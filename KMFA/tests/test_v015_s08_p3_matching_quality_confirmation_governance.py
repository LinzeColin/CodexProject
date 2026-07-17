from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s08_p3_matching_quality_confirmation as builder


FORMULA_ID = "FORM-KMFA-V015-S08-P3-MATCHING-QUALITY-CONFIRMATION-001"
PARAMETER_IDS = [f"PARAM-KMFA-{number}" for number in range(2030, 2040)]


class MatchingQualityConfirmationGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        self.final = self.manifest["phase_acceptance_status"] == "PASSED"

    def test_project_governance_matches_phase_state(self) -> None:
        acceptance = "PASSED" if self.final else "PENDING_FINAL_VALIDATION"
        decision = "CONTINUE_TO_S08_STAGE_REVIEW_ONLY" if self.final else "REMAIN_IN_S08_P3_FINAL_VALIDATION"
        for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml", "docs/governance/roadmap.yaml"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                "V015_S08_P3_MATCHING_QUALITY_CONFIRMATION",
                "KMFA-V015-S08-P3-MATCHING-QUALITY-CONFIRMATION-20260715",
                "ACC-KMFA-V015-S08-P3-MATCHING-QUALITY-CONFIRMATION",
                "active_formula_count: 347",
                "active_parameter_count: 1654",
                'current_parameter_range: "PARAM-KMFA-2030..2039"',
                f'phase_acceptance_status: "{acceptance}"',
                'stage_lifecycle_status: "IN_PROGRESS"',
                'stage_acceptance_status: "PENDING"',
                "stage_execution_percentage: 100",
                f'decision: "{decision}"',
                "s08_p3_started: true",
                f's08_p3_acceptance_status: "{acceptance}"',
                f"s08_stage_review_entry_allowed: {str(self.final).lower()}",
                "s08_stage_review_started: false",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text, f"missing {token} from {relative}")

    def test_formula_model_and_parameters_are_registered_once(self) -> None:
        formula_text = (builder.PROJECT_ROOT / "docs/governance/formula_registry.yaml").read_text(encoding="utf-8")
        model_text = (builder.PROJECT_ROOT / "docs/governance/model_registry.yaml").read_text(encoding="utf-8")
        metadata_model_text = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        self.assertEqual(formula_text.count(f'formula_id: "{FORMULA_ID}"'), 1)
        self.assertIn(FORMULA_ID, model_text)
        self.assertIn(FORMULA_ID, metadata_model_text)
        with (builder.PROJECT_ROOT / "docs/governance/parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        ids = [row["parameter_id"] for row in rows]
        for parameter_id in PARAMETER_IDS:
            self.assertEqual(ids.count(parameter_id), 1)
        self.assertEqual(sum(row.get("status") == "active" for row in rows), 1654)

    def test_chinese_entry_files_describe_the_real_boundary(self) -> None:
        for relative in ("功能清单.md", "开发记录.md", "模型参数文件.md", "HANDOFF.md"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("S08-P3", text)
            self.assertIn("128", text)
            self.assertIn("6", text)
        handoff = (builder.PROJECT_ROOT / "HANDOFF.md").read_text(encoding="utf-8")
        self.assertLess(handoff.index("S08-P3"), handoff.index("S08-P2"))

    def test_stage_review_and_release_remain_unperformed(self) -> None:
        self.assertFalse(self.manifest["s08_stage_review_started"])
        self.assertFalse(self.manifest["s08_stage_review_performed"])
        self.assertFalse(self.manifest["formal_report_generated"])
        self.assertFalse(self.manifest["github_upload_performed"])
        self.assertFalse(self.manifest["app_reinstall_performed"])


if __name__ == "__main__":
    unittest.main()
