from __future__ import annotations

import json
import unittest
from pathlib import Path

from KMFA.tools import build_v015_s06_p3_baseline_coverage_boundary as builder


class S06P3GovernanceTests(unittest.TestCase):
    def test_public_artifacts_match_phase_contract(self) -> None:
        builder.check_outputs()
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        matrix = json.loads(builder.TASK_MATRIX_PATH.read_text(encoding="utf-8"))
        self.assertEqual(manifest["phase_id"], "V015_S06_P3_BASELINE_COVERAGE_BOUNDARY")
        self.assertEqual(manifest["stage_execution_percentage"], 100)
        self.assertEqual(manifest["stage_acceptance_status"], "PENDING")
        self.assertFalse(manifest["s06_stage_review_started"])
        self.assertFalse(manifest["empirical_coverage_complete"])
        self.assertTrue(manifest["registered_gap_satisfies_stop_condition"])
        self.assertFalse(manifest["downstream_cross_period_claim_allowed"])
        self.assertFalse(manifest["tax_normalization_allowed"])
        self.assertFalse(manifest["open_items_may_be_treated_as_resolved"])
        self.assertEqual(matrix["task_execution_complete_count"], 3)

    def test_required_human_governance_files_are_chinese_and_current(self) -> None:
        combined = "\n".join(
            Path(path).read_text(encoding="utf-8")
            for path in ("KMFA/HANDOFF.md", "KMFA/功能清单.md", "KMFA/开发记录.md", "KMFA/模型参数文件.md")
        )
        for token in (
            "S06-P3", "基准覆盖", "跨期", "FORM-KMFA-V015-S06-P3-BASELINE-COVERAGE-BOUNDARY-001",
            "PARAM-KMFA-1966..1974", "S06 Stage", "GitHub", "App",
        ):
            self.assertIn(token, combined)

    def test_current_project_governance_preserves_s06p3_under_stage_review(self) -> None:
        combined = Path("KMFA/docs/governance/project.yaml").read_text(encoding="utf-8") + Path(
            "KMFA/metadata/project/project.yaml"
        ).read_text(encoding="utf-8")
        for token in (
            'current_phase_id: "V015_S06_STAGE_REVIEW"',
            "active_formula_count: 340", "active_parameter_count: 1595",
            'current_parameter_range: "PARAM-KMFA-1975..1980"',
            's06_p3_acceptance_status: "PASSED"', "s06_stage_review_started: true",
            's06_stage_review_acceptance_status: "PENDING_FINAL_VALIDATION"',
            "github_upload_performed: false", "app_reinstall_performed: false",
        ):
            self.assertIn(token, combined)


if __name__ == "__main__":
    unittest.main()
