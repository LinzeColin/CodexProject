from __future__ import annotations

import csv
import unittest

from KMFA.tools import build_v015_s16_stage_review as builder


MODEL_ID = "MOD-KMFA-QUALITY-GATE-001"
FORMULA_ID = "FORM-KMFA-V015-S16-STAGE-REVIEW-001"


class V015S16StageReviewGovernanceTests(unittest.TestCase):
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
            and 2488 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2505
        ]
        self.assertEqual(len(selected), 18)
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
            "predecessor_public_check_count == 183",
            "integration_binding_count == 45",
            "public_check_count == 240",
            "fixed_review_finding_count == 3",
            "open_review_finding_count == 0",
            "visible_fault_live_region_count == 1",
            "minimum_touch_target_px >= 44",
        ):
            self.assertIn(token, formula)
        self.assertIn("kmfa_v015_s16_stage_review:", model)
        self.assertIn("kmfa_v015_s16_stage_review:", metadata_model)

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
                'current_phase_kind: "STAGE_REVIEW"',
                "current_phase_is_taskpack_roadmap_phase: false",
                "current_task_is_taskpack_roadmap_task: false",
                "active_formula_count: 380",
                "active_parameter_count: 2120",
                'current_parameter_range: "PARAM-KMFA-2488..2505"',
                "s16_stage_review_started: true",
                "s16_stage_review_performed: false",
                "s17_p1_entry_allowed: false",
                "s17_p1_started: false",
            ):
                self.assertIn(token, text, relative)

    def test_traceability_version_and_assurance(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        self.assertIn(
            "REQ-KMFA-V015-S16-STAGE-REVIEW",
            (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8"),
        )
        version = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        self.assertIn(f'{MODEL_ID}: "{builder.VERSION}"', version)
        self.assertIn(f'kmfa_v015_s16_stage_review: "{builder.VERSION}"', version)
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        self.assertIn("total_active_parameters: 2120", assurance)
        self.assertIn("total_active_formulas: 380", assurance)


if __name__ == "__main__":
    unittest.main()
