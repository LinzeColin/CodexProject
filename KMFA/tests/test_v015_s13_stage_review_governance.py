from __future__ import annotations

import csv
import unittest

from KMFA.tools import build_v015_s13_stage_review as builder


MODEL_ID = "MOD-KMFA-V015-S02-P2-TRACEABILITY-001"
FORMULA_ID = "FORM-KMFA-V015-S13-STAGE-REVIEW-001"


class V015S13StageReviewGovernanceTests(unittest.TestCase):
    def test_registry_bindings(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        formula = (governance / "formula_registry.yaml").read_text(encoding="utf-8")
        model = (governance / "model_registry.yaml").read_text(encoding="utf-8")
        metadata_model = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        with (governance / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        selected = [row for row in rows if row["parameter_id"].startswith("PARAM-KMFA-") and 2290 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2301]
        self.assertEqual(len(selected), 12)
        self.assertTrue(all(row["model_id"] == MODEL_ID and row["formula_id"] == FORMULA_ID and row["status"] == "active" for row in selected))
        for token in (
            FORMULA_ID,
            "predecessor_receipt_count == 60",
            "predecessor_public_check_count == 254",
            "cross_phase_contract_pass_count == 36",
            "live_check_pass_count == 72",
            "fixed_review_finding_count == 4",
            "open_review_finding_count == 0",
            "review_explanation_mismatch_count == 0",
            "source_binding_count == 7",
            "automatic_execution_count == 0",
        ):
            self.assertIn(token, formula)
        self.assertIn("kmfa_v015_s13_stage_review:", model)
        self.assertIn("kmfa_v015_s13_stage_review:", metadata_model)

    def test_project_mirrors_name_pending_review(self) -> None:
        for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                builder.RUN_PHASE_ID,
                builder.TASK_ID,
                builder.ACCEPTANCE_ID,
                'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                "current_phase_is_taskpack_roadmap_phase: false",
                "current_task_is_taskpack_roadmap_task: false",
                "active_formula_count: 368",
                "active_parameter_count: 1916",
                'current_parameter_range: "PARAM-KMFA-2290..2301"',
                "s13_stage_review_started: true",
                "s13_stage_review_performed: false",
                "s14_p1_entry_allowed: false",
                "s14_p1_started: false",
            ):
                self.assertIn(token, text, relative)

    def test_traceability_version_and_assurance(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        self.assertIn("REQ-KMFA-V015-S13-STAGE-REVIEW", (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8"))
        version = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        self.assertIn(f'{MODEL_ID}: "{builder.VERSION}"', version)
        self.assertIn(f'kmfa_v015_s13_stage_review: "{builder.VERSION}"', version)
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        self.assertIn("total_active_parameters: 1916", assurance)
        self.assertIn("total_active_formulas: 368", assurance)


if __name__ == "__main__":
    unittest.main()
