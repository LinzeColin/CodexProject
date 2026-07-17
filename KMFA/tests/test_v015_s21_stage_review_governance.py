from __future__ import annotations

import csv
import json
import unittest

from KMFA.tools import build_v015_s21_stage_review as builder


MODEL_ID = "MOD-KMFA-QUALITY-GATE-001"
FORMULA_ID = "FORM-KMFA-V015-S21-STAGE-REVIEW-001"


class Stage21ReviewGovernanceTests(unittest.TestCase):
    def test_registry_bindings(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        formula = (governance / "formula_registry.yaml").read_text(encoding="utf-8")
        model = (governance / "model_registry.yaml").read_text(encoding="utf-8")
        metadata_model = (builder.PROJECT_ROOT / "metadata/model_registry.yaml").read_text(encoding="utf-8")
        with (governance / "parameter_registry.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        selected = [row for row in rows if row["parameter_id"].startswith("PARAM-KMFA-") and 2886 <= int(row["parameter_id"].rsplit("-", 1)[-1]) <= 2905]
        self.assertEqual(len(selected), 20)
        self.assertTrue(all(row["model_id"] == MODEL_ID and row["formula_id"] == FORMULA_ID and row["status"] == "active" for row in selected))
        for token in (
            FORMULA_ID, "predecessor_receipt_count == 60", "predecessor_public_check_count == 168",
            "integration_binding_count == 44", "review_public_check_count == 44",
            "fixed_finding_count == 3", "open_finding_count == 0", "technical_audit_score == 20",
            "filter_missing_count == 0", "selected_case_mismatch_count == 0",
            "scope_leak_count == 0", "raw_external_release_count == 0",
        ):
            self.assertIn(token, formula)
        self.assertIn("kmfa_v015_s21_stage_review:", model)
        self.assertIn("kmfa_v015_s21_stage_review:", metadata_model)

    def test_project_mirrors_match_review_lifecycle(self) -> None:
        manifest = json.loads(builder.MANIFEST_PATH.read_text(encoding="utf-8"))
        passed = manifest["stage_acceptance_status"] == "PASSED"
        for relative in ("docs/governance/project.yaml", "metadata/project/project.yaml"):
            text = (builder.PROJECT_ROOT / relative).read_text(encoding="utf-8")
            for token in (
                builder.RUN_PHASE_ID, builder.TASK_ID, builder.ACCEPTANCE_ID,
                'current_phase_kind: "STAGE_REVIEW_OVERLAY"',
                "current_phase_is_taskpack_roadmap_phase: false", "current_task_is_taskpack_roadmap_task: false",
                "active_formula_count: 400", "active_parameter_count: 2520",
                'current_parameter_range: "PARAM-KMFA-2886..2905"',
                "s21_stage_review_started: true",
                f"s21_stage_review_performed: {str(passed).lower()}",
                f"s22_entry_allowed: {str(passed).lower()}",
                f"s22_p1_entry_allowed: {str(passed).lower()}",
                "s22_p1_started: false",
            ):
                self.assertIn(token, text, relative)
            if passed:
                self.assertIn(f's21_stage_review_validation_run_id: "{manifest["validation_run_id"]}"', text)
                self.assertIn(f's21_stage_review_validation_head: "{manifest["validation_head"]}"', text)

    def test_traceability_version_and_assurance(self) -> None:
        governance = builder.PROJECT_ROOT / "docs/governance"
        self.assertIn("REQ-KMFA-V015-S21-STAGE-REVIEW", (governance / "TRACEABILITY_MATRIX.csv").read_text(encoding="utf-8"))
        version = (governance / "VERSION_MATRIX.yaml").read_text(encoding="utf-8")
        self.assertIn(f'{MODEL_ID}: "{builder.VERSION}"', version)
        self.assertIn(f'kmfa_v015_s21_stage_review: "{builder.VERSION}"', version)
        assurance = (governance / "ASSURANCE_STATUS.yaml").read_text(encoding="utf-8")
        self.assertIn("total_active_parameters: 2520", assurance)
        self.assertIn("total_active_formulas: 400", assurance)


if __name__ == "__main__":
    unittest.main()
