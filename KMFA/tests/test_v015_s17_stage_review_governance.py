from __future__ import annotations

import csv
import unittest

from KMFA.tools import build_v015_s17_stage_review as builder


MODEL_ID = "MOD-KMFA-QUALITY-GATE-001"
FORMULA_ID = "FORM-KMFA-V015-S17-STAGE-REVIEW-001"


class V015S17StageReviewGovernanceTests(unittest.TestCase):
    def test_registry_bindings(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        formula = (governance / "formula_registry.yaml").read_text(encoding="utf-8")
        model = (governance / "model_registry.yaml").read_text(encoding="utf-8")
        metadata_model = (
            builder.PROJECT_ROOT / "metadata/model_registry.yaml"
        ).read_text(encoding="utf-8")
        with (governance / "parameter_registry.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle))
        selected = [
            row
            for row in rows
            if row["parameter_id"].startswith("PARAM-KMFA-")
            and 2566 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2585
        ]
        self.assertEqual(len(selected), 20)
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
            "predecessor_receipt_count == 60",
            "predecessor_public_check_count == 199",
            "integration_binding_count == 40",
            "public_check_count == 253",
            "fixed_review_finding_count == 4",
            "open_review_finding_count == 0",
            "money_difference_cents == 0",
            "scope_leak_count == 0",
        ):
            self.assertIn(token, formula)
        self.assertIn("kmfa_v015_s17_stage_review:", model)
        self.assertIn("kmfa_v015_s17_stage_review:", metadata_model)

    def test_project_mirrors_name_pending_review(self) -> None:
        for relative in (
            "docs/governance/project.yaml",
            "metadata/project/project.yaml",
        ):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                builder.RUN_PHASE_ID,
                builder.TASK_ID,
                builder.ACCEPTANCE_ID,
                'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                "current_phase_is_taskpack_roadmap_phase: false",
                "current_task_is_taskpack_roadmap_task: false",
                "active_formula_count: 384",
                "active_parameter_count: 2200",
                'current_parameter_range: "PARAM-KMFA-2566..2585"',
                "s17_stage_review_started: true",
                "s17_stage_review_performed: false",
                "s18_p1_entry_allowed: false",
                "s18_p1_started: false",
            ):
                self.assertIn(token, text, relative)

    def test_traceability_version_and_assurance(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        self.assertIn(
            "REQ-KMFA-V015-S17-STAGE-REVIEW",
            (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8"),
        )
        version = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        self.assertIn(f'{MODEL_ID}: "{builder.VERSION}"', version)
        self.assertIn(f'kmfa_v015_s17_stage_review: "{builder.VERSION}"', version)
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        self.assertIn("total_active_parameters: 2200", assurance)
        self.assertIn("total_active_formulas: 384", assurance)


if __name__ == "__main__":
    unittest.main()
