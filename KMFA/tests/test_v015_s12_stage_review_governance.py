from __future__ import annotations

import csv
import unittest

from KMFA.tools import build_v015_s12_stage_review as builder


MODEL_ID = "MOD-KMFA-V015-S02-P2-TRACEABILITY-001"
FORMULA_ID = "FORM-KMFA-V015-S12-STAGE-REVIEW-001"


class V015S12StageReviewGovernanceTests(unittest.TestCase):
    def test_registry_bindings(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        formula = (governance / "formula_registry.yaml").read_text(encoding="utf-8")
        model = (governance / "model_registry.yaml").read_text(encoding="utf-8")
        metadata_model = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        with (governance / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        selected = [
            row
            for row in rows
            if row["parameter_id"].startswith("PARAM-KMFA-")
            and 2228 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2239
        ]
        self.assertEqual(len(selected), 12)
        self.assertTrue(
            all(
                row["model_id"] == MODEL_ID
                and row["formula_id"] == FORMULA_ID
                and row["status"] == "active"
                for row in selected
            )
        )
        for token in (
            FORMULA_ID,
            "predecessor_receipt_count == 63",
            "predecessor_public_check_count == 174",
            "cross_phase_contract_pass_count == 36",
            "live_check_pass_count == 68",
            "fixed_review_finding_count == 4",
            "open_review_finding_count == 0",
            "review_explanation_mismatch_count == 0",
            "target_cost_conservation_delta_cents == 0",
            "excluded_candidate_leak_count == 0",
        ):
            self.assertIn(token, formula)
        self.assertIn("kmfa_v015_s12_stage_review:", model)
        self.assertIn("kmfa_v015_s12_stage_review:", metadata_model)

    def test_project_mirrors_name_the_review(self) -> None:
        for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                builder.RUN_PHASE_ID,
                builder.TASK_ID,
                builder.ACCEPTANCE_ID,
                'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                "current_phase_is_taskpack_roadmap_phase: false",
                "current_task_is_taskpack_roadmap_task: false",
                "active_formula_count: 364",
                "active_parameter_count: 1854",
                'current_parameter_range: "PARAM-KMFA-2228..2239"',
                "s12_stage_review_started: true",
                "s13_p1_started: false",
                "github_upload_performed: false",
                "app_reinstall_performed: false",
            ):
                self.assertIn(token, text, relative)

    def test_traceability_version_and_assurance(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        self.assertIn("REQ-KMFA-V015-S12-STAGE-REVIEW", (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8"))
        version = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        self.assertIn(f'{MODEL_ID}: "{builder.VERSION}"', version)
        self.assertIn(f'kmfa_v015_s12_stage_review: "{builder.VERSION}"', version)
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        self.assertIn("total_active_parameters: 1854", assurance)
        self.assertIn("total_active_formulas: 364", assurance)


if __name__ == "__main__":
    unittest.main()
